import json
import streamlit as st

st.set_page_config(page_title="Aprovar revisão | Luna Seller", page_icon="🌙", layout="wide")

st.title("🌙 Aprovar revisão")
st.caption("Edite e aprove a sugestão da IA. Esta tela não publica nem altera nada no Mercado Livre.")

revisao = st.session_state.get("revisao_ml")
anuncio = st.session_state.get("anuncio_selecionado", {})

if not revisao:
    st.warning("Nenhuma revisão com IA foi gerada nesta sessão. Volte à página principal, selecione um anúncio e clique em 'Gerar revisão com IA'.")
    st.stop()

anuncio_id = revisao.get("id") or anuncio.get("id", "")

if anuncio_id:
    st.info(f"Anúncio em revisão: {anuncio_id}")

chave_base = str(anuncio_id or "sem_id")

if st.session_state.get("revisao_editavel_id") != anuncio_id:
    st.session_state["revisao_editavel_id"] = anuncio_id
    st.session_state["revisao_titulo_edit"] = revisao.get("titulo", "")
    st.session_state["revisao_descricao_edit"] = revisao.get("descricao", "")
    palavras = revisao.get("palavras", [])
    if isinstance(palavras, list):
        palavras = ", ".join(palavras)
    st.session_state["revisao_palavras_edit"] = palavras or ""

st.subheader("Título")
titulo = st.text_input(
    "Título para aprovação",
    key="revisao_titulo_edit",
    max_chars=60,
)
st.caption(f"{len(titulo)}/60 caracteres")

st.subheader("Descrição")
descricao = st.text_area(
    "Descrição para aprovação",
    key="revisao_descricao_edit",
    height=420,
)

st.subheader("Palavras-chave")
palavras_texto = st.text_area(
    "Palavras-chave para aprovação",
    key="revisao_palavras_edit",
    height=150,
    help="Separe as palavras-chave por vírgulas.",
)

st.divider()

if st.button("Aprovar revisão", type="primary", use_container_width=True):
    titulo_final = str(st.session_state.get("revisao_titulo_edit", titulo) or "").strip()
    descricao_final = str(st.session_state.get("revisao_descricao_edit", descricao) or "").strip()
    palavras_finais_texto = str(st.session_state.get("revisao_palavras_edit", palavras_texto) or "")
    palavras = [p.strip() for p in palavras_finais_texto.split(",") if p.strip()]

    if not titulo_final:
        st.error("O título está vazio. Confira antes de aprovar.")
    elif not descricao_final:
        st.error("A descrição está vazia. Confira antes de aprovar.")
    else:
        versao_aprovada = {
            "id": anuncio_id,
            "titulo": titulo_final,
            "descricao": descricao_final,
            "palavras": palavras,
            "status": "aprovado_para_revisao_manual",
        }
        st.session_state["revisao_aprovada"] = versao_aprovada
        st.session_state["revisao_aprovada_titulo"] = titulo_final
        st.session_state["revisao_aprovada_descricao"] = descricao_final
        st.session_state["revisao_aprovada_palavras"] = palavras
        st.success("Revisão aprovada e guardada no Luna Seller nesta sessão.")
        st.info("Nenhuma alteração foi enviada ao Mercado Livre.")

aprovada = st.session_state.get("revisao_aprovada")
if aprovada and aprovada.get("id") == anuncio_id:
    st.subheader("Versão aprovada")
    st.write(f"**Título:** {aprovada.get('titulo', '')}")
    st.text_area(
        "Descrição aprovada",
        value=aprovada.get("descricao", ""),
        height=300,
        disabled=True,
        key=f"descricao_aprovada_{chave_base}",
    )
    st.write("**Palavras-chave aprovadas:**")
    st.write(", ".join(aprovada.get("palavras", [])))

    st.download_button(
        "Baixar revisão aprovada",
        data=json.dumps(aprovada, ensure_ascii=False, indent=2),
        file_name=f"revisao_aprovada_{chave_base}.json",
        mime="application/json",
        use_container_width=True,
    )

st.caption("Modo seguro: esta página apenas edita e salva uma versão de revisão. Não publica no Mercado Livre.")