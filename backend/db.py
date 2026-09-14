import sqlite3
import os
from datetime import date

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'banca.db')

def get_db():
    """Retorna conexão com banco de dados"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    """Cria tabelas iniciais se não existirem"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Tabela de produtos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE,
            unidade TEXT NOT NULL,
            estoque_atual REAL DEFAULT 0
        )
    ''')
    
    # Tabela de doações
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS doacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER NOT NULL,
            quantidade REAL NOT NULL,
            doador TEXT NOT NULL,
            data DATE NOT NULL,
            observacao TEXT,
            FOREIGN KEY (produto_id) REFERENCES produtos(id)
        )
    ''')
    
    # Tabela de distribuições
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS distribuicoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER NOT NULL,
            quantidade REAL NOT NULL,
            beneficiario TEXT NOT NULL,
            data DATE NOT NULL,
            observacao TEXT,
            FOREIGN KEY (produto_id) REFERENCES produtos(id)
        )
    ''')
    
    conn.commit()
    
    # Inserir produtos iniciais se não existirem
    produtos_iniciais = [
        ('Arroz', 'saco', 0),
        ('Feijão', 'saco', 0),
        ('Óleo de cozinha', 'garrafa', 0),
        ('Leite em pó', 'caixa', 0),
        ('Açúcar', 'saco', 0),
        ('Farinha de trigo', 'saco', 0),
        ('Café em pó', 'caixa', 0),
        ('Sal', 'pacote', 0),
        ('Macarrão', 'pacote', 0),
        ('Cuscuz', 'saco', 0),
        ('Gelatina', 'unidade', 0),
        ('Chocolate em pó', 'caixa', 0),
    ]
    
    for nome, unidade, estoque in produtos_iniciais:
        try:
            cursor.execute('INSERT OR IGNORE INTO produtos (nome, unidade, estoque_atual) VALUES (?, ?, ?)',
                          (nome, unidade, estoque))
        except sqlite3.IntegrityError:
            pass
    
    conn.commit()
    conn.close()

def listar_produtos():
    """Lista todos os produtos com estoque atual"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, nome, unidade, estoque_atual FROM produtos ORDER BY nome')
    resultados = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return resultados

def atualizar_estoque(produto_id, quantidade):
    """Atualiza estoque (positivo = entrada, negativo = saída)"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE produtos SET estoque_atual = estoque_atual + ? WHERE id = ?',
                  (quantidade, produto_id))
    conn.commit()
    conn.close()

def adicionar_doacao(produto_id, quantidade, doador, data, observacao=''):
    """Registra uma doação e atualiza estoque"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Inserir doação
    cursor.execute('''
        INSERT INTO doacoes (produto_id, quantidade, doador, data, observacao)
        VALUES (?, ?, ?, ?, ?)
    ''', (produto_id, quantidade, doador, data, observacao))
    
    # Atualizar estoque (+)
    cursor.execute('UPDATE produtos SET estoque_atual = estoque_atual + ? WHERE id = ?',
                  (quantidade, produto_id))
    
    conn.commit()
    doacao_id = cursor.lastrowid
    conn.close()
    return doacao_id

def adicionar_distribuicao(produto_id, quantidade, beneficiario, data, observacao=''):
    """Registra uma distribuição e reduz estoque"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Verificar estoque suficiente
    cursor.execute('SELECT estoque_atual FROM produtos WHERE id = ?', (produto_id,))
    resultado = cursor.fetchone()
    
    if resultado and resultado['estoque_atual'] >= quantidade:
        # Inserir distribuição
        cursor.execute('''
            INSERT INTO distribuicoes (produto_id, quantidade, beneficiario, data, observacao)
            VALUES (?, ?, ?, ?, ?)
        ''', (produto_id, quantidade, beneficiario, data, observacao))
        
        # Atualizar estoque (-)
        cursor.execute('UPDATE produtos SET estoque_atual = estoque_atual - ? WHERE id = ?',
                      (quantidade, produto_id))
        
        conn.commit()
        distribuicao_id = cursor.lastrowid
        conn.close()
        return distribuicao_id, True
    else:
        conn.close()
        return None, False

def listar_doacoes(limit=50):
    """Lista últimas doações"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT d.id, d.quantidade, d.doador, d.data, d.observacao,
               p.nome as produto_nome, p.unidade
        FROM doacoes d
        JOIN produtos p ON d.produto_id = p.id
        ORDER BY d.data DESC, d.id DESC
        LIMIT ?
    ''', (limit,))
    resultados = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return resultados

def listar_distribuicoes(limit=50):
    """Lista últimas distribuições"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT d.id, d.quantidade, d.beneficiario, d.data, d.observacao,
               p.nome as produto_nome, p.unidade
        FROM distribuicoes d
        JOIN produtos p ON d.produto_id = p.id
        ORDER BY d.data DESC, d.id DESC
        LIMIT ?
    ''', (limit,))
    resultados = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return resultados

def resumo_estoque():
    """Retorna resumo do estoque (total de itens, produtos com estoque baixo)"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) as total FROM produtos')
    total_produtos = cursor.fetchone()['total']
    
    cursor.execute('SELECT SUM(estoque_atual) as total_estoque FROM produtos')
    total_estoque = cursor.fetchone()['total_estoque'] or 0
    
    cursor.execute('SELECT COUNT(*) as baixo FROM produtos WHERE estoque_atual > 0 AND estoque_atual < 5')
    baixo_estoque = cursor.fetchone()['baixo']
    
    cursor.execute('SELECT COUNT(*) as zero FROM produtos WHERE estoque_atual = 0')
    sem_estoque = cursor.fetchone()['zero']
    
    conn.close()
    return {
        'total_produtos': total_produtos,
        'total_estoque': total_estoque,
        'baixo_estoque': baixo_estoque,
        'sem_estoque': sem_estoque
    }
