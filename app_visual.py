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
    initial_sidebar_state="expanded",
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

/* BANNER SUPERIOR */
#banner-topo {
    background: linear-gradient(135deg, #231F1E 0%, #362C28 100%) !important;
    padding: 18px 26px !important;
    border-radius: 12px !important;
    border-bottom: 4px solid #C87D32 !important;
    display: flex !important;
    align-items: center !important;
    gap: 20px !important;
    margin-bottom: 12px !important;
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

/* MEGA-MENU CLARO E 100% LEGÍVEL (CREME COM TEXTO ESCURO) */
div[data-testid="stPopover"] button,
button[data-testid="stPopoverButton"] {
    background-color: #F7EFE2 !important;
    color: #231F1E !important;
    border: 2px solid #C87D32 !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    width: 100% !important;
    padding: 10px 14px !important;
    box-shadow: 0 2px 4px rgba(35, 31, 30, 0.08) !important;
}
div[data-testid="stPopover"] button p,
div[data-testid="stPopover"] button span,
div[data-testid="stPopover"] button div,
button[data-testid="stPopoverButton"] p,
button[data-testid="stPopoverButton"] span,
button[data-testid="stPopoverButton"] div {
    color: #231F1E !important;
    font-weight: 700 !important;
    opacity: 1 !important;
}
div[data-testid="stPopover"] button svg,
button[data-testid="stPopoverButton"] svg {
    fill: #231F1E !important;
    color: #231F1E !important;
}
div[data-testid="stPopover"] button:hover,
button[data-testid="stPopoverButton"]:hover {
    background-color: #FCEDC9 !important;
    border-color: #8C4A27 !important;
}

/* CONTEÚDO INTERNO DO POPOVER (FUNDO CLARO E LEGÍVEL) */
div[data-testid="stPopoverBody"] {
    background-color: #FDFBF7 !important;
    border: 2px solid #C87D32 !important;
    border-radius: 10px !important;
}
div[data-testid="stPopoverBody"] p,
div[data-testid="stPopoverBody"] span,
div[data-testid="stPopoverBody"] strong {
    color: #231F1E !important;
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
    background-color: #362C28 !important;
}
section[data-testid="stSidebar"] div.stVerticalBlock > div {
    margin-bottom: -0.4rem !important;
}
section[data-testid="stSidebar"] hr {
    margin: 0.6rem 0 !important;
    border-color: #C87D32 !important;
}

/* CARTÕES DE MÉTRICAS (SEM CORTAR TEXTO) */
[data-testid="stMetric"] {
    background-color: #FFFFFF !important;
    border: 1px solid #E6D7C3 !important;
    border-left: 5px solid #C87D32 !important;
    border-radius: 10px !important;
    padding: 12px 14px !important;
}
[data-testid="stMetricLabel"] * {
    color: #7A634E !important;
    font-weight: 600 !important;
}
[data-testid="stMetricValue"] * {
    color: #231F1E !important;
    font-weight: 700 !important;
    font-size: 1.5rem !important;
}
.stButton > button {
    background: linear-gradient(135deg, #C87D32 0%, #8C4A27 100%) !important;
    color: #FFFFFF !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    border: none !important;
}
.stButton > button * {
    color: #FFFFFF !important;
}
[data-testid="stDownloadButton"] button {
    background-color: #2E5A44 !important;
    color: #FFFFFF !important;
    border-radius: 8px !important;
    border: none !important;
}
[data-testid="stDownloadButton"] button * {
    color: #FFFFFF !important;
}
.sos-visual-box {
    background-color: #FFFFFF;
    border: 1px solid #E6D7C3;
    border-radius: 10px;
    padding: 12px;
    margin-bottom: 12px;
    text-align: center;
}
</style>
"""
st.markdown(CSS_ESTILO, unsafe_allow_html=True)

# ==========================================
# 2. CATÁLOGO DE RECEITAS PRONTAS (INSPIRADAS NA FLEISCHMANN, SEM LEITE EM PÓ)
# ==========================================
RECEITAS_PRONTAS = {
    "meu_primeiro_pao": {
        "titulo": "🍞 Pão Caseiro Tradicional",
        "nome_formato": "Pão Caseiro Tradicional",
        "peso_porcao_g": 550,
        "qtd_padrao": 2,
        "hidratacao_pct": 60,
        "sal_pct": 2.0,
        "tipo_fermento": "Seco",
        "integral_pct": 0,
        "acucar_pct": 6.0,
        "gordura_pct": 5.0,
        "ovos_pct": 5.0,
        "metodo": "macio",
        "contem_gluten": True,
        "extra_nota": "",
        "descricao": "O básico bem feito: massa macia, casca dourada e cheiro de padaria em casa.",
    },
    "pao_frances": {
        "titulo": "🥖 Pão Francês Caseiro Crocante",
        "nome_formato": "Pão Francês Caseiro",
        "peso_porcao_g": 75,
        "qtd_padrao": 8,
        "hidratacao_pct": 62,
        "sal_pct": 2.0,
        "tipo_fermento": "Seco",
        "integral_pct": 0,
        "acucar_pct": 1.5,
        "gordura_pct": 2.0,
        "ovos_pct": 0.0,
        "metodo": "frances",
        "contem_gluten": True,
        "extra_nota": "",
        "descricao": "Casca fina e crocante, miolo aerado e forno bem quente com vapor.",
    },
    "pao_batata": {
        "titulo": "🥔 Pão de Batata Fofinho",
        "nome_formato": "Pão de Batata Caseiro",
        "peso_porcao_g": 70,
        "qtd_padrao": 12,
        "hidratacao_pct": 54,
        "sal_pct": 2.0,
        "tipo_fermento": "Seco",
        "integral_pct": 0,
        "acucar_pct": 6.0,
        "gordura_pct": 8.0,
        "ovos_pct": 10.0,
        "metodo": "batata",
        "contem_gluten": True,
        "extra_nota": "🥔 **Ingrediente extra desta receita:** Adicione **30% de purê de batata cozida e espremida morna** (ex: 150g de purê para cada 500g de farinha). Use batata Asterix ou Inglesa.",
        "descricao": "O segredo está na batata cozida e espremida morna, deixando o miolo super úmido e macio.",
    },
    "pao_forma": {
        "titulo": "🥪 Pão de Forma Caseiro",
        "nome_formato": "Pão de Forma Caseiro",
        "peso_porcao_g": 600,
        "qtd_padrao": 2,
        "hidratacao_pct": 60,
        "sal_pct": 2.0,
        "tipo_fermento": "Seco",
        "integral_pct": 0,
        "acucar_pct": 6.0,
        "gordura_pct": 6.0,
        "ovos_pct": 0.0,
        "metodo": "macio",
        "contem_gluten": True,
        "extra_nota": "",
        "descricao": "Miolo fechado, uniforme e macio, ideal para fatiar, fazer sanduíches e torradas.",
    },
    "air_fryer": {
        "titulo": "🔥 Pão na Air Fryer (Rápido)",
        "nome_formato": "Pão na Air Fryer",
        "peso_porcao_g": 60,
        "qtd_padrao": 8,
        "hidratacao_pct": 60,
        "sal_pct": 2.0,
        "tipo_fermento": "Seco",
        "integral_pct": 0,
        "acucar_pct": 5.0,
        "gordura_pct": 6.0,
        "ovos_pct": 8.0,
        "metodo": "air_fryer",
        "contem_gluten": True,
        "extra_nota": "",
        "descricao": "Bolinhas de 60g que assam em 12 a 15 min a 180 °C sem precisar ligar o forno grande.",
    },
    "liquidificador": {
        "titulo": "⚡ Pão de Liquidificador (Sem Sova)",
        "nome_formato": "Pão de Liquidificador",
        "peso_porcao_g": 700,
        "qtd_padrao": 1,
        "hidratacao_pct": 78,
        "sal_pct": 1.2,
        "tipo_fermento": "Seco",
        "integral_pct": 0,
        "acucar_pct": 8.0,
        "gordura_pct": 30.0,
        "ovos_pct": 16.0,
        "metodo": "liquidificador",
        "contem_gluten": True,
        "extra_nota": "",
        "descricao": "Proporção clássica batida no liquidificador e assada direto na forma de bolo inglês.",
    },
    "sem_sova": {
        "titulo": "🥣 Pão Sem Sova (Na Tigela)",
        "nome_formato": "Pão Sem Sova",
        "peso_porcao_g": 700,
        "qtd_padrao": 1,
        "hidratacao_pct": 72,
        "sal_pct": 2.0,
        "tipo_fermento": "Seco",
        "integral_pct": 0,
        "acucar_pct": 2.0,
        "gordura_pct": 3.0,
        "ovos_pct": 0.0,
        "metodo": "sem_sova",
        "contem_gluten": True,
        "extra_nota": "",
        "descricao": "Basta misturar com colher e deixar o tempo desenvolver a massa. Zero esforço.",
    },
    "frigideira": {
        "titulo": "🍳 Pão de Frigideira (Sem Forno)",
        "nome_formato": "Pão de Frigideira",
        "peso_porcao_g": 90,
        "qtd_padrao": 6,
        "hidratacao_pct": 62,
        "sal_pct": 2.0,
        "tipo_fermento": "Seco",
        "integral_pct": 0,
        "acucar_pct": 3.0,
        "gordura_pct": 5.0,
        "ovos_pct": 0.0,
        "metodo": "frigideira",
        "contem_gluten": True,
        "extra_nota": "",
        "descricao": "Assado na frigideira tampada em fogo baixo. Pronto em minutos.",
    },
    "integral_100": {
        "titulo": "🌾 Pão 100% Integral Macio",
        "nome_formato": "Pão 100% Integral",
        "peso_porcao_g": 550,
        "qtd_padrao": 2,
        "hidratacao_pct": 68,
        "sal_pct": 2.0,
        "tipo_fermento": "Seco",
        "integral_pct": 100,
        "acucar_pct": 5.0,
        "gordura_pct": 6.0,
        "ovos_pct": 0.0,
        "metodo": "macio",
        "contem_gluten": True,
        "extra_nota": "",
        "descricao": "Hidratação ajustada para a farinha integral absorver água e não ficar ressecado.",
    },
    "meio_integral": {
        "titulo": "🌾 Pão Meio Integral (50/50)",
        "nome_formato": "Pão Meio Integral (50/50)",
        "peso_porcao_g": 550,
        "qtd_padrao": 2,
        "hidratacao_pct": 64,
        "sal_pct": 2.0,
        "tipo_fermento": "Seco",
        "integral_pct": 50,
        "acucar_pct": 5.0,
        "gordura_pct": 5.0,
        "ovos_pct": 0.0,
        "metodo": "macio",
        "contem_gluten": True,
        "extra_nota": "",
        "descricao": "Equilíbrio entre a leveza da farinha branca e as fibras da integral.",
    },
    "sem_gluten": {
        "titulo": "🚫 Pão Sem Glúten (Liquidificador)",
        "nome_formato": "Pão Sem Glúten",
        "peso_porcao_g": 650,
        "qtd_padrao": 1,
        "hidratacao_pct": 80,
        "sal_pct": 1.8,
        "tipo_fermento": "Seco",
        "integral_pct": 0,
        "acucar_pct": 5.0,
        "gordura_pct": 10.0,
        "ovos_pct": 20.0,
        "metodo": "sem_gluten",
        "contem_gluten": False,
        "extra_nota": "🌾 **Mix Sem Glúten:** Use mix pronto sem glúten ou combine farinha de arroz + polvilho doce + fécula de batata. A goma xantana já está calculada abaixo.",
        "descricao": "Feito no liquidificador ou batedeira com protocolo de goma xantana para dar liga.",
    },
    "brioche": {
        "titulo": "🥐 Brioche Caseiro que Desfia",
        "nome_formato": "Brioche Caseiro",
        "peso_porcao_g": 90,
        "qtd_padrao": 10,
        "hidratacao_pct": 35,
        "sal_pct": 2.0,
        "tipo_fermento": "Seco",
        "integral_pct": 0,
        "acucar_pct": 10.0,
        "gordura_pct": 25.0,
        "ovos_pct": 30.0,
        "metodo": "brioche",
        "contem_gluten": True,
        "extra_nota": "",
        "descricao": "Receita francesa amanteigada com miolo amarelo que desfia em fios.",
    },
    "pao_doce": {
        "titulo": "🍩 Pão Doce Caseiro (Trança/Rosca)",
        "nome_formato": "Pão Doce Caseiro",
        "peso_porcao_g": 80,
        "qtd_padrao": 12,
        "hidratacao_pct": 55,
        "sal_pct": 1.5,
        "tipo_fermento": "Seco",
        "integral_pct": 0,
        "acucar_pct": 16.0,
        "gordura_pct": 12.0,
        "ovos_pct": 12.0,
        "metodo": "macio",
        "contem_gluten": True,
