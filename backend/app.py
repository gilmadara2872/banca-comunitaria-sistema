from flask import Flask, request, jsonify, send_from_directory, session, redirect, render_template
from flask_cors import CORS
import os
import sys
from datetime import date

# Adicionar backend ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import (
    init_db, listar_produtos, adicionar_doacao, adicionar_distribuicao,
    listar_doacoes, listar_distribuicoes, resumo_estoque, atualizar_estoque,
    excluir_doacao, excluir_distribuicao, limpar_movimentacoes
)
from auth import conferir_senha, autenticado, exigir_login, _senha_configurada

frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'frontend')
app = Flask(__name__, static_folder=frontend_dir, static_url_path='')
CORS(app)

# A sessao do login precisa de uma chave secreta. Sem ela, Flask
# recusa o login. Em dev cai num valor fixo; em producao (Railway)
# a variavel SESSION_SECRET tem que estar definida.
app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET') or 'dev-banca-comunitaria-chave-temporaria'
app.config['PERMANENT_SESSION_LIFETIME'] = 60 * 60 * 12  # 12 horas

# ============================================
# LOGIN
# ============================================

@app.route('/login', methods=['GET'])
def login():
    """Tela de login"""
    if autenticado():
        return redirect('/')
    return send_from_directory(frontend_dir, 'login.html')


@app.route('/login', methods=['POST'])
def fazer_login():
    """Confere a senha e abre a sessao"""
    dados = request.get_json(silent=True) or request.form
    senha = (dados.get('senha') or '').strip()

    if not senha:
        return jsonify({'sucesso': False, 'erro': 'Digite a senha'}), 400

    if not _senha_configurada():
        return jsonify({
            'sucesso': False,
            'erro': 'Login ainda não configurado no servidor (falta ADMIN_SENHA)'
        }), 503

    if not conferir_senha(senha):
        return jsonify({'sucesso': False, 'erro': 'Senha incorreta'}), 401

    session.clear()
    session['logado'] = True
    session.permanent = True
    return jsonify({'sucesso': True})


@app.route('/logout', methods=['POST', 'GET'])
def logout():
    """Encerra a sessao"""
    session.clear()
    return redirect('/login')


@app.route('/api/sessao', methods=['GET'])
def status_sessao():
    """Diz ao frontend se ainda esta logado"""
    return jsonify({
        'autenticado': autenticado(),
        'login_configurado': bool(_senha_configurada())
    })


# Inicializar banco no início
init_db()

# ============================================
# ROTAS DE ESTOQUE
# ============================================

@app.route('/api/estoque', methods=['GET'])
@exigir_login
def get_estoque():
    """Retorna todos os produtos com estoque atual"""
    try:
        produtos = listar_produtos()
        resumo = resumo_estoque()
        return jsonify({
            'produtos': produtos,
            'resumo': resumo
        })
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

# ============================================
# ROTAS DE DOAÇÕES
# ============================================

@app.route('/api/doacoes', methods=['GET'])
@exigir_login
def get_doacoes():
    """Retorna lista de doações recentes"""
    try:
        limit = request.args.get('limit', 50, type=int)
        doacoes = listar_doacoes(limit)
        return jsonify({'doacoes': doacoes})
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@app.route('/api/doacoes', methods=['POST'])
@exigir_login
def post_doacao():
    """Registra uma nova doação"""
    try:
        dados = request.get_json()
        
        produto_id = dados.get('produto_id')
        quantidade = float(dados.get('quantidade', 0))
        doador = dados.get('doador', '').strip()
        data = dados.get('data', date.today().isoformat())
        observacao = dados.get('observacao', '').strip()
        
        if not produto_id:
            return jsonify({'erro': 'Produto é obrigatório'}), 400
        if quantidade <= 0:
            return jsonify({'erro': 'Quantidade deve ser maior que zero'}), 400
        if not doador:
            return jsonify({'erro': 'Doador é obrigatório'}), 400
        
        doacao_id = adicionar_doacao(produto_id, quantidade, doador, data, observacao)
        return jsonify({
            'sucesso': True,
            'mensagem': 'Doação registrada com sucesso',
            'id': doacao_id
        }), 201
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

# ============================================
# ROTAS DE DISTRIBUIÇÕES
# ============================================

@app.route('/api/distribuicoes', methods=['GET'])
@exigir_login
def get_distribuicoes():
    """Retorna lista de distribuições recentes"""
    try:
        limit = request.args.get('limit', 50, type=int)
        distribuicoes = listar_distribuicoes(limit)
        return jsonify({'distribuicoes': distribuicoes})
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@app.route('/api/distribuicoes', methods=['POST'])
@exigir_login
def post_distribuicao():
    """Registra uma nova distribuição"""
    try:
        dados = request.get_json()
        
        produto_id = dados.get('produto_id')
        quantidade = float(dados.get('quantidade', 0))
        beneficiario = dados.get('beneficiario', '').strip()
        data = dados.get('data', date.today().isoformat())
        observacao = dados.get('observacao', '').strip()
        
        if not produto_id:
            return jsonify({'erro': 'Produto é obrigatório'}), 400
        if quantidade <= 0:
            return jsonify({'erro': 'Quantidade deve ser maior que zero'}), 400
        if not beneficiario:
            return jsonify({'erro': 'Beneficiário é obrigatório'}), 400
        
        distribuicao_id, sucesso = adicionar_distribuicao(
            produto_id, quantidade, beneficiario, data, observacao
        )
        
        if sucesso:
            return jsonify({
                'sucesso': True,
                'mensagem': 'Distribuição registrada com sucesso',
                'id': distribuicao_id
            }), 201
        else:
            return jsonify({
                'sucesso': False,
                'erro': 'Estoque insuficiente para esta distribuição'
            }), 400
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

# ============================================
# EXCLUSÃO DE REGISTROS
# Cada exclusão desfaz o efeito no estoque: apagar uma doação
# desconta o que ela somou, apagar uma distribuição devolve.
# Sem isso os números do estoque ficam mentindo.
# ============================================

@app.route('/api/doacoes/<int:doacao_id>', methods=['DELETE'])
@exigir_login
def delete_doacao(doacao_id):
    """Apaga uma doação e desfaz o efeito no estoque"""
    try:
        if not excluir_doacao(doacao_id):
            return jsonify({'sucesso': False, 'erro': 'Doação não encontrada'}), 404
        return jsonify({'sucesso': True, 'mensagem': 'Doação excluída'})
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)}), 500


@app.route('/api/distribuicoes/<int:distribuicao_id>', methods=['DELETE'])
@exigir_login
def delete_distribuicao(distribuicao_id):
    """Apaga uma distribuição e desfaz o efeito no estoque"""
    try:
        if not excluir_distribuicao(distribuicao_id):
            return jsonify({'sucesso': False, 'erro': 'Distribuição não encontrada'}), 404
        return jsonify({'sucesso': True, 'mensagem': 'Distribuição excluída'})
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)}), 500


@app.route('/api/limpar', methods=['POST'])
@exigir_login
def limpar():
    """Apaga todas as movimentações e zera o estoque"""
    try:
        dados = request.get_json(silent=True) or {}

        # Apagar tudo e irreversivel: exige confirmacao explicita.
        if dados.get('confirmar') != 'APAGAR TUDO':
            return jsonify({
                'sucesso': False,
                'erro': 'É preciso confirmar o apagamento'
            }), 400

        apagadas = limpar_movimentacoes()
        return jsonify({
            'sucesso': True,
            'mensagem': 'Movimentações apagadas e estoque zerado',
            'apagadas': apagadas
        })
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)}), 500


# ============================================
# ROTA DE RESUMO
# ============================================

@app.route('/api/resumo', methods=['GET'])
@exigir_login
def get_resumo():
    """Retorna resumo do estoque"""
    try:
        resumo = resumo_estoque()
        return jsonify(resumo)
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

# ============================================
# ROTA PRINCIPAL (servir frontend)
# ============================================

@app.route('/')
@exigir_login
def index():
    """Serve o frontend"""
    return send_from_directory('../frontend', 'index.html')

@app.route('/stats')
@exigir_login
def stats():
    """Serve a página de estatísticas"""
    return send_from_directory(app.static_folder, 'stats.html')

@app.route('/dados')
@exigir_login
def dados_endpoint():
    """Retorna dados para o dashboard"""
    try:
        from db import listar_produtos, listar_doacoes, listar_distribuicoes
        return jsonify({
            'produtos': listar_produtos(),
            'doacoes': listar_doacoes(100),
            'distribuicoes': listar_distribuicoes(100)
        })
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)