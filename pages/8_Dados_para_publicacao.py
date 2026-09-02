import re
import streamlit as st
from armazenamento import carregar_estado, configurado, restaurar_ultimo_rascunho, salvar_estado

st.set_page_config(page_title="Dados para publicação | Luna Seller", page_icon="🛒", layout="centered")
st.title("🛒 Dados para publicação")
st.caption("Complete somente os dados que não podem ser inventados antes de preparar o anúncio para o Mercado Livre.")


def restaurar():
    if not configurado(): return {}
    try:
        if not st.session_state.get("rascunho_id"):
            salvo = restaurar_ultimo_rascunho()
            if salvo: st.session_state["rascunho_id"] = salvo["rascunho_id"]
        rid = st.session_state.get("rascunho_id")
        return carregar_estado(rid) if rid else {}
    except Exception as erro:
        st.warning(f"Não foi possível recuperar os dados salvos agora: {erro}")
        return {}


def normalizar_decimal(texto):
    texto = (texto or "").strip().replace("R$", "").replace(" ", "")
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    return texto


def ean_valido(codigo):
    codigo = re.sub(r"\D", "", codigo or "")
    if len(codigo) not in (8, 12, 13, 14): return False
    digitos = [int(x) for x in codigo]
    corpo, verificador = digitos[:-1], digitos[-1]
    soma = 0
    for i, d in enumerate(reversed(corpo)):
        soma += d * (3 if i % 2 == 0 else 1)
    calculado = (10 - soma % 10) % 10
    return calculado == verificador

estado = restaurar() or {}
dados_salvos = estado.get("dados_publicacao", {}) if isinstance(estado, dict) else {}
resultado = estado.get("resultado", {}) if isinstance(estado, dict) else {}

if not estado.get("anuncio_completo_aprovado"):
    st.warning("O anúncio completo ainda não aparece como aprovado no armazenamento. Você pode preencher os dados, mas nada será preparado para publicação até a aprovação final.")
else:
    st.success("✅ Anúncio completo aprovado para continuar a preparação.")

if isinstance(resultado, dict) and resultado.get("categoria_sugerida"):
    st.info(f"Categoria sugerida pela IA: {resultado.get('categoria_sugerida')}. A categoria oficial do Mercado Livre ainda será validada antes da publicação.")

st.subheader("💰 Venda")
preco = st.text_input("Preço de venda (R$)", value=str(dados_salvos.get("preco", "")), placeholder="Ex.: 79,90")
estoque = st.number_input("Quantidade em estoque", min_value=0, step=1, value=int(dados_salvos.get("estoque", 1) or 0))
condicao = st.selectbox("Condição do produto", ["Novo", "Usado"], index=0 if dados_salvos.get("condicao", "Novo") == "Novo" else 1)

st.divider(); st.subheader("🏷️ Códigos do fornecedor")
st.caption("Copie exatamente como aparece no fornecedor. O Luna Seller não cria nem altera esses códigos.")
sku = st.text_input("SKU do fornecedor", value=str(dados_salvos.get("sku", "")), placeholder="Cole aqui o SKU usado pelo seu fornecedor")
ean = st.text_input("EAN / GTIN do fornecedor", value=str(dados_salvos.get("ean", "")), placeholder="Ex.: código de barras com 8, 12, 13 ou 14 dígitos")
sem_ean = st.checkbox("Este produto realmente não possui EAN / GTIN", value=bool(dados_salvos.get("sem_ean", False)))

st.divider(); st.subheader("📂 Categoria")
categoria = st.text_input("Categoria / tipo do produto", value=str(dados_salvos.get("categoria", resultado.get("categoria_sugerida", "") if isinstance(resultado, dict) else "")), help="Por enquanto usamos este texto como referência. Antes da publicação o Luna Seller consultará a categoria oficial e os atributos exigidos pelo Mercado Livre.")

if st.button("💾 Salvar dados para publicação", type="primary", use_container_width=True):
    erros = []
    try:
        preco_num = float(normalizar_decimal(preco))
        if preco_num <= 0: erros.append("Informe um preço maior que zero.")
    except Exception:
        erros.append("Informe um preço válido, por exemplo 79,90.")
        preco_num = None
    if estoque < 1: erros.append("Informe pelo menos 1 unidade em estoque.")
    if not sku.strip(): erros.append("Informe o SKU exatamente como consta no fornecedor.")
    ean_limpo = re.sub(r"\D", "", ean or "")
    if not sem_ean:
        if not ean_limpo: erros.append("Informe o EAN/GTIN ou marque que o produto realmente não possui código.")
        elif not ean_valido(ean_limpo): erros.append("O EAN/GTIN informado não passou na validação do dígito verificador. Confira o código do fornecedor.")
    if not categoria.strip(): erros.append("Informe o tipo/categoria do produto.")

    if erros:
        for erro in erros: st.error(erro)
    else:
        dados = {
            "preco": f"{preco_num:.2f}",
            "estoque": int(estoque),
            "condicao": condicao,
            "sku": sku.strip(),
            "ean": "" if sem_ean else ean_limpo,
            "sem_ean": bool(sem_ean),
            "categoria": categoria.strip(),
        }
        st.session_state["dados_publicacao"] = dados
        rid = st.session_state.get("rascunho_id")
        if configurado() and rid:
            try:
                novo_estado = carregar_estado(rid) or {}
                novo_estado["dados_publicacao"] = dados
                novo_estado["dados_publicacao_confirmados"] = True
                salvar_estado(rid, novo_estado)
                st.success("✅ Dados salvos com segurança.")
            except Exception as erro:
                st.error(f"Os dados ficaram nesta sessão, mas não foi possível salvá-los permanentemente: {erro}")
        else:
            st.success("✅ Dados conferidos nesta sessão.")
        st.info("Próximo passo: consultar o Mercado Livre para confirmar a categoria oficial e descobrir os atributos obrigatórios desse produto. Ainda não publicamos nada.")

st.divider(); st.warning("🔒 Salvar esta tela não publica o anúncio. SKU e EAN nunca são gerados ou modificados pelo Luna Seller.")
