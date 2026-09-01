import io
import os
import subprocess
import tempfile

import imageio.v2 as imageio
import imageio_ffmpeg
import numpy as np
import streamlit as st
from PIL import Image, ImageEnhance

from armazenamento import baixar_bytes, carregar_estado, configurado, restaurar_ultimo_rascunho, salvar_bytes, salvar_estado

st.set_page_config(page_title="Vídeo do produto | Luna Seller", page_icon="🎬", layout="wide")
st.title("🎬 Vídeo do produto")
st.caption("Crie um vídeo vertical natural usando as fotos já aprovadas, com movimento suave e música instrumental.")

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
    """Preenche o 9:16 inteiro com a própria foto, sem quadro interno."""
    img = Image.open(io.BytesIO(dados)).convert("RGB")
    escala = max(largura / img.width, altura / img.height)
    img = img.resize((int(img.width * escala), int(img.height * escala)), Image.Resampling.LANCZOS)
    x = max(0, (img.width - largura) // 2)
    y = max(0, (img.height - altura) // 2)
    return img.crop((x, y, x + largura, y + altura))


def criar_trilha_wav(caminho, duracao=12.0, taxa=44100):
    """Trilha instrumental ambiente simples, original e sem arquivo musical externo."""
    t = np.arange(int(duracao * taxa), dtype=np.float32) / taxa
    audio = np.zeros_like(t)
    acordes = [(261.63, 329.63, 392.00), (220.00, 261.63, 329.63), (174.61, 220.00, 261.63), (196.00, 246.94, 293.66)]
    bloco = duracao / len(acordes)
    for i, acorde in enumerate(acordes):
        ini = int(i * bloco * taxa); fim = min(len(t), int((i + 1) * bloco * taxa))
        local = np.arange(fim - ini, dtype=np.float32) / taxa
        onda = sum(np.sin(2 * np.pi * f * local) for f in acorde) / len(acorde)
        envelope = np.minimum(1.0, local / 0.35) * np.minimum(1.0, (bloco - local) / 0.45)
        audio[ini:fim] += 0.13 * onda * np.clip(envelope, 0, 1)
    # Pequeno pulso musical para dar vida sem ficar chamativo.
    for batida in np.arange(0, duracao, 0.75):
        ini = int(batida * taxa); tam = min(int(0.12 * taxa), len(audio) - ini)
        if tam > 0:
            local = np.arange(tam, dtype=np.float32) / taxa
            audio[ini:ini+tam] += 0.025 * np.sin(2*np.pi*110*local) * np.exp(-18*local)
    audio = np.clip(audio, -0.8, 0.8)
    pcm = (audio * 32767).astype(np.int16)
    import wave
    with wave.open(caminho, "wb") as wav:
        wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(taxa); wav.writeframes(pcm.tobytes())


def criar_video(fotos):
    largura, altura = 720, 1280
    fps = 20; duracao_total = 12.0; transicao = 0.35
    duracao_foto = duracao_total / len(fotos)
    frames_por_foto = int(duracao_foto * fps); frames_transicao = int(transicao * fps)
    bases = [preparar_imagem(f, largura, altura) for f in fotos]

    sem_audio = tempfile.NamedTemporaryFile(delete=False, suffix="_silent.mp4"); sem_audio.close()
    trilha = tempfile.NamedTemporaryFile(delete=False, suffix=".wav"); trilha.close()
    saida = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4"); saida.close()

    writer = imageio.get_writer(sem_audio.name, fps=fps, codec="libx264", quality=7, macro_block_size=None, ffmpeg_log_level="error", output_params=["-pix_fmt", "yuv420p", "-movflags", "+faststart"])
    try:
        for indice, base in enumerate(bases):
            proxima = bases[indice + 1] if indice + 1 < len(bases) else None
            for n in range(frames_por_foto):
                p = n / max(frames_por_foto - 1, 1)
                # Movimento cinematográfico leve: 1,2% de zoom e pequeno deslocamento lateral.
                zoom = 1.0 + 0.012 * p
                w = int(largura / zoom); h = int(altura / zoom)
                desloc = int((p - 0.5) * 10)
                cx = largura // 2 + (desloc if indice % 2 == 0 else -desloc)
                x0 = max(0, min(largura - w, cx - w // 2)); y0 = (altura - h) // 2
                frame = base.crop((x0, y0, x0+w, y0+h)).resize((largura, altura), Image.Resampling.LANCZOS)
                frame = ImageEnhance.Sharpness(frame).enhance(1.02)
                if proxima is not None and n >= frames_por_foto - frames_transicao:
                    alpha = (n - (frames_por_foto - frames_transicao)) / max(frames_transicao, 1)
                    frame = Image.blend(frame, proxima, min(1.0, alpha))
                writer.append_data(np.asarray(frame))
    finally:
        writer.close()

    criar_trilha_wav(trilha.name, duracao_total)
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    comando = [ffmpeg, "-y", "-i", sem_audio.name, "-i", trilha.name, "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", saida.name]
    subprocess.run(comando, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    with open(saida.name, "rb") as f: dados = f.read()
    for arq in (sem_audio.name, trilha.name, saida.name):
        try: os.unlink(arq)
        except OSError: pass
    return dados

restaurar_dados()
foto_salva = st.session_state.get("foto_original_anuncio")
fotos_aprovadas = st.session_state.get("fotos_aprovadas", False)
fotos = [st.session_state.get(chave) for chave in CHAVES_FOTOS if st.session_state.get(chave)]

st.success("✅ Nova versão: tela vertical preenchida + movimento natural + música instrumental suave.")
st.info("O vídeo usa somente as fotos aprovadas e uma trilha instrumental criada pelo próprio Luna Seller. Nada é enviado automaticamente ao Mercado Livre.")
if foto_salva: st.success("📷 Foto original do produto encontrada.")
if fotos_aprovadas: st.success(f"🖼️ Fotos profissionais aprovadas: {len(fotos)} encontrada(s).")
else: st.warning("Antes de criar o vídeo, confira e aprove as fotos do produto.")

st.divider(); st.subheader("🎥 Criar vídeo natural com som")
st.write("As fotos agora ocupam a tela inteira, sem moldura central. O movimento é bem discreto e o vídeo recebe uma música instrumental ambiente.")
st.markdown("**Duração:** ~12 segundos  |  **Formato:** 720 × 1280 (9:16)  |  **Zoom:** muito leve (~1%)  |  **Áudio:** música instrumental")

pode_gerar = bool(fotos_aprovadas and len(fotos) >= 2)
if st.button("🎬 Montar vídeo natural com som", type="primary", use_container_width=True, disabled=not pode_gerar):
    try:
        with st.spinner("Montando o vídeo e adicionando a música..."):
            video = criar_video(fotos)
            st.session_state["video_produto_bytes"] = video; st.session_state["video_aprovado"] = False
            rid = st.session_state.get("rascunho_id")
            if configurado() and rid:
                salvar_bytes(f"rascunhos/{rid}/{VIDEO_PATH}", video, "video/mp4")
                estado = carregar_estado(rid); estado["video_criado"] = True; estado["video_aprovado"] = False; estado["video_com_audio"] = True; salvar_estado(rid, estado)
        st.success("✅ Vídeo com som criado e salvo."); st.rerun()
    except Exception as erro:
        st.error(f"Não foi possível montar o vídeo: {erro}")

video = st.session_state.get("video_produto_bytes")
if video:
    st.divider(); st.subheader("👀 Revisar vídeo")
    st.video(video, format="video/mp4", width=420)
    st.caption("Assista com o volume ligado e confira o enquadramento, as transições e a música.")
    aprovado = st.checkbox("Conferi o vídeo e aprovo esta versão.", value=bool(st.session_state.get("video_aprovado", False)))
    st.session_state["video_aprovado"] = bool(aprovado)
    rid = st.session_state.get("rascunho_id")
    if configurado() and rid:
        try:
            estado = carregar_estado(rid); estado["video_criado"] = True; estado["video_aprovado"] = bool(aprovado); salvar_estado(rid, estado)
        except Exception: pass
    if aprovado: st.success("✅ Vídeo aprovado para a próxima etapa.")

st.divider(); st.warning("O vídeo só seguirá adiante depois da sua aprovação.")
