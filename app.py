import base64
import json
import os
import re
import unicodedata
from pathlib import Path

import streamlit as st
from openai import OpenAI


ARQUIVO_AUTOSAVE = Path("rascunho_autosalvo.json")


st.set_page_config(
    page_title="Luna Seller AI",
    page_icon="🌙",
    layout="wide",
)


def limpar_texto(valor: str) -> str:
    return re.sub(r"\s+", " ", valor or "").strip()


def sem_acentos(valor: str) -> str:
    normalizado = unicodedata.normalize("NFKD", valor)
    return "".join(c for c in normalizado if not unicodedata.combining(c))


def valor_generico(valor: str) -> bool:
    chave = sem_acentos(limpar_texto(valor)).lower().strip(".,;:/|-_()[]{}")
    return chave in {"generica", "generico", "sem marca", "nao se aplica", "n/a", "na"}


def gerar_titulo(nome: str, marca: str, modelo: str, destaque: str) -> str:
    titulo = limpar_texto(nome)
    palavras_vistas = {
        sem_acentos(p).lower().strip(".,;:/|-_()[]{}")
        for p in titulo.split()
        if p
    }

    def trecho_sem_repeticao(trecho: str) -> str:
        novas = []
        for palavra in limpar_texto(trecho).split():
            chave = sem_acentos(palavra).lower().strip(".,;:/|-_()[]{}")
            if chave and chave not in palavras_vistas:
                novas.append(palavra.strip(".,;:/|-_()[]{}"))
                palavras_vistas.add(chave)
        return " ".join(novas)

    marca_limpa = limpar_texto(marca)
    if marca_limpa and not valor_generico(marca_limpa):
        extra = trecho_sem_repeticao(marca_limpa)
        if extra and len(f"{titulo} {extra}".strip()) <= 60:
            titulo = f"{titulo} {extra}".strip()

    extra_modelo = trecho_sem_repeticao(modelo)
    if extra_modelo and len(f"{titulo} {extra_modelo}".strip()) <= 60:
        titulo = f"{titulo} {extra_modelo}".strip()

    destaque_normalizado = limpar_texto(destaque)
    destaque_normalizado = re.sub(r"\s*,\s*", " ", destaque_normalizado)
    destaque_normalizado = re.sub(r"\be\s+com\b", "com", destaque_normalizado, flags=re.IGNORECASE)
    destaque_limpo = trecho_sem_repeticao(destaque_normalizado)
    if destaque_limpo:
        candidato_completo = f"{titulo} {destaque_limpo}".strip()
        if len(candidato_completo) <= 60:
            titulo = candidato_completo

    palavras_finais_proibidas = {"e", "de", "da", "do", "das", "dos", "com", "para", "por", "em"}
    partes = titulo.split()
    while partes and sem_acentos(partes[-1]).lower().strip(".,;:/|-_()[]{}") in palavras_finais_proibidas:
        partes.pop()

           conectores = {"e", "de", "da", "do", "das", "dos", "com", "para", "por", "em"}
        titulo_formatado = []
        
        for i, palavra in enumerate(partes):
            chave = sem_acentos(palavra).lower().strip(".,;:/|-_()[]{}")
        
            if i > 0 and chave in conectores:
                titulo_formatado.append(palavra.lower())
            elif palavra.isupper() and len(palavra) > 1:
                titulo_formatado.append(palavra)
            else:
                titulo_formatado.append(palavra[:1].upper() + palavra[1:].lower())
        
        return " ".join(titulo_formatado)




def gerar_descricao(dados: dict) -> str:
    nome = limpar_texto(dados.get("nome", "")) or "Produto"
    resumo = limpar_texto(dados.get("resumo", ""))
    destaque = limpar_texto(dados.get("destaque", ""))
    conteudo = limpar_texto(dados.get("conteudo_embalagem", ""))
    garantia = limpar_texto(dados.get("garantia", ""))

    linhas = [nome, ""]
    if resumo:
        linhas.append(resumo)
    elif destaque:
        linhas.append(f"{nome} com {destaque.lower()}, uma opção prática para o uso no dia a dia.")
    else:
        linhas.append(f"{nome} para quem busca praticidade no dia a dia.")

    destaques = []
    if destaque:
        destaques.append(destaque)
    for item in dados.get("diferenciais", "").splitlines():
        item_limpo = limpar_texto(item).lstrip("-• ")
        if item_limpo and item_limpo not in destaques:
            destaques.append(item_limpo)
    if destaques:
        linhas.extend(["", "DESTAQUES DO PRODUTO"])
        linhas.extend(f"- {item}" for item in destaques)

    caracteristicas = [
        ("Marca", dados.get("marca", "")),
        ("Modelo", dados.get("modelo", "")),
        ("Cor", dados.get("cor", "")),
        ("Material", dados.get("material", "")),
        ("Voltagem", dados.get("voltagem", "")),
        ("Dimensões", dados.get("dimensoes", "")),
    ]
    caracteristicas_validas = []
    for rotulo, valor in caracteristicas:
        valor_limpo = limpar_texto(valor)
        if not valor_limpo or valor_generico(valor_limpo):
            continue
        if rotulo == "Modelo":
            nome_chave = sem_acentos(nome).lower()
            modelo_chave = sem_acentos(valor_limpo).lower()
            palavras_modelo = [p for p in modelo_chave.split() if len(p) > 2]
            if palavras_modelo and all(p in nome_chave for p in palavras_modelo):
                continue
        caracteristicas_validas.append((rotulo, valor_limpo))
    if caracteristicas_validas:
        linhas.extend(["", "ESPECIFICAÇÕES"])
        linhas.extend(f"- {rotulo}: {valor}" for rotulo, valor in caracteristicas_validas)

    if conteudo:
        linhas.extend(["", "CONTEÚDO DA EMBALAGEM", f"- {conteudo}"])
    if garantia:
        linhas.extend(["", "GARANTIA", f"- {garantia}"])

    linhas.extend([
        "",
        "ANTES DA COMPRA",
        "- Confira as medidas, voltagem e demais especificações informadas no anúncio.",
        "- As cores podem apresentar pequena variação conforme a tela.",
        "- Em caso de dúvidas, utilize o campo de perguntas antes da compra.",
    ])
    return "\n".join(linhas)


def gerar_palavras_chave(dados: dict) -> list[str]:
    base = [dados["nome"], dados["categoria"], dados["marca"], dados["modelo"], dados["cor"], dados["destaque"]]
    termos = []
    vistos = set()
    for item in base:
        for termo in re.split(r"[,;/|]", item or ""):
            termo = limpar_texto(termo).lower()
            chave = sem_acentos(termo)
            if termo and chave not in vistos:
                vistos.add(chave)
                termos.append(termo)
    return termos


def chave_openai() -> str:
    try:
        return st.secrets.get("OPENAI_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")
    except Exception:
        return os.getenv("OPENAI_API_KEY", "")


def analisar_foto_produto(foto) -> dict:
    api_key = chave_openai()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY não configurada")

    bytes_foto = foto.getvalue()
    tipo_mime = foto.type or "image/jpeg"
    imagem_b64 = base64.b64encode(bytes_foto).decode("utf-8")
    data_url = f"data:{tipo_mime};base64,{imagem_b64}"

    client = OpenAI(api_key=api_key)
    resposta = client.responses.create(
        model="gpt-5-mini",
        store=False,
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            "Analise esta foto de produto para ajudar a criar um anúncio de marketplace. "
                            "Retorne SOMENTE um objeto JSON válido com estas chaves: "
                            "nome, categoria, marca, modelo, destaque, cor, material, voltagem, dimensoes, "
                            "conteudo_embalagem, resumo, diferenciais. "
                            "Use português do Brasil. Não invente informações. Se algo não estiver visível ou "
                            "não puder ser inferido com boa confiança, use string vazia. Para diferenciais, use "
                            "uma string com um item por linha. Nunca adivinhe marca, modelo, voltagem, dimensões, "
                            "certificações ou conteúdo da embalagem apenas pela aparência."
                        ),
                    },
                    {
                        "type": "input_image",
                        "image_url": data_url,
                    },
                ],
            }
        ],
    )

    texto = resposta.output_text.strip()
    if texto.startswith("```"):
        texto = re.sub(r"^```(?:json)?\s*", "", texto)
        texto = re.sub(r"\s*```$", "", texto)
    dados = json.loads(texto)
    campos = [
        "nome", "categoria", "marca", "modelo", "destaque", "cor", "material",
        "voltagem", "dimensoes", "conteudo_embalagem", "resumo", "diferenciais",
    ]
    return {campo: limpar_texto(dados.get(campo, "")) if campo != "diferenciais" else (dados.get(campo, "") or "") for campo in campos}


def aplicar_sugestoes_foto(sugestoes: dict) -> int:
    preenchidos = 0
    for campo, valor in sugestoes.items():
        chave = f"campo_{campo}"
        atual = st.session_state.get(chave, "")
        if valor and not limpar_texto(atual):
            st.session_state[chave] = valor
            preenchidos += 1
    return preenchidos


def carregar_rascunho(salvo: dict) -> None:
    dados_salvos = salvo.get("dados_do_produto", {})
    for campo in ["nome", "categoria", "marca", "modelo", "destaque", "cor", "material", "voltagem", "dimensoes", "garantia", "conteudo_embalagem", "resumo", "diferenciais"]:
        st.session_state[f"campo_{campo}"] = dados_salvos.get(campo, "")
    palavras_salvas = salvo.get("palavras_chave", [])
    if isinstance(palavras_salvas, list):
        palavras_salvas = ", ".join(palavras_salvas)
    st.session_state["resultado_titulo"] = gerar_titulo(
        dados_salvos.get("nome", ""),
        dados_salvos.get("marca", ""),
        dados_salvos.get("modelo", ""),
        dados_salvos.get("destaque", ""),
    )
    st.session_state["resultado_descricao"] = gerar_descricao(dados_salvos)
    st.session_state["resultado_palavras"] = palavras_salvas
    st.session_state["dados_rascunho"] = dados_salvos
    st.session_state["rascunho_criado"] = True


def iniciar_novo_anuncio() -> None:
    for campo in ["nome", "categoria", "marca", "modelo", "destaque", "cor", "material", "voltagem", "dimensoes", "garantia", "conteudo_embalagem", "resumo", "diferenciais"]:
        st.session_state[f"campo_{campo}"] = ""
    for chave in ["resultado_titulo", "resultado_descricao", "resultado_palavras", "dados_rascunho"]:
        st.session_state.pop(chave, None)
    st.session_state["rascunho_criado"] = False


st.title("🌙 Luna Seller AI")
st.caption("Primeira versão: crie um rascunho profissional para revisar antes de publicar.")

st.subheader("Recuperar um rascunho")
arquivo_importado = st.file_uploader(
    "Selecione o arquivo rascunho_luna_seller.json que está na pasta Downloads",
    type=["json"],
    key="arquivo_rascunho_baixado",
)
if arquivo_importado is not None:
    if st.button("Carregar rascunho baixado", use_container_width=True):
        try:
            carregar_rascunho(json.load(arquivo_importado))
            st.success("Rascunho baixado recuperado. Confira os dados abaixo.")
        except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
            st.error("Este arquivo não pôde ser lido. Selecione o rascunho baixado pelo Luna Seller.")

if ARQUIVO_AUTOSAVE.exists():
    st.info("Existe um rascunho salvo automaticamente neste computador.")
    if st.button("Recuperar último preenchimento", use_container_width=True):
        try:
            salvo = json.loads(ARQUIVO_AUTOSAVE.read_text(encoding="utf-8"))
            carregar_rascunho(salvo)
            st.success("Último rascunho recuperado.")
        except (OSError, json.JSONDecodeError):
            st.error("Não foi possível recuperar o rascunho salvo.")

col_foto, col_form = st.columns([1, 2], gap="large")
with col_foto:
    st.subheader("Foto do produto")
    foto = st.file_uploader("Envie uma imagem", type=["png", "jpg", "jpeg", "webp"], key="foto_produto")
    if foto:
        st.image(foto, caption="Imagem para conferência", use_container_width=True)
        if st.button("Analisar foto com IA", use_container_width=True):
            if not chave_openai():
                st.warning("A análise por foto precisa de uma chave da OpenAI configurada no aplicativo.")
            else:
                try:
                    with st.spinner("Analisando a foto..."):
                        sugestoes = analisar_foto_produto(foto)
                        quantidade = aplicar_sugestoes_foto(sugestoes)
                    if quantidade:
                        st.success(f"Foto analisada. {quantidade} campo(s) preenchido(s) para sua revisão.")
                    else:
                        st.info("A foto foi analisada, mas não havia dados seguros para preencher automaticamente.")
                except (json.JSONDecodeError, RuntimeError, ValueError) as erro:
                    st.error(f"Não foi possível analisar a foto: {erro}")
                except Exception:
                    st.error("Não foi possível analisar a foto agora. Tente novamente em instantes.")
    else:
        st.info("A foto é opcional. Quando a análise por IA estiver configurada, ela poderá sugerir alguns campos.")

with col_form:
    st.subheader("Informações do produto")
    nome = st.text_input("Nome do produto *", placeholder="Ex.: Chaleira elétrica inox", key="campo_nome")
    categoria = st.text_input("Categoria", placeholder="Ex.: Eletroportáteis", key="campo_categoria")
    marca = st.text_input("Marca", key="campo_marca")
    modelo = st.text_input("Modelo", key="campo_modelo")
    destaque = st.text_input("Principal destaque", placeholder="Ex.: 1,8 L com desligamento automático", key="campo_destaque")
    col1, col2 = st.columns(2)
    with col1:
        cor = st.text_input("Cor", key="campo_cor")
        material = st.text_input("Material", key="campo_material")
        voltagem = st.text_input("Voltagem", key="campo_voltagem")
    with col2:
        dimensoes = st.text_input("Dimensões", key="campo_dimensoes")
        garantia = st.text_input("Garantia", key="campo_garantia")
        conteudo_embalagem = st.text_input("Conteúdo da embalagem", key="campo_conteudo_embalagem")
    resumo = st.text_area(
        "Resumo de venda",
        placeholder="Explique em uma ou duas frases para quem é o produto e qual problema ele resolve.",
        key="campo_resumo",
    )
    diferenciais = st.text_area(
        "Diferenciais (um por linha)",
        placeholder="Desligamento automático\nBase giratória\nIndicador luminoso",
        key="campo_diferenciais",
    )

dados = {
    "nome": limpar_texto(nome),
    "categoria": limpar_texto(categoria),
    "marca": limpar_texto(marca),
    "modelo": limpar_texto(modelo),
    "destaque": limpar_texto(destaque),
    "cor": limpar_texto(cor),
    "material": limpar_texto(material),
    "voltagem": limpar_texto(voltagem),
    "dimensoes": limpar_texto(dimensoes),
    "garantia": limpar_texto(garantia),
    "conteudo_embalagem": limpar_texto(conteudo_embalagem),
    "resumo": limpar_texto(resumo),
    "diferenciais": diferenciais,
}

st.divider()
if "rascunho_criado" not in st.session_state:
    st.session_state["rascunho_criado"] = False

if st.button("Gerar anúncio para revisão", type="primary", use_container_width=True):
    if not dados["nome"]:
        st.error("Preencha pelo menos o nome do produto.")
    else:
        palavras = gerar_palavras_chave(dados)
        st.session_state["resultado_titulo"] = gerar_titulo(
            dados["nome"], dados["marca"], dados["modelo"], dados["destaque"]
        )
        st.session_state["resultado_descricao"] = gerar_descricao(dados)
        st.session_state["resultado_palavras"] = ", ".join(palavras)
        st.session_state["dados_rascunho"] = dados.copy()
        st.session_state["rascunho_criado"] = True

if st.session_state["rascunho_criado"]:
    st.success("Rascunho criado. Revise tudo antes de publicar.")
    st.subheader("Título sugerido")
    dados_titulo = st.session_state.get("dados_rascunho", {})
    titulo_atual = gerar_titulo(
        dados_titulo.get("nome", ""),
        dados_titulo.get("marca", ""),
        dados_titulo.get("modelo", ""),
        dados_titulo.get("destaque", ""),
    )
    st.session_state["resultado_titulo"] = titulo_atual
    st.text_area(f"{len(titulo_atual)}/60 caracteres", value=titulo_atual, height=90, disabled=True)
    st.subheader("Descrição sugerida")
    st.text_area("Descrição", height=420, key="resultado_descricao")
    st.subheader("Palavras-chave")
    st.text_area("Palavras-chave", height=110, key="resultado_palavras")
    palavras_editadas = [
        limpar_texto(item)
        for item in st.session_state["resultado_palavras"].split(",")
        if limpar_texto(item)
    ]
    arquivo = {
        "dados_do_produto": st.session_state["dados_rascunho"],
        "titulo_sugerido": st.session_state["resultado_titulo"],
        "descricao_sugerida": st.session_state["resultado_descricao"],
        "palavras_chave": palavras_editadas,
        "status": "rascunho_para_revisao",
    }
    try:
        ARQUIVO_AUTOSAVE.write_text(
            json.dumps(arquivo, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        st.caption("Rascunho salvo automaticamente neste computador.")
    except OSError:
        st.warning("Não foi possível salvar a cópia automática.")

    col_baixar, col_novo = st.columns(2)
    with col_baixar:
        st.download_button(
            "Baixar rascunho",
            data=json.dumps(arquivo, ensure_ascii=False, indent=2),
            file_name="rascunho_luna_seller.json",
            mime="application/json",
            use_container_width=True,
        )
    with col_novo:
        st.button("Novo anúncio", on_click=iniciar_novo_anuncio, use_container_width=True)

st.caption(
    "Esta versão não publica no Mercado Livre. A análise por foto, quando ativada, envia apenas a imagem selecionada à OpenAI para sugerir campos; revise tudo antes de usar."
)
