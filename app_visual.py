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
""", unsafe_allow_html=True)

# ==========================================
# 2. FUNÇÕES AUXILIARES (MEDIDAS, PREPARO, CRONOGRAMA, NUTRICIONAL, WHATSAPP)
# ==========================================
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
    if tipo == "farinha":
        return f"{formatar_fracao(gramas / 120.0)} xíc."
    if tipo == "agua":
        return f"{formatar_fracao(gramas / 240.0)} xíc."
    if tipo == "sal":
        return f"{formatar_fracao(gramas / 5.0)} col. chá"
    if tipo == "acucar":
        return f"{formatar_fracao(gramas / 12.0)} col. sopa"
    if tipo == "gordura":
        return f"{formatar_fracao(gramas / 15.0)} col. sopa"
    if tipo == "leite_po":
        return f"{formatar_fracao(gramas / 10.0)} col. sopa"
    if tipo == "fermento_seco":
        return f"{formatar_fracao(gramas / 10.0)} col. sopa"
    if tipo == "fermento_fresco":
        return f"{formatar_fracao(gramas / 15.0)} tab."
    if tipo == "levain":
        return f"{formatar_fracao(gramas / 240.0)} xíc."
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
            "1. **Mistura Seca:** Em uma tigela grande, misture bem a farinha sem glúten, a goma xantana, o sal, o fermento e os demais secos.",
            f"2. **Hidratação:** Adicione a água (a {temp_agua} °C) e os líquidos aos poucos, batendo com batedeira (gancho ou raquete) por 4 a 5 minutos até formar uma massa cremosa e homogênea.",
            "3. **Modelagem Direta:** Massas sem glúten não precisam de primeira fermentação longa. Transfira direto para a forma untada e alise a superfície com uma espátula molhada.",
            "4. **Crescimento:** Cubra e deixe crescer em local protegido por 35 a 50 minutos (até atingir a borda da forma).",
            "5. **Forno:** Asse em forno preaquecido a 190 °C por 35 a 45 minutos até dourar bem. Espere esfriar completamente antes de fatiar."
        ]

    if tipo_massa == "focaccia":
        return [
            f"1. **Mistura Inicial:** Misture a farinha, o fermento e a água (a {temp_agua} °C) até não restar farinha seca. Descanse 15 minutos e incorpore o sal e o azeite.",
            "2. **Dobras (Stretch & Fold):** Faça 3 séries de dobras na própria tigela com intervalos de 30 minutos para criar estrutura e bolhas de ar.",
            "3. **Fermentação na Forma:** Transfira a massa para uma assadeira bem untada com azeite e deixe descansar por 45 a 60 minutos até preencher a forma.",
            "4. **Cobertura e Covinhas:** Regue com azeite, pressione a massa suavemente com a ponta dos dedos para criar as covinhas e salpique sal grosso e alecrim.",
            "5. **Forno:** Asse em forno preaquecido a 220 °C por 20 a 25 minutos até ficar dourada e crocante por fora."
        ]

    if tipo_massa == "rustico":
        return [
            f"1. **Autólise:** Misture apenas a farinha e a água (a {temp_agua} °C) e deixe descansar coberto por 30 minutos para desenvolver o glúten naturalmente.",
            "2. **Incorporação:** Adicione o fermento e o sal, misturando bem até homogeneizar.",
            "3. **Dobras:** Realize 3 a 4 séries de dobras a cada 30 minutos na tigela. Deixe fermentar até crescer cerca de 60%.",
            f"4. **Divisão e Modelagem:** Divida em {qtd_un} porção(ões) de {peso_un}g (se aplicável), faça a pré-modelagem, descanse 15 minutos e modele com tensão.",
            "5. **Forno com Vapor:** Preaqueça o forno no máximo (230 °C a 250 °C) com uma assadeira vazia embaixo. Faça o corte (pestana), leve ao forno e jogue água/gelo na assadeira inferior para gerar vapor nos primeiros 15 minutos. Asse por 25 a 35 minutos."
        ]

    return [
        f"1. **Mistura Inicial:** Em uma tigela ou masseira, misture a farinha, o fermento, o açúcar e o leite em pó. Adicione a água (a {temp_agua} °C) e os ovos aos poucos até formar uma massa única.",
        "2. **Sova e Ponto de Véu:** Sove por cerca de 8 minutos. Adicione o sal e, por último, a manteiga/gordura em ponto de pomada, sovando até a massa ficar bem lisa, elástica e soltar das mãos.",
        "3. **Primeira Fermentação:** Forme uma bola, cubra com plástico ou pano úmido e deixe descansar por 40 a 60 minutos (ou até dobrar de volume).",
        f"4. **Divisão e Modelagem:** Divida a massa em {qtd_un} unidade(s) de {peso_un}g, boleie, deixe descansar 10 minutos para relaxar o glúten e modele no formato de {nome_formato}.",
        "5. **Segunda Fermentação e Forno:** Acomode na assadeira untada e deixe dobrar de volume (35 a 50 min). Pincele gema com leite (opcional) e asse em forno preaquecido a 180 °C por 18 a 25 min (pães pequenos) ou 30 a 35 min (pães grandes)."
    ]

def gerar_cronograma_reverso(hora_pronto: datetime.time, nome_formato: str, receita: dict, contem_gluten: bool) -> list:
    tipo_massa = classificar_massa(nome_formato, receita, contem_gluten)
    base_dt = datetime.datetime.combine(datetime.date.today(), hora_pronto)

    if tipo_massa == "sem_gluten":
        etapas_min = [
            (95, "🥣 Pesagem e mistura dos ingredientes (batedeira)"),
            (85, "🍞 Transferir para a forma untada e alisar"),
            (40, "🔥 Preaquecer forno a 190 °C"),
            (35, "⏲️ Colocar no forno"),
