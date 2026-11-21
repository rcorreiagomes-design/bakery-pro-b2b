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
# Mude para True quando quiser bloquear os recursos PRO para não-assinantes
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

st.markdown("""
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

    /* RÓTULOS E CONTROLOS DO CORPO (Sem afetar o banner) */
    label, div[data-baseweb="select"] span, .stSlider label, .stNumberInput label {
        color: #2B2118 !important;
    }

    /* BLINDAGEM EXCLUSIVA DO BANNER SUPERIOR */
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

    /* ABAS NO TOPO */
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

    /* UPLOAD */
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

    /* BARRA LATERAL */
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
        background-color: #362C28 !
