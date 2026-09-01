import streamlit as st
from armazenamento import baixar_bytes, carregar_estado, configurado, restaurar_ultimo_rascunho, salvar_estado

st.set_page_config(page_title="Revisar anúncio completo | Luna Seller", page_icon="✅", layout="wide")
st.title("✅ Revisar anúncio completo")
st.caption("Última conferência antes de preparar qualquer envio ao Mercado Livre.")

CHAVES_FOTOS = ["foto_principal_ia", "foto_detalhes_ia", "foto_beneficios_ia", "foto_uso_ia", "foto_informativa_ia"]
ARQUIVOS_FOTOS = {chave: f"{i+1}_{chave}.png" for i, chave in enumerate(CHAVES_FOTOS)}


def restaurar():
    if not configurado(): return
    try:
        if not st.session_state.get("rascunho_id"):
            salvo = restaurar_ultimo_rascunho()
            if salvo:
                st.session_state["rascunho_id"] = salvo["rascunho_id"]
                if salvo["estado"].get("resultado"):
                    st.session_state["modo_vendedora_resultado"] = salvo["estado"]["resultado"]
        rid = st.session_state.get("rascunho_id")
        if not rid: return
        estado = carregar_estado(rid)
        if estado.get("resultado") and not st.session_state.get("modo_vendedora_resultado"):
            st.session_state["modo_vendedora_resultado"] = estado["resultado"]
        st.session_state["fotos_aprovadas"] = bool(estado.get("fotos_aprovadas", False))
        st.session_state["video_aprovado"] = bool(estado.get("video_aprovado", False))
        for chave in CHAVES_FOTOS:
            if not st.session_state.get(chave):
                dados = baixar_bytes(f"rascunhos/{rid}/fotos/{ARQUIVOS_FOTOS[chave]}")
                if dados: st.session_state[chave] = dados
        if not st.session_state.get("video_produto_bytes"):
            video = baixar_bytes(f"rascunhos/{rid}/video/video_produto.mp4")
            if video: st.session_state["video_produto_bytes"] = video
    except Exception as erro:
        st.warning(f"Não foi possível recuperar todos os dados agora: {erro}")

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
