import json
import streamlit as st

st.set_page_config(page_title="Preparar atualização | Luna Seller", page_icon="🌙", layout="wide")

st.title("🌙 Preparar atualização")
st.caption("Revise a versão aprovada antes de qualquer envio. Esta tela não publica nem altera nada no Mercado Livre.")

aprovada = st.session_state.get("revisao_aprovada")
anuncio = st.session_state.get("anuncio_selecionado", {})

if not aprovada:
    st.warning("Nenhuma revisão aprovada foi encontrada nesta sessão. Volte à página 'Aprovar revisão' e aprove uma versão primeiro.")
    st.stop()

anuncio_id = aprovada.get("id") or anuncio.get("id", "")

st.success("Versão aprovada carregada com sucesso.")

if anuncio_id:
    st.write(f"**Código Mercado Livre:** {anuncio_id}")

st.subheader("Conteúdo aprovado")

st.write("**Título aprovado:**")
st.write(aprovada.get("titulo", ""))

st.write("**Descrição aprovada:**")
st.text_area(
    "Descrição pronta para conferência",
    value=aprovada.get("descricao", ""),
    height=420,
    disabled=True,
    key=f"preparar_descricao_{anuncio_id}",
)

st.write("**Palavras-chave aprovadas:**")
st.write(", ".join(aprovada.get("palavras", [])))

st.divider()
st.subheader("Plano de atualização")

plano = {
    "id": anuncio_id,
    "titulo": aprovada.get("titulo", ""),
    "descricao": aprovada.get("descricao", ""),
    "palavras": aprovada.get("palavras", []),
    "status": "pronto_para_conferencia_manual",
    "enviar_ao_mercado_livre": False,
}

st.info(
    "Modo seguro: este plano apenas organiza a versão aprovada. "
    "Nenhuma alteração será enviada ao Mercado Livre nesta etapa."
)

st.download_button(
    "Baixar plano de atualização",
    data=json.dumps(plano, ensure_ascii=False, indent=2),
    file_name=f"plano_atualizacao_{anuncio_id or 'anuncio'}.json",
    mime="application/json",
    use_container_width=True,
)

st.caption("Próxima etapa futura: criar uma confirmação explícita antes de qualquer envio ao Mercado Livre.")