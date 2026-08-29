import base64
import io

import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="Revisar fotos | Luna Seller", page_icon="🌙", layout="wide")
st.title("🌙 Revisar fotos do produto")
st.caption("Confira as imagens preparadas para o anúncio antes do envio ao Mercado Livre.")

anuncio = st.session_state.get("anuncio_selecionado", {})
if anuncio.get("id"):
    st.info(f"Anúncio selecionado: {anuncio['id']}")

st.subheader("📸 Padrão de imagens do Luna Seller")
st.write("O conjunto padrão terá até 5 imagens profissionais para revisão:")
st.markdown("**1. Foto principal — capa do anúncio**")
st.write("Produto grande em destaque sobre fundo branco, com até 3 círculos laterais mostrando detalhes reais ou formas de uso quando isso puder ser feito com segurança.")
st.markdown("**2. Foto de detalhes do produto**")
st.write("Produto completo em destaque com closes profissionais de componentes e acabamento reais.")
st.markdown("**3. Foto de benefícios**")
st.write("Apresenta os principais benefícios com textos curtos e profissionais em português.")
st.markdown("**4. Foto do produto em uso**")
st.write("Mostra o produto em um ambiente ou situação realista e adequada à sua finalidade.")
st.markdown("**5. Foto informativa**")
st.write("Reúne informações úteis confirmadas no anúncio, sem inventar especificações.")

st.divider()
st.subheader("🖼️ Imagens preparadas para revisão")

foto_original = None
foto_salva = st.session_state.get("foto_original_anuncio")
if isinstance(foto_salva, dict) and foto_salva.get("bytes"):
    foto_original = foto_salva["bytes"]
else:
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


def gerar_imagem(chave, prompt, mensagem):
    api_key = st.secrets.get("OPENAI_API_KEY")
    if not api_key:
        st.error("A chave da OpenAI não foi encontrada nas configurações do aplicativo.")
        return
    nome = "produto.jpg"
    if isinstance(foto_salva, dict):
        nome = foto_salva.get("nome") or nome
    arquivo = io.BytesIO(foto_original)
    arquivo.name = nome
    client = OpenAI(api_key=api_key)
    resultado = client.images.edit(
        model="gpt-image-1.5", image=arquivo, prompt=prompt,
        size="1024x1024", quality="medium", input_fidelity="high"
    )
    imagem_bytes = base64.b64decode(resultado.data[0].b64_json)
    st.session_state[chave] = imagem_bytes
    fotos = []
    if st.session_state.get("foto_principal_ia"):
        fotos.append(st.session_state["foto_principal_ia"])
    if st.session_state.get("foto_detalhes_ia"):
        fotos.append(st.session_state["foto_detalhes_ia"])
    st.session_state["fotos_preparadas"] = fotos
    st.success(mensagem)


st.divider()
st.subheader("✨ 1. Criar foto principal profissional")
st.caption("Padrão aprovado: produto grande, fundo branco e detalhes laterais em círculos.")
if foto_original is not None and st.button("✨ Gerar foto principal", type="primary", use_container_width=True):
    try:
        with st.spinner("Preparando a foto principal no padrão Luna Seller..."):
            gerar_imagem(
                "foto_principal_ia",
                "Crie uma imagem quadrada profissional de catálogo usando SOMENTE o produto real da referência. Fundo branco puro. Produto principal grande, nítido e com contraste comercial forte, ocupando cerca de 65 a 75% da imagem no lado esquerdo ou centro-esquerda. No lado direito, até três círculos verticais com borda fina escura mostrando detalhes REAIS do próprio produto. Preserve rigorosamente formato, proporções, cor, acabamento, peças, tampa e acessórios. Não redesenhe, não troque peças e não invente funções, acessórios, alimentos, líquidos, medidas, capacidade, marca ou logotipo. Se não houver informação para uma cena de uso segura, use apenas closes de detalhes visíveis. Sem textos, números, selos ou ícones. Iluminação de estúdio clara, reflexos definidos, boa saturação e contraste, sombras suaves, alta nitidez e aparência premium de e-commerce.",
                "✅ Foto principal criada. Confira antes de aprovar."
            )
    except Exception as erro:
        st.error(f"Não foi possível gerar a foto principal: {erro}")

if st.session_state.get("foto_principal_ia"):
    st.image(st.session_state["foto_principal_ia"], caption="Foto principal profissional", width=520)

st.divider()
st.subheader("🔎 2. Criar foto de detalhes")
st.write("A segunda imagem destaca acabamento e componentes reais do produto em closes profissionais.")
st.caption("Sem inventar peças, medidas ou características.")

if foto_original is not None:
    if st.button("🔎 Gerar foto de detalhes", use_container_width=True):
        try:
            with st.spinner("Preparando a foto de detalhes..."):
                gerar_imagem(
                    "foto_detalhes_ia",
                    "Crie a segunda imagem profissional de um anúncio de marketplace usando SOMENTE o produto real da foto de referência. A imagem deve ser quadrada, clara, moderna e com fundo branco ou cinza muito claro. Mostre o produto completo de forma elegante e inclua de 2 a 4 closes bem organizados dos detalhes visuais mais importantes que realmente aparecem na referência, como tampa, abertura, encaixe, acabamento, textura, bordas ou componentes existentes. Preserve exatamente formato, proporções, cor, quantidade de peças e acessórios reais. Não invente componentes, funções, materiais específicos, medidas, capacidade, marca, logotipo, líquidos ou acessórios. Não escreva especificações técnicas. Não altere o design do produto. Use iluminação de estúdio forte e limpa, contraste agradável, reflexos definidos quando adequados, alta nitidez e aparência premium de catálogo de e-commerce.",
                    "✅ Foto de detalhes criada. Confira o resultado abaixo."
                )
        except Exception as erro:
            st.error(f"Não foi possível gerar a foto de detalhes: {erro}")
else:
    st.warning("Envie primeiro uma foto no Modo Vendedora.")

if st.session_state.get("foto_detalhes_ia"):
    st.image(st.session_state["foto_detalhes_ia"], caption="Foto de detalhes profissional", width=520)

fotos_preparadas = st.session_state["fotos_preparadas"]
if not fotos_preparadas:
    st.warning("Ainda não há imagens profissionais preparadas nesta sessão.")
    st.stop()

st.success(f"{len(fotos_preparadas)} imagem(ns) pronta(s) para revisão.")
nomes_fotos = ["Foto principal profissional", "Foto de detalhes profissional"][:len(fotos_preparadas)]

st.divider()
st.subheader("🔎 Conferência das imagens")
for i, foto in enumerate(fotos_preparadas):
    st.markdown(f"### {i + 1}. {nomes_fotos[i]}")
    st.image(foto, caption=nomes_fotos[i], width=420)
    st.divider()

st.warning("Nenhuma imagem desta página é enviada automaticamente ao Mercado Livre.")
confirmar_fotos = st.checkbox("Conferi as imagens e aprovo este conjunto de fotos.")
st.session_state["fotos_aprovadas"] = bool(confirmar_fotos)
if confirmar_fotos:
    st.success("Fotos aprovadas para a próxima etapa.")
