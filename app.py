import base64
import json
import os
import re
import unicodedata
from pathlib import Path

import streamlit as st
from openai import OpenAI


ARQUIVO_AUTOSAVE = Path("rascunho_autosalvo.json")


st.set_page_config(
    page_title="Luna Seller AI",
    page_icon="🌙",
    layout="wide",
)


def limpar_texto(valor: str) -> str:
    return re.sub(r"\s+", " ", valor