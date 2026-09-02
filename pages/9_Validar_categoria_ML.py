import streamlit as st
from armazenamento import carregar_estado, configurado, restaurar_ultimo_rascunho, salvar_estado
from mercado_livre import prever_categorias, consultar_categoria, consultar_atributos_categoria

st.set_page_config(page_title="Validar categoria ML | Luna Seller", page_icon="🔎", layout="centered")
st.title("🔎 Validar categoria no Mercado Livre")
st.caption("O Luna Seller consulta o Mercado Livre para sugerir a categoria oficial. Nada é publicado nesta etapa.")


def restaurar():
    if not configurado(): return {}, None
    if not st.session_state.get("rascunho_id"):
        salvo = restaurar_ultimo_rascunho()
        if salvo: st.session_state["rascunho_id"] = salvo["rascunho_id"]
    rid = st.session_state.get("rascunho_id")
    return (carregar_estado(rid) or {}, rid) if rid else ({}, None)

estado, rid = restaurar()
dados = estado.get("dados_publicacao", {})
resultado = estado.get("resultado", {})

titulo = str(resultado.get("titulo", "") or dados.get("categoria", "")).strip()
st.write("**Produto usado na busca:**", titulo or "Não encontrado")

access_token = st.session_state.get("ml_access_token") or st.session_state.get("access_token")
if not access_token:
    st.warning("⚠️ A conexão atual com o Mercado Livre não está ativa nesta sessão. Volte à página principal e clique em ‘Conectar ao Mercado Livre’. Depois retorne aqui.")
    st.stop()

if not dados.get("dados_publicacao_confirmados") and not estado.get("dados_publicacao_confirmados"):
    st.warning("Salve primeiro os Dados para publicação.")
    st.stop()

if st.button("🔎 Consultar categoria oficial", type="primary", use_container_width=True):
    try:
        with st.spinner("Consultando o Mercado Livre..."):
            sugestoes = prever_categorias(access_token, titulo, limite=5)
        st.session_state["ml_sugestoes_categoria"] = sugestoes if isinstance(sugestoes, list) else []
    except Exception as erro:
        st.error(f"Não foi possível consultar a categoria agora: {erro}")

sugestoes = st.session_state.get("ml_sugestoes_categoria", [])
if sugestoes:
    opcoes = []
    mapa = {}
    for item in sugestoes:
        cat_id = item.get("category_id") or item.get("id")
        nome = item.get("category_name") or item.get("name") or cat_id
        dominio = item.get("domain_name") or ""
        if cat_id:
            rotulo = f"{nome} — {dominio}" if dominio else str(nome)
            opcoes.append(rotulo); mapa[rotulo] = cat_id
    if opcoes:
        escolha = st.radio("Confira e escolha a categoria que corresponde ao produto:", opcoes)
        if st.button("✅ Confirmar esta categoria", use_container_width=True):
            category_id = mapa[escolha]
            try:
                with st.spinner("Buscando atributos exigidos..."):
                    categoria = consultar_categoria(access_token, category_id)
                    atributos = consultar_atributos_categoria(access_token, category_id)
                obrigatorios = []
                recomendados = []
                for atributo in atributos if isinstance(atributos, list) else []:
                    tags = atributo.get("tags", {}) or {}
                    item = {"id": atributo.get("id"), "nome": atributo.get("name"), "tipo": atributo.get("value_type"), "valores": atributo.get("values", [])[:50]}
                    if tags.get("required") or tags.get("catalog_required"):
                        obrigatorios.append(item)
                    elif tags.get("recommended"):
                        recomendados.append(item)
                validacao = {"category_id": category_id, "category_name": categoria.get("name", escolha), "path_from_root": categoria.get("path_from_root", []), "atributos_obrigatorios": obrigatorios, "atributos_recomendados": recomendados}
                novo = carregar_estado(rid) or estado
                novo["categoria_ml"] = validacao
                novo["categoria_ml_confirmada"] = True
                salvar_estado(rid, novo)
                st.session_state["categoria_ml"] = validacao
                st.success(f"✅ Categoria confirmada: {validacao['category_name']}")
                st.info(f"O Mercado Livre retornou {len(obrigatorios)} atributo(s) marcado(s) como obrigatório(s). Na próxima tela vamos preencher somente o que realmente for necessário.")
            except Exception as erro:
                st.error(f"A categoria foi localizada, mas não foi possível carregar todos os detalhes: {erro}")

st.divider()
st.warning("🔒 Esta página apenas consulta e salva a categoria escolhida. Nenhum anúncio é criado ou alterado no Mercado Livre.")
