import base64
import io

import streamlit as st
from openai import OpenAI

st.set_page_config(
    page_title="Revisar fotos | Luna Seller",
    page_icon="🌙",
    layout="wide"
)

st.title("🌙 Revisar fotos do produto")
st.caption("Confira as imagens preparadas para o anúncio antes do envio ao Mercado Livre.")

anuncio = st.session_state.get("anuncio_selecionado", {})
anuncio_id = anuncio.get("id", "")

if anuncio_id:
    st.info(f"Anúncio selecionado: {anuncio_id}")

st.subheader("📸 Padrão de imagens do Luna Seller")
st.write("O conjunto padrão terá até 5 imagens profissionais para revisão:")

st.markdown("**1. Foto principal — capa do anúncio**")
st.write("Produto bem destacado, fundo branco e limpo, sem textos, selos, bordas ou objetos decorativos.")
st.caption("A IA deve preservar fielmente formato, cor, quantidade de peças e características visuais do produto original.")

st.markdown("**2. Foto de detalhes do produto**")
st.write("Destaca acabamento, componentes, materiais e detalhes importantes do produto.")

st.markdown("**3. Foto de benefícios**")
st.write("Apresenta os principais benefícios com textos curtos e profissionais em português.")

st.markdown("**4. Foto do produto em uso**")
st.write("Mostra o produto em um ambiente ou situação realista e adequada à sua finalidade.")

st.markdown("**5. Foto informativa**")
st.write("Reúne informações úteis confirmadas no anúncio, sem inventar medidas, potência, capacidade, certificações ou outras especificações.")

st.divider()
st.subheader("🖼️ Imagens preparadas para revisão")

foto_original = None
foto_salva = st.session_state.get("foto_original_anuncio")

if isinstance(foto_salva, dict) and foto_salva.get("bytes"):
    foto_original = foto_salva["bytes"]
else:
    for chave, valor in st.session_state.items():
        if str(chave).startswith("foto_produto_") and valor is not None:
            foto_original = valor.getvalue() if hasattr(valor, "getvalue") else valor
            break

if foto_original is not None:
    st.success("✅ Foto original do anúncio encontrada automaticamente.")
    st.caption("Você não precisa carregar novamente a foto que colocou no Modo Vendedora.")
    with st.expander("Ver foto original"):
        st.image(foto_original, caption="Foto original do produto", width=420)
else:
    st.info("A foto original ainda não foi encontrada nesta sessão. Envie a foto no Modo Vendedora para iniciar um anúncio novo.")

if "fotos_preparadas" not in st.session_state:
    st.session_state["fotos_preparadas"] = []

st.divider()
st.subheader("✨ Criar foto principal profissional")
st.write("O Luna Seller usa a foto original como referência e prepara a capa do anúncio.")
st.caption("Fundo branco, produto em destaque, sem textos e sem inventar características.")

if foto_original is not None:
    if st.button("✨ Gerar foto principal", type="primary", use_container_width=True):
        try:
            api_key = st.secrets.get("OPENAI_API_KEY")
            if not api_key:
                st.error("A chave da OpenAI não foi encontrada nas configurações do aplicativo.")
            else:
                client = OpenAI(api_key=api_key)
                nome = "produto.jpg"
                if isinstance(foto_salva, dict):
                    nome = foto_salva.get("nome") or nome

                arquivo = io.BytesIO(foto_original)
                arquivo.name = nome

                with st.spinner("Preparando a foto principal profissional..."):
                    resultado = client.images.edit(
                        model="gpt-image-1.5",
                        image=arquivo,
                        prompt=(
                            "Crie uma foto principal profissional para anúncio de marketplace usando exatamente o produto da imagem de referência. "
                            "Preserve fielmente o formato, proporções, cor, acabamento, peças, tampa, acessórios e todos os detalhes visuais reais do produto. "
                            "Não invente, remova ou altere componentes. Não adicione marca, logotipo, texto, selo, borda, medidas, objetos decorativos ou acessórios novos. "
                            "Use fundo branco puro e limpo, iluminação de estúdio realista, produto centralizado, inteiro, nítido e bem destacado, com sombra suave e natural. "
                            "A imagem deve parecer uma fotografia comercial profissional e adequada para capa de anúncio no Mercado Livre."
                        ),
                        size="1024x1024",
                        quality="medium",
                        input_fidelity="high",
                    )

                imagem_b64 = resultado.data[0].b64_json
                imagem_bytes = base64.b64decode(imagem_b64)
                st.session_state["foto_principal_ia"] = imagem_bytes
                st.session_state["fotos_preparadas"] = [imagem_bytes]
                st.success("✅ Foto principal criada. Confira o resultado abaixo antes de aprovar.")
        except Exception as erro:
            st.error(f"Não foi possível gerar a foto agora: {erro}")
else:
    st.warning("Envie primeiro uma foto no Modo Vendedora.")

fotos_preparadas = st.session_state["fotos_preparadas"]

if st.session_state.get("foto_principal_ia"):
    st.markdown("### ⭐ Foto principal gerada pela IA")
    st.image(st.session_state["foto_principal_ia"], caption="Foto principal profissional", width=520)
    st.caption("Confira se o produto permaneceu fiel ao original. Nada será enviado ao Mercado Livre sem sua aprovação.")

with st.expander("🧪 Adicionar imagens manualmente para teste"):
    fotos_teste = st.file_uploader(
        "Escolha uma ou mais imagens",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True,
        help="Opção temporária apenas para testar a área de revisão."
    )
    if fotos_teste:
        st.session_state["fotos_preparadas"] = fotos_teste
        fotos_preparadas = fotos_teste

if not fotos_preparadas:
    st.warning("Ainda não há imagens profissionais preparadas nesta sessão.")
    if foto_original is not None:
        st.info("A foto original já está vinculada. Clique em Gerar foto principal para preparar a primeira imagem profissional.")
    st.stop()

st.success(f"{len(fotos_preparadas)} imagem(ns) pronta(s) para revisão.")

nomes_fotos = []
for i, foto in enumerate(fotos_preparadas):
    if isinstance(foto, (bytes, bytearray)):
        nomes_fotos.append("Foto principal profissional" if i == 0 else f"Foto {i + 1}")
    else:
        nomes_fotos.append(getattr(foto, "name", f"Foto {i + 1}"))

st.divider()
st.subheader("⭐ Foto principal")

foto_principal = st.selectbox(
    "Selecione a imagem que será a capa do anúncio",
    options=range(len(fotos_preparadas)),
    format_func=lambda i: nomes_fotos[i]
)
st.session_state["foto_principal_indice"] = foto_principal
st.info(f"Foto principal selecionada: {nomes_fotos[foto_principal]}")
st.caption("Regra da capa: fundo branco, produto em destaque e nenhuma escrita sobre a imagem.")

st.divider()
st.subheader("🔎 Conferência das imagens")

for i, foto in enumerate(fotos_preparadas):
    tipos = ["Foto principal", "Detalhes", "Benefícios", "Produto em uso", "Informativa"]
    titulo_tipo = tipos[i] if i < len(tipos) else "Imagem adicional"
    st.markdown(f"### {i + 1}. {titulo_tipo}")
    st.image(foto, caption=nomes_fotos[i], width=420)
    if i == foto_principal:
        st.success("⭐ Selecionada como foto principal.")
    st.divider()

st.warning("Nenhuma imagem desta página é enviada automaticamente ao Mercado Livre.")

confirmar_fotos = st.checkbox("Conferi as imagens e aprovo este conjunto de fotos.")

if confirmar_fotos:
    st.session_state["fotos_aprovadas"] = True
    st.success("Fotos aprovadas para a próxima etapa.")
else:
    st.session_state["fotos_aprovadas"] = False
