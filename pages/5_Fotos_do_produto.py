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


def atualizar_lista_fotos():
    chaves = ["foto_principal_ia", "foto_detalhes_ia", "foto_beneficios_ia"]
    st.session_state["fotos_preparadas"] = [st.session_state[c] for c in chaves if st.session_state.get(c)]


def gerar_imagem(chave, prompt, mensagem):
    api_key = st.secrets.get("OPENAI_API_KEY")
    if not api_key:
        st.error("A chave da OpenAI não foi encontrada nas configurações do aplicativo.")
        return
    nome = foto_salva.get("nome", "produto.jpg") if isinstance(foto_salva, dict) else "produto.jpg"
    arquivo = io.BytesIO(foto_original)
    arquivo.name = nome
    client = OpenAI(api_key=api_key)
    resultado = client.images.edit(
        model="gpt-image-1.5", image=arquivo, prompt=prompt,
        size="1024x1024", quality="medium", input_fidelity="high"
    )
    st.session_state[chave] = base64.b64decode(resultado.data[0].b64_json)
    atualizar_lista_fotos()
    st.success(mensagem)


st.divider()
st.subheader("✨ 1. Foto principal profissional")
st.caption("Padrão aprovado: produto grande, fundo branco e detalhes laterais em círculos.")
if foto_original is not None and st.button("✨ Gerar foto principal", type="primary", use_container_width=True):
    try:
        with st.spinner("Preparando a foto principal..."):
            gerar_imagem(
                "foto_principal_ia",
                "Crie uma imagem quadrada profissional de catálogo usando SOMENTE o produto real da referência. Fundo branco puro. Produto principal grande, nítido e com contraste comercial forte, ocupando cerca de 65 a 75% da imagem no lado esquerdo ou centro-esquerda. No lado direito, até três círculos verticais com borda fina escura mostrando detalhes REAIS do próprio produto. Preserve rigorosamente formato, proporções, cor, acabamento, peças, tampa e acessórios. Não redesenhe, não troque peças e não invente funções, acessórios, medidas, capacidade, marca ou logotipo. Sem textos, números, selos ou ícones. Iluminação de estúdio clara, reflexos definidos, boa saturação e contraste, alta nitidez e aparência premium de e-commerce.",
                "✅ Foto principal criada. Confira antes de aprovar."
            )
    except Exception as erro:
        st.error(f"Não foi possível gerar a foto principal: {erro}")
if st.session_state.get("foto_principal_ia"):
    st.image(st.session_state["foto_principal_ia"], caption="Foto principal profissional", width=520)

st.divider()
st.subheader("🔎 2. Foto de detalhes")
st.write("A segunda imagem pode usar um ambiente realista e sofisticado para valorizar o produto e seus detalhes.")
st.caption("O fundo não precisa ser branco. O produto deve continuar fiel ao original.")
if foto_original is not None and st.button("🔎 Gerar foto de detalhes", use_container_width=True):
    try:
        with st.spinner("Preparando a foto de detalhes..."):
            gerar_imagem(
                "foto_detalhes_ia",
                "Crie a segunda imagem profissional de um anúncio de marketplace usando SOMENTE o produto real da referência. Use um ambiente realista, elegante e coerente com a finalidade do produto; NÃO use fundo branco simples. Faça uma composição premium de catálogo: produto completo em destaque e de 2 a 4 closes organizados de detalhes reais, como tampa, abertura, encaixe, acabamento, textura ou componentes visíveis. O cenário pode ter superfície e fundo desfocados com iluminação quente ou natural, mas nunca deve esconder o produto. Preserve exatamente formato, proporções, cor, quantidade de peças e acessórios reais. Não invente componentes, funções, materiais específicos, medidas, capacidade, marca, logotipo ou acessórios. Não altere o design. Alta nitidez, contraste agradável e iluminação comercial sofisticada.",
                "✅ Foto de detalhes criada. Confira o resultado abaixo."
            )
    except Exception as erro:
        st.error(f"Não foi possível gerar a foto de detalhes: {erro}")
if st.session_state.get("foto_detalhes_ia"):
    st.image(st.session_state["foto_detalhes_ia"], caption="Foto de detalhes profissional", width=520)

st.divider()
st.subheader("💡 3. Foto de benefícios")
st.write("A terceira imagem apresenta benefícios de forma visual e profissional.")
st.caption("O Luna Seller usa somente informações confirmadas no anúncio e características visíveis.")

info_confirmada = " | ".join(
    f"{campo}: {resultado_anuncio.get(campo)}"
    for campo in ["produto", "marca", "modelo", "cor", "material"]
    if resultado_anuncio.get(campo)
)

if foto_original is not None and st.button("💡 Gerar foto de benefícios", use_container_width=True):
    try:
        with st.spinner("Preparando a foto de benefícios..."):
            gerar_imagem(
                "foto_beneficios_ia",
                f"Crie a terceira imagem profissional de marketplace usando SOMENTE o produto real da referência. Informações confirmadas disponíveis: {info_confirmada or 'nenhuma informação textual adicional confirmada'}. Mostre o produto fiel ao original em composição comercial atraente, com fundo contextual elegante e espaço visual organizado para destacar de 2 a 3 benefícios APENAS quando forem claramente confirmados pela imagem ou pelas informações confirmadas fornecidas. Se um benefício não estiver confirmado, não invente; prefira destacar visualmente acabamento, praticidade de componentes visíveis e apresentação do produto sem fazer alegações técnicas. Se usar texto, escreva em português do Brasil, muito curto, legível e sem erros, usando somente fatos confirmados. Nunca escreva capacidade, duração térmica, potência, resistência, certificação, material específico, compatibilidade ou desempenho sem confirmação. Preserve exatamente formato, cor, quantidade de peças e acessórios. Aparência premium, moderna e limpa de e-commerce.",
                "✅ Foto de benefícios criada. Confira o resultado abaixo."
            )
    except Exception as erro:
        st.error(f"Não foi possível gerar a foto de benefícios: {erro}")
if st.session_state.get("foto_beneficios_ia"):
    st.image(st.session_state["foto_beneficios_ia"], caption="Foto de benefícios profissional", width=520)

atualizar_lista_fotos()
fotos_preparadas = st.session_state["fotos_preparadas"]
if not fotos_preparadas:
    st.warning("Ainda não há imagens profissionais preparadas nesta sessão.")
    st.stop()

nomes_padrao = ["Foto principal profissional", "Foto de detalhes profissional", "Foto de benefícios profissional"]
st.success(f"{len(fotos_preparadas)} imagem(ns) pronta(s) para revisão.")
st.divider()
st.subheader("🔎 Conferência das imagens")
for i, foto in enumerate(fotos_preparadas):
    nome = nomes_padrao[i] if i < len(nomes_padrao) else f"Foto {i + 1}"
    st.markdown(f"### {i + 1}. {nome}")
    st.image(foto, caption=nome, width=420)
    st.divider()

st.warning("Nenhuma imagem desta página é enviada automaticamente ao Mercado Livre.")
confirmar_fotos = st.checkbox("Conferi as imagens e aprovo este conjunto de fotos.")
st.session_state["fotos_aprovadas"] = bool(confirmar_fotos)
if confirmar_fotos:
    st.success("Fotos aprovadas para a próxima etapa.")
