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
    help="Nesta etapa, as fotos ficam apenas para conferência no Luna Seller e não são enviadas ao Mercado Livre.",
)

if fotos:
    st.success(f"{len(fotos)} foto(s) carregada(s) para conferência.")

    nomes_fotos = [foto.name for foto in fotos]
    st.subheader("Foto principal")
    principal_nome = st.selectbox(
        "Escolha qual foto será a principal",
        options=nomes_fotos,
        index=0,
        help="Esta escolha fica apenas no Luna Seller nesta etapa. Nada é enviado ao Mercado Livre.",
    )

    st.session_state["foto_principal_nome"] = principal_nome
    st.info(f"Foto principal selecionada: {principal_nome}")

    st.subheader("Conferência das fotos")
    colunas = st.columns(3)
    for indice, foto in enumerate(fotos):
        with colunas[indice % 3]:
            legenda = f"Foto {indice + 1}: {foto.name}"
            if foto.name == principal_nome:
                legenda += " — PRINCIPAL"
            st.image(foto, caption=legenda, use_container_width=True)
else:
    st.info("Clique em 'Browse files' para escolher fotos do seu computador.")

st.divider()
st.subheader("Próximas funções desta área")
st.write("• Organizar a ordem das fotos")
st.write("• Conferir as imagens antes do envio")
st.write("• Preparar imagens profissionais para o produto")
st.write("• Adicionar o envio seguro das fotos ao Mercado Livre somente com sua confirmação")

st.warning("Modo seguro: nenhuma foto desta página é enviada automaticamente ao Mercado Livre.")
