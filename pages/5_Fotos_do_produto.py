import streamlit as st

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

if "fotos_preparadas" not in st.session_state:
    st.session_state["fotos_preparadas"] = []

fotos_preparadas = st.session_state["fotos_preparadas"]

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
    st.warning("Ainda não há imagens preparadas nesta sessão.")
    st.info("No fluxo final, a foto original será fornecida no início do anúncio e a IA preparará o conjunto antes desta etapa de revisão.")
    st.stop()

st.success(f"{len(fotos_preparadas)} imagem(ns) pronta(s) para revisão.")

nomes_fotos = [getattr(foto, "name", f"Foto {i + 1}") for i, foto in enumerate(fotos_preparadas)]

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
    tipo = ["Foto principal", "Detalhes", "Benefícios", "Produto em uso", "Informativa"]
    titulo_tipo = tipo[i] if i < len(tipo) else "Imagem adicional"
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
