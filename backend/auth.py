"""
Autenticacao - controle de acesso do sistema.

Usa uma senha unica, compartilhada pela equipe. Quem sabe a senha
entra; quem nao sabe, nao mexe no banco.

A senha fica no ambiente (ADMIN_SENHA no Railway) e nunca e
gravada no codigo. Em ausencia dela, o sistema avisa no log e
sobe protegido: nenhuma senha padrao fraca.
"""
import os
import hmac
import hashlib

from flask import session, redirect, url_for, jsonify, request


def _senha_configurada():
    """Senha vem do ambiente. Nao existe valor padrao no codigo."""
    return os.environ.get('ADMIN_SENHA', '').strip()


def hashing(senha):
    return hashlib.sha256(senha.encode('utf-8')).hexdigest()


def conferir_senha(tentativa):
    """Compara a senha com a do ambiente, em tempo constante."""
    senha_certa = _senha_configurada()
    if not senha_certa:
        return False
    return hmac.compare_digest(hashing(tentativa or ''), hashing(senha_certa))


def autenticado():
    return bool(session.get('logado'))


def exigir_login(view):
    """Protege uma rota: sem sessao, manda para o login.

    Navegador recebe redirect para a tela de login.
    Chamadas de API (fetch/XHR) recebem 401 em JSON, para o
    frontend poder reagir em vez de receber HTML.
    """
    def wrapper(*args, **kwargs):
        if autenticado():
            return view(*args, **kwargs)

        eh_api = (
            request.path.startswith('/api/')
            or request.accept_mimetypes.best == 'application/json'
            or request.is_json
        )

        if eh_api:
            return jsonify({'erro': 'Não autenticado'}), 401

        return redirect(url_for('login'))

    wrapper.__name__ = view.__name__
    wrapper.__doc__ = view.__doc__
    return wrapper
