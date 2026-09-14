"""
Database module - SQLAlchemy with PostgreSQL support
Environment: DATABASE_URL (PostgreSQL URL) or falls back to SQLite file
"""
import os
from datetime import date
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, Text, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()

class Produto(Base):
    __tablename__ = 'produtos'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False, unique=True)
    unidade = Column(String(50), nullable=False)
    estoque_atual = Column(Float, default=0)
    
    doacoes = relationship("Doacao", back_populates="produto")
    distribuicoes = relationship("Distribuicao", back_populates="produto")

class Doacao(Base):
    __tablename__ = 'doacoes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    produto_id = Column(Integer, ForeignKey('produtos.id'), nullable=False)
    quantidade = Column(Float, nullable=False)
    doador = Column(String(200), nullable=False)
    data = Column(Date, nullable=False, default=date.today)
    observacao = Column(Text, nullable=True)
    
    produto = relationship("Produto", back_populates="doacoes")

class Distribuicao(Base):
    __tablename__ = 'distribuicoes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    produto_id = Column(Integer, ForeignKey('produtos.id'), nullable=False)
    quantidade = Column(Float, nullable=False)
    beneficiario = Column(String(200), nullable=False)
    data = Column(Date, nullable=False, default=date.today)
    observacao = Column(Text, nullable=True)
    
    produto = relationship("Produto", back_populates="distribuicoes")


# Database setup
def get_engine():
    """Create engine from DATABASE_URL or SQLite fallback"""
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        # Railway provides DATABASE_URL in format: postgres://user:pass@host:5432/db
        # SQLAlchemy needs postgresql:// scheme
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
        return create_engine(db_url)
    else:
        # Fallback to SQLite for local development
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'banca.db')
        return create_engine(f'sqlite:///{db_path}')


def get_session():
    """Get database session"""
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session(), engine


def init_db():
    """Create tables and insert initial products"""
    session, engine = get_session()
    Base.metadata.create_all(engine)
    
    # Check if products already exist
    if session.query(Produto).count() == 0:
        produtos_iniciais = [
            Produto(nome='Arroz', unidade='saco'),
            Produto(nome='Feijão', unidade='saco'),
            Produto(nome='Óleo de cozinha', unidade='garrafa'),
            Produto(nome='Leite em pó', unidade='caixa'),
            Produto(nome='Açúcar', unidade='saco'),
            Produto(nome='Farinha de trigo', unidade='saco'),
            Produto(nome='Café em pó', unidade='caixa'),
            Produto(nome='Sal', unidade='pacote'),
            Produto(nome='Macarrão', unidade='pacote'),
            Produto(nome='Cuscuz', unidade='saco'),
            Produto(nome='Gelatina', unidade='unidade'),
            Produto(nome='Chocolate em pó', unidade='caixa'),
        ]
        session.add_all(produtos_iniciais)
        session.commit()
    
    session.close()


def listar_produtos():
    """Lista todos os produtos com estoque atual"""
    session, _ = get_session()
    produtos = session.query(Produto).order_by(Produto.nome).all()
    resultados = [{'id': p.id, 'nome': p.nome, 'unidade': p.unidade, 'quantidade': p.estoque_atual} for p in produtos]
    session.close()
    return resultados


def atualizar_estoque(produto_id, quantidade):
    """Atualiza estoque (positivo = entrada, negativo = saída)"""
    session, _ = get_session()
    produto = session.query(Produto).filter_by(id=produto_id).first()
    if produto:
        produto.estoque_atual += quantidade
        session.commit()
    session.close()


def adicionar_doacao(produto_id, quantidade, doador, data, observacao=''):
    """Registra uma doação e atualiza estoque"""
    session, _ = get_session()
    
    # Inserir doação
    doacao = Doacao(
        produto_id=produto_id,
        quantidade=quantidade,
        doador=doador,
        data=data or date.today(),
        observacao=observacao
    )
    session.add(doacao)
    
    # Atualizar estoque (+)
    produto = session.query(Produto).filter_by(id=produto_id).first()
    if produto:
        produto.estoque_atual += quantidade
    
    session.commit()
    doacao_id = doacao.id
    session.close()
    return doacao_id


def adicionar_distribuicao(produto_id, quantidade, beneficiario, data, observacao=''):
    """Registra uma distribuição e reduz estoque"""
    session, _ = get_session()
    
    # Verificar estoque suficiente
    produto = session.query(Produto).filter_by(id=produto_id).first()
    
    if produto and produto.estoque_atual >= quantidade:
        # Inserir distribuição
        distribuicao = Distribuicao(
            produto_id=produto_id,
            quantidade=quantidade,
            beneficiario=beneficiario,
            data=data or date.today(),
            observacao=observacao
        )
        session.add(distribuicao)
        
        # Atualizar estoque (-)
        produto.estoque_atual -= quantidade
        
        session.commit()
        distribuicao_id = distribuicao.id
        session.close()
        return distribuicao_id, True
    else:
        session.close()
        return None, False


def listar_doacoes(limit=50):
    """Lista últimas doações"""
    session, _ = get_session()
    q = session.query(
        Doacao.id,
        Doacao.quantidade,
        Doacao.doador,
        Doacao.data,
        Doacao.observacao,
        Produto.nome.label('produto_nome'),
        Produto.unidade.label('unidade')
    ).join(Produto).order_by(Doacao.data.desc(), Doacao.id.desc()).limit(limit)
    
    resultados = [{
        'id': r.id, 'quantidade': r.quantidade, 'doador': r.doador,
        'data': r.data.isoformat() if r.data else None,
        'observacao': r.observacao,
        'nome': r.produto_nome, 'unidade': r.unidade
    } for r in q.all()]
    session.close()
    return resultados


def listar_distribuicoes(limit=50):
    """Lista últimas distribuições"""
    session, _ = get_session()
    q = session.query(
        Distribuicao.id,
        Distribuicao.quantidade,
        Distribuicao.beneficiario,
        Distribuicao.data,
        Distribuicao.observacao,
        Produto.nome.label('produto_nome'),
        Produto.unidade.label('unidade')
    ).join(Produto).order_by(Distribuicao.data.desc(), Distribuicao.id.desc()).limit(limit)
    
    resultados = [{
        'id': r.id, 'quantidade': r.quantidade, 'beneficiario': r.beneficiario,
        'data': r.data.isoformat() if r.data else None,
        'observacao': r.observacao,
        'nome': r.produto_nome, 'unidade': r.unidade
    } for r in q.all()]
    session.close()
    return resultados


def resumo_estoque():
    """Retorna resumo do estoque"""
    session, _ = get_session()
    
    total_produtos = session.query(func.count(Produto.id)).scalar() or 0
    total_estoque = session.query(func.sum(Produto.estoque_atual)).scalar() or 0
    baixo_estoque = session.query(func.count(Produto.id)).filter(
        Produto.estoque_atual > 0, Produto.estoque_atual < 5
    ).scalar() or 0
    sem_estoque = session.query(func.count(Produto.id)).filter(
        Produto.estoque_atual == 0
    ).scalar() or 0
    
    session.close()
    return {
        'total_produtos': total_produtos,
        'total_estoque': total_estoque or 0,
        'baixo_estoque': baixo_estoque,
        'sem_estoque': sem_estoque
    }