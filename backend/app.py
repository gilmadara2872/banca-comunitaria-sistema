from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import sys
from datetime import date

# Adicionar backend ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import (
    init_db, listar_produtos, adicionar_doacao, adicionar_distribuicao,
    listar_doacoes, listar_distribuicoes, resumo_estoque, atualizar_estoque
)

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

# Inicializar banco no início
init_db()

# ============================================
# ROTAS DE ESTOQUE
# ============================================

@app.route('/api/estoque', methods=['GET'])
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
def get_doacoes():
    """Retorna lista de doações recentes"""
    try:
        limit = request.args.get('limit', 50, type=int)
        doacoes = listar_doacoes(limit)
        return jsonify({'doacoes': doacoes})
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@app.route('/api/doacoes', methods=['POST'])
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
def get_distribuicoes():
    """Retorna lista de distribuições recentes"""
    try:
        limit = request.args.get('limit', 50, type=int)
        distribuicoes = listar_distribuicoes(limit)
        return jsonify({'distribuicoes': distribuicoes})
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@app.route('/api/distribuicoes', methods=['POST'])
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
# ROTA DE RESUMO
# ============================================

@app.route('/api/resumo', methods=['GET'])
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
def index():
    """Serve o frontend"""
    return send_from_directory('../frontend', 'index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
