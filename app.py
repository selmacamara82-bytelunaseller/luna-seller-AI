import json
import re
import unicodedata

import streamlit as st


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


def gerar_titulo(nome: str, marca: str, modelo: str, destaque: str) -> str:
    partes = [nome, marca, modelo, destaque]
    titulo = limpar_texto(" ".join(parte for parte in partes if limpar_texto(parte)))
    return titulo[:60].rstrip()


def gerar_descricao(dados: dict) -> str:
    nome = dados["nome"] or "Produto"
    linhas = [
        f"{nome}",
        "",
        limpar_texto(dados["resumo"])
        or f"Uma opção prática e funcional para quem procura {nome.lower()} com qualidade.",
        "",
        "PRINCIPAIS CARACTERÍSTICAS",
    ]

    caracteristicas = [
        ("Marca", dados["marca"]),
        ("Modelo", dados["modelo"]),
        ("Cor", dados["cor"]),
        ("Material", dados["material"]),
        ("Voltagem", dados["voltagem"]),
        ("Dimensões", dados["dimensoes"]),
        ("Conteúdo da embalagem", dados["conteudo_embalagem"]),
        ("Garantia", dados["garantia"]),
    ]
    for rotulo, valor in caracteristicas:
        if limpar_texto(valor):
            linhas.append(f"- {rotulo}: {limpar_texto(valor)}")

    extras = [limpar_texto(item) for item in dados["diferenciais"].splitlines() if limpar_texto(item)]
    if extras:
        linhas.extend(["", "DIFERENCIAIS"])
        linhas.extend(f"- {item.lstrip('-• ')}" for item in extras)

    linhas.extend(
        [
            "",
            "INFORMAÇÕES IMPORTANTES",
            "- Confira as medidas e especificações antes da compra.",
            "- As cores podem apresentar pequena variação conforme a tela.",
            "- Em caso de dúvidas, utilize o campo de perguntas.",
        ]
    )
    return "\n".join(linhas)


def gerar_palavras_chave(dados: dict) -> list[str]:
    base = [
        dados["nome"],
        dados["categoria"],
        dados["marca"],
        dados["modelo"],
        dados["cor"],
        dados["destaque"],
    ]
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


st.title("🌙 Luna Seller AI")
st.caption("Primeira versão: crie um rascunho profissional para revisar antes de publicar.")

col_foto, col_form = st.columns([1, 2], gap="large")

with col_foto:
    st.subheader("Foto do produto")
    foto = st.file_uploader("Envie uma imagem", type=["png", "jpg", "jpeg", "webp"])
    if foto:
        st.image(foto, caption="Imagem para conferência", use_container_width=True)
    else:
        st.info("A foto é opcional nesta primeira versão.")

with col_form:
    st.subheader("Informações do produto")
    nome = st.text_input("Nome do produto *", placeholder="Ex.: Chaleira elétrica inox")
    categoria = st.text_input("Categoria", placeholder="Ex.: Eletroportáteis")
    marca = st.text_input("Marca")
    modelo = st.text_input("Modelo")
    destaque = st.text_input("Principal destaque", placeholder="Ex.: 1,8 L com desligamento automático")

    col1, col2 = st.columns(2)
    with col1:
        cor = st.text_input("Cor")
        material = st.text_input("Material")
        voltagem = st.text_input("Voltagem")
    with col2:
        dimensoes = st.text_input("Dimensões")
        garantia = st.text_input("Garantia")
        conteudo_embalagem = st.text_input("Conteúdo da embalagem")

    resumo = st.text_area(
        "Resumo de venda",
        placeholder="Explique em uma ou duas frases para quem é o produto e qual problema ele resolve.",
    )
    diferenciais = st.text_area(
        "Diferenciais (um por linha)",
        placeholder="Desligamento automático\nBase giratória\nIndicador luminoso",
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

if st.button("Gerar anúncio para revisão", type="primary", use_container_width=True):
    if not dados["nome"]:
        st.error("Preencha pelo menos o nome do produto.")
    else:
        titulo = gerar_titulo(
            dados["nome"], dados["marca"], dados["modelo"], dados["destaque"]
        )
        descricao = gerar_descricao(dados)
        palavras = gerar_palavras_chave(dados)

        st.success("Rascunho criado. Revise tudo antes de publicar.")
        st.subheader("Título sugerido")
        st.text_area(
            f"{len(titulo)}/60 caracteres",
            value=titulo,
            height=90,
            key="resultado_titulo",
        )

        st.subheader("Descrição sugerida")
        st.text_area(
            "Descrição",
            value=descricao,
            height=420,
            key="resultado_descricao",
        )

        st.subheader("Palavras-chave")
        texto_palavras = ", ".join(palavras)
        st.text_area(
            "Palavras-chave",
            value=texto_palavras,
            height=110,
            key="resultado_palavras",
        )

        arquivo = {
            "dados_do_produto": dados,
            "titulo_sugerido": titulo,
            "descricao_sugerida": descricao,
            "palavras_chave": palavras,
            "status": "rascunho_para_revisao",
        }
        st.download_button(
            "Baixar rascunho",
            data=json.dumps(arquivo, ensure_ascii=False, indent=2),
            file_name="rascunho_luna_seller.json",
            mime="application/json",
            use_container_width=True,
        )

st.caption(
    "Esta versão não publica no Mercado Livre e não envia dados para serviços externos. "
    "Você continua no controle e revisa o anúncio primeiro."
)
