import base64
import json
import re

import streamlit as st
from openai import OpenAI
from armazenamento import baixar_bytes, carregar_estado, configurado, restaurar_ultimo_rascunho, salvar_estado

st.set_page_config(page_title="Revisar anúncio completo | Luna Seller", page_icon="✅", layout="wide")
st.title("✅ Revisar anúncio completo")
st.caption("Última conferência antes de preparar qualquer envio ao Mercado Livre.")

CHAVES_FOTOS = ["foto_principal_ia", "foto_detalhes_ia", "foto_beneficios_ia", "foto_uso_ia", "foto_informativa_ia"]
ARQUIVOS_FOTOS = {chave: f"{i+1}_{chave}.png" for i, chave in enumerate(CHAVES_FOTOS)}


def resultado_valido(valor):
    return isinstance(valor, dict) and bool(valor.get("titulo") or valor.get("descricao"))


def limpar_json(texto):
    texto = texto.strip()
    if texto.startswith("```"):
        texto = re.sub(r"^```(?:json)?\s*", "", texto)
        texto = re.sub(r"\s*```$", "", texto)
    return json.loads(texto)


def restaurar():
    if not configurado(): return
    try:
        salvo = restaurar_ultimo_rascunho()
        rid_atual = st.session_state.get("rascunho_id")
        if salvo:
            rid_salvo = salvo["rascunho_id"]
            estado_salvo = salvo.get("estado", {}) or {}
            if not rid_atual or rid_atual != rid_salvo:
                st.session_state["rascunho_id"] = rid_salvo
                rid_atual = rid_salvo
            st.session_state["foto_original_anuncio"] = {
                "bytes": salvo["original"],
                "nome": estado_salvo.get("original_nome", "produto.jpg"),
                "tipo": estado_salvo.get("original_tipo", "image/jpeg"),
            }
            if resultado_valido(estado_salvo.get("resultado")):
                st.session_state["modo_vendedora_resultado"] = estado_salvo["resultado"]
        if not rid_atual: return
        estado = carregar_estado(rid_atual) or {}
        if resultado_valido(estado.get("resultado")):
            st.session_state["modo_vendedora_resultado"] = estado["resultado"]
        st.session_state["fotos_aprovadas"] = bool(estado.get("fotos_aprovadas", False))
        st.session_state["video_aprovado"] = bool(estado.get("video_aprovado", False))
        for chave in CHAVES_FOTOS:
            if not st.session_state.get(chave):
                dados = baixar_bytes(f"rascunhos/{rid_atual}/fotos/{ARQUIVOS_FOTOS[chave]}")
                if dados: st.session_state[chave] = dados
        if not st.session_state.get("video_produto_bytes"):
            video = baixar_bytes(f"rascunhos/{rid_atual}/video/video_produto.mp4")
            if video: st.session_state["video_produto_bytes"] = video
    except Exception as erro:
        st.warning(f"Não foi possível recuperar todos os dados agora: {erro}")


def recuperar_texto_com_ia():
    foto = st.session_state.get("foto_original_anuncio") or {}
    dados = foto.get("bytes") if isinstance(foto, dict) else None
    if not dados:
        raise RuntimeError("A foto original não foi encontrada.")
    api_key = st.secrets.get("OPENAI_API_KEY", "")
    if not api_key:
        raise RuntimeError("A chave da IA não está configurada.")
    mime = foto.get("tipo") or "image/jpeg"
    data_url = f"data:{mime};base64,{base64.b64encode(dados).decode('utf-8')}"
    prompt = """
Você é o assistente do Luna Seller para Mercado Livre Brasil.
O texto deste anúncio foi perdido, mas a foto original do produto foi preservada.
Reconstrua SOMENTE o texto do anúncio de forma profissional e segura.
Não invente capacidade, marca, modelo, medidas, material, desempenho, certificações ou acessórios que não estejam claramente visíveis.
O título deve ter no máximo 60 caracteres, começar pelo nome do produto e usar apenas atributos confirmados pela imagem.
A descrição deve ser objetiva, clara, em português do Brasil e sem alegações não comprovadas.
Gere também palavras-chave úteis.
Retorne SOMENTE JSON válido neste formato:
{"titulo":"","descricao":"","palavras_chave":[]}
"""
    resposta = OpenAI(api_key=api_key).responses.create(
        model="gpt-5-mini",
        store=False,
        input=[{"role":"user","content":[{"type":"input_text","text":prompt},{"type":"input_image","image_url":data_url}]}],
    )
    recuperado = limpar_json(resposta.output_text)
    atual = st.session_state.get("modo_vendedora_resultado")
    if not isinstance(atual, dict): atual = {}
    atual.update(recuperado)
    st.session_state["modo_vendedora_resultado"] = atual
    rid = st.session_state.get("rascunho_id")
    if configurado() and rid:
        estado = carregar_estado(rid) or {}
        estado["resultado"] = atual
        salvar_estado(rid, estado)


restaurar()
resultado = st.session_state.get("modo_vendedora_resultado") or {}
fotos = [st.session_state.get(c) for c in CHAVES_FOTOS if st.session_state.get(c)]
video = st.session_state.get("video_produto_bytes")
fotos_ok = bool(st.session_state.get("fotos_aprovadas"))
video_ok = bool(st.session_state.get("video_aprovado"))

titulo = resultado.get("titulo", "") if isinstance(resultado, dict) else ""
descricao = resultado.get("descricao", "") if isinstance(resultado, dict) else ""
palavras = resultado.get("palavras_chave", []) if isinstance(resultado, dict) else []
if isinstance(palavras, list): palavras_texto = ", ".join(str(x) for x in palavras)
else: palavras_texto = str(palavras or "")

st.subheader("📝 Texto do anúncio")
if not titulo or not descricao:
    st.warning("O texto antigo do anúncio não ficou salvo, mas a foto original, as fotos profissionais e o vídeo estão seguros.")
    if st.button("✨ Recuperar título e descrição", type="primary", use_container_width=True):
        try:
            with st.spinner("Recuperando o texto a partir da foto original..."):
                recuperar_texto_com_ia()
            st.success("✅ Texto recuperado e salvo.")
            st.rerun()
        except Exception as erro:
            st.error(f"Não foi possível recuperar o texto: {erro}")

st.markdown("**Título**")
st.write(titulo or "Título ainda não encontrado.")
st.markdown("**Descrição**")
st.text_area("Descrição preparada", value=descricao, height=220, disabled=True, label_visibility="collapsed")
if palavras_texto:
    st.markdown("**Palavras-chave**")
    st.write(palavras_texto)

st.divider(); st.subheader("🖼️ Fotos")
if fotos:
    colunas = st.columns(min(5, len(fotos)))
    for i, foto in enumerate(fotos):
        with colunas[i % len(colunas)]: st.image(foto, caption=f"Foto {i+1}", use_container_width=True)
if fotos_ok: st.success("✅ Fotos aprovadas.")
else: st.warning("As fotos ainda não estão aprovadas.")

st.divider(); st.subheader("🎬 Vídeo")
if video: st.video(video, format="video/mp4", width=360)
else: st.warning("Vídeo ainda não encontrado.")
if video_ok: st.success("✅ Vídeo aprovado.")
else: st.warning("O vídeo ainda não está aprovado.")

st.divider(); st.subheader("🔎 Conferência final")
pronto = bool(titulo and descricao and fotos_ok and video_ok and len(fotos) > 0 and video)
if pronto:
    st.success("Tudo que já preparamos está reunido nesta tela.")
    confirmar = st.checkbox("Conferi título, descrição, fotos e vídeo e aprovo o anúncio completo.")
    if confirmar:
        rid = st.session_state.get("rascunho_id")
        if configurado() and rid:
            try:
                estado = carregar_estado(rid); estado["anuncio_completo_aprovado"] = True; salvar_estado(rid, estado)
            except Exception as erro:
                st.warning(f"A aprovação ficou nesta sessão, mas não foi possível salvá-la agora: {erro}")
        st.session_state["anuncio_completo_aprovado"] = True
        st.success("✅ Anúncio completo aprovado. Nenhum envio foi feito ao Mercado Livre.")
        st.info("Próxima etapa: preencher os dados obrigatórios do Mercado Livre, como categoria, preço, estoque e condições de venda, antes de preparar a publicação.")
else:
    st.warning("Ainda falta algum item aprovado antes da conferência final.")

st.warning("🔒 Esta página é somente para revisão. Nada é publicado automaticamente.")
