import io
import os
import tempfile

import imageio.v2 as imageio
import numpy as np
import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter

from armazenamento import baixar_bytes, carregar_estado, configurado, restaurar_ultimo_rascunho, salvar_bytes, salvar_estado

st.set_page_config(page_title="Vídeo do produto | Luna Seller", page_icon="🎬", layout="wide")
st.title("🎬 Vídeo do produto")
st.caption("Monte um vídeo vertical profissional usando as fotos já aprovadas, sem custo de geração de vídeo por IA.")

CHAVES_FOTOS = ["foto_principal_ia", "foto_detalhes_ia", "foto_beneficios_ia", "foto_uso_ia", "foto_informativa_ia"]
ARQUIVOS_FOTOS = {chave: f"{i+1}_{chave}.png" for i, chave in enumerate(CHAVES_FOTOS)}
VIDEO_PATH = "video/video_produto.mp4"


def restaurar_dados():
    if not configurado(): return
    try:
        if not st.session_state.get("rascunho_id"):
            salvo = restaurar_ultimo_rascunho()
            if salvo:
                st.session_state["rascunho_id"] = salvo["rascunho_id"]
                estado = salvo["estado"]
                st.session_state["foto_original_anuncio"] = {"bytes": salvo["original"], "nome": estado.get("original_nome", "produto.jpg"), "tipo": estado.get("original_tipo", "image/jpeg")}
        rid = st.session_state.get("rascunho_id")
        if rid:
            estado = carregar_estado(rid)
            st.session_state["fotos_aprovadas"] = bool(estado.get("fotos_aprovadas", False))
            st.session_state["video_aprovado"] = bool(estado.get("video_aprovado", False))
            for chave in CHAVES_FOTOS:
                if not st.session_state.get(chave):
                    dados = baixar_bytes(f"rascunhos/{rid}/fotos/{ARQUIVOS_FOTOS[chave]}")
                    if dados: st.session_state[chave] = dados
            if not st.session_state.get("video_produto_bytes"):
                video = baixar_bytes(f"rascunhos/{rid}/{VIDEO_PATH}")
                if video: st.session_state["video_produto_bytes"] = video
    except Exception as erro:
        st.warning(f"Não foi possível recuperar todos os arquivos agora: {erro}")


def preparar_imagem(dados, largura=720, altura=1280):
    original = Image.open(io.BytesIO(dados)).convert("RGB")
    # Fundo vertical desfocado preenche 9:16 sem cortar o produto.
    escala_fundo = max(largura / original.width, altura / original.height)
    fundo = original.resize((int(original.width * escala_fundo), int(original.height * escala_fundo)), Image.Resampling.LANCZOS)
    x = (fundo.width - largura) // 2; y = (fundo.height - altura) // 2
    fundo = fundo.crop((x, y, x + largura, y + altura)).filter(ImageFilter.GaussianBlur(22))
    fundo = ImageEnhance.Brightness(fundo).enhance(0.82)
    # Foto completa por cima: sem recortar laterais nem aproximar demais.
    margem = 54
    escala_frente = min((largura - 2*margem) / original.width, (altura - 2*margem) / original.height)
    frente = original.resize((int(original.width * escala_frente), int(original.height * escala_frente)), Image.Resampling.LANCZOS)
    base = fundo.copy()
    px = (largura - frente.width) // 2; py = (altura - frente.height) // 2
    base.paste(frente, (px, py))
    return base


def criar_video(fotos):
    largura, altura = 720, 1280
    fps = 20; duracao_total = 12.0; transicao = 0.25
    duracao_foto = duracao_total / len(fotos)
    frames_por_foto = int(duracao_foto * fps); frames_transicao = int(transicao * fps)
    bases = [preparar_imagem(f, largura, altura) for f in fotos]
    arquivo_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4"); arquivo_temp.close()
    writer = imageio.get_writer(arquivo_temp.name, fps=fps, codec="libx264", quality=7, macro_block_size=None, ffmpeg_log_level="error", output_params=["-pix_fmt", "yuv420p", "-movflags", "+faststart"])
    try:
        for indice, base in enumerate(bases):
            proxima = bases[indice + 1] if indice + 1 < len(bases) else None
            for n in range(frames_por_foto):
                progresso = n / max(frames_por_foto - 1, 1)
                # Movimento bem discreto: no máximo 2% de zoom.
                zoom = 1.0 + (0.02 * progresso if indice % 2 == 0 else 0.02 * (1-progresso))
                w = int(largura / zoom); h = int(altura / zoom)
                x0 = (largura - w) // 2; y0 = (altura - h) // 2
                frame_img = base.crop((x0, y0, x0+w, y0+h)).resize((largura, altura), Image.Resampling.LANCZOS)
                frame_img = ImageEnhance.Sharpness(frame_img).enhance(1.03)
                if proxima is not None and n >= frames_por_foto - frames_transicao:
                    alpha = (n - (frames_por_foto - frames_transicao)) / max(frames_transicao, 1)
                    frame_img = Image.blend(frame_img, proxima, min(1.0, alpha))
                writer.append_data(np.asarray(frame_img))
    finally:
        writer.close()
    with open(arquivo_temp.name, "rb") as f: dados = f.read()
    os.unlink(arquivo_temp.name)
    return dados

restaurar_dados()
foto_salva = st.session_state.get("foto_original_anuncio")
fotos_aprovadas = st.session_state.get("fotos_aprovadas", False)
fotos = [st.session_state.get(chave) for chave in CHAVES_FOTOS if st.session_state.get(chave)]

st.success("✅ Vídeo realmente vertical 9:16, com enquadramento completo do produto e zoom suave.")
st.info("Este teste usa somente as fotos aprovadas. Não gera novas imagens por IA e não envia nada automaticamente ao Mercado Livre.")
if foto_salva: st.success("📷 Foto original do produto encontrada.")
else: st.warning("A foto original não foi encontrada.")
if fotos_aprovadas: st.success(f"🖼️ Fotos profissionais aprovadas: {len(fotos)} encontrada(s).")
else: st.warning("Antes de criar o vídeo, confira e aprove as fotos do produto.")

st.divider(); st.subheader("🎥 Criar vídeo com as fotos")
st.write("O Luna Seller manterá cada foto inteira dentro do quadro vertical, usando fundo desfocado para preencher a tela, movimento discreto e transições suaves.")
st.markdown("**Duração:** ~12 segundos  |  **Formato do arquivo:** 720 × 1280 (9:16)  |  **Zoom:** leve (máx. 2%)")
st.caption("🔊 Nesta versão o vídeo ainda fica sem som. Depois de aprovarmos o enquadramento, adicionaremos uma trilha de fundo segura.")

pode_gerar = bool(fotos_aprovadas and len(fotos) >= 2)
if st.button("🎬 Montar nova versão vertical", type="primary", use_container_width=True, disabled=not pode_gerar):
    try:
        with st.spinner("Montando a nova versão vertical..."):
            video = criar_video(fotos)
            st.session_state["video_produto_bytes"] = video; st.session_state["video_aprovado"] = False
            rid = st.session_state.get("rascunho_id")
            if configurado() and rid:
                salvar_bytes(f"rascunhos/{rid}/{VIDEO_PATH}", video, "video/mp4")
                estado = carregar_estado(rid); estado["video_criado"] = True; estado["video_aprovado"] = False; salvar_estado(rid, estado)
        st.success("✅ Nova versão vertical criada e salva."); st.rerun()
    except Exception as erro:
        st.error(f"Não foi possível montar o vídeo: {erro}")

video = st.session_state.get("video_produto_bytes")
if video:
    st.divider(); st.subheader("👀 Revisar vídeo")
    # largura limitada para a prévia também parecer vertical na tela do computador.
    st.video(video, format="video/mp4", width=420)
    st.caption("Confira principalmente se o produto aparece inteiro e se o zoom ficou confortável.")
    aprovado = st.checkbox("Conferi o vídeo e aprovo esta versão.", value=bool(st.session_state.get("video_aprovado", False)))
    st.session_state["video_aprovado"] = bool(aprovado)
    rid = st.session_state.get("rascunho_id")
    if configurado() and rid:
        try:
            estado = carregar_estado(rid); estado["video_criado"] = True; estado["video_aprovado"] = bool(aprovado); salvar_estado(rid, estado)
        except Exception: pass
    if aprovado: st.success("✅ Vídeo aprovado para a próxima etapa.")

st.divider(); st.warning("O vídeo só seguirá adiante depois da sua aprovação.")
