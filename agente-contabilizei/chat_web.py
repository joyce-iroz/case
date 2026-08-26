"""
Chat web do agente, via Streamlit.

Local:
    streamlit run chat_web.py

Deploy grátis:
    1. Suba este repositório no GitHub (SEM o arquivo .env).
    2. share.streamlit.io > New app > aponte pro repo > arquivo chat_web.py.
    3. Em "Advanced settings > Secrets", cole o conteúdo do seu .env
       (mesmo formato chave=valor).
"""
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from app.gemini_agent import perguntar  # noqa: E402

st.set_page_config(page_title="Agente Contabilizei", page_icon="📊")
st.title("📊 Agente — Mercado de Abertura de Empresas")

if "historico" not in st.session_state:
    st.session_state.historico = []
if "mensagens_exibidas" not in st.session_state:
    st.session_state.mensagens_exibidas = []

for role, conteudo in st.session_state.mensagens_exibidas:
    with st.chat_message(role):
        st.markdown(conteudo)

pergunta = st.chat_input("Pergunte algo sobre os dados...")
if pergunta:
    st.session_state.mensagens_exibidas.append(("user", pergunta))
    with st.chat_message("user"):
        st.markdown(pergunta)

    with st.chat_message("assistant"):
        with st.spinner("Consultando..."):
            resposta, st.session_state.historico = perguntar(
                pergunta, st.session_state.historico
            )
        st.markdown(resposta)
    st.session_state.mensagens_exibidas.append(("assistant", resposta))
