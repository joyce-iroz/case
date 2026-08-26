"""
Chat web do agente, via Streamlit.

Local:
    streamlit run chat_web.py

Deploy grátis:
    1. share.streamlit.io > New app > aponte pro repo > arquivo chat_web.py.

"""
import os
import uuid

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from app.gemini_agent import perguntar  # noqa: E402

st.set_page_config(page_title="Agente Contabilizei", page_icon="📊")
st.title("📊 Agente — Mercado de Abertura de Empresas")

if "historico" not in st.session_state:
    st.session_state.historico = []
if "mensagens_exibidas" not in st.session_state:
    # cada item: (role, texto, lista_de_graficos, lista_de_relatorios_pdf)
    st.session_state.mensagens_exibidas = []


def _renderizar_extras(graficos, relatorios):
    for caminho in graficos:
        st.image(caminho)
    for caminho in relatorios:
        with open(caminho, "rb") as f:
            st.download_button(
                "📄 Baixar relatório em PDF",
                data=f.read(),
                file_name=os.path.basename(caminho),
                mime="application/pdf",
                key=f"download_{uuid.uuid4().hex}",
            )


for role, conteudo, graficos, relatorios in st.session_state.mensagens_exibidas:
    with st.chat_message(role):
        st.markdown(conteudo)
        _renderizar_extras(graficos, relatorios)

pergunta = st.chat_input("Pergunte algo, peça um gráfico ou um relatório em PDF...")
if pergunta:
    st.session_state.mensagens_exibidas.append(("user", pergunta, [], []))
    with st.chat_message("user"):
        st.markdown(pergunta)

    with st.chat_message("assistant"):
        with st.spinner("Consultando..."):
            resposta, st.session_state.historico, graficos, relatorios = perguntar(
                pergunta, st.session_state.historico
            )
        st.markdown(resposta)
        _renderizar_extras(graficos, relatorios)
    st.session_state.mensagens_exibidas.append(("assistant", resposta, graficos, relatorios))
