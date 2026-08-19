import hashlib
import hmac
import base64
import json
import os
import re
import unicodedata
from pathlib import Path

import streamlit as st
from openai import OpenAI
from mercado_livre import criar_estado, criar_url_autorizacao, trocar_codigo_por_token, consultar_usuario, listar_anuncios

ARQUIVO_AUTOSAVE = Path("rascunho_autosalvo.json")
st.set_page_config(page_title="Luna Seller AI", page_icon="🌙", layout="wide")


def limpar_texto(valor: str) -> str:
    return re.sub(r"\s+", " ", valor or "").strip()


def sem_acentos(valor: str) -> str:
    normalizado = unicodedata.normalize("NFKD", valor)
    return "".join(c for c in normalizado if not unicodedata.combining(c))


def valor_generico(valor: str) -> bool:
    chave = sem_acentos(limpar_texto(valor)).lower().strip(".,;:/|-_()[]{}")
    return chave in {"generica", "generico", "sem marca", "nao se aplica", "n/a", "na"}


def formatar_titulo(texto: str) -> str:
    conectores = {"e", "de", "da", "do", "das", "dos", "com", "para", "por", "em"}
    partes = limpar_texto(texto).split()
    while partes and sem_acentos(partes[-1]).lower().strip(".,;:/|-_()[]{}") in conectores:
        partes.pop()
    saida = []
    for i, palavra in enumerate(partes):
        chave = sem_acentos(palavra).lower().strip(".,;:/|-_()[]{}")
        if i > 0 and chave in conectores:
            saida.append(palavra.lower())
        elif palavra.isupper() and len(palavra) > 1:
            saida.append(palavra)
        else:
            saida.append(palavra[:1].upper() + palavra[1:].lower())
    return " ".join(saida)


def extrair_variacoes_cor(instrucoes: str) -> list[str]:
    texto = limpar_texto(instrucoes)
    if not texto:
        return []
    padrao = re.search(r"varia(?:ç|c)(?:ão|oes|ões)\s+de\s+cor(?:es)?\s*[:\-]?\s*([^.;\n]+)", texto, flags=re.I)
    if not padrao:
        padrao = re.search(r"cores?\s*[:\-]\s*([^.;\n]+)", texto, flags=re.I)
    if not padrao:
        return []
    trecho = padrao.group(1)
    partes = re.split(r"\s*,\s*|\s+/\s+|\s+e\s+", trecho, flags=re.I)
    resultado = []
    vistos = set()
    for parte in partes:
        parte = limpar_texto(parte).strip(" .,:;-_")
        parte = re.sub(r"^(cor|cores)\s+", "", parte, flags=re.I)
        chave = sem_acentos(parte).lower()
        if 2 <= len(parte) <= 30 and chave not in vistos:
            vistos.add(chave)
            resultado.append(parte)
    return resultado[:8]


def contexto_ia(dados: dict) -> str:
    campos = {k: limpar_texto(v) for k, v in dados.items() if isinstance(v, str) and limpar_texto(v)}
    instrucao_usuario = campos.pop("instrucoes_ia", "")
    variacoes = extrair_variacoes_cor(instrucao_usuario)
    cor_referencia = campos.get("cor", "")
    if variacoes:
        campos.pop("cor", None)
    contexto = "Dados confirmados do produto: " + json.dumps(campos, ensure_ascii=False)
    if variacoes:
        contexto += "\nVariações de cor declaradas pela vendedora: " + ", ".join(variacoes) + "."
        if cor_referencia:
            contexto += " A cor vista/preenchida anteriormente (" + cor_referencia + ") é apenas referência da foto e não deve substituir as variações anunciadas."
        contexto += " Não trate as cores como kit; cada cor é uma opção de variação do mesmo anúncio."
    if instrucao_usuario:
        contexto += (
            "\nInstrução adicional da vendedora: " + instrucao_usuario +
            "\nSiga essa instrução quando ela não contradizer dados técnicos confirmados. "
            "Nunca invente certificações, marca, modelo, medidas, capacidade ou conteúdo da embalagem."
        )
    return contexto


def chave_openai() -> str:
    try:
        return st.secrets.get("OPENAI_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")
    except Exception:
        return os.getenv("OPENAI_API_KEY", "")


def gerar_titulo(dados: dict) -> str:
    limite = 60
    api_key = chave_openai()
    variacoes = extrair_variacoes_cor(dados.get("instrucoes_ia", ""))
    if api_key:
        prompt = (
            "Crie UM título comercial para marketplace no Brasil. Retorne SOMENTE JSON válido no formato {\"titulo\":\"...\"}. "
            "Máximo 60 caracteres, natural e fácil de pesquisar. Comece pelo produto principal. "
            "Quando houver variações de cor, não use como cor principal a cor da foto/referência. Você pode omitir cores do título ou usar 'Cores'/'Várias Cores' se couber. "
            "Quando houver kit, destaque a quantidade. Não repita sinônimos, não use parênteses ou termos promocionais e não invente dados. " + contexto_ia(dados)
        )
        try:
            client = OpenAI(api_key=api_key)
            resposta = client.responses.create(model="gpt-5-mini", store=False, input=prompt)
            texto = resposta.output_text.strip()
            if texto.startswith("```"):
                texto = re.sub(r"^```(?:json)?\s*", "", texto)
                texto = re.sub(r"\s*```$", "", texto)
            titulo_ia = limpar_texto(json.loads(texto).get("titulo", ""))
            if 8 <= len(titulo_ia) <= limite:
                return formatar_titulo(titulo_ia)
        except Exception:
            pass

    nome = limpar_texto(dados.get("nome", "")) or "Produto"
    marca = limpar_texto(dados.get("marca", "")); modelo = limpar_texto(dados.get("modelo", ""))
    cor = limpar_texto(dados.get("cor", "")); material = limpar_texto(dados.get("material", ""))
    instrucoes = limpar_texto(dados.get("instrucoes_ia", ""))
    base = limpar_texto(re.sub(r"\([^)]*\)", " ", nome))
    internos = re.findall(r"\(([^)]*)\)", nome)
    candidatos = [base] + internos
    kit = re.search(r"\b(?:kit|conjunto)\s+(?:com\s+|de\s+)?(\d+)\b", sem_acentos(instrucoes).lower())
    if kit:
        candidatos.insert(0, f"Kit {kit.group(1)}")
    if marca and not valor_generico(marca): candidatos.append(marca)
    if modelo and not valor_generico(modelo): candidatos.append(modelo)
    if material and not valor_generico(material): candidatos.append(material)
    if variacoes:
        candidatos.append("Várias Cores")
    elif cor and not valor_generico(cor):
        candidatos.append(re.split(r"[,(/]", cor)[0].strip())
    texto_extra = " ".join([limpar_texto(dados.get("destaque", "")), limpar_texto(dados.get("diferenciais", ""))])
    texto_norm = sem_acentos(texto_extra).lower()
    atributos = [(r"\bfiltro\b", "com Filtro"), (r"\bsem fio\b", "Sem Fio"), (r"\brecarregavel\b", "Recarregável"), (r"\bdobravel\b", "Dobrável"), (r"\bcontrole remoto\b", "Controle Remoto"), (r"\bluz e som\b", "Luz e Som"), (r"\bdesligamento automatico\b", "Desligamento Automático"), (r"\bsem pedais?\b", "Sem Pedais"), (r"\b2 em 1\b", "2 em 1"), (r"\b3 em 1\b", "3 em 1")]
    candidatos.extend(re.findall(r"\b\d+(?:[.,]\d+)?\s*(?:ml|l|litros?|kg|g|cm|mm|w|v)\b", texto_norm)[:2])
    for padrao, frase in atributos:
        if re.search(padrao, texto_norm): candidatos.append(frase)
    titulo, vistas = "", set()
    for frase in candidatos:
        frase = limpar_texto(frase).strip(".,;:/|-_()[]{}")
        novas = []
        for p in frase.split():
            chave = sem_acentos(p).lower().strip(".,;:/|-_()[]{}")
            if chave and chave not in vistas:
                novas.append(p); vistas.add(chave)
        candidato = limpar_texto(f"{titulo} {' '.join(novas)}")
        if novas and len(candidato) <= limite:
            titulo = candidato
    return formatar_titulo(titulo or base)


def orientacoes_antes_compra(dados: dict, variacoes: list[str]) -> list[str]:
    linhas = ["ANTES DA COMPRA"]
    dimensoes = limpar_texto(dados.get("dimensoes", ""))
    voltagem = limpar_texto(dados.get("voltagem", ""))
    cor = limpar_texto(dados.get("cor", ""))
    if dimensoes:
        linhas.append("- Confira as dimensões informadas no anúncio antes da compra.")
    if voltagem:
        linhas.append("- Confira a voltagem informada no anúncio antes da compra.")
    if variacoes:
        linhas.append("- Selecione a variação desejada antes de finalizar a compra.")
    elif cor:
        linhas.append("- As cores podem apresentar pequena variação conforme a tela.")
    if not dimensoes and not voltagem and not cor and not variacoes:
        linhas.append("- Confira as características e demais especificações informadas no anúncio.")
    linhas.append("- Em caso de dúvidas, utilize o campo de perguntas antes da compra.")
    return linhas


def gerar_descricao(dados: dict) -> str:
    api_key = chave_openai()
    instrucoes = limpar_texto(dados.get("instrucoes_ia", ""))
    variacoes = extrair_variacoes_cor(instrucoes)
    if api_key and instrucoes:
        prompt = (
            "Crie uma descrição profissional em português do Brasil para marketplace. Retorne SOMENTE JSON válido no formato {\"descricao\":\"...\"}. "
            "Use seções claras. Se houver variações de cor, crie uma seção VARIAÇÕES e liste exatamente as cores declaradas pela vendedora; diga para o cliente selecionar a cor desejada antes da compra. "
            "Não trate variações como kit e não apresente a cor da foto/referência como única cor do anúncio. "
            "Se houver kit, deixe quantidade e conteúdo claros. Na seção antes da compra, mencione dimensões somente se dimensões tiverem sido informadas e voltagem somente se voltagem tiver sido informada. "
            "Não invente dados. " + contexto_ia(dados)
        )
        try:
            client = OpenAI(api_key=api_key)
            resposta = client.responses.create(model="gpt-5-mini", store=False, input=prompt)
            texto = resposta.output_text.strip()
            if texto.startswith("```"):
                texto = re.sub(r"^```(?:json)?\s*", "", texto); texto = re.sub(r"\s*```$", "", texto)
            descricao = str(json.loads(texto).get("descricao", "")).strip()
            if len(descricao) >= 80:
                return descricao
        except Exception:
            pass

    nome = limpar_texto(dados.get("nome", "")) or "Produto"
    resumo = limpar_texto(dados.get("resumo", "")); destaque = limpar_texto(dados.get("destaque", ""))
    conteudo = limpar_texto(dados.get("conteudo_embalagem", "")); garantia = limpar_texto(dados.get("garantia", ""))
    linhas = [nome, "", resumo or (f"{nome} com {destaque.lower()}, uma opção prática para o uso no dia a dia." if destaque else f"{nome} para quem busca praticidade no dia a dia.")]
    if variacoes:
        linhas.extend(["", "VARIAÇÕES", "- Cores disponíveis: " + ", ".join(variacoes), "- Selecione a cor desejada antes da compra.", "- As cores são variações do mesmo produto e não formam um kit."])
    elif instrucoes:
        linhas.extend(["", "INSTRUÇÃO DO ANÚNCIO", f"- {instrucoes}"])
    destaques = []
    if destaque: destaques.append(destaque)
    for item in dados.get("diferenciais", "").splitlines():
        item = limpar_texto(item).lstrip("-• ")
        if item and item not in destaques: destaques.append(item)
    if destaques:
        linhas.extend(["", "DESTAQUES DO PRODUTO"] + [f"- {x}" for x in destaques])
    validas = []
    for rotulo, valor in [("Marca",dados.get("marca","")),("Modelo",dados.get("modelo","")),("Cor",dados.get("cor","")),("Material",dados.get("material","")),("Voltagem",dados.get("voltagem","")),("Dimensões",dados.get("dimensoes",""))]:
        if variacoes and rotulo == "Cor":
            continue
        valor = limpar_texto(valor)
        if valor and not valor_generico(valor): validas.append((rotulo, valor))
    if validas:
        linhas.extend(["", "ESPECIFICAÇÕES"] + [f"- {r}: {v}" for r,v in validas])
    if conteudo: linhas.extend(["", "CONTEÚDO DA EMBALAGEM", f"- {conteudo}"])
    if garantia: linhas.extend(["", "GARANTIA", f"- {garantia}"])
    linhas.extend([""] + orientacoes_antes_compra(dados, variacoes))
    return "\n".join(linhas)


def normalizar_lista_palavras(itens) -> list[str]:
    if not isinstance(itens, list): return []
    resultado, vistos = [], set(); genericos = {"produto","modelo","qualidade","oferta","promoção","barato","original","novo"}
    for item in itens:
        termo = limpar_texto(str(item)).lower().strip(" ,.;:/|-_"); chave = sem_acentos(termo)
        if not termo or len(termo) < 3 or len(termo) > 55 or chave in genericos or chave in vistos: continue
        vistos.add(chave); resultado.append(termo)
        if len(resultado) >= 20: break
    return resultado


def gerar_palavras_chave_fallback(dados: dict) -> list[str]:
    nome = limpar_texto(dados.get("nome", "")); categoria = limpar_texto(dados.get("categoria", "")); cor = limpar_texto(dados.get("cor", "")); material = limpar_texto(dados.get("material", "")); instrucoes = limpar_texto(dados.get("instrucoes_ia", ""))
    variacoes = extrair_variacoes_cor(instrucoes)
    base = limpar_texto(re.sub(r"\([^)]*\)", "", nome)); termos = [base]
    if categoria and not valor_generico(categoria): termos.append(categoria)
    if variacoes:
        termos.append(f"{base} várias cores")
        for variacao in variacoes:
            termos.append(f"{base} {variacao}")
    elif cor and not valor_generico(cor):
        termos.append(f"{base} {re.split(r'[,(/]', cor)[0].strip()}")
    if material and not valor_generico(material): termos.append(f"{base} {' '.join(material.split()[:3])}")
    kit = re.search(r"\b(?:kit|conjunto)\s+(?:com\s+|de\s+)?(\d+)\b", sem_acentos(instrucoes).lower())
    if kit: termos.extend([f"kit {kit.group(1)} {base}", f"{base} kit {kit.group(1)} unidades"])
    return normalizar_lista_palavras(termos)


def gerar_palavras_chave(dados: dict) -> list[str]:
    api_key = chave_openai()
    if api_key:
        prompt = (
            "Crie palavras-chave para marketplace no Brasil. Retorne SOMENTE JSON válido no formato {\"palavras_chave\":[...]}. "
            "Gere 15 a 20 frases curtas e naturais, até 55 caracteres. Se houver variações de cor, use as cores declaradas como variações e não a cor da foto como cor principal. "
            "Não trate as variações como kit. Se houver kit real, considere a quantidade. Não invente dados nem use termos promocionais. " + contexto_ia(dados)
        )
        try:
            client = OpenAI(api_key=api_key)
            resposta = client.responses.create(model="gpt-5-mini", store=False, input=prompt)
            texto = resposta.output_text.strip()
            if texto.startswith("```"):
                texto = re.sub(r"^```(?:json)?\s*", "", texto); texto = re.sub(r"\s*```$", "", texto)
            palavras = normalizar_lista_palavras(json.loads(texto).get("palavras_chave", []))
            if len(palavras) >= 10: return palavras
        except Exception:
            pass
    return gerar_palavras_chave_fallback(dados)


def analisar_foto_produto(foto) -> dict:
    api_key = chave_openai()
    if not api_key: raise RuntimeError("OPENAI_API_KEY não configurada")
    data_url = f"data:{foto.type or 'image/jpeg'};base64,{base64.b64encode(foto.getvalue()).decode('utf-8')}"
    client = OpenAI(api_key=api_key)
    resposta = client.responses.create(model="gpt-5-mini", store=False, input=[{"role":"user","content":[{"type":"input_text","text":"Analise esta foto de produto para anúncio de marketplace. Retorne SOMENTE JSON válido com: nome, categoria, marca, modelo, destaque, cor, material, voltagem, dimensoes, conteudo_embalagem, resumo, diferenciais. Português do Brasil. Não invente informações; use string vazia quando não houver confiança."},{"type":"input_image","image_url":data_url}]}])
    texto = resposta.output_text.strip()
    if texto.startswith("```"):
        texto = re.sub(r"^```(?:json)?\s*", "", texto); texto = re.sub(r"\s*```$", "", texto)
    obj = json.loads(texto)
    campos = ["nome","categoria","marca","modelo","destaque","cor","material","voltagem","dimensoes","conteudo_embalagem","resumo","diferenciais"]
    return {campo: limpar_texto(obj.get(campo, "")) if campo != "diferenciais" else (obj.get(campo, "") or "") for campo in campos}


def aplicar_sugestoes_foto(sugestoes: dict) -> int:
    preenchidos = 0
    for campo, valor in sugestoes.items():
        chave = f"campo_{campo}"
        if valor and not limpar_texto(st.session_state.get(chave, "")):
            st.session_state[chave] = valor; preenchidos += 1
    return preenchidos


def carregar_rascunho(salvo: dict) -> None:
    dados_salvos = salvo.get("dados_do_produto", {})
    for campo in ["nome","categoria","marca","modelo","destaque","cor","material","voltagem","dimensoes","garantia","conteudo_embalagem","resumo","diferenciais","instrucoes_ia"]:
        st.session_state[f"campo_{campo}"] = dados_salvos.get(campo, "")
    palavras = salvo.get("palavras_chave", [])
    if isinstance(palavras, list): palavras = ", ".join(palavras)
    st.session_state["resultado_titulo"] = salvo.get("titulo_sugerido") or gerar_titulo(dados_salvos)
    st.session_state["resultado_descricao"] = salvo.get("descricao_sugerida") or gerar_descricao(dados_salvos)
    st.session_state["resultado_palavras"] = palavras
    st.session_state["dados_rascunho"] = dados_salvos
    st.session_state["rascunho_criado"] = True


def iniciar_novo_anuncio() -> None:
    for campo in ["nome","categoria","marca","modelo","destaque","cor","material","voltagem","dimensoes","garantia","conteudo_embalagem","resumo","diferenciais","instrucoes_ia"]:
        st.session_state[f"campo_{campo}"] = ""
    for chave in ["resultado_titulo","resultado_descricao","resultado_palavras","dados_rascunho"]:
        st.session_state.pop(chave, None)
    st.session_state["rascunho_criado"] = False
    st.session_state["foto_uploader_id"] = st.session_state.get("foto_uploader_id", 0) + 1


def avisos_revisao_inteligente(dados: dict) -> list[str]:
    avisos = []
    texto_produto = sem_acentos(" ".join([
        limpar_texto(dados.get("nome", "")),
        limpar_texto(dados.get("categoria", "")),
        limpar_texto(dados.get("destaque", "")),
        limpar_texto(dados.get("resumo", "")),
        limpar_texto(dados.get("diferenciais", "")),
    ])).lower()

    termos_eletricos = [
        "eletrico", "eletrica", "eletronico", "eletronica", "eletroportatil",
        "liquidificador", "cafeteira eletrica", "chaleira eletrica", "mixer",
        "secador", "ferro de passar", "ventilador", "aspirador", "aquecedor"
    ]
    if any(termo in texto_produto for termo in termos_eletricos) and not limpar_texto(dados.get("voltagem", "")):
        avisos.append("Voltagem não informada para um produto que pode precisar dessa especificação.")

    termos_dimensoes = ["cesto", "organizador", "prateleira", "estante", "cadeira", "armario", "movel"]
    if any(termo in texto_produto for termo in termos_dimensoes) and not limpar_texto(dados.get("dimensoes", "")):
        avisos.append("Dimensões não informadas; confira se são importantes para este produto.")

    instrucoes = limpar_texto(dados.get("instrucoes_ia", ""))
    kit = re.search(r"\b(?:kit|conjunto)\s+(?:com\s+|de\s+)?(\d+)\b", sem_acentos(instrucoes).lower())
    if kit:
        quantidade = kit.group(1)
        conteudo = sem_acentos(limpar_texto(dados.get("conteudo_embalagem", ""))).lower()
        if quantidade not in conteudo:
            avisos.append(f"O pedido indica kit com {quantidade} unidades; confira o conteúdo da embalagem.")

    return avisos


st.title("🌙 Luna Seller AI")
st.caption("Crie um rascunho profissional para revisar antes de publicar.")
st.subheader("Recuperar um rascunho")
arquivo_importado = st.file_uploader("Selecione o arquivo rascunho_luna_seller.json que está na pasta Downloads", type=["json"], key="arquivo_rascunho_baixado")
if arquivo_importado is not None and st.button("Carregar rascunho baixado", use_container_width=True):
    try:
        carregar_rascunho(json.load(arquivo_importado)); st.success("Rascunho recuperado. Confira os dados abaixo.")
    except Exception:
        st.error("Este arquivo não pôde ser lido.")
if ARQUIVO_AUTOSAVE.exists():
    st.info("Existe um rascunho salvo automaticamente neste computador.")
    if st.button("Recuperar último preenchimento", use_container_width=True):
        try:
            carregar_rascunho(json.loads(ARQUIVO_AUTOSAVE.read_text(encoding="utf-8"))); st.success("Último rascunho recuperado.")
        except Exception:
            st.error("Não foi possível recuperar o rascunho salvo.")

col_foto, col_form = st.columns([1,2], gap="large")
with col_foto:
    st.subheader("Foto do produto")
    foto = st.file_uploader("Envie uma imagem", type=["png","jpg","jpeg","webp"], key=f"foto_produto_{st.session_state.get('foto_uploader_id',0)}")
    if foto:
        st.image(foto, caption="Imagem para conferência", use_container_width=True)
        if st.button("Analisar foto com IA", use_container_width=True):
            try:
                with st.spinner("Analisando a foto..."):
                    quantidade = aplicar_sugestoes_foto(analisar_foto_produto(foto))
                st.success(f"Foto analisada. {quantidade} campo(s) preenchido(s) para sua revisão.")
            except Exception as erro:
                st.error(f"Não foi possível analisar a foto agora: {erro}")
    else:
        st.info("A foto é opcional. A IA pode sugerir alguns campos para sua revisão.")

with col_form:
    st.subheader("Informações do produto")
    nome = st.text_input("Nome do produto *", placeholder="Ex.: Chaleira elétrica inox", key="campo_nome")
    categoria = st.text_input("Categoria", key="campo_categoria"); marca = st.text_input("Marca", key="campo_marca"); modelo = st.text_input("Modelo", key="campo_modelo"); destaque = st.text_input("Principal destaque", key="campo_destaque")
    col1,col2 = st.columns(2)
    with col1:
        cor = st.text_input("Cor", key="campo_cor"); material = st.text_input("Material", key="campo_material"); voltagem = st.text_input("Voltagem", key="campo_voltagem")
    with col2:
        dimensoes = st.text_input("Dimensões", key="campo_dimensoes"); garantia = st.text_input("Garantia", key="campo_garantia"); conteudo_embalagem = st.text_input("Conteúdo da embalagem", key="campo_conteudo_embalagem")
    resumo = st.text_area("Resumo de venda", key="campo_resumo")
    diferenciais = st.text_area("Diferenciais (um por linha)", key="campo_diferenciais")
    st.subheader("Instruções para a IA")
    st.caption("Opcional. Diga como este anúncio deve ser criado. Ex.: kit com 3 unidades, destacar uma característica ou informar variações.")
    instrucoes_ia = st.text_area("Pedido especial para este anúncio", placeholder="Ex.: Criar como kit com 3 unidades e destacar a quantidade no título e na descrição.", key="campo_instrucoes_ia")

dados = {"nome":limpar_texto(nome),"categoria":limpar_texto(categoria),"marca":limpar_texto(marca),"modelo":limpar_texto(modelo),"destaque":limpar_texto(destaque),"cor":limpar_texto(cor),"material":limpar_texto(material),"voltagem":limpar_texto(voltagem),"dimensoes":limpar_texto(dimensoes),"garantia":limpar_texto(garantia),"conteudo_embalagem":limpar_texto(conteudo_embalagem),"resumo":limpar_texto(resumo),"diferenciais":diferenciais,"instrucoes_ia":limpar_texto(instrucoes_ia)}
st.divider()
if "rascunho_criado" not in st.session_state:
    st.session_state["rascunho_criado"] = False
if st.button("Gerar anúncio para revisão", type="primary", use_container_width=True):
    if not dados["nome"]:
        st.error("Preencha pelo menos o nome do produto.")
    else:
        with st.spinner("Criando o anúncio..."):
            st.session_state["resultado_titulo"] = gerar_titulo(dados)
            st.session_state["resultado_descricao"] = gerar_descricao(dados)
            st.session_state["resultado_palavras"] = ", ".join(gerar_palavras_chave(dados))
            st.session_state["dados_rascunho"] = dados.copy()
            st.session_state["rascunho_criado"] = True
if st.session_state["rascunho_criado"]:
    st.success("Rascunho criado. Revise tudo antes de publicar.")
    st.subheader("Título sugerido")
    titulo_atual = st.session_state.get("resultado_titulo", "")
    st.text_area(f"{len(titulo_atual)}/60 caracteres", value=titulo_atual, height=90, disabled=True)
    st.subheader("Descrição sugerida")
    st.text_area("Descrição", height=420, key="resultado_descricao")
    st.subheader("Palavras-chave")
    st.text_area("Palavras-chave", height=130, key="resultado_palavras")
    palavras_editadas = [limpar_texto(x) for x in st.session_state["resultado_palavras"].split(",") if limpar_texto(x)]
    arquivo = {"dados_do_produto":st.session_state["dados_rascunho"],"titulo_sugerido":st.session_state["resultado_titulo"],"descricao_sugerida":st.session_state["resultado_descricao"],"palavras_chave":palavras_editadas,"status":"rascunho_para_revisao"}
    try:
        ARQUIVO_AUTOSAVE.write_text(json.dumps(arquivo, ensure_ascii=False, indent=2), encoding="utf-8")
        st.caption("Rascunho salvo automaticamente neste computador.")
    except OSError:
        st.warning("Não foi possível salvar a cópia automática.")

    avisos_revisao = avisos_revisao_inteligente(st.session_state["dados_rascunho"])
    if avisos_revisao:
        st.warning("⚠️ Antes de baixar, confira: " + " | ".join(avisos_revisao))
    else:
        st.success("✅ Revisão automática concluída: nenhum alerta importante encontrado.")

    col_baixar,col_novo = st.columns(2)
    with col_baixar:
        st.download_button("Baixar rascunho", data=json.dumps(arquivo, ensure_ascii=False, indent=2), file_name="rascunho_luna_seller.json", mime="application/json", use_container_width=True)
    with col_novo:
        st.button("Novo anúncio", on_click=iniciar_novo_anuncio, use_container_width=True)
st.caption("Esta versão não publica no Mercado Livre. Revise tudo antes de usar.")

st.divider()
st.subheader("Mercado Livre")

ML_CLIENT_ID = st.secrets.get("MERCADO_LIVRE_CLIENT_ID", "")
ML_CLIENT_SECRET = st.secrets.get("MERCADO_LIVRE_CLIENT_SECRET", "")
ML_REDIRECT_URI = "https://luna-seller-ai-4sy77wyfcelrvp8nfk4dme.streamlit.app/"

ml_nonce = criar_estado()
ml_assinatura = hmac.new(
    ML_CLIENT_SECRET.encode("utf-8"),
    ml_nonce.encode("utf-8"),
    hashlib.sha256,
).hexdigest()

ml_estado_oauth = f"{ml_nonce}.{ml_assinatura}"

codigo_ml = st.query_params.get("code")
estado_ml = st.query_params.get("state")
estado_ml_valido = False

if estado_ml and "." in estado_ml:
    ml_nonce_recebido, ml_assinatura_recebida = estado_ml.rsplit(".", 1)

    ml_assinatura_esperada = hmac.new(
        ML_CLIENT_SECRET.encode("utf-8"),
        ml_nonce_recebido.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    estado_ml_valido = hmac.compare_digest(
        ml_assinatura_recebida,
        ml_assinatura_esperada,
    )

if codigo_ml and "ml_access_token" not in st.session_state:
    if not estado_ml_valido:
        st.error("Não foi possível validar a conexão com o Mercado Livre.")
    else:
        try:
            tokens = trocar_codigo_por_token(
                ML_CLIENT_ID,
                ML_CLIENT_SECRET,
                ML_REDIRECT_URI,
                codigo_ml,
            )

            st.session_state["ml_access_token"] = tokens.get("access_token", "")
            st.session_state["ml_refresh_token"] = tokens.get("refresh_token", "")

            usuario_ml = consultar_usuario(st.session_state["ml_access_token"])
            st.session_state["ml_usuario"] = usuario_ml

            st.query_params.clear()
            st.success("Mercado Livre conectado com sucesso.")
        except Exception as erro:
            st.error(f"Não foi possível concluir a conexão: {erro}")

if st.session_state.get("ml_access_token"):
    usuario_ml = st.session_state.get("ml_usuario", {})
    apelido_ml = usuario_ml.get("nickname", "Conta conectada")
    st.success(f"✅ Mercado Livre conectado: {apelido_ml}")
else:
    if not ML_CLIENT_ID or not ML_CLIENT_SECRET:
        st.warning("As credenciais do Mercado Livre ainda não estão configuradas.")
    else:
        url_autorizacao_ml = criar_url_autorizacao(
            ML_CLIENT_ID,
            ML_REDIRECT_URI,
            ml_estado_oauth,
        )

        st.link_button(
            "Conectar ao Mercado Livre",
            url_autorizacao_ml,
            use_container_width=True,
        )

if st.session_state.get("ml_access_token"):
    st.subheader("Seus anúncios no Mercado Livre")

    if st.button("Carregar meus anúncios", use_container_width=True):
        try:
            usuario_ml = st.session_state.get("ml_usuario", {})
            user_id = usuario_ml.get("id")

            anuncios_ml = listar_anuncios(
                st.session_state["ml_access_token"],
                user_id,
                limite=20,
            )

            resultados = anuncios_ml.get("results", [])

            if resultados:
                st.success(f"{len(resultados)} anúncio(s) encontrado(s).")
                for anuncio_id in resultados:
                    st.write(anuncio_id)
            else:
                st.info("Nenhum anúncio encontrado nesta conta.")

        except Exception as erro:
            st.error(f"Não foi possível carregar os anúncios: {erro}")
