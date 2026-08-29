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

CHAVES_FOTOS = ["foto_principal_ia", "foto_detalhes_ia", "foto_beneficios_ia", "foto_uso_ia", "foto_informativa_ia"]
NOMES_FOTOS = ["Foto principal profissional", "Foto de detalhes profissional", "Foto de benefícios profissional", "Foto do produto em uso", "Foto informativa profissional"]

def atualizar_lista_fotos():
    st.session_state["fotos_preparadas"] = [st.session_state[c] for c in CHAVES_FOTOS if st.session_state.get(c)]

def gerar_imagem(chave, prompt, mensagem):
    api_key = st.secrets.get("OPENAI_API_KEY")
    if not api_key:
        st.error("A chave da OpenAI não foi encontrada nas configurações do aplicativo.")
        return
    nome = foto_salva.get("nome", "produto.jpg") if isinstance(foto_salva, dict) else "produto.jpg"
    arquivo = io.BytesIO(foto_original); arquivo.name = nome
    resultado = OpenAI(api_key=api_key).images.edit(model="gpt-image-1.5", image=arquivo, prompt=prompt, size="1024x1024", quality="medium", input_fidelity="high")
    st.session_state[chave] = base64.b64decode(resultado.data[0].b64_json)
    atualizar_lista_fotos(); st.success(mensagem)

def botao_regenerar(chave, rotulo, prompt):
    if st.session_state.get(chave) and st.button(f"🔄 Gerar outra {rotulo}", key=f"regen_{chave}", use_container_width=True):
        try:
            with st.spinner("Criando uma nova opção..."):
                gerar_imagem(chave, prompt, "✅ Nova opção criada. Confira o resultado.")
        except Exception as erro:
            st.error(f"Não foi possível gerar outra imagem: {erro}")

prompt_principal = "Crie uma imagem quadrada profissional de catálogo usando SOMENTE o produto real da referência. Fundo branco puro. Produto principal grande no lado esquerdo ou centro-esquerda. No lado direito, até três círculos verticais mostrando detalhes REAIS. Preserve rigorosamente formato, cor, peças e acessórios. Não invente nem duplique itens. Sem textos. Alta nitidez e aparência premium."
prompt_detalhes = "Crie imagem quadrada premium usando SOMENTE o produto real da referência, em ambiente realista e elegante, sem fundo branco simples. Mostre o produto completo e 2 a 4 closes de detalhes reais. Preserve exatamente formato, cor, quantidade de peças e acessórios. Não invente nem duplique componentes. Alta nitidez e iluminação sofisticada."
prompt_beneficios = "Crie imagem profissional usando SOMENTE o produto real. REGRA ABSOLUTA: não escreva benefícios, materiais, desempenho ou especificações que não tenham sido explicitamente confirmados pela vendedora. Na dúvida, faça composição visual premium SEM TEXTO, destacando apenas detalhes visíveis. Preserve exatamente o produto e não duplique itens."
prompt_uso = "Crie uma fotografia quadrada profissional mostrando o produto real da referência em uso cotidiano natural e atraente. REGRA ABSOLUTA DE QUANTIDADE: deve existir UMA ÚNICA UNIDADE do produto principal na cena. Nunca mostre uma segunda unidade inteira ou parcial do mesmo produto. Se a referência possuir acessórios removíveis, mostre apenas os acessórios reais e cada peça no máximo uma vez. Não duplique corpo, recipiente, tampa, copo ou componente. Uma pessoa ou mão pode segurar essa única unidade. Preserve exatamente formato, proporções, cor e acessórios. Não invente funções, especificações, marca ou benefícios. Sem texto. Ambiente realista e fotografia comercial premium."
prompt_informativa = "Crie a quinta imagem profissional de marketplace usando SOMENTE o produto real da referência. Faça uma composição limpa, moderna e informativa mostrando o produto e seus componentes reais de maneira organizada. Use somente informações que estejam visualmente comprovadas; NÃO escreva capacidade, medidas, material, desempenho, certificação, marca, modelo ou qualquer especificação não confirmada. Se não houver dados textuais seguros, faça a imagem informativa SEM TEXTO, usando setas ou organização visual apenas para destacar peças e detalhes existentes sem alegações. Preserve exatamente quantidade, formato, cor e acessórios; não invente nem duplique itens. Fundo elegante e alta nitidez."

secoes = [
    ("✨ 1. Foto principal profissional", "foto_principal_ia", "✨ Gerar foto principal", prompt_principal),
    ("🔎 2. Foto de detalhes", "foto_detalhes_ia", "🔎 Gerar foto de detalhes", prompt_detalhes),
    ("💡 3. Foto de benefícios", "foto_beneficios_ia", "💡 Gerar foto de benefícios", prompt_beneficios),
    ("🌿 4. Foto do produto em uso", "foto_uso_ia", "🌿 Gerar foto do produto em uso", prompt_uso),
    ("ℹ️ 5. Foto informativa", "foto_informativa_ia", "ℹ️ Gerar foto informativa", prompt_informativa),
]

for indice, (titulo, chave, botao, prompt) in enumerate(secoes):
    st.divider(); st.subheader(titulo)
    if indice == 0: st.caption("Capa: fundo branco, produto grande e detalhes laterais.")
    elif indice == 1: st.caption("Ambiente realista com closes dos detalhes reais.")
    elif indice == 2: st.caption("Sem alegações não confirmadas. Na dúvida, sem texto.")
    elif indice == 3: st.caption("Cena natural com apenas UMA unidade do produto principal.")
    else: st.caption("Organiza informações e componentes reais sem inventar especificações.")
    if foto_original is not None and st.button(botao, key=f"gerar_{chave}", type="primary" if indice == 0 else "secondary", use_container_width=True):
        try:
            with st.spinner("Preparando imagem profissional..."):
                gerar_imagem(chave, prompt, "✅ Imagem criada. Confira o resultado abaixo.")
        except Exception as erro:
            st.error(f"Não foi possível gerar a imagem: {erro}")
    if st.session_state.get(chave):
        st.image(st.session_state[chave], caption=NOMES_FOTOS[indice], width=520)
        botao_regenerar(chave, "versão", prompt)

atualizar_lista_fotos()
fotos_preparadas = st.session_state.get("fotos_preparadas", [])
if not fotos_preparadas:
    st.warning("Ainda não há imagens profissionais preparadas nesta sessão."); st.stop()

st.success(f"{len(fotos_preparadas)} imagem(ns) pronta(s) para revisão.")
st.divider(); st.subheader("🔎 Conferência das imagens")
for i, foto in enumerate(fotos_preparadas):
    nome = NOMES_FOTOS[i] if i < len(NOMES_FOTOS) else f"Foto {i + 1}"
    st.markdown(f"### {i + 1}. {nome}"); st.image(foto, caption=nome, width=420); st.divider()

st.warning("Nenhuma imagem desta página é enviada automaticamente ao Mercado Livre.")
confirmar_fotos = st.checkbox("Conferi as imagens e aprovo este conjunto de fotos.")
st.session_state["fotos_aprovadas"] = bool(confirmar_fotos)
if confirmar_fotos: st.success("Fotos aprovadas para a próxima etapa.")
