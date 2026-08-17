import base64
import json
import os
import re
import unicodedata
from pathlib import Path

import streamlit as st
from openai import OpenAI

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


def contexto_ia(dados: dict) -> str:
    campos = {k: limpar_texto(v) for k, v in dados.items() if isinstance(v, str) and limpar_texto(v)}
    instrucao_usuario = campos.pop("instrucoes_ia", "")
    contexto = "Dados confirmados do produto: " + json.dumps(campos, ensure_ascii=False)
    if instrucao_usuario:
        contexto += (
            "\nInstrução adicional da vendedora: " + instrucao_usuario +
            "\nSiga essa instrução somente quando ela não contradizer os dados confirmados. "
            "Nunca invente características técnicas, certificações, marca, modelo, medidas ou itens não informados."
        )
    return contexto


def gerar_titulo(dados: dict) -> str:
    limite = 60
    api_key = chave_openai()
    if api_key:
        instrucao = (
            "Crie UM título comercial para anúncio em marketplace no Brasil. "
            "Retorne SOMENTE JSON válido no formato {\"titulo\":\"...\"}. "
            "Máximo 60 caracteres, natural e fácil de pesquisar. Comece pelo produto principal. "
            "Considere a instrução adicional da vendedora, inclusive kit, quantidade, variação ou algo que deve ser destacado/evitado. "
            "Não repita sinônimos, não use parênteses ou termos promocionais e não invente dados. "
            "Marca genérica ou ausente não deve aparecer. " + contexto_ia(dados)
        )
        try:
            client = OpenAI(api_key=api_key)
            resposta = client.responses.create(model="gpt-5-mini", store=False, input=instrucao)
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
    internos = re.findall(r"\(([^)]*)\)", nome)
    base = limpar_texto(re.sub(r"\([^)]*\)", " ", nome))
    candidatos = [base] + internos
    kit = re.search(r"\b(?:kit|conjunto)\s+(?:com\s+|de\s+)?(\d+)\b", sem_acentos(instrucoes).lower())
    if kit: candidatos.insert(0, f"Kit {kit.group(1)}")
    if marca and not valor_generico(marca): candidatos.append(marca)
    if modelo and not valor_generico(modelo): candidatos.append(modelo)
    if material and not valor_generico(material): candidatos.append(material)
    if cor and not valor_generico(cor): candidatos.append(re.split(r"[,(/]", cor)[0].strip())
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
            if chave and chave not in vistas: novas.append(p); vistas.add(chave)
        candidato = limpar_texto(f"{titulo} {' '.join(novas)}")
        if novas and len(candidato) <= limite: titulo = candidato
    return formatar_titulo(titulo or base)


def gerar_descricao(dados: dict) -> str:
    api_key = chave_openai(); instrucoes = limpar_texto(dados.get("instrucoes_ia", ""))
    if api_key and instrucoes:
        prompt = (
            "Crie uma descrição profissional em português do Brasil para marketplace. "
            "Retorne SOMENTE JSON válido no formato {\"descricao\":\"...\"}. "
            "Use seções claras, destaques, especificações, conteúdo da embalagem quando informado e orientação antes da compra. "
            "Siga a instrução adicional da vendedora, mas não invente dados. " + contexto_ia(dados)
        )
        try:
            client = OpenAI(api_key=api_key); resposta = client.responses.create(model="gpt-5-mini", store=False, input=prompt)
            texto = resposta.output_text.strip()
            if texto.startswith("```"): texto = re.sub(r"^```(?:json)?\s*", "", texto); texto = re.sub(r"\s*```$", "", texto)
            descricao = str(json.loads(texto).get("descricao", "")).strip()
            if len(descricao) >= 80: return descricao
        except Exception: pass
    nome = limpar_texto(dados.get("nome", "")) or "Produto"; resumo = limpar_texto(dados.get("resumo", "")); destaque = limpar_texto(dados.get("destaque", "")); conteudo = limpar_texto(dados.get("conteudo_embalagem", "")); garantia = limpar_texto(dados.get("garantia", ""))
    linhas = [nome, "", resumo or (f"{nome} com {destaque.lower()}, uma opção prática para o uso no dia a dia." if destaque else f"{nome} para quem busca praticidade no dia a dia.")]
    if instrucoes: linhas.extend(["", "INSTRUÇÃO DO ANÚNCIO", f"- {instrucoes}"])
    destaques = []
    if destaque: destaques.append(destaque)
    for item in dados.get("diferenciais", "").splitlines():
        item = limpar_texto(item).lstrip("-• ")
        if item and item not in destaques: destaques.append(item)
    if destaques: linhas.extend(["", "DESTAQUES DO PRODUTO"] + [f"- {x}" for x in destaques])
    validas = []
    for rotulo, valor in [("Marca",dados.get("marca","")),("Modelo",dados.get("modelo","")),("Cor",dados.get("cor","")),("Material",dados.get("material","")),("Voltagem",dados.get("voltagem","")),("Dimensões",dados.get("dimensoes",""))]:
        valor = limpar_texto(valor)
        if valor and not valor_generico(valor): validas.append((rotulo, valor))
    if validas: linhas.extend(["", "ESPECIFICAÇÕES"] + [f"- {r}: {v}" for r,v in validas])
    if conteudo: linhas.extend(["", "CONTEÚDO DA EMBALAGEM", f"- {conteudo}"])
    if garantia: linhas.extend(["", "GARANTIA", f"- {garantia}"])
    linhas.extend(["", "ANTES DA COMPRA", "- Confira as medidas, voltagem e demais especificações informadas no anúncio.", "- As cores podem apresentar pequena variação conforme a tela.", "- Em caso de dúvidas, utilize o campo de perguntas antes da compra."])
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
    base = limpar_texto(re.sub(r"\([^)]*\)", "", nome)); termos = [base]
    if categoria and not valor_generico(categoria): termos.append(categoria)
    if cor and not valor_generico(cor): termos.append(f"{base} {re.split(r'[,(/]', cor)[0].strip()}")
    if material and not valor_generico(material): termos.append(f"{base} {' '.join(material.split()[:3])}")
    kit = re.search(r"\b(?:kit|conjunto)\s+(?:com\s+|de\s+)?(\d+)\b", sem_acentos(instrucoes).lower())
    if kit: termos.extend([f"kit {kit.group(1)} {base}", f"{base} kit {kit.group(1)} unidades"])
    return normalizar_lista_palavras(termos)


def gerar_palavras_chave(dados: dict) -> list[str]:
    api_key = chave_openai()
    if api_key:
        prompt = (
            "Crie palavras-chave para marketplace no Brasil. Retorne SOMENTE JSON válido no formato {\"palavras_chave\":[...]}. "
            "Gere 15 a 20 frases de busca curtas, naturais e diferentes, com até 55 caracteres. "
            "Considere a instrução adicional da vendedora, inclusive kit, quantidade e variações. Não invente dados nem use termos promocionais. " + contexto_ia(dados)
        )
        try:
            client = OpenAI(api_key=api_key); resposta = client.responses.create(model="gpt-5-mini", store=False, input=prompt); texto = resposta.output_text.strip()
            if texto.startswith("```"): texto = re.sub(r"^```(?:json)?\s*", "", texto); texto = re.sub(r"\s*```$", "", texto)
            palavras = normalizar_lista_palavras(json.loads(texto).get("palavras_chave", []))
            if len(palavras) >= 10: return palavras
        except Exception: pass
    return gerar_palavras_chave_fallback(dados)


def chave_openai() -> str:
    try: return st.secrets.get("OPENAI_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")
    except Exception: return os.getenv("OPENAI_API_KEY", "")


def analisar_foto_produto(foto) -> dict:
    api_key = chave_openai()
    if not api_key: raise RuntimeError("OPENAI_API_KEY não configurada")
    data_url = f"data:{foto.type or 'image/jpeg'};base64,{base64.b64encode(foto.getvalue()).decode('utf-8')}"
    client = OpenAI(api_key=api_key)
    resposta = client.responses.create(model="gpt-5-mini", store=False, input=[{"role":"user","content":[{"type":"input_text","text":"Analise esta foto de produto para anúncio de marketplace. Retorne SOMENTE JSON válido com: nome, categoria, marca, modelo, destaque, cor, material, voltagem, dimensoes, conteudo_embalagem, resumo, diferenciais. Português do Brasil. Não invente informações; use string vazia quando não houver confiança."},{"type":"input_image","image_url":data_url}]}])
    texto = resposta.output_text.strip()
    if texto.startswith("```"): texto = re.sub(r"^```(?:json)?\s*", "", texto); texto = re.sub(r"\s*```$", "", texto)
    dados = json.loads(texto); campos = ["nome","categoria","marca","modelo","destaque","cor","material","voltagem","dimensoes","conteudo_embalagem","resumo","diferenciais"]
    return {campo: limpar_texto(dados.get(campo, "")) if campo != "diferenciais" else (dados.get(campo, "") or "") for campo in campos}


def aplicar_sugestoes_foto(sugestoes: dict) -> int:
    preenchidos = 0
    for campo, valor in sugestoes.items():
        chave = f"campo_{campo}"
        if valor and not limpar_texto(st.session_state.get(chave, "")): st.session_state[chave] = valor; preenchidos += 1
    return preenchidos


def carregar_rascunho(salvo: dict) -> None:
    dados_salvos = salvo.get("dados_do_produto", {})
    for campo in ["nome","categoria","marca","modelo","destaque","cor","material","voltagem","dimensoes","garantia","conteudo_embalagem","resumo","diferenciais","instrucoes_ia"]: st.session_state[f"campo_{campo}"] = dados_salvos.get(campo, "")
    palavras = salvo.get("palavras_chave", []); palavras = ", ".join(palavras) if isinstance(palavras, list) else palavras
    st.session_state["resultado_titulo"] = salvo.get("titulo_sugerido") or gerar_titulo(dados_salvos); st.session_state["resultado_descricao"] = salvo.get("descricao_sugerida") or gerar_descricao(dados_salvos); st.session_state["resultado_palavras"] = palavras; st.session_state["dados_rascunho"] = dados_salvos; st.session_state["rascunho_criado"] = True


def iniciar_novo_anuncio() -> None:
    for campo in ["nome","categoria","marca","modelo","destaque","cor","material","voltagem","dimensoes","garantia","conteudo_embalagem","resumo","diferenciais","instrucoes_ia"]: st.session_state[f"campo_{campo}"] = ""
    for chave in ["resultado_titulo","resultado_descricao","resultado_palavras","dados_rascunho"]: st.session_state.pop(chave, None)
    st.session_state["rascunho_criado"] = False; st.session_state["foto_uploader_id"] = st.session_state.get("foto_uploader_id", 0) + 1


st.title("🌙 Luna Seller AI")
st.caption("Crie um rascunho profissional para revisar antes de publicar.")
st.subheader("Recuperar um rascunho")
arquivo_importado = st.file_uploader("Selecione o arquivo rascunho_luna_seller.json que está na pasta Downloads", type=["json"], key="arquivo_rascunho_baixado")
if arquivo_importado is not None and st.button("Carregar rascunho baixado", use_container_width=True):
    try: carregar_rascunho(json.load(arquivo_importado)); st.success("Rascunho recuperado. Confira os dados abaixo.")
    except Exception: st.error("Este arquivo não pôde ser lido.")
if ARQUIVO_AUTOSAVE.exists():
    st.info("Existe um rascunho salvo automaticamente neste computador.")
    if st.button("Recuperar último preenchimento", use_container_width=True):
        try: carregar_rascunho(json.loads(ARQUIVO_AUTOSAVE.read_text(encoding="utf-8"))); st.success("Último rascunho recuperado.")
        except Exception: st.error("Não foi possível recuperar o rascunho salvo.")

col_foto, col_form = st.columns([1,2], gap="large")
with col_foto:
    st.subheader("Foto do produto")
    foto = st.file_uploader("Envie uma imagem", type=["png","jpg","jpeg","webp"], key=f"foto_produto_{st.session_state.get('foto_uploader_id',0)}")
    if foto:
        st.image(foto, caption="Imagem para conferência", use_container_width=True)
        if st.button("Analisar foto com IA", use_container_width=True):
            try:
                with st.spinner("Analisando a foto..."): quantidade = aplicar_sugestoes_foto(analisar_foto_produto(foto))
                st.success(f"Foto analisada. {quantidade} campo(s) preenchido(s) para sua revisão.")
            except Exception as erro: st.error(f"Não foi possível analisar a foto agora: {erro}")
    else: st.info("A foto é opcional. A IA pode sugerir alguns campos para sua revisão.")

with col_form:
    st.subheader("Informações do produto")
    nome = st.text_input("Nome do produto *", placeholder="Ex.: Chaleira elétrica inox", key="campo_nome"); categoria = st.text_input("Categoria", key="campo_categoria"); marca = st.text_input("Marca", key="campo_marca"); modelo = st.text_input("Modelo", key="campo_modelo"); destaque = st.text_input("Principal destaque", key="campo_destaque")
    col1,col2 = st.columns(2)
    with col1: cor = st.text_input("Cor", key="campo_cor"); material = st.text_input("Material", key="campo_material"); voltagem = st.text_input("Voltagem", key="campo_voltagem")
    with col2: dimensoes = st.text_input("Dimensões", key="campo_dimensoes"); garantia = st.text_input("Garantia", key="campo_garantia"); conteudo_embalagem = st.text_input("Conteúdo da embalagem", key="campo_conteudo_embalagem")
    resumo = st.text_area("Resumo de venda", key="campo_resumo"); diferenciais = st.text_area("Diferenciais (um por linha)", key="campo_diferenciais")
    st.subheader("Instruções para a IA")
    st.caption("Opcional. Diga como este anúncio deve ser criado. Ex.: kit com 3 unidades, destacar uma característica ou informar variações.")
    instrucoes_ia = st.text_area("Pedido especial para este anúncio", placeholder="Ex.: Criar como kit com 3 unidades e destacar a quantidade no título e na descrição.", key="campo_instrucoes_ia")

dados = {"nome":limpar_texto(nome),"categoria":limpar_texto(categoria),"marca":limpar_texto(marca),"modelo":limpar_texto(modelo),"destaque":limpar_texto(destaque),"cor":limpar_texto(cor),"material":limpar_texto(material),"voltagem":limpar_texto(voltagem),"dimensoes":limpar_texto(dimensoes),"garantia":limpar_texto(garantia),"conteudo_embalagem":limpar_texto(conteudo_embalagem),"resumo":limpar_texto(resumo),"diferenciais":diferenciais,"instrucoes_ia":limpar_texto(instrucoes_ia)}
st.divider()
if "rascunho_criado" not in st.session_state: st.session_state["rascunho_criado"] = False
if st.button("Gerar anúncio para revisão", type="primary", use_container_width=True):
    if not dados["nome"]: st.error("Preencha pelo menos o nome do produto.")
    else:
        with st.spinner("Criando o anúncio..."):
            st.session_state["resultado_titulo"] = gerar_titulo(dados); st.session_state["resultado_descricao"] = gerar_descricao(dados); st.session_state["resultado_palavras"] = ", ".join(gerar_palavras_chave(dados)); st.session_state["dados_rascunho"] = dados.copy(); st.session_state["rascunho_criado"] = True
if st.session_state["rascunho_criado"]:
    st.success("Rascunho criado. Revise tudo antes de publicar.")
    st.subheader("Título sugerido"); titulo_atual = st.session_state.get("resultado_titulo", ""); st.text_area(f"{len(titulo_atual)}/60 caracteres", value=titulo_atual, height=90, disabled=True)
    st.subheader("Descrição sugerida"); st.text_area("Descrição", height=420, key="resultado_descricao")
    st.subheader("Palavras-chave"); st.text_area("Palavras-chave", height=130, key="resultado_palavras")
    palavras_editadas = [limpar_texto(x) for x in st.session_state["resultado_palavras"].split(",") if limpar_texto(x)]
    arquivo = {"dados_do_produto":st.session_state["dados_rascunho"],"titulo_sugerido":st.session_state["resultado_titulo"],"descricao_sugerida":st.session_state["resultado_descricao"],"palavras_chave":palavras_editadas,"status":"rascunho_para_revisao"}
    try: ARQUIVO_AUTOSAVE.write_text(json.dumps(arquivo, ensure_ascii=False, indent=2), encoding="utf-8"); st.caption("Rascunho salvo automaticamente neste computador.")
    except OSError: st.warning("Não foi possível salvar a cópia automática.")
    col_baixar,col_novo = st.columns(2)
    with col_baixar: st.download_button("Baixar rascunho", data=json.dumps(arquivo, ensure_ascii=False, indent=2), file_name="rascunho_luna_seller.json", mime="application/json", use_container_width=True)
    with col_novo: st.button("Novo anúncio", on_click=iniciar_novo_anuncio, use_container_width=True)
st.caption("Esta versão não publica no Mercado Livre. Revise tudo antes de usar.")