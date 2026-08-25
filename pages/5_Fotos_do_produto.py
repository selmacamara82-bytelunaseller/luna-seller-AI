import streamlit as st

st.set_page_config(page_title="Fotos do produto | Luna Seller", page_icon="🌙", layout="wide")

st.title("🌙 Fotos do produto")
st.caption("Organize e confira as imagens do anúncio dentro do Luna Seller antes de qualquer envio ao Mercado Livre.")

anuncio = st.session_state.get("anuncio_selecionado", {})
anuncio_id = anuncio.get("id", "")

if anuncio_id:
    st.info(f"Anúncio selecionado: {anuncio_id}")
else:
    st.warning("Nenhum anúncio está selecionado nesta sessão. Você ainda pode testar o envio de fotos abaixo.")

st.subheader("Adicionar fotos")
fotos = st.file_uploader(
    "Escolha uma ou mais fotos do produto",
    type=["jpg", "jpeg", "png", "webp"],
    accept_multiple_files=True,
    help="Nesta primeira etapa, as fotos ficam apenas para conferência no Luna Seller e não são enviadas ao Mercado Livre.",
)

if fotos:
    st.success(f"{len(fotos)} foto(s) carregada(s) para conferência.")
    st.caption("Você poderá revisar cada imagem antes de qualquer envio futuro ao anúncio.")

    colunas = st.columns(3)
    for indice, foto in enumerate(fotos):
        with colunas[indice % 3]:
            st.image(foto, caption=f"Foto {indice + 1}: {foto.name}", use_container_width=True)
else:
    st.info("Clique em 'Browse files' para escolher fotos do seu computador.")

st.divider()
st.subheader("Próximas funções desta área")
st.write("• Escolher a foto principal do anúncio")
st.write("• Organizar a ordem das fotos")
st.write("• Conferir as imagens antes do envio")
st.write("• Preparar imagens profissionais para o produto")
st.write("• Adicionar o envio seguro das fotos ao Mercado Livre somente com sua confirmação")

st.warning("Modo seguro: nenhuma foto desta página é enviada automaticamente ao Mercado Livre.")
