import streamlit as st

st.set_page_config(page_title="Vídeo do produto | Luna Seller", page_icon="🎬", layout="wide")
st.title("🎬 Vídeo do produto")
st.caption("Prepare o vídeo do anúncio seguindo as diretrizes do Mercado Livre.")

st.success("✅ Padrão do Luna Seller: vídeo vertical 9:16 com 12 segundos.")

st.subheader("🛡️ Regras aplicadas ao vídeo")
st.write("""
- Formato vertical **9:16**.
- Duração padrão de **12 segundos**.
- Mostrar claramente o produto correspondente ao anúncio.
- Mostrar o produto em movimento ou em situação de uso, sem usar apenas imagens estáticas.
- Não inventar características, funções, medidas, capacidade ou benefícios.
- Não mostrar preço, promoção, cupom, telefone, endereço ou redes sociais.
- Não usar marcas d'água ou conteúdo de terceiros.
- Não mostrar nem fazer referência a menores de idade.
- Preservar as zonas seguras para não cobrir o produto com elementos da interface.
- Manter boa iluminação e aparência profissional.
""")

st.info("A geração do vídeo será sempre iniciada por você. Nada será enviado automaticamente ao Mercado Livre.")

foto_salva = st.session_state.get("foto_original_anuncio")
fotos_aprovadas = st.session_state.get("fotos_aprovadas", False)

if foto_salva:
    st.success("📷 Foto original do produto disponível para servir de referência.")
else:
    st.warning("Volte ao Modo Vendedora e envie a foto original do produto antes de criar o vídeo.")

if fotos_aprovadas:
    st.success("🖼️ Fotos profissionais aprovadas.")
else:
    st.warning("Antes do vídeo final, confira e aprove as fotos do produto.")

st.divider()
st.subheader("🎥 Gerar vídeo profissional")
st.caption("O vídeo usará o produto real como referência e deverá permanecer fiel à aparência e aos componentes do anúncio.")

estilo = st.selectbox(
    "Estilo do vídeo",
    ["Produto em uso", "Apresentação elegante do produto", "Detalhes e movimento"],
    index=0,
)

sugestao_video = st.text_input(
    "Sugestão para o vídeo (opcional)",
    placeholder="Ex.: mostrar a abertura e depois o produto sendo usado",
)

st.markdown("**Duração:** 12 segundos  |  **Formato:** vertical 9:16")

if st.button("🎬 Gerar vídeo de 12 segundos", type="primary", use_container_width=True, disabled=not bool(foto_salva)):
    st.session_state["video_estilo"] = estilo
    st.session_state["video_sugestao"] = sugestao_video
    st.warning("A área do vídeo está preparada. A geração será ativada depois da validação técnica final da API, para evitar cobrança ou geração incompatível durante os testes.")

st.divider()
st.warning("O vídeo deverá ser revisado e aprovado por você antes de qualquer envio ao Mercado Livre.")
