import json
import streamlit as st

from mercado_livre import atualizar_item, atualizar_descricao

st.set_page_config(page_title="Preparar atualização | Luna Seller", page_icon="🌙", layout="wide")

st.title("🌙 Preparar atualização")
st.caption("Revise a versão aprovada antes de qualquer envio ao Mercado Livre.")

aprovada = st.session_state.get("revisao_aprovada")
anuncio = st.session_state.get("anuncio_selecionado", {})

if not aprovada:
    st.warning("Nenhuma revisão aprovada foi encontrada nesta sessão. Volte à página 'Aprovar revisão' e aprove uma versão primeiro.")
    st.stop()

anuncio_id = aprovada.get("id") or anuncio.get("id", "")

titulo_aprovado = str(
    aprovada.get("titulo") or st.session_state.get("revisao_aprovada_titulo", "") or ""
).strip()
descricao_aprovada = str(
    aprovada.get("descricao") or st.session_state.get("revisao_aprovada_descricao", "") or ""
).strip()
palavras_aprovadas = aprovada.get("palavras") or st.session_state.get("revisao_aprovada_palavras", []) or []

st.success("Versão aprovada carregada com sucesso.")

if anuncio_id:
    st.write(f"**Código Mercado Livre:** {anuncio_id}")

st.subheader("Conteúdo aprovado")
st.write("**Título aprovado:**")
st.write(titulo_aprovado or "—")

st.write("**Descrição aprovada:**")
st.text_area(
    "Descrição pronta para conferência",
    value=descricao_aprovada,
    height=420,
    disabled=True,
    key=f"preparar_descricao_{anuncio_id}",
)

st.write("**Palavras-chave aprovadas:**")
st.write(", ".join(palavras_aprovadas))

conteudo_pronto = bool(titulo_aprovado and descricao_aprovada)
if conteudo_pronto:
    st.success(f"Conteúdo conferido: descrição carregada ({len(descricao_aprovada)} caracteres).")
else:
    st.error("A versão aprovada está incompleta. O envio ao Mercado Livre foi bloqueado. Volte em 'Aprovar revisão' e aprove novamente.")

st.divider()
st.subheader("Plano de atualização")

plano = {
    "id": anuncio_id,
    "titulo": titulo_aprovado,
    "descricao": descricao_aprovada,
    "palavras": palavras_aprovadas,
    "status": "pronto_para_conferencia_manual" if conteudo_pronto else "bloqueado_conteudo_incompleto",
    "enviar_ao_mercado_livre": False,
}

st.info(
    "Confira o plano antes do envio. As palavras-chave ficam no Luna Seller para apoio e não são enviadas como um campo separado ao Mercado Livre."
)

st.download_button(
    "Baixar plano de atualização",
    data=json.dumps(plano, ensure_ascii=False, indent=2),
    file_name=f"plano_atualizacao_{anuncio_id or 'anuncio'}.json",
    mime="application/json",
    use_container_width=True,
)

st.divider()
st.subheader("Enviar atualização ao Mercado Livre")
st.warning("Esta área pode alterar o anúncio real. Nada será enviado sem sua confirmação abaixo.")

if not conteudo_pronto:
    st.info("Envio desativado até que título e descrição aprovados estejam carregados corretamente.")
    st.stop()

access_token = st.session_state.get("ml_access_token", "")

if not access_token:
    st.info("A conexão com o Mercado Livre não está ativa nesta sessão. Volte à página principal e conecte sua conta antes de enviar.")
    st.stop()

if not anuncio_id:
    st.error("Não foi possível identificar o código do anúncio. Nenhuma alteração pode ser enviada.")
    st.stop()

sold_quantity = anuncio.get("sold_quantity", 0) or 0
try:
    sold_quantity = int(sold_quantity)
except (TypeError, ValueError):
    sold_quantity = 0

alterar_titulo = False
if sold_quantity > 0:
    st.info(f"Este anúncio registra {sold_quantity} venda(s). Por segurança, o Luna Seller não enviará alteração de título nesta etapa.")
else:
    alterar_titulo = st.checkbox("Atualizar também o título aprovado", value=False)

alterar_descricao = st.checkbox("Atualizar a descrição aprovada", value=False)

st.subheader("Resumo final antes do envio")
col1, col2 = st.columns(2)
with col1:
    st.metric("Anúncio", anuncio_id)
with col2:
    st.metric("Itens selecionados", int(bool(alterar_titulo)) + int(bool(alterar_descricao)))

st.write(f"**Título:** {'SERÁ ALTERADO' if alterar_titulo else 'não será alterado'}")
st.write(f"**Descrição:** {'SERÁ ALTERADA' if alterar_descricao else 'não será alterada'}")

if alterar_titulo:
    st.caption(f"Novo título: {titulo_aprovado}")
if alterar_descricao:
    st.caption(f"Descrição aprovada: {len(descricao_aprovada)} caracteres")

if not (alterar_titulo or alterar_descricao):
    st.info("Selecione acima pelo menos uma alteração para continuar.")

confirmacao = st.checkbox("Conferi o resumo acima e autorizo a atualização selecionada no Mercado Livre.")
palavra = st.text_input("Para confirmar, digite ATUALIZAR", value="", placeholder="ATUALIZAR")

ha_alteracao = alterar_titulo or alterar_descricao
confirmacao_valida = confirmacao and palavra.strip().upper() == "ATUALIZAR"

if st.button(
    "Confirmar e atualizar no Mercado Livre",
    type="primary",
    use_container_width=True,
    disabled=not (ha_alteracao and confirmacao_valida),
):
    try:
        resultados = []

        if alterar_titulo:
            atualizar_item(access_token, anuncio_id, {"title": titulo_aprovado})
            resultados.append("título")

        if alterar_descricao:
            atualizar_descricao(access_token, anuncio_id, descricao_aprovada)
            resultados.append("descrição")

        st.success("Atualização enviada com sucesso: " + " e ".join(resultados) + ".")
        st.info("Confira o anúncio no Mercado Livre antes de fazer qualquer nova alteração.")
    except Exception as erro:
        st.error(f"O Mercado Livre não aceitou a atualização. Nenhuma nova tentativa será feita automaticamente. Detalhes: {erro}")
