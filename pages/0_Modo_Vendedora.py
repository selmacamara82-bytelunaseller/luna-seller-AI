import base64
import json
import os
import re

import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="Modo Vendedora | Luna Seller", page_icon="🌙", layout="centered")


def chave_openai():
    try:
        return st.secrets.get("OPENAI_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")
    except Exception:
        return os.getenv("OPENAI_API_KEY", "")


def limpar_json(texto):
    texto = texto.strip()
    if texto.startswith("```"):
        texto = re.sub(r"^```(?:json)?\s*", "", texto)
        texto = re.sub(r"\s*```$", "", texto)
    return json.loads(texto)


def criar_anuncio(foto, sugestao):
    api_key = chave_openai()
    if not api_key:
        raise RuntimeError("A chave da IA não está configurada.")

    mime = foto.type or "image/jpeg"
    dados_foto = base64.b64encode(foto.getvalue()).decode("utf-8")
    data_url = f"data:{mime};base64,{dados_foto}"
    pedido = sugestao.strip() or "Sem sugestão adicional."

    prompt = f"""
Você é o assistente do Luna Seller para criação de anúncio no Mercado Livre Brasil.
Analise cuidadosamente a foto do produto e crie um rascunho profissional.
Sugestão opcional da vendedora: {pedido}

REGRAS IMPORTANTES:
- Não invente marca, modelo, medidas, voltagem, certificação, quantidade, material ou acessórios que não estejam visíveis ou confirmados.
- Se uma informação não puder ser confirmada pela imagem, deixe o campo correspondente vazio.
- O título deve ter no máximo 60 caracteres, ser natural e próprio para busca.
- A descrição deve ser clara, profissional e em português do Brasil.
- Não use alegações promocionais falsas.
- Gere palavras-chave úteis para pesquisa.

Retorne SOMENTE JSON válido neste formato:
{{
  "produto": "",
  "categoria_sugerida": "",
  "marca": "",
  "modelo": "",
  "cor": "",
  "material": "",
  "voltagem": "",
  "titulo": "",
  "descricao": "",
  "palavras_chave": [],
  "dados_para_confirmar": []
}}
"""

    client = OpenAI(api_key=api_key)
    resposta = client.responses.create(
        model="gpt-5-mini",
        store=False,
        input=[{
            "role": "user",
            "content": [
                {"type": "input_text", "text": prompt},
                {"type": "input_image", "image_url": data_url},
            ],
        }],
    )
    return limpar_json(resposta.output_text)


def novo_produto():
    for chave in ["modo_vendedora_resultado", "foto_original_anuncio"]:
        st.session_state.pop(chave, None)
    st.session_state["modo_vendedora_upload_id"] = st.session_state.get("modo_vendedora_upload_id", 0) + 1


st.title("🌙 Luna Seller")
st.subheader("Modo Vendedora")
st.caption("Coloque a foto. Se quiser, escreva uma sugestão. O Luna Seller prepara o anúncio para você revisar.")

st.markdown("### 1. Foto do produto")
foto = st.file_uploader(
    "Escolher foto",
    type=["png", "jpg", "jpeg", "webp"],
    key=f"modo_vendedora_foto_{st.session_state.get('modo_vendedora_upload_id', 0)}",
)

if foto is not None:
    st.session_state["foto_original_anuncio"] = {
        "bytes": foto.getvalue(),
        "nome": foto.name,
        "tipo": foto.type or "image/jpeg",
    }
    st.image(foto, caption="Foto original do produto", use_container_width=True)

st.markdown("### 2. Sugestão para a IA")
sugestao = st.text_area(
    "Opcional",
    placeholder="Ex.: É um kit com 3 unidades. Destacar a quantidade no anúncio.",
    height=90,
)

if st.button("✨ Criar anúncio completo", type="primary", use_container_width=True):
    if foto is None:
        st.error("Escolha primeiro uma foto do produto.")
    else:
        try:
            with st.spinner("Analisando a foto e preparando seu anúncio..."):
                st.session_state["modo_vendedora_resultado"] = criar_anuncio(foto, sugestao)
            st.success("Anúncio preparado. Agora é só conferir.")
        except Exception as erro:
            st.error(f"Não foi possível preparar o anúncio: {erro}")

resultado = st.session_state.get("modo_vendedora_resultado")
if resultado:
    st.divider()
    st.markdown("### 3. Revisar")

    titulo = st.text_input("Título", value=resultado.get("titulo", ""), max_chars=60)
    descricao = st.text_area("Descrição", value=resultado.get("descricao", ""), height=360)

    palavras = resultado.get("palavras_chave", []) or []
    st.text_area("Palavras-chave", value=", ".join(str(x) for x in palavras), height=100)

    confirmar = resultado.get("dados_para_confirmar", []) or []
    if confirmar:
        st.warning("Antes de publicar, confirme: " + " • ".join(str(x) for x in confirmar))
    else:
        st.success("A IA não encontrou dados importantes pendentes de confirmação.")

    with st.expander("Ver informações identificadas pela IA"):
        for campo, rotulo in [
            ("produto", "Produto"),
            ("categoria_sugerida", "Categoria sugerida"),
            ("marca", "Marca"),
            ("modelo", "Modelo"),
            ("cor", "Cor"),
            ("material", "Material"),
            ("voltagem", "Voltagem"),
        ]:
            valor = resultado.get(campo, "")
            if valor:
                st.write(f"**{rotulo}:** {valor}")

    st.info("Próximas etapas: preparar fotos profissionais e vídeo, revisar e enviar ao Mercado Livre.")
    st.button("Começar outro produto", on_click=novo_produto, use_container_width=True)

st.divider()
st.caption("Fluxo: Foto → IA → Revisão → Fotos e vídeo → Mercado Livre")