import os
import secrets
from urllib.parse import urlencode

import requests


URL_AUTORIZACAO = "https://auth.mercadolivre.com.br/authorization"
URL_TOKEN = "https://api.mercadolibre.com/oauth/token"
URL_API = "https://api.mercadolibre.com"


def criar_estado():
    """Cria um código aleatório de segurança para o processo OAuth."""
    return secrets.token_urlsafe(32)


def criar_url_autorizacao(client_id, redirect_uri, state):
    """Cria o endereço para autorizar o Luna Seller no Mercado Livre."""
    parametros = {
        "response_type": "code",
        "client_id": str(client_id),
        "redirect_uri": redirect_uri,
        "state": state,
    }

    return f"{URL_AUTORIZACAO}?{urlencode(parametros)}"


def trocar_codigo_por_token(client_id, client_secret, redirect_uri, code):
    """Troca o código de autorização por Access Token."""
    dados = {
        "grant_type": "authorization_code",
        "client_id": str(client_id),
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": redirect_uri,
    }

    resposta = requests.post(
        URL_TOKEN,
        data=dados,
        headers={
            "accept": "application/json",
            "content-type": "application/x-www-form-urlencoded",
        },
        timeout=30,
    )

    resposta.raise_for_status()
    return resposta.json()


def renovar_token(client_id, client_secret, refresh_token):
    """Obtém um novo Access Token utilizando o Refresh Token."""
    dados = {
        "grant_type": "refresh_token",
        "client_id": str(client_id),
        "client_secret": client_secret,
        "refresh_token": refresh_token,
    }

    resposta = requests.post(
        URL_TOKEN,
        data=dados,
        headers={
            "accept": "application/json",
            "content-type": "application/x-www-form-urlencoded",
        },
        timeout=30,
    )

    resposta.raise_for_status()
    return resposta.json()


def consultar_usuario(access_token):
    """Confirma qual conta do Mercado Livre está conectada."""
    resposta = requests.get(
        f"{URL_API}/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=30,
    )

    resposta.raise_for_status()
    return resposta.json()
