import streamlit as st
from PIL import Image
import io
import os
import base64
import json
import datetime
from urllib.parse import quote
import pandas as pd
from fpdf import FPDF
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
import firebase_admin
from firebase_admin import credentials, firestore

from motor_calculadora import CalculadoraPanificacao

# ==========================================
# CONFIGURAÇÃO DE MONETIZAÇÃO (PAYWALL PRO)
# ==========================================
ATIVAR_PAYWALL = False
CHAVE_MESTRA_ADMIN = "MASSA2026"

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA & ESTÉTICA
# ==========================================
st.set_page_config(
    page_title="Massa Tradicional | Panificação Artesanal & B2B",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

CSS_ESTILO = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

.stApp {
    background-color: #FDFBF7;
    color: #2B2118;
    font-family: 'Plus Jakarta Sans', sans-serif;
}
h1, h2, h3, h4 {
    font-family: 'Playfair Display', serif !important;
    color: #231F1E !important;
}
label, div[data-baseweb="select"] span, .stSlider label, .stNumberInput label {
    color: #2B2118 !important;
}
#banner-topo {
    background: linear-gradient(135deg, #231F1E 0%, #362C28 100%) !important;
    padding: 20px 26px !important;
    border-radius: 12px !important;
    border-bottom: 4px solid #C87D32 !important;
    display: flex !important;
    align-items: center !important;
    gap: 20px !important;
    margin-bottom: 16px !important;
}
#banner-topo .titulo-principal {
    color: #FCEDC9 !important;
    font-family: 'Playfair Display', serif !important;
    font-size: 2.1rem !important;
    font-weight: 700 !important;
    margin: 0 !important;
    padding: 0 !important;
    line-height: 1.2 !important;
    display: block !important;
}
#banner-topo .subtitulo-principal {
    color: #D6C7B2 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.95rem !important;
    margin: 4px 0 0 0 !important;
    display: block !important;
}
button[data-baseweb="tab"] {
    background-color: transparent !important;
}
button[data-baseweb="tab"] div,
button[data-baseweb="tab"] p,
button[data-baseweb="tab"] span {
    color: #231F1E !important;
    font-weight: 700 !important;
    font-size: 1.02rem !important;
    opacity: 1 !important;
}
button[data-baseweb="tab"][aria-selected="true"] div,
button[data-baseweb="tab"][aria-selected="true"] p,
button[data-baseweb="tab"][aria-selected="true"] span {
    color: #C87D32 !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    border-bottom-color: #C87D32 !important;
}
[data-testid="stFileUploader"] section {
    background-color: #FCEDC9 !important;
    border: 2px dashed #C87D32 !important;
}
[data-testid="stFileUploader"] section * {
    color: #231F1E !important;
}
[data-testid="stFileUploader"] button {
    background-color: #231F1E !important;
    color: #FCEDC9 !important;
    border: none !important;
}
[data-testid="stFileUploader"] button * {
    color: #FCEDC9 !important;
}
section[data-testid="stSidebar"] {
    background-color: #231F1E !important;
    border-right: 2px solid #C87D32;
    padding-top: 1rem !important;
    padding-bottom: 1rem !important;
}
section[data-testid="stSidebar"] * {
    color: #F5EFE6 !important;
}
section[data-testid="stSidebar"] input,
section[data-testid="stSidebar"] select,
section[data-testid="stSidebar"] div[data-baseweb="select"] * {
    color: #FFFFFF !important;
    background-color: #362C28 !important;
}
section[data-testid="stSidebar"] div.stVerticalBlock > div {
    margin-bottom: -0.5rem !important;
}
section[data-testid="stSidebar"] hr {
    margin: 0.6rem 0 !important;
    border-color: #C87D32 !important;
}
[data-testid="stMetric"] {
    background-color: #FFFFFF !important;
    border: 1px solid #E6D7C3 !important;
    border-left: 5px solid #C87D32 !important;
    border-radius: 10px !important;
    padding: 14px !important;
}
[data-testid="stMetricLabel"] * {
    color: #7A634E !important;
    font-weight: 600 !important;
}
[data-testid="stMetricValue"] * {
    color: #231F1E !important;
    font-weight: 700 !important;
}
.stButton > button {
    background: linear-gradient(135deg, #C87D32 0%, #8C4A27 100%) !important;
    color: #FFFFFF !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    border: none !important;
}
[data-testid="stDownloadButton"] button {
    background-color: #2E5A44 !important;
    color: #FFFFFF !important;
    border-radius: 8px !important;
    border: none !important;
}
</style>
"""
st.markdown(CSS_ESTILO, unsafe_allow_html=True)

# ==========================================
# 2. FUNÇÕES AUXILIARES
# ==========================================
def obter_secret(chave: str, padrao=""):
    try:
        if chave in st.secrets:
            return st.secrets[chave]
    except Exception:
        pass
    return os.environ.get(chave, padrao)

def formatar_fracao(valor: float) -> str:
    if valor <= 0:
        return "0"
    inteiro = int(valor)
    resto = valor - inteiro
    frac = ""
    if resto >= 0.875:
        inteiro += 1
    elif resto >= 0.625:
        frac = "3/4"
    elif resto >= 0.375:
        frac = "1/2"
    elif resto >= 0.125:
        frac = "1/4"

    if inteiro > 0 and frac:
        return f"{inteiro} e {frac}"
    if inteiro > 0:
        return f"{inteiro}"
    if frac:
        return frac
    return "1 pitada"

def converter_medida_caseira(gramas: float, tipo: str) -> str:
    if not gramas or gramas <= 0:
        return "0"
    fatores = {
        "farinha": (120.0, "xíc."),
        "agua": (240.0, "xíc."),
        "sal": (5.0, "col. chá"),
        "acucar": (12.0, "col. sopa"),
        "gordura": (15.0, "col. sopa"),
        "leite_po": (10.0, "col. sopa"),
        "fermento_seco": (10.0, "col. sopa"),
        "fermento_fresco": (15.0, "tab."),
        "levain": (240.0, "xíc."),
    }
    if tipo in fatores:
        div, un = fatores[tipo]
        return f"{formatar_fracao(gramas / div)} {un}"
    return f"{gramas} g"

def classificar_massa(nome_formato: str, receita: dict, contem_gluten: bool) -> str:
    formato_lower = str(nome_formato).lower()
    if not contem_gluten:
        return "sem_gluten"
    if "focaccia" in formato_lower:
        return "focaccia"
    if "rústico" in formato_lower or "francês" in formato_lower or not receita.get("massa_enriquecida"):
        return "rustico"
    return "macio"

def gerar_modo_preparo(nome_formato: str, receita: dict, contem_gluten: bool) -> list:
    temp_agua = receita.get("temp_agua_c", 22)
    peso_un = receita.get("peso_porcao_g", 0)
    qtd_un = receita.get("qtd_unidades", 1)
    tipo_massa = classificar_massa(nome_formato, receita, contem_gluten)

    if tipo_massa == "sem_gluten":
        return [
            "1. **Mistura Seca:** Misture a farinha sem glúten, goma xantana, sal, fermento e secos.",
            f"2.
