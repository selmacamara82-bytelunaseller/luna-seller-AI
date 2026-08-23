import streamlit as st

st.set_page_config(page_title="Selecionar anúncio | Luna Seller AI", page_icon="🌙", layout="wide")

st.title("🌙 Selecionar anúncio")
st.caption("Escolha um anúncio já carregado no Luna Seller. Esta tela não publica nem altera nada no Mercado Livre.")

lista_anuncios = st.session_state.get("lista_anuncios", [])

if not lista_anuncios:
    st.info("Primeiro volte à página principal e clique em 'Carregar meus anúncios'. Depois retorne a esta página.")
    st.stop()

opcoes = {f"{item.get('titulo', 'Título não encontrado')} — {item.get('id', '')}": item for item in lista_anuncios}

rotulo_selecionado = st.selectbox(
    "Selecione um anúncio",
    options=list(opcoes.keys()),
    index=0,
)

anuncio_selecionado = opcoes[rotulo_selecionado]
st.session_state["anuncio_selecionado"] = anuncio_selecionado

st.success("Anúncio selecionado para trabalhar no Luna Seller.")
st.write(f"**Título:** {anuncio_selecionado.get('titulo', 'Título não encontrado')}")
st.write(f"**Código Mercado Livre:** {anuncio_selecionado.get('id', '')}")

st.divider()
st.info("Por enquanto esta etapa apenas seleciona o anúncio. Nenhuma alteração é enviada ao Mercado Livre.")
