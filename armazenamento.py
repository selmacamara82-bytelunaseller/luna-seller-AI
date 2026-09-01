import hashlib
import json
import os

import streamlit as st
from supabase import create_client


def _segredo(nome, padrao=""):
    try:
        return st.secrets.get(nome, padrao) or os.getenv(nome, padrao)
    except Exception:
        return os.getenv(nome, padrao)


def configurado():
    return bool(_segredo("SUPABASE_URL") and _segredo("SUPABASE_SERVICE_ROLE_KEY"))


def _cliente():
    url = _segredo("SUPABASE_URL")
    chave = _segredo("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not chave:
        raise RuntimeError("O armazenamento seguro ainda não está configurado.")
    return create_client(url, chave)


def _bucket():
    return _segredo("SUPABASE_BUCKET", "luna-seller-fotos")


def criar_id_rascunho(dados):
    return hashlib.sha256(dados).hexdigest()[:24]


def salvar_bytes(caminho, dados, content_type="application/octet-stream"):
    storage = _cliente().storage.from_(_bucket())
    opcoes = {"content-type": content_type, "upsert": "true"}
    try:
        storage.upload(caminho, dados, opcoes)
    except Exception:
        storage.update(caminho, dados, opcoes)


def baixar_bytes(caminho):
    try:
        return _cliente().storage.from_(_bucket()).download(caminho)
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
