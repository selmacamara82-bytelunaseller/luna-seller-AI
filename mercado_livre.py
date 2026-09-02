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
    parametros = {"response_type": "code", "client_id": str(client_id), "redirect_uri": redirect_uri, "state": state}
    return f"{URL_AUTORIZACAO}?{urlencode(parametros)}"


def trocar_codigo_por_token(client_id, client_secret, redirect_uri, code):
    dados = {"grant_type": "authorization_code", "client_id": str(client_id), "client_secret": client_secret, "code": code, "redirect_uri": redirect_uri}
    resposta = requests.post(URL_TOKEN, data=dados, headers={"accept": "application/json", "content-type": "application/x-www-form-urlencoded"}, timeout=30)
    resposta.raise_for_status(); return resposta.json()


def renovar_token(client_id, client_secret, refresh_token):
    dados = {"grant_type": "refresh_token", "client_id": str(client_id), "client_secret": client_secret, "refresh_token": refresh_token}
    resposta = requests.post(URL_TOKEN, data=dados, headers={"accept": "application/json", "content-type": "application/x-www-form-urlencoded"}, timeout=30)
    resposta.raise_for_status(); return resposta.json()


def consultar_usuario(access_token):
    resposta = requests.get(f"{URL_API}/users/me", headers={"Authorization": f"Bearer {access_token}"}, timeout=30)
    resposta.raise_for_status(); return resposta.json()


def listar_anuncios(access_token, user_id, limite=100):
    resposta = requests.get(f"{URL_API}/users/{user_id}/items/search", headers={"Authorization": f"Bearer {access_token}"}, params={"limit": limite}, timeout=30)
    resposta.raise_for_status(); return resposta.json()


def consultar_anuncio(access_token, item_id):
    resposta = requests.get(f"{URL_API}/items/{item_id}", headers={"Authorization": f"Bearer {access_token}"}, timeout=30)
    resposta.raise_for_status(); return resposta.json()


def prever_categorias(access_token, titulo, limite=3, site_id="MLB"):
    """Consulta o preditor oficial de categorias do Mercado Livre Brasil."""
    resposta = requests.get(
        f"{URL_API}/sites/{site_id}/domain_discovery/search",
        headers={"Authorization": f"Bearer {access_token}"},
        params={"q": str(titulo).strip(), "limit": limite}, timeout=30,
    )
    resposta.raise_for_status(); return resposta.json()


def consultar_categoria(access_token, category_id):
    resposta = requests.get(f"{URL_API}/categories/{category_id}", headers={"Authorization": f"Bearer {access_token}"}, timeout=30)
    resposta.raise_for_status(); return resposta.json()


def consultar_atributos_categoria(access_token, category_id):
    """Obtém a ficha de atributos e regras da categoria selecionada."""
    resposta = requests.get(f"{URL_API}/categories/{category_id}/attributes", headers={"Authorization": f"Bearer {access_token}"}, timeout=30)
    resposta.raise_for_status(); return resposta.json()


def atualizar_item(access_token, item_id, campos):
    if not isinstance(campos, dict) or not campos: raise ValueError("Nenhum campo foi informado para atualização.")
    resposta = requests.put(f"{URL_API}/items/{item_id}", json=campos, headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json", "Accept": "application/json"}, timeout=30)
    resposta.raise_for_status(); return resposta.json()


def atualizar_descricao(access_token, item_id, descricao):
    texto = str(descricao or "").strip()
    if not texto: raise ValueError("A descrição não pode ficar vazia.")
    resposta = requests.put(f"{URL_API}/items/{item_id}/description", params={"api_version": 2}, json={"plain_text": texto}, headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json", "Accept": "application/json"}, timeout=30)
    resposta.raise_for_status(); return resposta.json()
