import json
import streamlit as st
from mercado_livre import consultar_anuncio

st.set_page_config(page_title="Detalhes do anúncio | Luna Seller AI", page_icon="🌙", layout="wide")

st.title("🌙 Detalhes do anúncio")
st.caption("Consulta para revisão. Esta tela não publica nem altera nada no Mercado Livre.")

anuncio = st.session_state.get("anuncio_selecionado")
access_token = st.session_state.get("ml_access_token")

if not anuncio:
    st.warning("Nenhum anúncio foi selecionado nesta sessão. Volte à página principal, carregue seus anúncios e selecione um anúncio.")
    st.stop()

if not access_token:
    st.warning("A conexão com o Mercado Livre não está ativa nesta sessão. Volte à página principal e conecte sua conta.")
    st.stop()

item_id = anuncio.get("id")

try:
    detalhes = consultar_anuncio(access_token, item_id)
except Exception as erro:
    st.error(f"Não foi possível carregar os detalhes do anúncio: {erro}")
    st.stop()

st.success("Dados do anúncio carregados com sucesso.")

st.subheader("Resumo")
st.write(f"**Título:** {detalhes.get('title', anuncio.get('titulo', 'Título não encontrado'))}")
st.write(f"**Código Mercado Livre:** {detalhes.get('id', item_id)}")
st.write(f"**Status:** {detalhes.get('status', 'Não informado')}")
st.write(f"**Preço:** {detalhes.get('price', 'Não informado')}")
st.write(f"**Quantidade disponível:** {detalhes.get('available_quantity', 'Não informada')}")
st.write(f"**Quantidade vendida:** {detalhes.get('sold_quantity', 'Não informada')}")
st.write(f"**Condição:** {detalhes.get('condition', 'Não informada')}")

permalink = detalhes.get("permalink")
if permalink:
    st.link_button("Abrir anúncio no Mercado Livre", permalink, use_container_width=True)

st.divider()
st.subheader("Dados principais para revisão")

col1, col2 = st.columns(2)
with col1:
    st.text_input("Título atual", value=str(detalhes.get("title", "")), disabled=True)
    st.text_input("Preço atual", value=str(detalhes.get("price", "")), disabled=True)
    st.text_input("Quantidade disponível", value=str(detalhes.get("available_quantity", "")), disabled=True)
with col2:
    st.text_input("Categoria", value=str(detalhes.get("category_id", "")), disabled=True)
    st.text_input("Tipo de anúncio", value=str(detalhes.get("listing_type_id", "")), disabled=True)
    st.text_input("Condição", value=str(detalhes.get("condition", "")), disabled=True)

atributos = detalhes.get("attributes", []) or []
if atributos:
    st.subheader("Atributos do produto")
    linhas = []
    for atributo in atributos:
        nome = atributo.get("name") or atributo.get("id") or "Atributo"
        valor = atributo.get("value_name")
        if valor in (None, ""):
            valor = atributo.get("value_id") or "Não informado"
        linhas.append({"Atributo": nome, "Valor": valor})
    st.dataframe(linhas, use_container_width=True, hide_index=True)

variacoes = detalhes.get("variations", []) or []
if variacoes:
    st.subheader("Variações")
    for i, variacao in enumerate(variacoes, start=1):
        with st.expander(f"Variação {i}"):
            st.write(f"**ID:** {variacao.get('id', 'Não informado')}")
            st.write(f"**Preço:** {variacao.get('price', detalhes.get('price', 'Não informado'))}")
            st.write(f"**Quantidade disponível:** {variacao.get('available_quantity', 'Não informada')}")
            combinacoes = variacao.get("attribute_combinations", []) or []
            for combinacao in combinacoes:
                st.write(f"**{combinacao.get('name', combinacao.get('id', 'Atributo'))}:** {combinacao.get('value_name', combinacao.get('value_id', 'Não informado'))}")

st.divider()
st.info("Modo seguro: os dados acima são apenas para consulta. Nenhuma alteração foi enviada ao Mercado Livre.")

with st.expander("Ver resposta técnica completa"):
    st.code(json.dumps(detalhes, ensure_ascii=False, indent=2), language="json")
