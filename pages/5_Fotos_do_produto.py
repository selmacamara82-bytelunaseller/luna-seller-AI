import streamlit as st

st.set_page_config(
    page_title="Revisar fotos | Luna Seller",
    page_icon="🌙",
    layout="wide"
)

st.title("🌙 Revisar fotos do produto")
st.caption(
    "Confira as imagens preparadas para o anúncio antes do envio ao Mercado Livre."
)

anuncio = st.session_state.get("anuncio_selecionado", {})
anuncio_id = anuncio.get("id", "")

if anuncio_id:
    st.info(f"Anúncio selecionado: {anuncio_id}")

st.subheader("📸 Imagens preparadas")

st.write(
    "Nesta etapa, as imagens do produto já deverão estar preparadas pelo "
    "Luna Seller para sua revisão."
)

if "fotos_preparadas" not in st.session_state:
    st.session_state["fotos_preparadas"] = []

fotos_preparadas = st.session_state["fotos_preparadas"]

with st.expander("🧪 Adicionar imagens manualmente para teste"):
    fotos_teste = st.file_uploader(
        "Escolha uma ou mais imagens",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True,
        help="Esta opção é temporária e serve apenas para testar a área de revisão."
    )

    if fotos_teste:
        st.session_state["fotos_preparadas"] = fotos_teste
        fotos_preparadas = fotos_teste

if not fotos_preparadas:
    st.warning(
        "Ainda não há imagens preparadas nesta sessão. "
        "No fluxo final, a IA do Luna Seller preparará as imagens "
        "antes de chegar a esta etapa."
    )

    st.info(
        "Enquanto estamos construindo essa função, abra a área de teste acima "
        "para carregar imagens e conferir como ficará a revisão."
    )

    st.stop()

st.success(
    f"{len(fotos_preparadas)} imagem(ns) pronta(s) para revisão."
)

st.divider()

st.subheader("⭐ Escolher foto principal")

nomes_fotos = [
    getattr(foto, "name", f"Foto {i + 1}")
    for i, foto in enumerate(fotos_preparadas)
]

foto_principal = st.selectbox(
    "Selecione a imagem que será a capa do anúncio",
    options=range(len(fotos_preparadas)),
    format_func=lambda i: nomes_fotos[i]
)

st.session_state["foto_principal_indice"] = foto_principal

st.info(
    f"Foto principal selecionada: {nomes_fotos[foto_principal]}"
)

st.divider()

st.subheader("🖼️ Conferência das imagens")

for i, foto in enumerate(fotos_preparadas):
    st.markdown(f"### Foto {i + 1}")

    st.image(
        foto,
        caption=nomes_fotos[i],
        width=420
    )

    if i == foto_principal:
        st.success("⭐ Esta será a foto principal do anúncio.")

    st.divider()

st.subheader("🤖 Próxima etapa da IA")

st.write(
    "Quando conectarmos a geração automática, o Luna Seller poderá usar "
    "a foto original do produto para preparar versões profissionais, "
    "como capa em fundo branco, benefícios, detalhes e imagem de uso."
)

st.warning(
    "Nenhuma imagem desta página é enviada automaticamente ao Mercado Livre."
)

confirmar_fotos = st.checkbox(
    "Conferi as imagens e aprovo este conjunto de fotos."
)

if confirmar_fotos:
    st.session_state["fotos_aprovadas"] = True
    st.success("Fotos aprovadas para a próxima etapa.")
else:
    st.session_state["fotos_aprovadas"] = False
