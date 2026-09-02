import hmac

import streamlit as st

st.set_page_config(page_title="Diagnóstico Mercado Livre", page_icon="🔎")

st.title("Diagnóstico Mercado Livre")
st.caption("Teste seguro para conferir se a chave salva no Streamlit é exatamente igual à chave atual do Mercado Livre.")

st.warning(
    "Cole a chave somente no campo abaixo. Ela não é exibida, não é gravada no GitHub e não será mostrada no resultado."
)

try:
    segredo_salvo = str(st.secrets.get("MERCADO_LIVRE_CLIENT_SECRET", ""))
except Exception:
    segredo_salvo = ""

segredo_digitado = st.text_input(
    "Chave secreta atual do Mercado Livre",
    type="password",
    value="",
    autocomplete="off",
)

if st.button("Comparar com a chave salva", type="primary", use_container_width=True):
    if not segredo_digitado:
        st.error("Cole a chave secreta no campo antes de comparar.")
    elif not segredo_salvo:
        st.error("O Streamlit não encontrou MERCADO_LIVRE_CLIENT_SECRET nos Secrets.")
    elif hmac.compare_digest(segredo_digitado, segredo_salvo):
        st.success("RESULTADO: as duas chaves são exatamente iguais, caractere por caractere.")
        st.info(
            "Isso descarta espaço extra, caractere invisível ou chave diferente no Streamlit. "
            "O próximo passo será tratar a credencial/aplicação no Mercado Livre."
        )
    else:
        st.error("RESULTADO: a chave do Mercado Livre e a chave salva no Streamlit são diferentes.")
        st.info("Nesse caso, atualize o Secret do Streamlit com a chave atual do Mercado Livre.")

st.caption("Por segurança, este diagnóstico não mostra nem registra o conteúdo das chaves.")
