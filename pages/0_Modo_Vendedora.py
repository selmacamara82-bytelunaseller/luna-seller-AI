import base64
import json
import os
import re

import streamlit as st
from openai import OpenAI
from armazenamento import configurado, criar_id_rascunho, restaurar_ultimo_rascunho, salvar_estado, salvar_original

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
- Não invente marca, modelo, capacidade, medidas, voltagem, certificação, quantidade, material ou acessórios que não estejam visíveis ou confirmados.
- Se uma informação não puder ser confirmada pela imagem, deixe o campo correspondente vazio.
- O título deve ter no máximo 60 caracteres e ser forte para busca no Mercado Livre.
- No título, comece pelo nome exato do produto e depois use os atributos de maior intenção de compra que estejam confirmados, como capacidade, material, tamanho, quantidade, modelo ou função.
- Aproveite bem o limite de 60 caracteres quando houver dados confirmados; evite títulos curtos e genéricos.
- Não repita palavras ou sinônimos só para preencher espaço e não use termos como promoção, oferta, melhor ou imperdível.
- Nunca coloque no título um dado apenas provável. Se a capacidade, marca ou modelo não estiverem confirmados, omita-os.
- A descrição deve ser clara, profissional e em português do Brasil.
- Não afirme compatibilidade com lava-louças, ausência de BPA, certificações ou grau específico de material sem confirmação explícita.
- Em dados_para_confirmar, inclua somente informações essenciais para vender corretamente que realmente façam falta, como capacidade, voltagem, quantidade, marca/modelo quando aplicável ou medidas quando forem relevantes. Não peça certificações ou características opcionais sem necessidade.
- Gere palavras-chave úteis para pesquisa.

Retorne SOMENTE JSON válido neste formato:
{{"produto":"","categoria_sugerida":"","marca":"","modelo":"","cor":"","material":"","voltagem":"","titulo":"","descricao":"","palavras_chave":[],"dados_para_confirmar":[]}}
"""
    client = OpenAI(api_key=api_key)
    resposta = client.responses.create(model="gpt-5-mini", store=False, input=[{"role":"user","content":[{"type":"input_text","text":prompt},{"type":"input_image","image_url":data_url}]}])
    return limpar_json(resposta.output_text)


def persistir_original(dados, nome, tipo):
    if not configurado():
        return
    rascunho_id = criar_id_rascunho(dados)
    st.session_state["rascunho_id"] = rascunho_id
    caminho = salvar_original(rascunho_id, dados, nome, tipo)
    estado = {"original_caminho": caminho, "original_nome": nome, "original_tipo": tipo, "resultado": st.session_state.get("modo_vendedora_resultado", {}), "fotos_aprovadas": False}
    salvar_estado(rascunho_id, estado)


def tentar_restaurar():
    if st.session_state.get("foto_original_anuncio") or not configurado():
        return
    try:
        salvo = restaurar_ultimo_rascunho()
        if salvo:
            estado = salvo["estado"]
            st.session_state["rascunho_id"] = salvo["rascunho_id"]
            st.session_state["foto_original_anuncio"] = {"bytes": salvo["original"], "nome": estado.get("original_nome", "produto.jpg"), "tipo": estado.get("original_tipo", "image/jpeg")}
            if estado.get("resultado"):
                st.session_state["modo_vendedora_resultado"] = estado["resultado"]
    except Exception:
        pass


def novo_produto():
    for chave in ["modo_vendedora_resultado", "foto_original_anuncio", "rascunho_id", "foto_principal_ia", "foto_detalhes_ia", "foto_beneficios_ia", "foto_uso_ia", "foto_informativa_ia", "fotos_aprovadas"]:
        st.session_state.pop(chave, None)
    st.session_state["modo_vendedora_upload_id"] = st.session_state.get("modo_vendedora_upload_id", 0) + 1


tentar_restaurar()
st.title("🌙 Luna Seller")
st.subheader("Modo Vendedora")
st.caption("Coloque a foto. Se quiser, escreva uma sugestão. O Luna Seller prepara o anúncio para você revisar.")
st.markdown("### 1. Foto do produto")
foto = st.file_uploader("Escolher foto", type=["png","jpg","jpeg","webp"], key=f"modo_vendedora_foto_{st.session_state.get('modo_vendedora_upload_id',0)}")

if foto is not None:
    dados = foto.getvalue(); tipo = foto.type or "image/jpeg"
    st.session_state["foto_original_anuncio"] = {"bytes":dados,"nome":foto.name,"tipo":tipo}
    try:
        persistir_original(dados, foto.name, tipo)
    except Exception as erro:
        st.warning(f"A foto está disponível nesta sessão, mas ainda não foi possível salvá-la permanentemente: {erro}")
    st.image(foto, caption="Foto original do produto", use_container_width=True)
elif st.session_state.get("foto_original_anuncio"):
    st.image(st.session_state["foto_original_anuncio"]["bytes"], caption="Última foto recuperada do armazenamento seguro", use_container_width=True)
    st.success("💾 Último rascunho recuperado automaticamente.")

st.markdown("### 2. Sugestão para a IA")
sugestao = st.text_area("Opcional", placeholder="Ex.: É um kit com 3 unidades. Destacar a quantidade no anúncio.", height=90)

if st.button("✨ Criar anúncio completo", type="primary", use_container_width=True):
    fonte = foto
    if fonte is None:
        st.error("Escolha primeiro uma foto do produto.")
    else:
        try:
            with st.spinner("Analisando a foto e preparando seu anúncio..."):
                resultado_novo = criar_anuncio(fonte, sugestao)
                st.session_state["modo_vendedora_resultado"] = resultado_novo
                if configurado() and st.session_state.get("rascunho_id"):
                    estado = {"original_caminho": f"rascunhos/{st.session_state['rascunho_id']}/original{os.path.splitext(fonte.name)[1].lower() or '.jpg'}", "original_nome": fonte.name, "original_tipo": fonte.type or "image/jpeg", "resultado": resultado_novo, "fotos_aprovadas": False}
                    salvar_estado(st.session_state["rascunho_id"], estado)
            st.success("Anúncio preparado. Agora é só conferir.")
        except Exception as erro:
            st.error(f"Não foi possível preparar o anúncio: {erro}")

resultado = st.session_state.get("modo_vendedora_resultado")
if resultado:
    st.divider(); st.markdown("### 3. Revisar")
    st.text_input("Título", value=resultado.get("titulo", ""), max_chars=60)
    st.text_area("Descrição", value=resultado.get("descricao", ""), height=360)
    palavras = resultado.get("palavras_chave", []) or []
    st.text_area("Palavras-chave", value=", ".join(str(x) for x in palavras), height=100)
    confirmar = resultado.get("dados_para_confirmar", []) or []
    if confirmar: st.warning("Antes de publicar, confirme: " + " • ".join(str(x) for x in confirmar))
    else: st.success("A IA não encontrou dados importantes pendentes de confirmação.")
    with st.expander("Ver informações identificadas pela IA"):
        for campo, rotulo in [("produto","Produto"),("categoria_sugerida","Categoria sugerida"),("marca","Marca"),("modelo","Modelo"),("cor","Cor"),("material","Material"),("voltagem","Voltagem")]:
            valor = resultado.get(campo, "")
            if valor: st.write(f"**{rotulo}:** {valor}")
    st.info("Próximas etapas: preparar fotos profissionais e vídeo, revisar e enviar ao Mercado Livre.")
    st.button("Começar outro produto", on_click=novo_produto, use_container_width=True)

st.divider(); st.caption("Fluxo: Foto → IA → Revisão → Fotos e vídeo → Mercado Livre")
