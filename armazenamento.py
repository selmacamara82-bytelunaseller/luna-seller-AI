import hashlib
import json
import os
import urllib.error
import urllib.parse
import urllib.request

import streamlit as st


def _segredo(nome, padrao=""):
    try:
        return st.secrets.get(nome, padrao) or os.getenv(nome, padrao)
    except Exception:
        return os.getenv(nome, padrao)


def configurado():
    return bool(_segredo("SUPABASE_URL") and _segredo("SUPABASE_SERVICE_ROLE_KEY"))


def _url_base():
    url = (_segredo("SUPABASE_URL") or "").rstrip("/")
    if not url:
        raise RuntimeError("O endereço do armazenamento ainda não está configurado.")
    return url


def _chave():
    chave = _segredo("SUPABASE_SERVICE_ROLE_KEY")
    if not chave:
        raise RuntimeError("A chave do armazenamento ainda não está configurada.")
    return chave


def _bucket():
    return _segredo("SUPABASE_BUCKET", "luna-seller-fotos")


def _headers(content_type=None, upsert=False):
    chave = _chave()
    headers = {"apikey": chave, "Authorization": f"Bearer {chave}"}
    if content_type:
        headers["Content-Type"] = content_type
    if upsert:
        headers["x-upsert"] = "true"
    return headers


def _objeto_url(caminho):
    bucket = urllib.parse.quote(_bucket().strip().strip("/"), safe="")
    caminho_limpo = str(caminho).strip().strip("/")
    caminho_codificado = urllib.parse.quote(caminho_limpo, safe="/")
    return f"{_url_base()}/storage/v1/object/{bucket}/{caminho_codificado}"


def criar_id_rascunho(dados):
    return hashlib.sha256(dados).hexdigest()[:24]


def salvar_bytes(caminho, dados, content_type="application/octet-stream"):
    req = urllib.request.Request(_objeto_url(caminho), data=dados, headers=_headers(content_type, upsert=True), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resposta:
            resposta.read()
    except urllib.error.HTTPError as erro:
        detalhe = erro.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Supabase respondeu {erro.code}: {detalhe or erro.reason}") from erro


def baixar_bytes(caminho):
    req = urllib.request.Request(_objeto_url(caminho), headers=_headers(), method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as resposta:
            return resposta.read()
    except urllib.error.HTTPError as erro:
        if erro.code == 404:
            return None
        detalhe = erro.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Supabase respondeu {erro.code}: {detalhe or erro.reason}") from erro
    except Exception:
        return None


def salvar_json(caminho, dados):
    salvar_bytes(caminho, json.dumps(dados, ensure_ascii=False).encode("utf-8"), "application/json")


def baixar_json(caminho):
    dados = baixar_bytes(caminho)
    if not dados:
        return None
    try:
        return json.loads(dados.decode("utf-8"))
    except Exception:
        return None


def salvar_ultimo_rascunho(rascunho_id):
    salvar_json("controle/ultimo_rascunho.json", {"rascunho_id": rascunho_id})


def ultimo_rascunho_id():
    dados = baixar_json("controle/ultimo_rascunho.json") or {}
    return dados.get("rascunho_id")


def salvar_estado(rascunho_id, estado):
    salvar_json(f"rascunhos/{rascunho_id}/estado.json", estado)
    salvar_ultimo_rascunho(rascunho_id)


def carregar_estado(rascunho_id):
    return baixar_json(f"rascunhos/{rascunho_id}/estado.json") or {}


def salvar_original(rascunho_id, dados, nome="produto.jpg", tipo="image/jpeg"):
    extensao = os.path.splitext(nome)[1].lower() or ".jpg"
    caminho = f"rascunhos/{rascunho_id}/original{extensao}"
    salvar_bytes(caminho, dados, tipo)
    return caminho


def restaurar_ultimo_rascunho():
    rascunho_id = ultimo_rascunho_id()
    if not rascunho_id:
        return None
    estado = carregar_estado(rascunho_id)
    caminho = estado.get("original_caminho")
    original = baixar_bytes(caminho) if caminho else None
    if not original:
        return None
    return {"rascunho_id": rascunho_id, "estado": estado, "original": original}
