import base64
import io
import streamlit as st
from openai import OpenAI
from armazenamento import baixar_bytes, carregar_estado, configurado, restaurar_ultimo_rascunho, salvar_bytes, salvar_estado

st.set_page_config(page_title="Revisar fotos | Luna Seller", page_icon="🌙", layout="wide")
st.title("🌙 Revisar fotos do produto")
st.caption("Confira as imagens preparadas para o anúncio antes do envio ao Mercado Livre.")

CHAVES_FOTOS = ["foto_principal_ia", "foto_detalhes_ia", "foto_beneficios_ia", "foto_uso_ia", "foto_informativa_ia"]
NOMES_FOTOS = ["Foto principal profissional", "Foto de detalhes profissional", "Foto de benefícios profissional", "Foto do produto em uso", "Foto informativa profissional"]
ARQUIVOS_FOTOS = {chave: f"{i+1}_{chave}.png" for i, chave in enumerate(CHAVES_FOTOS)}


def restaurar_dados():
    if not configurado(): return
    try:
        if not st.session_state.get("rascunho_id"):
            salvo = restaurar_ultimo_rascunho()
            if salvo:
                st.session_state["rascunho_id"] = salvo["rascunho_id"]
                estado = salvo["estado"]
                st.session_state["foto_original_anuncio"] = {"bytes": salvo["original"], "nome": estado.get("original_nome", "produto.jpg"), "tipo": estado.get("original_tipo", "image/jpeg")}
                if estado.get("resultado"): st.session_state["modo_vendedora_resultado"] = estado["resultado"]
        rid = st.session_state.get("rascunho_id")
        if rid:
            estado = carregar_estado(rid)
            st.session_state["fotos_aprovadas"] = bool(estado.get("fotos_aprovadas", False))
            for chave in CHAVES_FOTOS:
                if not st.session_state.get(chave):
                    dados = baixar_bytes(f"rascunhos/{rid}/fotos/{ARQUIVOS_FOTOS[chave]}")
                    if dados: st.session_state[chave] = dados
    except Exception as erro:
        st.warning(f"Não foi possível recuperar o armazenamento permanente agora: {erro}")


def atualizar_lista_fotos():
    st.session_state["fotos_preparadas"] = [(c, st.session_state[c]) for c in CHAVES_FOTOS if st.session_state.get(c)]


def persistir_estado(aprovadas=None):
    rid = st.session_state.get("rascunho_id")
    if not (configurado() and rid): return
    estado = carregar_estado(rid)
    if aprovadas is not None: estado["fotos_aprovadas"] = bool(aprovadas)
    salvar_estado(rid, estado)


def gerar_imagem(chave, prompt, mensagem):
    api_key = st.secrets.get("OPENAI_API_KEY")
    if not api_key:
        st.error("A chave da OpenAI não foi encontrada nas configurações do aplicativo."); return
    nome = foto_salva.get("nome", "produto.jpg") if isinstance(foto_salva, dict) else "produto.jpg"
    arquivo = io.BytesIO(foto_original); arquivo.name = nome
    resultado = OpenAI(api_key=api_key).images.edit(model="gpt-image-1.5", image=arquivo, prompt=prompt, size="1024x1024", quality="medium", input_fidelity="high")
    dados = base64.b64decode(resultado.data[0].b64_json)
    st.session_state[chave] = dados
    rid = st.session_state.get("rascunho_id")
    if configurado() and rid:
        salvar_bytes(f"rascunhos/{rid}/fotos/{ARQUIVOS_FOTOS[chave]}", dados, "image/png")
    atualizar_lista_fotos(); st.success(mensagem + (" 💾 Salva com segurança." if configurado() and rid else ""))


def botao_regenerar(chave, rotulo, prompt):
    if st.session_state.get(chave) and st.button(f"🔄 Gerar outra {rotulo}", key=f"regen_{chave}", use_container_width=True):
        try:
            with st.spinner("Criando uma nova opção..."): gerar_imagem(chave, prompt, "✅ Nova opção criada. Confira o resultado.")
        except Exception as erro: st.error(f"Não foi possível gerar outra imagem: {erro}")

restaurar_dados()
foto_salva = st.session_state.get("foto_original_anuncio")
foto_original = foto_salva.get("bytes") if isinstance(foto_salva, dict) else None
if foto_original is not None:
    st.success("✅ Foto original do anúncio encontrada automaticamente.")
    with st.expander("Ver foto original"): st.image(foto_original, caption="Foto original do produto", width=420)
else:
    st.info("Envie a foto no Modo Vendedora para iniciar um anúncio novo.")

prompt_principal = "Crie uma imagem quadrada profissional de catálogo usando SOMENTE o produto real da referência. Fundo branco puro. Produto principal grande no lado esquerdo ou centro-esquerda. No lado direito, até três círculos verticais mostrando detalhes REAIS. Preserve rigorosamente formato, cor, peças e acessórios. Não invente nem duplique itens. Sem textos. Alta nitidez e aparência premium."
prompt_detalhes = "Crie imagem quadrada premium usando SOMENTE o produto real da referência, em ambiente realista e elegante, sem fundo branco simples. Mostre o produto completo e 2 a 4 closes de detalhes reais. Preserve exatamente formato, cor, quantidade de peças e acessórios. Não invente nem duplique componentes. Alta nitidez e iluminação sofisticada."
prompt_beneficios = "Crie imagem profissional usando SOMENTE o produto real. REGRA ABSOLUTA: não escreva benefícios, materiais, desempenho ou especificações que não tenham sido explicitamente confirmados pela vendedora. Na dúvida, faça composição visual premium SEM TEXTO, destacando apenas detalhes visíveis. Preserve exatamente o produto e não duplique itens."
prompt_uso = "Crie uma fotografia quadrada profissional mostrando o produto real da referência em uso cotidiano natural e atraente. REGRA ABSOLUTA DE QUANTIDADE: deve existir UMA ÚNICA UNIDADE do produto principal na cena. Nunca mostre uma segunda unidade inteira ou parcial do mesmo produto. Se a referência possuir acessórios removíveis, mostre apenas os acessórios reais e cada peça no máximo uma vez. Não duplique corpo, recipiente, tampa, copo ou componente. Uma pessoa ou mão pode segurar essa única unidade. Preserve exatamente formato, proporções, cor e acessórios. Não invente funções, especificações, marca ou benefícios. Sem texto. Ambiente realista e fotografia comercial premium."
prompt_informativa = "Crie a quinta imagem profissional de marketplace usando SOMENTE o produto real da referência. Faça uma composição limpa, moderna e informativa mostrando o produto e seus componentes reais de maneira organizada. Use somente informações que estejam visualmente comprovadas; NÃO escreva capacidade, medidas, material, desempenho, certificação, marca, modelo ou qualquer especificação não confirmada. Se não houver dados textuais seguros, faça a imagem informativa SEM TEXTO, usando setas ou organização visual apenas para destacar peças e detalhes existentes sem alegações. Preserve exatamente quantidade, formato, cor e acessórios; não invente nem duplique itens. Fundo elegante e alta nitidez."
secoes = [("✨ 1. Foto principal profissional","foto_principal_ia","✨ Gerar foto principal",prompt_principal),("🔎 2. Foto de detalhes","foto_detalhes_ia","🔎 Gerar foto de detalhes",prompt_detalhes),("💡 3. Foto de benefícios","foto_beneficios_ia","💡 Gerar foto de benefícios",prompt_beneficios),("🌿 4. Foto do produto em uso","foto_uso_ia","🌿 Gerar foto do produto em uso",prompt_uso),("ℹ️ 5. Foto informativa","foto_informativa_ia","ℹ️ Gerar foto informativa",prompt_informativa)]

for indice,(titulo,chave,botao,prompt) in enumerate(secoes):
    st.divider(); st.subheader(titulo)
    if indice == 0: st.caption("Capa: fundo branco, produto grande e detalhes laterais.")
    elif indice == 1: st.caption("Ambiente realista com closes dos detalhes reais.")
    elif indice == 2: st.caption("Sem alegações não confirmadas. Na dúvida, sem texto.")
    elif indice == 3: st.caption("Cena natural com apenas UMA unidade do produto principal.")
    else: st.caption("Organiza informações e componentes reais sem inventar especificações.")
    if foto_original is not None and st.button(botao,key=f"gerar_{chave}",type="primary" if indice==0 else "secondary",use_container_width=True):
        try:
            with st.spinner("Preparando imagem profissional..."): gerar_imagem(chave,prompt,"✅ Imagem criada. Confira o resultado abaixo.")
        except Exception as erro: st.error(f"Não foi possível gerar a imagem: {erro}")
    if st.session_state.get(chave):
        st.image(st.session_state[chave],caption=NOMES_FOTOS[indice],width=520); botao_regenerar(chave,"versão",prompt)

atualizar_lista_fotos(); fotos_preparadas = st.session_state.get("fotos_preparadas",[])
if not fotos_preparadas:
    st.warning("Ainda não há imagens profissionais preparadas."); st.stop()
st.success(f"{len(fotos_preparadas)} imagem(ns) pronta(s) para revisão e armazenada(s) permanentemente.")
st.divider(); st.subheader("🔎 Conferência das imagens")
for i,(chave,foto) in enumerate(fotos_preparadas):
    indice = CHAVES_FOTOS.index(chave); nome = NOMES_FOTOS[indice]
    st.markdown(f"### {i+1}. {nome}"); st.image(foto,caption=nome,width=420); st.divider()
st.warning("Nenhuma imagem desta página é enviada automaticamente ao Mercado Livre.")
confirmar_fotos = st.checkbox("Conferi as imagens e aprovo este conjunto de fotos.", value=bool(st.session_state.get("fotos_aprovadas",False)))
st.session_state["fotos_aprovadas"] = bool(confirmar_fotos)
try: persistir_estado(confirmar_fotos)
except Exception as erro: st.warning(f"A aprovação ficou nesta sessão, mas não foi possível salvá-la permanentemente: {erro}")
if confirmar_fotos: st.success("Fotos aprovadas para a próxima etapa.")
