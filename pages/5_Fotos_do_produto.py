import base64
import io
import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="Revisar fotos | Luna Seller", page_icon="🌙", layout="wide")
st.title("🌙 Revisar fotos do produto")
st.caption("Confira as imagens preparadas para o anúncio antes do envio ao Mercado Livre.")

foto_salva = st.session_state.get("foto_original_anuncio")
foto_original = foto_salva.get("bytes") if isinstance(foto_salva, dict) else None
resultado_anuncio = st.session_state.get("modo_vendedora_resultado", {}) or {}
if foto_original is None:
    for chave, valor in st.session_state.items():
        if str(chave).startswith("foto_produto_") and valor is not None:
            foto_original = valor.getvalue() if hasattr(valor, "getvalue") else valor
            break

if foto_original is not None:
    st.success("✅ Foto original do anúncio encontrada automaticamente.")
    with st.expander("Ver foto original"):
        st.image(foto_original, caption="Foto original do produto", width=420)
else:
    st.info("Envie a foto no Modo Vendedora para iniciar um anúncio novo.")

if "fotos_preparadas" not in st.session_state:
    st.session_state["fotos_preparadas"] = []

CHAVES_FOTOS = ["foto_principal_ia", "foto_detalhes_ia", "foto_beneficios_ia", "foto_uso_ia"]
NOMES_FOTOS = ["Foto principal profissional", "Foto de detalhes profissional", "Foto de benefícios profissional", "Foto do produto em uso"]

def atualizar_lista_fotos():
    st.session_state["fotos_preparadas"] = [st.session_state[c] for c in CHAVES_FOTOS if st.session_state.get(c)]

def gerar_imagem(chave, prompt, mensagem):
    api_key = st.secrets.get("OPENAI_API_KEY")
    if not api_key:
        st.error("A chave da OpenAI não foi encontrada nas configurações do aplicativo.")
        return
    nome = foto_salva.get("nome", "produto.jpg") if isinstance(foto_salva, dict) else "produto.jpg"
    arquivo = io.BytesIO(foto_original)
    arquivo.name = nome
    client = OpenAI(api_key=api_key)
    resultado = client.images.edit(model="gpt-image-1.5", image=arquivo, prompt=prompt, size="1024x1024", quality="medium", input_fidelity="high")
    st.session_state[chave] = base64.b64decode(resultado.data[0].b64_json)
    atualizar_lista_fotos()
    st.success(mensagem)

st.divider()
st.subheader("✨ 1. Foto principal profissional")
st.caption("Padrão aprovado: produto grande, fundo branco e detalhes laterais em círculos.")
if foto_original is not None and st.button("✨ Gerar foto principal", type="primary", use_container_width=True):
    try:
        with st.spinner("Preparando a foto principal..."):
            gerar_imagem("foto_principal_ia", "Crie uma imagem quadrada profissional de catálogo usando SOMENTE o produto real da referência. Fundo branco puro. Produto principal grande e nítido no lado esquerdo ou centro-esquerda. No lado direito, até três círculos verticais com borda fina escura mostrando detalhes REAIS do próprio produto. Preserve rigorosamente formato, proporções, cor, acabamento, peças, tampa e acessórios. Não invente funções, acessórios, medidas, capacidade, marca ou logotipo. Sem textos, números, selos ou ícones. Iluminação de estúdio clara, contraste forte e aparência premium de e-commerce.", "✅ Foto principal criada. Confira antes de aprovar.")
    except Exception as erro:
        st.error(f"Não foi possível gerar a foto principal: {erro}")
if st.session_state.get("foto_principal_ia"):
    st.image(st.session_state["foto_principal_ia"], caption=NOMES_FOTOS[0], width=520)

st.divider()
st.subheader("🔎 2. Foto de detalhes")
st.caption("Ambiente realista e sofisticado, com closes dos componentes reais.")
if foto_original is not None and st.button("🔎 Gerar foto de detalhes", use_container_width=True):
    try:
        with st.spinner("Preparando a foto de detalhes..."):
            gerar_imagem("foto_detalhes_ia", "Crie uma imagem quadrada premium usando SOMENTE o produto real da referência. Use ambiente realista, elegante e coerente com a finalidade do produto, sem fundo branco simples. Mostre o produto completo e de 2 a 4 closes de detalhes reais como tampa, abertura, encaixe, acabamento ou componentes visíveis. Preserve exatamente formato, proporções, cor, quantidade de peças e acessórios. Não invente componentes, funções, medidas, capacidade, marca ou logotipo. Alta nitidez e iluminação comercial sofisticada.", "✅ Foto de detalhes criada. Confira o resultado abaixo.")
    except Exception as erro:
        st.error(f"Não foi possível gerar a foto de detalhes: {erro}")
if st.session_state.get("foto_detalhes_ia"):
    st.image(st.session_state["foto_detalhes_ia"], caption=NOMES_FOTOS[1], width=520)

st.divider()
st.subheader("💡 3. Foto de benefícios")
st.write("A terceira imagem valoriza visualmente o produto sem inventar benefícios.")
st.caption("Texto só é permitido quando a informação estiver explicitamente confirmada pela vendedora.")

# Campos inferidos pela IA a partir da imagem não são tratados como confirmação suficiente para texto promocional.
sugestao_confirmada = st.session_state.get("sugestao_vendedora_confirmada", "")
if foto_original is not None and st.button("💡 Gerar foto de benefícios", use_container_width=True):
    try:
        with st.spinner("Preparando a foto de benefícios..."):
            gerar_imagem("foto_beneficios_ia", f"Crie a terceira imagem profissional usando SOMENTE o produto real da referência. Informação explicitamente confirmada pela vendedora, se houver: {sugestao_confirmada or 'NENHUMA'}. REGRA ABSOLUTA: se não houver informação explicitamente confirmada, NÃO escreva nenhum benefício, característica, material, desempenho ou especificação na imagem. Nesse caso faça uma composição visual premium sem texto, destacando apenas detalhes visíveis do produto. Nunca transforme aparência visual em afirmação textual: não escreva inox, premium, resistente, térmico, durável, prático, capacidade, desempenho ou qualquer outro atributo apenas por parecer provável. Se houver informação confirmada, use somente essa informação, em português curto e legível. Preserve exatamente o produto e seus acessórios reais. Fundo contextual elegante, composição moderna e aparência profissional de e-commerce.", "✅ Foto de benefícios criada. Confira o resultado abaixo.")
    except Exception as erro:
        st.error(f"Não foi possível gerar a foto de benefícios: {erro}")
if st.session_state.get("foto_beneficios_ia"):
    st.image(st.session_state["foto_beneficios_ia"], caption=NOMES_FOTOS[2], width=520)

st.divider()
st.subheader("🌿 4. Foto do produto em uso")
st.write("A quarta imagem mostra o produto em uma situação realista e adequada à sua finalidade.")
st.caption("A cena deve parecer natural, sem alterar o produto nem inventar funções.")
if foto_original is not None and st.button("🌿 Gerar foto do produto em uso", use_container_width=True):
    try:
        with st.spinner("Criando uma cena realista com o produto..."):
            gerar_imagem("foto_uso_ia", "Crie a quarta imagem profissional de marketplace usando SOMENTE o produto real da referência. Coloque o produto em uma situação de uso cotidiana, natural e visualmente atraente que seja óbvia e segura a partir do tipo de produto visível. O produto deve ser o protagonista e permanecer fiel em formato, proporções, cor, acabamento, quantidade de peças e acessórios. A cena pode incluir mãos ou uma pessoa usando o produto somente se isso ajudar a demonstrar um uso óbvio, sem alterar o produto. Não invente funções, acessórios, especificações, marca, capacidade, desempenho ou benefícios. Não coloque texto, números ou selos. Se o uso específico não puder ser inferido com segurança, mostre o produto simplesmente posicionado em um ambiente realista coerente, sem demonstrar uma função incerta. Fotografia comercial realista, iluminação natural ou de estúdio contextual, alta nitidez e aparência premium.", "✅ Foto do produto em uso criada. Confira o resultado abaixo.")
    except Exception as erro:
        st.error(f"Não foi possível gerar a foto em uso: {erro}")
if st.session_state.get("foto_uso_ia"):
    st.image(st.session_state["foto_uso_ia"], caption=NOMES_FOTOS[3], width=520)

atualizar_lista_fotos()
fotos_preparadas = st.session_state["fotos_preparadas"]
if not fotos_preparadas:
    st.warning("Ainda não há imagens profissionais preparadas nesta sessão.")
    st.stop()

st.success(f"{len(fotos_preparadas)} imagem(ns) pronta(s) para revisão.")
st.divider()
st.subheader("🔎 Conferência das imagens")
for i, foto in enumerate(fotos_preparadas):
    nome = NOMES_FOTOS[i] if i < len(NOMES_FOTOS) else f"Foto {i + 1}"
    st.markdown(f"### {i + 1}. {nome}")
    st.image(foto, caption=nome, width=420)
    st.divider()

st.warning("Nenhuma imagem desta página é enviada automaticamente ao Mercado Livre.")
confirmar_fotos = st.checkbox("Conferi as imagens e aprovo este conjunto de fotos.")
st.session_state["fotos_aprovadas"] = bool(confirmar_fotos)
if confirmar_fotos:
    st.success("Fotos aprovadas para a próxima etapa.")
