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
        "extra_nota": "",
        "descricao": "Massa fofa e brilhante, perfeita para tranças, roscas ou creme de confeiteiro.",
    },
    "cachorro_quente": {
        "titulo": "🌭 Pão de Cachorro-Quente",
        "nome_formato": "Pão de Cachorro-Quente",
        "peso_porcao_g": 70,
        "qtd_padrao": 15,
        "hidratacao_pct": 58,
        "sal_pct": 2.0,
        "tipo_fermento": "Seco",
        "integral_pct": 0,
        "acucar_pct": 6.0,
        "gordura_pct": 5.0,
        "ovos_pct": 0.0,
        "metodo": "macio",
        "contem_gluten": True,
        "extra_nota": "",
        "descricao": "Bisnaga macia e estruturada para hot dog artesanal.",
    },
    "rustico": {
        "titulo": "🥖 Pão Rústico / Italiano",
        "nome_formato": "Pão Rústico / Campagne",
        "peso_porcao_g": 700,
        "qtd_padrao": 2,
        "hidratacao_pct": 66,
        "sal_pct": 2.2,
        "tipo_fermento": "Seco",
        "integral_pct": 15,
        "acucar_pct": 0.0,
        "gordura_pct": 0.0,
        "ovos_pct": 0.0,
        "metodo": "rustico",
        "contem_gluten": True,
        "extra_nota": "",
        "descricao": "Casca crocante e miolo aberto, com toque de 15% de farinha integral.",
    },
    "focaccia": {
        "titulo": "🫒 Focaccia de Alecrim",
        "nome_formato": "Focaccia Individual",
        "peso_porcao_g": 450,
        "qtd_padrao": 2,
        "hidratacao_pct": 72,
        "sal_pct": 2.2,
        "tipo_fermento": "Seco",
        "integral_pct": 0,
        "acucar_pct": 0.0,
        "gordura_pct": 6.0,
        "ovos_pct": 0.0,
        "metodo": "focaccia",
        "contem_gluten": True,
        "extra_nota": "",
        "descricao": "Massa de alta hidratação com azeite, covinhas, sal grosso e alecrim.",
    },
}

# ==========================================
# 3. ILUSTRAÇÕES VISUAIS DO SOS PADEIRO
# ==========================================
def renderizar_modelo_sos(chave: str, diretorio_base: str):
    for ext in ["jpg", "jpeg", "png"]:
        caminho_foto = os.path.join(diretorio_base, "imagens_sos", f"{chave}.{ext}")
        if os.path.exists(caminho_foto):
            st.image(caminho_foto, use_container_width=True)
            return

    svgs = {
        "mole": (
            '<svg viewBox="0 0 420 135" width="100%" xmlns="http://www.w3.org/2000/svg">'
            '<rect x="5" y="5" width="195" height="125" rx="10" fill="#FDF2F2" stroke="#E57373"/>'
            '<text x="102" y="24" text-anchor="middle" font-size="12" font-weight="bold" fill="#B71C1C">❌ Massa Mole / Espalhada</text>'
            '<ellipse cx="102" cy="98" rx="72" ry="18" fill="#F3E5AB" stroke="#C8A96A" stroke-width="2"/>'
            '<path d="M50 96 Q75 82 105 95 T155 96" fill="none" stroke="#D4B475" stroke-width="2"/>'
            '<text x="102" y="122" text-anchor="middle" font-size="10" fill="#7A634E">Escorre na bancada e gruda demais</text>'
            '<rect x="220" y="5" width="195" height="125" rx="10" fill="#F1F8F4" stroke="#66BB6A"/>'
            '<text x="317" y="24" text-anchor="middle" font-size="12" font-weight="bold" fill="#1B5E20">✅ Ponto Ideal (Lisa e Firme)</text>'
            '<path d="M262 105 C262 58 372 58 372 105 Z" fill="#F3E5AB" stroke="#C8A96A" stroke-width="2"/>'
            '<text x="317" y="122" text-anchor="middle" font-size="10" fill="#2E5A44">Segura o formato arredondado</text>'
            '</svg>'
        ),
        "pesado": (
            '<svg viewBox="0 0 420 135" width="100%" xmlns="http://www.w3.org/2000/svg">'
            '<rect x="5" y="5" width="195" height="125" rx="10" fill="#FDF2F2" stroke="#E57373"/>'
            '<text x="102" y="24" text-anchor="middle" font-size="12" font-weight="bold" fill="#B71C1C">❌ Miolo Pesado / Fechado</text>'
            '<path d="M40 105 C40 72 164 72 164 105 Z" fill="#DFC896" stroke="#8C4A27" stroke-width="3"/>'
            '<rect x="46" y="94" width="112" height="9" fill="#BFA36F" rx="3"/>'
            '<text x="102" y="122" text-anchor="middle" font-size="10" fill="#7A634E">Baixo, denso e faixa embatumada</text>'
            '<rect x="220" y="5" width="195" height="125" rx="10" fill="#F1F8F4" stroke="#66BB6A"/>'
            '<text x="317" y="24" text-anchor="middle" font-size="12" font-weight="bold" fill="#1B5E20">✅ Miolo Aerado e Leve</text>'
            '<path d="M255 105 C255 42 379 42 379 105 Z" fill="#FAF0D7" stroke="#A65E2E" stroke-width="3"/>'
            '<circle cx="290" cy="82" r="5" fill="#E6D2A8"/><circle cx="318" cy="70" r="6" fill="#E6D2A8"/>'
            '<circle cx="342" cy="85" r="5" fill="#E6D2A8"/><circle cx="308" cy="92" r="4" fill="#E6D2A8"/>'
            '<text x="317" y="122" text-anchor="middle" font-size="10" fill="#2E5A44">Alto, macio e com alvéolos</text>'
            '</svg>'
        ),
        "rachado": (
            '<svg viewBox="0 0 420 135" width="100%" xmlns="http://www.w3.org/2000/svg">'
            '<rect x="5" y="5" width="195" height="125" rx="10" fill="#FDF2F2" stroke="#E57373"/>'
            '<text x="102" y="24" text-anchor="middle" font-size="12" font-weight="bold" fill="#B71C1C">❌ Estouro na Lateral</text>'
            '<path d="M40 105 C40 48 164 48 164 105 Z" fill="#C87D32" stroke="#7A4419" stroke-width="2"/>'
            '<path d="M135 88 L162 82 L154 96 L168 95" fill="none" stroke="#FFF3D6" stroke-width="4"/>'
            '<text x="102" y="122" text-anchor="middle" font-size="10" fill="#7A634E">Rasgou na lateral (pouca fermentação)</text>'
            '<rect x="220" y="5" width="195" height="125" rx="10" fill="#F1F8F4" stroke="#66BB6A"/>'
            '<text x="317" y="24" text-anchor="middle" font-size="12" font-weight="bold" fill="#1B5E20">✅ Abertura no Corte (Pestana)</text>'
            '<path d="M255 105 C255 46 379 46 379 105 Z" fill="#C87D32" stroke="#7A4419" stroke-width="2"/>'
            '<path d="M292 60 Q318 44 345 62" fill="none" stroke="#FFF3D6" stroke-width="5" stroke-linecap="round"/>'
            '<text x="317" y="122" text-anchor="middle" font-size="10" fill="#2E5A44">Expansão controlada no topo</text>'
            '</svg>'
        ),
        "murchou": (
            '<svg viewBox="0 0 420 135" width="100%" xmlns="http://www.w3.org/2000/svg">'
            '<rect x="5" y="5" width="195" height="125" rx="10" fill="#FDF2F2" stroke="#E57373"/>'
            '<text x="102" y="24" text-anchor="middle" font-size="12" font-weight="bold" fill="#B71C1C">❌ Afundou no Meio</text>'
            '<path d="M40 105 L45 65 Q102 86 159 65 L164 105 Z" fill="#C87D32" stroke="#7A4419" stroke-width="2"/>'
            '<text x="102" y="122" text-anchor="middle" font-size="10" fill="#7A634E">Passou do ponto (superfermentou)</text>'
            '<rect x="220" y="5" width="195" height="125" rx="10" fill="#F1F8F4" stroke="#66BB6A"/>'
            '<text x="317" y="24" text-anchor="middle" font-size="12" font-weight="bold" fill="#1B5E20">✅ Topo Arredondado Firme</text>'
            '<path d="M255 105 C255 42 379 42 379 105 Z" fill="#C87D32" stroke="#7A4419" stroke-width="2"/>'
            '<text x="317" y="122" text-anchor="middle" font-size="10" fill="#2E5A44">Assado no ponto exato do dedo</text>'
            '</svg>'
        ),
        "palida": (
            '<svg viewBox="0 0 420 135" width="100%" xmlns="http://www.w3.org/2000/svg">'
            '<rect x="5" y="5" width="195" height="125" rx="10" fill="#FDF2F2" stroke="#E57373"/>'
            '<text x="102" y="24" text-anchor="middle" font-size="12" font-weight="bold" fill="#B71C1C">❌ Casca Pálida e Opaca</text>'
            '<path d="M40 105 C40 48 164 48 164 105 Z" fill="#EFE4C8" stroke="#CBB994" stroke-width="2"/>'
            '<text x="102" y="122" text-anchor="middle" font-size="10" fill="#7A634E">Forno frio ou sem vapor/pincelada</text>'
            '<rect x="220" y="5" width="195" height="125" rx="10" fill="#F1F8F4" stroke="#66BB6A"/>'
            '<text x="317" y="24" text-anchor="middle" font-size="12" font-weight="bold" fill="#1B5E20">✅ Casca Dourada Caramelizada</text>'
            '<path d="M255 105 C255 48 379 48 379 105 Z" fill="#B96A24" stroke="#6E3B10" stroke-width="2"/>'
            '<text x="317" y="122" text-anchor="middle" font-size="10" fill="#2E5A44">Forno bem preaquecido</text>'
            '</svg>'
        ),
    }
    svg_html = svgs.get(chave, "")
    if svg_html:
        st.markdown(f'<div class="sos-visual-box">{svg_html}</div>', unsafe_allow_html=True)

# ==========================================
# 4. FUNÇÕES AUXILIARES
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
        "fermento_seco": (10.0, "col. sopa"),
        "fermento_fresco": (15.0, "tab."),
        "levain": (240.0, "xíc."),
    }
    if tipo in fatores:
        div, un = fatores[tipo]
        return f"{formatar_fracao(gramas / div)} {un}"
    return f"{gramas} g"

def classificar_massa(nome_formato: str, receita: dict, contem_gluten: bool, metodo_forcado: str = "") -> str:
    if metodo_forcado:
        return metodo_forcado
    formato_lower = str(nome_formato).lower()
    if not contem_gluten:
        return "sem_gluten"
    if "focaccia" in formato_lower:
        return "focaccia"
    if "francês" in formato_lower:
        return "frances"
    if "rústico" in formato_lower or not receita.get("massa_enriquecida"):
        return "rustico"
    return "macio"

def gerar_modo_preparo(nome_formato: str, receita: dict, contem_gluten: bool, integral_pct: int = 0, metodo_forcado: str = "") -> list:
    temp_agua = receita.get("temp_agua_c", 22)
    peso_un = receita.get("peso_porcao_g", 0)
    qtd_un = receita.get("qtd_unidades", 1)
    tipo_massa = classificar_massa(nome_formato, receita, contem_gluten, metodo_forcado)

    dica_integral = ""
    if integral_pct >= 50:
        dica_integral = " (Dica integral: deixe descansar 20 min após misturar a água para o farelo hidratar bem.)"

    if tipo_massa == "frances":
        return [
            f"1. **Mistura e Sova:** Misture a farinha com o fermento seco. Junte o açúcar, sal, manteiga/óleo e a água ({temp_agua} °C). Sove até ficar lisa e elástica e descanse 30 min.",
            f"2. **Modelagem em 2 Etapas:** Divida em {qtd_un} partes de {peso_un}g, abra com rolo e enrole pressionando como rocambole. Cubra, descanse 15 min e repita a modelagem para casca fina.",
            "3. **Crescimento Final:** Deixe crescer coberto por cerca de 40 a 50 minutos enquanto o forno preaquece no máximo (225 °C a 250 °C) com uma assadeira funda vazia na grade inferior.",
            "4. **Corte e Vapor:** Faça um corte raso com lâmina afiada em cada pão. Coloque no forno, despeje água fervente na assadeira de baixo e feche rápido. Asse 15 min com vapor.",
            "5. **Crocância:** Retire a assadeira de água e asse por mais 10 a 15 min até dourar. Esfrie sobre grade (nunca coberto com pano) para manter a casca crocante.",
        ]
    if tipo_massa == "batata":
        return [
            "1. **Purê de Batata:** Cozinhe batatas Asterix ou Inglesas sem sal por 15-20 min até ficarem macias. Escorra bem e esprema ainda mornas (não deixe aguado).",
            f"2. **Mistura:** Bata ou misture o purê morno com água ({temp_agua} °C), ovos, açúcar, sal e manteiga. Junte a farinha e o fermento aos poucos.",
            "3. **Sova sem Excesso de Farinha:** A massa de pão de batata é naturalmente mais pegajosa. Unte as mãos e a bancada com um fio de óleo em vez de jogar muita farinha.",
            f"4. **Fermentação e Modelagem:** Deixe dobrar de volume (50 min). Divida em {qtd_un} bolinhas de {peso_un}g, acomode na assadeira e deixe crescer mais 35 min.",
            "5. **Forno:** Pincele gema diluída com um fio de água/leite de forma bem leve e asse a 180 °C por 20 a 25 min até dourar.",
        ]
    if tipo_massa == "brioche":
        return [
            f"1. **Mistura com Ovos:** Misture farinha, fermento, açúcar e sal. Adicione os ovos em temperatura ambiente e a água ({temp_agua} °C) aos poucos até formar massa firme.",
            "2. **Incorporação da Manteiga:** Sove até desenvolver glúten e adicione a manteiga gelada em cubos aos poucos. Se a massa esquentar (>25 °C), leve à geladeira por 15 min e retome.",
            "3. **Maturação a Frio:** Cubra e deixe fermentar 1h em temperatura ambiente, depois leve à geladeira (mínimo 4h ou de um dia para o outro) para firmar a manteiga.",
            f"4. **Modelagem Rápida:** Com a massa fria, divida em {qtd_un} porções de {peso_un}g (bolinhas, forma ou trança). Deixe dobrar de volume em temperatura ambiente (1h30 a 2h).",
            "5. **Forno:** Pincele gema e asse a 180 °C por 18-22 min (pequenos) ou 30-35 min (trança/forma). Espere esfriar 30 min na grade antes de fatiar.",
        ]
    if tipo_massa == "sem_sova":
        return [
            f"1. **Mistura na Tigela:** Misture todos os ingredientes com uma colher de pau usando água a {temp_agua} °C até não sobrar farinha seca.",
            "2. **Descanso Longo:** Cubra bem com plástico filme e deixe crescer de 2 a 3 horas em temperatura ambiente (ou 8h na geladeira).",
            "3. **Modelagem Leve:** Polvilhe farinha na bancada, despeje a massa sem apertar demais e dobre as pontas para o centro formando uma bola.",
            "4. **Segunda Fermentação:** Deixe descansar 30 min sobre papel manteiga enquanto o forno preaquece a 230 °C.",
            "5. **Forno:** Asse a 230 °C por 30 a 35 min (em panela de ferro tampada: 20 min tampado + 15 min destampado).",
        ]
    if tipo_massa == "air_fryer":
        return [
            f"1. **Mistura e Sova:** Misture farinha e fermento seco. Junte açúcar, sal, manteiga, ovo e água/líquido ({temp_agua} °C). Sove 6-8 min até ficar lisa.",
            f"2. **Modelagem:** Divida em {qtd_un} bolinhas de {peso_un}g (o tamanho ideal para assar por igual na Air Fryer sem queimar por fora).",
            "3. **Fermentação na Cesta:** Acomode na cesta com espaço entre elas e deixe crescer dentro da própria Air Fryer desligada por 35 a 45 min.",
            "4. **Assar:** Asse a 180 °C por 10 a 15 min até dourar (se dourar rápido demais no topo, reduza para 160 °C ou cubra com alumínio na metade do tempo).",
            "5. **Finalização:** Para casca ainda mais macia, pincele um pouco de manteiga derretida assim que retirar da cesta.",
        ]
    if tipo_massa == "liquidificador":
        return [
            f"1. **Bater Líquidos:** No liquidificador, bata a água ({temp_agua} °C), ovos, óleo, açúcar, sal e o fermento seco por 1 minuto.",
            "2. **Misturar a Farinha:** Despeje o líquido em uma tigela e misture a farinha aos poucos com uma colher até ficar uma massa mole e homogênea.",
            "3. **Forma Untada:** Transfira para forma de pão untada e enfarinhada (preenchendo metade da altura).",
            "4. **Crescimento:** Cubra com plástico e deixe crescer cerca de 50 a 60 min até dobrar de volume.",
            "5. **Forno:** Asse em forno preaquecido a 180 °C por cerca de 30 minutos até dourar bem. Espere amornar para desenformar.",
        ]
    if tipo_massa == "frigideira":
        return [
            f"1. **Mistura:** Misture farinha, fermento, açúcar, sal, água ({temp_agua} °C) e óleo. Sove por 5 min até ficar macia.",
            "2. **Descanso:** Cubra e deixe descansar por 25 minutos.",
            f"3. **Abrir Discos:** Divida em {qtd_un} porções de {peso_un}g e abra em discos de cerca de 1 cm de espessura.",
            "4. **Frigideira Tampada:** Aqueça frigideira antiaderente em fogo bem baixo (fio de óleo). Coloque o disco e tampe.",
            "5. **Virar:** Deixe 4 a 5 minutos de cada lado até dourar e assar por dentro.",
        ]
    if tipo_massa == "sem_gluten":
        return [
            "1. **Mistura Seca:** Misture o mix de farinha sem glúten, a goma xantana, sal, açúcar e fermento seco.",
            f"2. **Bater no Liquidificador/Batedeira:** Adicione a água ({temp_agua} °C), ovos e óleo, batendo por 4 min até ficar um creme liso.",
            "3. **Modelagem Direta:** Despeje direto na forma untada e alise a superfície com espátula molhada.",
            "4. **Crescimento:** Cubra e deixe crescer em local protegido por 35 a 45 min até perto da borda.",
            "5. **Forno:** Asse a 190 °C por 35 a 45 min. Espere esfriar completamente antes de fatiar.",
        ]
    if tipo_massa == "focaccia":
        return [
            f"1. **Mistura Inicial:** Misture farinha, fermento e água ({temp_agua} °C). Descanse 15 min e junte sal e azeite.",
            "2. **Dobras:** Faça 3 séries de dobras (Stretch & Fold) na tigela com intervalos de 30 min.",
            "3. **Fermentação na Forma:** Transfira para assadeira bem untada com azeite e descanse 45 a 60 min.",
            "4. **Cobertura:** Regue com azeite, faça covinhas com os dedos e salpique sal grosso e alecrim.",
            "5. **Forno:** Asse em forno preaquecido a 220 °C por 20 a 25 min até dourar bem.",
        ]
    if tipo_massa == "rustico":
        return [
            f"1. **Autólise:** Misture apenas a(s) farinha(s) e a água ({temp_agua} °C) e descanse coberto por 30 min.{dica_integral}",
            "2. **Incorporação:** Adicione o fermento e o sal, misturando até homogeneizar.",
            "3. **Dobras:** Faça 3 a 4 séries de dobras a cada 30 min. Fermente até crescer cerca de 60%.",
            f"4. **Divisão e Modelagem:** Divida em {qtd_un} porção(ões) de {peso_un}g, pré-modele, descanse 15 min e modele com tensão.",
            "5. **Forno com Vapor:** Preaqueça a 240 °C com assadeira vazia embaixo. Faça o corte e use vapor nos primeiros 15 min. Asse por 25-35 min.",
        ]
    return [
        f"1. **Mistura Inicial:** Misture a(s) farinha(s), o fermento e o açúcar. Junte a água ({temp_agua} °C) e os ovos aos poucos.{dica_integral}",
        "2. **Sova e Teste da Janela:** Sove por 8 a 10 min. Adicione o sal e, por último, a manteiga em pomada até a massa esticar fina sem rasgar.",
        "3. **Primeira Fermentação:** Cubra a massa e deixe descansar por 50 a 60 min até dobrar de volume.",
        f"4. **Divisão e Modelagem:** Divida em {qtd_un} un. de {peso_un}g, boleie, descanse 10 min e modele ({nome_formato}).",
        "5. **Segunda Fermentação e Forno:** Deixe dobrar na assadeira (35-50 min). Asse a 180-200 °C por 20-35 min. Bata na base: se soar oco, está pronto! Nunca corte ainda quente.",
    ]

def gerar_cronograma_reverso(hora_pronto: datetime.time, nome_formato: str, receita: dict, contem_gluten: bool, metodo_forcado: str = "") -> list:
    tipo_massa = classificar_massa(nome_formato, receita, contem_gluten, metodo_forcado)
    base_dt = datetime.datetime.combine(datetime.date.today(), hora_pronto)

    if tipo_massa in ["air_fryer", "frigideira"]:
        etapas_min = [
            (75, "🥣 Mistura e sova rápida"),
            (60, "✂️ Modelar bolinhas/discos e descansar"),
            (15, "🔥 Assar na Air Fryer / Frigideira"),
            (0, "✅ Pães quentinhos prontos!"),
        ]
    elif tipo_massa in ["liquidificador", "sem_gluten"]:
        etapas_min = [
            (95, "⚡ Bater líquidos e misturar a farinha"),
            (85, "🍞 Despejar na forma untada e cobrir"),
            (40, "🔥 Preaquecer forno a 180-190 °C"),
            (35, "⏲️ Levar ao forno"),
            (0, "✅ Pão pronto! Esfriar na grade"),
        ]
    elif tipo_massa == "frances":
        etapas_min = [
            (145, "🥣 Mistura e sova até ficar elástica"),
            (130, "⏳ 1º descanso (30 min)"),
            (100, "✂️ Dividir e 1ª modelagem (rocambole) + 15 min descanso"),
            (85, "🥖 2ª modelagem e fermentação final"),
            (50, "🔥 Preaquecer forno no máximo (240 °C) com assadeira vazia"),
            (30, "🔪 Fazer corte e assar 15 min com vapor + 15 min seco"),
            (0, "✅ Pão francês crocante pronto!"),
        ]
    elif tipo_massa == "sem_sova":
        etapas_min = [
            (215, "🥣 Misturar tudo na tigela com colher"),
            (65, "✂️ Modelar bola na bancada enfarinhada"),
            (45, "🔥 Preaquecer forno a 230 °C"),
            (35, "⏲️ Levar ao forno"),
            (0, "✅ Pão crocante pronto!"),
        ]
    elif tipo_massa == "rustico":
        etapas_min = [
            (270, "💧 Autólise (farinha + água)"),
            (240, "🦠 Incorporar fermento e sal"),
            (210, "🔄 1ª dobra"),
            (180, "🔄 2ª dobra"),
            (150, "🔄 3ª dobra e fermentação em bloco"),
            (90, "✂️ Divisão, pré-modelagem e modelagem"),
            (55, "🔥 Preaquecer forno no máximo (240 °C)"),
            (30, "🔪 Corte (pestana) e assar com vapor"),
            (0, "✅ Pão rústico pronto!"),
        ]
    else:
        etapas_min = [
            (155, "🥣 Mistura e sova até ponto de véu"),
            (135, "⏳ Início da 1ª fermentação"),
            (85, "✂️ Divisão, boleamento e modelagem"),
            (70, "⏳ Início da 2ª fermentação na assadeira"),
            (40, "🔥 Preaquecer forno a 180 °C"),
            (25, "🥚 Pincelar gema e levar ao forno"),
            (0, "✅ Fornada pronta!"),
        ]

    agenda = []
    for min_antes, desc in etapas_min:
        horario = (base_dt - datetime.timedelta(minutes=min_antes)).strftime("%H:%M")
        agenda.append({"Horário": horario, "Etapa da Produção": desc})
    return agenda

def calcular_tabela_nutricional(receita: dict) -> dict:
    farinha = float(receita.get("farinha_g", 0) or 0)
    acucar = float(receita.get("acucar_g", 0) or 0)
    gordura = float(receita.get("gordura_g", 0) or 0)
    ovos = float(receita.get("ovos_g", 0) or 0)
    sal = float(receita.get("sal_g", 0) or 0)
    fermento = float(receita.get("fermento_g", 0) or 0)

    kcal = farinha * 3.60 + acucar * 3.87 + gordura * 7.17 + ovos * 1.43 + fermento * 2.95
    carb = farinha * 0.75 + acucar * 1.00 + ovos * 0.01 + fermento * 0.38
    prot = farinha * 0.11 + gordura * 0.01 + ovos * 0.13 + fermento * 0.38
    gord = farinha * 0.014 + gordura * 0.81 + ovos * 0.095 + fermento * 0.04
    sodio_mg = sal * 388.0 + ovos * 1.4

    qtd_un = int(receita.get("qtd_unidades", 1) or 1)
    peso_un = float(receita.get("peso_porcao_g", 0) or 0)
    peso_total = float(receita.get("peso_total_g", 100) or 100)

    if peso_un > 0 and qtd_un > 0:
        divisor = qtd_un
        rotulo_porcao = f"1 unidade ({int(peso_un)}g massa crua)"
    else:
        divisor = max(peso_total / 100.0, 1.0)
        rotulo_porcao = "Porção de 100g (massa crua)"

    return {
        "porcao": rotulo_porcao,
        "kcal": round(kcal / divisor),
        "carboidratos_g": round(carb / divisor, 1),
        "proteinas_g": round(prot / divisor, 1),
        "gorduras_g": round(gord / divisor, 1),
        "sodio_mg": round(sodio_mg / divisor),
    }

def montar_texto_whatsapp(dados_ia: dict, receita: dict, usar_caseira: bool, chave_ferm: str, passos: list, integral_pct: int) -> str:
    linhas = [
        "🌾 *MASSA TRADICIONAL - FICHA DE PRODUÇÃO*",
        f"🥖 *Formato:* {receita.get('nome_formato')} ({receita.get('qtd_unidades')} un. de {receita.get('peso_porcao_g')}g)",
        f"🏷️ *Farinha:* {dados_ia.get('marca')} | *Massa Total:* {receita.get('peso_total_g')}g",
        "",
        "📋 *INGREDIENTES:*",
    ]

    def fmt(val_g, tipo_med, sufixo="g"):
        if usar_caseira:
            return f"{converter_medida_caseira(val_g, tipo_med)} ({val_g}{sufixo})"
        return f"{val_g} {sufixo}"

    farinha_total = float(receita.get("farinha_g", 0) or 0)
    if integral_pct > 0:
        far_int = round(farinha_total * (integral_pct / 100.0))
        far_bra = round(farinha_total - far_int)
        if far_bra > 0:
            linhas.append(f"• Farinha Branca: {fmt(far_bra, 'farinha')}")
        linhas.append(f"• Farinha Integral ({integral_pct}%): {fmt(far_int, 'farinha')}")
    else:
        linhas.append(f"• Farinha de Trigo: {fmt(farinha_total, 'farinha')}")

    linhas.append(f"• Água ({receita.get('temp_agua_c')}°C): {fmt(receita.get('agua_ml', 0), 'agua', 'ml')}")
    linhas.append(f"• Sal: {fmt(receita.get('sal_g', 0), 'sal')}")
    linhas.append(f"• Fermento ({receita.get('tipo_fermento')}): {fmt(receita.get('fermento_g', 0), chave_ferm)}")

    if (receita.get("acucar_g", 0) or 0) > 0:
        linhas.append(f"• Açúcar: {fmt(receita.get('acucar_g', 0), 'acucar')}")
    if (receita.get("gordura_g", 0) or 0) > 0:
        linhas.append(f"• Manteiga/Óleo: {fmt(receita.get('gordura_g', 0), 'gordura')}")
    if (receita.get("ovos_g", 0) or 0) > 0:
        linhas.append(f"• Ovos: {receita.get('ovos_g')} g (~{receita.get('unidades_ovos_inteiras')} un.)")
    if not dados_ia.get("contem_gluten", True) and "goma_xantana_g" in receita:
        linhas.append(f"• Goma Xantana: {receita.get('goma_xantana_g')} g")

    linhas.append("")
    linhas.append("👨‍🍳 *MODO DE PREPARO:*")
    for p in passos:
        linhas.append(p.replace("**", "*"))

    return "\n".join(linhas)

# ==========================================
# 5. IA / LEITOR DE RÓTULOS & FIREBASE
# ==========================================
class RotuloFarinha(BaseModel):
    marca: str = Field(description="Nome comercial ou fabricante da farinha")
    proteina_g_por_50g: float = Field(description="Proteína em gramas para porção de 50g")
    forca_estimada: str = Field(description="'Alta' se proteína >= 6.0, 'Média' se >= 5.0, senão 'Baixa'")
    hidratacao_minima: int = Field(description="Hidratação recomendada (%): 65 se Alta, 60 se Média, 55 se Baixa")
    contem_gluten: bool = Field(description="True se contiver glúten, False se for sem glúten")

def analisar_imagem_farinha(img: Image.Image, chave_api_val: str) -> dict:
    if not chave_api_val:
        return {"erro": "Chave da API Gemini não configurada no servidor."}
    client = genai.Client(api_key=chave_api_val)
    prompt = "Analise o rótulo/tabela nutricional desta farinha. Extraia marca, proteína por 50g, força, hidratação mínima e contem_gluten."
    configuracao = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=RotuloFarinha,
        temperature=0.1,
    )
    for modelo in ["gemini-2.5-flash", "gemini-2.0-flash"]:
        try:
            response = client.models.generate_content(model=modelo, contents=[prompt, img], config=configuracao)
            return json.loads(response.text)
        except Exception:
            continue
    return {"erro": "Falha na análise com a IA Gemini."}

if not firebase_admin._apps:
    caminho_cred = os.path.join(os.path.dirname(__file__), "firebase_key.json")
    try:
        if os.path.exists(caminho_cred):
            cred = credentials.Certificate(caminho_cred)
            firebase_admin.initialize_app(cred)
        elif "firebase" in st.secrets:
            cred = credentials.Certificate(dict(st.secrets["firebase"]))
            firebase_admin.initialize_app(cred)
    except Exception:
        pass

db = firestore.client() if firebase_admin._apps else None

def verificar_acesso_pro(credencial: str) -> bool:
    if not ATIVAR_PAYWALL:
        return True
    chave = str(credencial or "").strip()
    if not chave:
        return False
    if chave.upper() == CHAVE_MESTRA_ADMIN:
        return True
    if db is not None:
        try:
            doc = db.collection("usuarios_pro").document(chave.lower()).get()
            if doc.exists and doc.to_dict().get("ativo", True):
                return True
        except Exception:
            return False
    return False

diretorio_atual = os.path.dirname(__file__)
caminho_logo = None
for nome_arq in ["logo_limpo.png", "logo_clean.png", "logo.png"]:
    if os.path.exists(os.path.join(diretorio_atual, nome_arq)):
        caminho_logo = os.path.join(diretorio_atual, nome_arq)
        break

def obter_base64_da_imagem(caminho):
    img = Image.open(caminho)
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()

def limpar_texto_pdf(texto: str) -> str:
    return str(texto).encode("latin-1", "replace").decode("latin-1")

logo_b64 = obter_base64_da_imagem(caminho_logo) if caminho_logo else None
chave_api = obter_secret("GEMINI_API_KEY", "")

# ==========================================
# 6. ESTADO DE NAVEGAÇÃO & GERADOR DE PRESET
# ==========================================
if "pagina_atual" not in st.session_state:
    st.session_state["pagina_atual"] = "receita_pronta"
if "receita_id_atual" not in st.session_state:
    st.session_state["receita_id_atual"] = "meu_primeiro_pao"

c_farinha = st.session_state.get("c_farinha", 5.50)
c_fermento = st.session_state.get("c_fermento", 35.0)
c_acucar = st.session_state.get("c_acucar", 4.50)
c_sal = st.session_state.get("c_sal", 3.0)
c_gordura = st.session_state.get("c_gordura", 18.0)
c_ovo_unidade = st.session_state.get("c_ovo_unidade", 0.75)
margem_lucro = st.session_state.get("margem_lucro", 100.0)

def gerar_receita_preset(receita_id: str, qtd_override: int = None, temp_amb: float = 24.0):
    preset = RECEITAS_PRONTAS[receita_id]
    qtd = qtd_override if qtd_override is not None else preset["qtd_padrao"]
    peso_total_preset = int(qtd * preset["peso_porcao_g"])
    tem_gluten = preset.get("contem_gluten", True)
    dados_preset = {
        "marca": f"Receita Padrão ({preset['nome_formato']})",
        "proteina_g_por_50g": 6.0,
        "forca_estimada": "Padrão",
        "hidratacao_minima": preset["hidratacao_pct"],
        "contem_gluten": tem_gluten,
    }
    calc_p = CalculadoraPanificacao(
        peso_total_massa=peso_total_preset,
        hidratacao_pct=preset["hidratacao_pct"],
        sal_pct=preset["sal_pct"],
        tipo_fermento=preset["tipo_fermento"],
        temp_ambiente=temp_amb,
        contem_gluten=tem_gluten,
        peso_porcao_g=preset["peso_porcao_g"],
        nome_formato=preset["nome_formato"],
        acucar_pct=preset["acucar_pct"],
        gordura_pct=preset["gordura_pct"],
        leite_po_pct=0.0,
        ovos_pct=preset["ovos_pct"],
        custo_farinha_kg=c_farinha,
        custo_fermento_kg=c_fermento,
        custo_acucar_kg=c_acucar,
        custo_gordura_kg=c_gordura,
        custo_leite_po_kg=0.0,
        custo_ovo_unidade=c_ovo_unidade,
        custo_sal_kg=c_sal,
        margem_lucro_pct=margem_lucro,
    )
    st.session_state["resultado_atual"] = {
        "dados_ia": dados_preset,
        "receita": calc_p.calcular(),
        "integral_pct": preset["integral_pct"],
        "metodo": preset.get("metodo", "macio"),
        "extra_nota": preset.get("extra_nota", ""),
    }

# ==========================================
# 7. BANNER & MEGA-MENU SUPERIOR (CLARO E LEGÍVEL)
# ==========================================
if logo_b64:
    logo_html = '<img src="data:image/png;base64,' + logo_b64 + '" style="width: 100%; height: 100%; object-fit: contain;">'
else:
    logo_html = "🌾"

banner_html = (
    '<div id="banner-topo">'
    f'<div style="width: 78px; height: 78px; flex-shrink: 0;">{logo_html}</div>'
    '<div>'
    '<div class="titulo-principal">Massa Tradicional</div>'
    '<div class="subtitulo-principal">Receitas Prontas, Calculadora Profissional & B2B Intelligence</div>'
    '</div></div>'
)
st.markdown(banner_html, unsafe_allow_html=True)

nav1, nav2, nav3, nav4 = st.columns(4)

with nav1:
    with st.popover("🍞 Receitas Prontas", use_container_width=True):
        mc1, mc2, mc3 = st.columns(3)
        with mc1:
            st.markdown("**⚡ Pão Fácil**")
            for rid in ["meu_primeiro_pao", "pao_frances", "pao_batata", "air_fryer", "liquidificador", "sem_sova", "frigideira"]:
                if st.button(RECEITAS_PRONTAS[rid]["titulo"], key=f"nav_{rid}", use_container_width=True):
                    st.session_state["pagina_atual"] = "receita_pronta"
                    st.session_state["receita_id_atual"] = rid
                    gerar_receita_preset(rid)
                    st.rerun()
        with mc2:
            st.markdown("**🌾 Integrais & Especiais**")
            for rid in ["integral_100", "meio_integral", "sem_gluten", "pao_forma", "cachorro_quente"]:
                if st.button(RECEITAS_PRONTAS[rid]["titulo"], key=f"nav_{rid}", use_container_width=True):
                    st.session_state["pagina_atual"] = "receita_pronta"
                    st.session_state["receita_id_atual"] = rid
                    gerar_receita_preset(rid)
                    st.rerun()
        with mc3:
            st.markdown("**🥐 Doces & Artesanais**")
            for rid in ["brioche", "pao_doce", "rustico", "focaccia"]:
                if st.button(RECEITAS_PRONTAS[rid]["titulo"], key=f"nav_{rid}", use_container_width=True):
                    st.session_state["pagina_atual"] = "receita_pronta"
                    st.session_state["receita_id_atual"] = rid
                    gerar_receita_preset(rid)
                    st.rerun()

with nav2:
    with st.popover("🛠️ Faça Você Mesmo", use_container_width=True):
        st.markdown("**Monte sua receita do zero**")
        if st.button("🚀 Calculadora Avançada & Scanner IA", key="nav_calc", use_container_width=True):
            st.session_state["pagina_atual"] = "calculadora"
            st.rerun()
        if st.button("🧈 Enriquecimento (Açúcar / Manteiga / Ovos)", key="nav_extra", use_container_width=True):
            st.session_state["pagina_atual"] = "enriquecimento"
            st.rerun()
        if st.button("💰 Tabela de Custos & Precificação", key="nav_custos", use_container_width=True):
            st.session_state["pagina_atual"] = "custos"
            st.rerun()

with nav3:
    with st.popover("📚 Escola & SOS Padeiro", use_container_width=True):
        ec1, ec2 = st.columns(2)
        with ec1:
            st.markdown("**📖 Aprenda o Básico**")
            if st.button("🦠 Diferenças de Fermentos", key="nav_escola_ferm", use_container_width=True):
                st.session_state["pagina_atual"] = "escola"
                st.rerun()
            if st.button("🙌 Como Sovar & Ponto de Véu", key="nav_escola_sova", use_container_width=True):
                st.session_state["pagina_atual"] = "escola"
                st.rerun()
        with ec2:
            st.markdown("**🆘 SOS Visual**")
            if st.button("🔍 Abrir Diagnóstico Visual de Pães", key="nav_sos", use_container_width=True):
                st.session_state["pagina_atual"] = "sos"
                st.rerun()

with nav4:
    with st.popover("📊 B2B & PRO", use_container_width=True):
        st.markdown("**Gestão & Assinatura**")
        if st.button("📊 Telemetria B2B (Firebase)", key="nav_b2b", use_container_width=True):
            st.session_state["pagina_atual"] = "b2b"
            st.rerun()

# ==========================================
# 8. BARRA LATERAL CONTEXTUAL
# ==========================================
FORMATOS_PADARIA = {
    "Pão de Cachorro-Quente (70g)": 70,
    "Pão Francês (75g)": 75,
    "Pão de Hambúrguer / Brioche (90g)": 90,
    "Focaccia Individual (250g)": 250,
    "Pão de Forma Tradicional (550g)": 550,
    "Pão Integral Tradicional (550g)": 550,
    "Pão de Forma Grande (650g)": 650,
    "Pão Rústico / Campagne (800g)": 800,
    "Personalizado (Definir gramas)": 0,
    "Peça Única (Sem divisão)": -1,
}

with st.sidebar:
    if caminho_logo:
        st.image(caminho_logo, width=65)

    pagina = st.session_state["pagina_atual"]

    if pagina == "receita_pronta":
        rid_atual = st.session_state["receita_id_atual"]
        preset_atual = RECEITAS_PRONTAS[rid_atual]
        st.markdown("### ⚡ Ajuste Rápido")
        st.caption(f"Receita ativa: **{preset_atual['nome_formato']}**")
        qtd_pronta = st.number_input("Quantas unidades?", min_value=1, max_value=100, value=preset_atual["qtd_padrao"], step=1)
        temp_ambiente = st.number_input("Temp. Ambiente (°C)", min_value=10.0, max_value=40.0, value=24.0, step=0.5)
        if st.button("🔄 Atualizar Quantidade", use_container_width=True):
            gerar_receita_preset(rid_atual, qtd_pronta, temp_ambiente)
    elif pagina in ["calculadora", "enriquecimento", "custos"]:
        st.markdown("### 🥖 Planejamento Avançado")
        opcoes_modo = [
            "Pelo Peso Total da Massa (g)",
            "Pela Quantidade de Pães",
            "Por Farinha Disponível (Estoque)",
        ]
        modo_planeamento = st.radio("Modo de Cálculo:", opcoes_modo)
        formato_escolhido = st.selectbox("Formato do Pão", list(FORMATOS_PADARIA.keys()))
        peso_padrao = FORMATOS_PADARIA[formato_escolhido]

        if peso_padrao == 0:
            peso_porcao_g = st.number_input("Peso por unidade (g)", min_value=20, max_value=3000, value=100, step=5)
            nome_formato = "Porção Personalizada"
        elif peso_padrao == -1:
            peso_porcao_g = 0
            nome_formato = "Peça Única"
        else:
            peso_porcao_g = peso_padrao
            nome_formato = formato_escolhido.split(" (")[0]

        if modo_planeamento == "Pelo Peso Total da Massa (g)":
            peso_desejado = st.slider("Peso Total (g)", 500, 15000, 3500, 100)
        elif modo_planeamento == "Pela Quantidade de Pães":
            if peso_porcao_g <= 0:
                peso_porcao_g = 70
            qtd_encomenda = st.number_input("Quantidade de Pães", min_value=1, max_value=500, value=50, step=1)
            peso_desejado = int(qtd_encomenda * peso_porcao_g)
            st.info(f"⚖️ **Massa Total:** {peso_desejado} g")
        else:
            farinha_disponivel_g = st.number_input("Farinha Disponível (g)", min_value=100, max_value=50000, value=1000, step=100)
            peso_desejado = int(farinha_disponivel_g * 1.65)
            st.info(f"🌾 **Estoque Farinha:** {farinha_disponivel_g}g")

        default_integral = 50 if "Integral" in formato_escolhido else 0
        farinha_integral_pct = st.slider("Farinha Integral (%)", 0, 100, default_integral, 10)
        tipo_fermento = st.selectbox("Fermento", ["Seco (1%)", "Fresco (3%)", "Levain (20%)"])
        fermento_limpo = tipo_fermento.split(" ")[0]
        sal_pct = st.slider("Sal (%)", 1.0, 3.5, 2.0, 0.1)
        temp_ambiente = st.number_input("Temp. Ambiente (°C)", min_value=10.0, max_value=40.0, value=24.0, step=0.5)
    else:
        st.markdown("### 🌾 Massa Tradicional")
        st.caption("Use o menu superior para escolher uma receita pronta ou montar a sua.")
        temp_ambiente = 24.0

    st.markdown("---")
    st.markdown("### 🔑 Acesso PRO")
    credencial_pro = st.text_input("E-mail ou Chave PRO", placeholder="seu@email.com")
    usuario_pro = verificar_acesso_pro(credencial_pro)
    if not ATIVAR_PAYWALL:
        st.caption("🟢 Modo Teste: Recursos PRO liberados")
    elif usuario_pro:
        st.success("✅ Plano PRO Ativo")
    else:
        st.warning("🔒 Modo Gratuito")

# ==========================================
# 9. CONTEÚDO PRINCIPAL POR PÁGINA
# ==========================================
mostrar_resultado = False
acucar_pct = st.session_state.get("acucar_pct", 5.0)
gordura_pct = st.session_state.get("gordura_pct", 5.0)
ovos_pct = st.session_state.get("ovos_pct", 0.0)

if pagina == "receita_pronta":
    mostrar_resultado = True
    rid_atual = st.session_state["receita_id_atual"]
    preset_atual = RECEITAS_PRONTAS[rid_atual]
    if "resultado_atual" not in st.session_state:
        gerar_receita_preset(rid_atual, qtd_pronta, temp_ambiente)

    st.info(
        f"**{preset_atual['titulo']}** — {preset_atual['descricao']}\n\n"
        "💡 Quer trocar de pão? Clique em **🍞 Receitas Prontas** no menu acima. Quer mudar a quantidade? Ajuste na barra lateral à esquerda."
    )

elif pagina == "enriquecimento":
    st.subheader("🧈 Enriquecimento da Massa (% sobre a Farinha)")
    st.info("Defina açúcar, manteiga/óleo e ovos em percentagem sobre o peso da farinha.")
    opcoes_perfil = [
        "Cachorro-Quente / Forma (Macio)",
        "Hambúrguer / Brioche (Rico)",
        "Pão Integral Macio",
        "Pão Rústico (0%)",
        "Personalizado",
    ]
    perfil = st.selectbox("Perfil Rápido", opcoes_perfil)
    if "Cachorro" in perfil:
        def_acucar, def_gord, def_ovos = 6.0, 5.0, 0.0
    elif "Hambúrguer" in perfil:
        def_acucar, def_gord, def_ovos = 10.0, 15.0, 10.0
    elif "Integral" in perfil:
        def_acucar, def_gord, def_ovos = 5.0, 6.0, 0.0
    elif "Rústico" in perfil:
        def_acucar, def_gord, def_ovos = 0.0, 0.0, 0.0
    else:
        def_acucar, def_gord, def_ovos = float(acucar_pct), float(gordura_pct), float(ovos_pct)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.session_state["acucar_pct"] = st.slider("Açúcar (%)", 0.0, 25.0, def_acucar, 0.5)
    with c2:
        st.session_state["gordura_pct"] = st.slider("Manteiga / Óleo (%)", 0.0, 30.0, def_gord, 0.5)
    with c3:
        st.session_state["ovos_pct"] = st.slider("Ovos (%)", 0.0, 30.0, def_ovos, 1.0)

    if st.button("🚀 Ir para Calculadora & Gerar Ficha"):
        st.session_state["pagina_atual"] = "calculadora"
        st.rerun()

elif pagina == "custos":
    st.subheader("💰 Tabela de Custos dos Insumos & Margem Comercial")
    st.info("Informe o preço pago pelos ingredientes para calcular o custo total, custo por pão e preço sugerido.")
    cc1, cc2 = st.columns(2)
    with cc1:
        st.number_input("Farinha (R$/kg)", min_value=2.0, max_value=20.0, value=float(c_farinha), step=0.5, key="c_farinha")
        st.number_input("Fermento (R$/kg)", min_value=10.0, max_value=100.0, value=float(c_fermento), step=1.0, key="c_fermento")
        st.number_input("Açúcar (R$/kg)", min_value=2.0, max_value=15.0, value=float(c_acucar), step=0.5, key="c_acucar")
        st.number_input("Sal (R$/kg)", min_value=1.0, max_value=10.0, value=float(c_sal), step=0.5, key="c_sal")
    with cc2:
        st.number_input("Manteiga / Gordura (R$/kg)", min_value=5.0, max_value=60.0, value=float(c_gordura), step=1.0, key="c_gordura")
        st.number_input("Ovo (R$ por UNIDADE)", min_value=0.20, max_value=2.00, value=float(c_ovo_unidade), step=0.05, key="c_ovo_unidade")
        st.slider("Margem de Lucro Desejada (%)", 20.0, 300.0, float(margem_lucro), 10.0, key="margem_lucro")

    if st.button("🚀 Voltar para Calculadora"):
        st.session_state["pagina_atual"] = "calculadora"
        st.rerun()

elif pagina == "calculadora":
    mostrar_resultado = True
    st.subheader("🚀 Calculadora Avançada & Scanner de Rótulo")
    st.info("Configure peso, formato e % de farinha integral na barra lateral. Se quiser, envie a foto da farinha para a IA ler a proteína.")
    col_up, col_prev = st.columns([2, 1])
    with col_up:
        if usuario_pro:
            foto_upload = st.file_uploader("Enviar foto da tabela nutricional (Opcional)", type=["jpg", "jpeg", "png"])
        else:
            foto_upload = None
            st.warning("🔒 O Scanner de Rótulos por IA é exclusivo do **Plano PRO**.")
        b_acao = st.button("✨ Calcular Ficha de Produção Completa")

    if foto_upload is not None:
        img = Image.open(foto_upload)
        with col_prev:
            st.image(img, caption="Rótulo", use_container_width=True)

    if b_acao:
        with st.spinner("Processando cálculo matemático e inteligência..."):
            dados_ia = {
                "marca": "Farinha Padrão / Manual",
                "proteina_g_por_50g": 6.0,
                "forca_estimada": "Alta",
                "hidratacao_minima": 60,
                "contem_gluten": True,
            }
            if foto_upload is not None:
                if not chave_api:
                    st.error("⚠️ Chave API Gemini não configurada nas Secrets do Streamlit.")
                else:
                    res_ia = analisar_imagem_farinha(Image.open(foto_upload), chave_api)
                    if "erro" not in res_ia:
                        dados_ia = res_ia

            hidr_ajustada = int(dados_ia.get("hidratacao_minima", 60) + round(farinha_integral_pct * 0.08))
            calc = CalculadoraPanificacao(
                peso_total_massa=peso_desejado,
                hidratacao_pct=hidr_ajustada,
                sal_pct=sal_pct,
                tipo_fermento=fermento_limpo,
                temp_ambiente=temp_ambiente,
                contem_gluten=dados_ia.get("contem_gluten", True),
                peso_porcao_g=peso_porcao_g,
                nome_formato=nome_formato,
                acucar_pct=acucar_pct,
                gordura_pct=gordura_pct,
                leite_po_pct=0.0,
                ovos_pct=ovos_pct,
                custo_farinha_kg=c_farinha,
                custo_fermento_kg=c_fermento,
                custo_acucar_kg=c_acucar,
                custo_gordura_kg=c_gordura,
                custo_leite_po_kg=0.0,
                custo_ovo_unidade=c_ovo_unidade,
                custo_sal_kg=c_sal,
                margem_lucro_pct=margem_lucro,
            )
            st.session_state["resultado_atual"] = {
                "dados_ia": dados_ia,
                "receita": calc.calcular(),
                "integral_pct": farinha_integral_pct,
                "metodo": "",
                "extra_nota": "",
            }
            st.success("Ficha calculada com sucesso!")

elif pagina == "escola":
    st.subheader("📚 Escola do Pão — Guia Rápido para Iniciantes")
    with st.expander("🦠 Diferenças entre Fermento Seco, Fresco e Levain", expanded=True):
        st.markdown(
            "- **Fermento Biológico Seco (1%):** É o mais prático para iniciantes. Vem em sachê de 10g e vai direto na farinha, sem precisar dissolver antes.\n"
            "- **Fermento Biológico Fresco (3%):** Vendido em tabletes refrigerados (15g). Use **3 vezes** o peso do fermento seco (10g seco = 30g fresco).\n"
            "- **Levain / Fermento Natural (20%):** Feito apenas de farinha e água fermentados. Traz casca crocante, sabor complexo e maior digestibilidade."
        )
    with st.expander("🙌 Como Sovar e Teste da Janela (Ponto de Véu)"):
        st.markdown(
            "- **Na mão:** Empurre a massa para frente com a base da palma, dobre de volta e gire 90°. Repita por 8 a 10 minutos.\n"
            "- **Teste da Janela:** Estique um pedacinho da massa devagar com os dedos. Se abrir fino quase transparente sem rasgar, o glúten está pronto!"
        )
    with st.expander("⏱️ Regras de Ouro da Fermentação e Forno"):
        st.markdown(
            "- **Temperatura da água:** Prefira entre 25 °C e 30 °C (nunca acima de 40 °C, pois mata o fermento).\n"
            "- **Sal x Fermento:** Nunca coloque o sal encostado direto no fermento — misture o fermento na farinha primeiro.\n"
            "- **Nunca corte quente:** O miolo termina de cozinhar fora do forno; espere esfriar sobre uma grade para não ficar empapado."
        )

elif pagina == "sos":
    st.subheader("🆘 SOS Padeiro — Guia Visual de Diagnóstico")
    st.info("Compare o visual do seu pão com os modelos abaixo para descobrir o que aconteceu e como corrigir.")

    with st.expander("💧 A massa ficou muito mole ou grudenta", expanded=True):
        renderizar_modelo_sos("mole", diretorio_atual)
        st.markdown(
            "- **Causa:** Farinha com menos proteína, excesso de água ou falta de desenvolvimento de glúten.\n"
            "- **Solução imediata:** Descanse 15 min coberta e faça 2 séries de dobras com mãos untadas. Se precisar, adicione farinha aos poucos (1 col. sopa por vez)."
        )
    with st.expander("🧱 O pão ficou pesado, duro ou com miolo fechado"):
        renderizar_modelo_sos("pesado", diretorio_atual)
        st.markdown(
            "- **Causa:** Falta de fermentação, excesso de farinha na bancada ou fermento inativo.\n"
            "- **Solução:** Teste o fermento em água morna com açúcar (deve espumar em 10 min) e aguarde a massa dobrar de volume."
        )
    with st.expander("🌋 O pão rachou na lateral ou abriu fora do corte"):
        renderizar_modelo_sos("rachado", diretorio_atual)
        st.markdown(
            "- **Causa:** Fermentação insuficiente na 2ª etapa ou falta de vapor no início.\n"
            "- **Solução:** Fermente mais 10-15 min antes de assar e faça o corte em ângulo de 45°."
        )
    with st.expander("📉 O pão cresceu muito e murchou no forno"):
        renderizar_modelo_sos("murchou", diretorio_atual)
        st.markdown(
            "- **Causa:** Superfermentação (passou do ponto).\n"
            "- **Solução:** Faça o teste do dedo: aperte leve; se voltar devagar deixando leve marca, leve ao forno. Em dias quentes (>28 °C), use água gelada."
        )
    with st.expander("🥖 A casca ficou pálida ou seca demais"):
        renderizar_modelo_sos("palida", diretorio_atual)
        st.markdown(
            "- **Causa:** Forno frio ou tempo excessivo em temperatura baixa.\n"
            "- **Solução:** Preaqueça o forno por 20 min. Pincele gema em pães macios ou use vapor nos primeiros 15 min em pães rústicos."
        )

elif pagina == "b2b":
    st.subheader("📊 Telemetria B2B & Histórico")
    st.info("Histórico de farinhas escaneadas e simulações salvas no Firebase.")
    if db is None:
        st.info("Firebase não configurado.")
    else:
        try:
            docs = db.collection("scans_farinha").stream()
            lista = [d.to_dict() for d in docs]
            if lista:
                st.dataframe(pd.DataFrame(lista), use_container_width=True)
            else:
                st.info("Nenhum registo na base de dados.")
        except Exception as e:
            st.error(f"Erro: {e}")

# ==========================================
# 10. EXIBIÇÃO DOS RESULTADOS (FICHA TÉCNICA)
# ==========================================
if mostrar_resultado and "resultado_atual" in st.session_state:
    res = st.session_state["resultado_atual"]
    dados_ia = res["dados_ia"]
    receita = res["receita"]
    integral_pct = int(res.get("integral_pct", 0) or 0)
    metodo_forcado = res.get("metodo", "")
    extra_nota = res.get("extra_nota", "")
    contem_gluten = dados_ia.get("contem_gluten", True)

    st.markdown("---")
    if not contem_gluten:
        st.warning("⚠️ **PROTOCOLO SEM GLÚTEN:** Adicionado 2% de Goma Xantana.")
    if integral_pct > 0:
        st.info(f"🌾 **Receita com {integral_pct}% de Farinha Integral:** Hidratação ajustada automaticamente para manter o pão macio.")
    if extra_nota:
        st.warning(extra_nota)

    st.subheader(f"📋 Ficha Técnica — {dados_ia.get('marca')} ({receita.get('peso_total_g', 0)}g de Massa)")

    unidade_exibicao = st.radio(
        "Escolha como deseja visualizar os ingredientes:",
        ["🥄 Medidas Caseiras (Xícaras / Colheres)", "⚖️ Balança (gramas / ml)"],
        horizontal=True,
    )
    usar_caseira = "Caseiras" in unidade_exibicao

    tipo_ferm = str(receita.get("tipo_fermento", "Seco")).lower()
    chave_ferm = "fermento_seco"
    if "fresco" in tipo_ferm:
        chave_ferm = "fermento_fresco"
    elif "levain" in tipo_ferm:
        chave_ferm = "levain"

    farinha_g = float(receita.get("farinha_g", 0) or 0)
    farinha_int_g = round(farinha_g * (integral_pct / 100.0)) if integral_pct > 0 else 0
    farinha_bra_g = round(farinha_g - farinha_int_g)
    agua_ml = receita.get("agua_ml", 0) or 0
    sal_g = receita.get("sal_g", 0) or 0
    fermento_g = receita.get("fermento_g", 0) or 0

    if integral_pct > 0 and farinha_bra_g > 0:
        m0, m1, m2, m3, m4 = st.columns(5)
        if usar_caseira:
            m0.metric("🌾 Far. Branca", converter_medida_caseira(farinha_bra_g, "farinha"), f"{farinha_bra_g} g")
            m1.metric(f"🌾 Far. Integral ({integral_pct}%)", converter_medida_caseira(farinha_int_g, "farinha"), f"{farinha_int_g} g")
            m2.metric("💧 Água", converter_medida_caseira(agua_ml, "agua"), f"{agua_ml} ml | {receita.get('temp_agua_c')} °C")
            m3.metric("🧂 Sal", converter_medida_caseira(sal_g, "sal"), f"{sal_g} g")
            m4.metric("🦠 Fermento", converter_medida_caseira(fermento_g, chave_ferm), f"{fermento_g} g")
        else:
            m0.metric("🌾 Far. Branca", f"{farinha_bra_g} g")
            m1.metric(f"🌾 Far. Integral ({integral_pct}%)", f"{farinha_int_g} g")
            m2.metric("💧 Água", f"{agua_ml} ml", f"Ideal: {receita.get('temp_agua_c')} °C")
            m3.metric("🧂 Sal", f"{sal_g} g")
            m4.metric("🦠 Fermento", f"{fermento_g} g")
    else:
        titulo_far = "🌾 Farinha Integral (100%)" if integral_pct == 100 else "🌾 Farinha Base"
        m1, m2, m3, m4 = st.columns(4)
        if usar_caseira:
            m1.metric(titulo_far, converter_medida_caseira(farinha_g, "farinha"), f"{int(farinha_g)} g")
            m2.metric("💧 Água", converter_medida_caseira(agua_ml, "agua"), f"{agua_ml} ml | {receita.get('temp_agua_c')} °C")
            m3.metric("🧂 Sal", converter_medida_caseira(sal_g, "sal"), f"{sal_g} g")
            m4.metric("🦠 Fermento", converter_medida_caseira(fermento_g, chave_ferm), f"{fermento_g} g")
        else:
            m1.metric(titulo_far, f"{int(farinha_g)} g")
            m2.metric("💧 Água", f"{agua_ml} ml", f"Ideal: {receita.get('temp_agua_c')} °C")
            m3.metric("🧂 Sal", f"{sal_g} g")
            m4.metric("🦠 Fermento", f"{fermento_g} g")

    acucar_g = receita.get("acucar_g", 0) or 0
    gordura_g = receita.get("gordura_g", 0) or 0
    ovos_g = receita.get("ovos_g", 0) or 0
    ovos_un = receita.get("unidades_ovos_inteiras", 0) or 0

    if acucar_g > 0 or gordura_g > 0 or ovos_g > 0:
        e1, e2, e3 = st.columns(3)
        if usar_caseira:
            e1.metric("🍬 Açúcar", converter_medida_caseira(acucar_g, "acucar"), f"{acucar_g} g")
            e2.metric("🧈 Manteiga / Óleo", converter_medida_caseira(gordura_g, "gordura"), f"{gordura_g} g")
            e3.metric("🥚 Ovos", f"{ovos_un} un.", f"{ovos_g} g")
        else:
            e1.metric("🍬 Açúcar", f"{acucar_g} g")
            e2.metric("🧈 Manteiga / Óleo", f"{gordura_g} g")
            e3.metric("🥚 Ovos", f"{ovos_g} g", f"~{ovos_un} unidades")

    if not contem_gluten and "goma_xantana_g" in receita:
        st.metric("🧪 Goma Xantana (Liga Sem Glúten)", f"{receita.get('goma_xantana_g')} g")

    p1, p2, p3 = st.columns(3)
    p1.metric("🥖 Formato", receita.get("nome_formato", "-"), f"{receita.get('peso_porcao_g', 0)}g/un")
    p2.metric("📦 Rendimento", f"{receita.get('qtd_unidades', 0)} unidades")
    p3.metric("✂️ Sobra", f"{receita.get('sobra_massa_g', 0)} g")

    passos_preparo = gerar_modo_preparo(receita.get("nome_formato", ""), receita, contem_gluten, integral_pct, metodo_forcado)
    with st.expander("👨‍🍳 Modo de Preparo Profissional (Passo a Passo)", expanded=True):
        for passo in passos_preparo:
            st.markdown(passo)

    with st.expander("⏰ Cronograma Reverso da Fornada (Planeje o Horário)"):
        hora_alvo = st.time_input("Que horas você quer o pão saindo do forno?", value=datetime.time(18, 0))
        agenda_fornada = gerar_cronograma_reverso(hora_alvo, receita.get("nome_formato", ""), receita, contem_gluten, metodo_forcado)
        st.table(pd.DataFrame(agenda_fornada))

    with st.expander("🥗 Estimativa de Tabela Nutricional (Referência TACO)"):
        nutri = calcular_tabela_nutricional(receita)
        st.caption(f"Valores aproximados para: **{nutri['porcao']}** (estimativa informativa).")
        n1, n2, n3, n4, n5 = st.columns(5)
        n1.metric("🔥 Calorias", f"{nutri['kcal']} kcal")
        n2.metric("🌾 Carboidratos", f"{nutri['carboidratos_g']} g")
        n3.metric("💪 Proteínas", f"{nutri['proteinas_g']} g")
        n4.metric("🧈 Gorduras", f"{nutri['gorduras_g']} g")
        n5.metric("🧂 Sódio", f"{nutri['sodio_mg']} mg")

    st.markdown("#### 💰 Custos & Precificação Comercial")
    custo_tot = float(receita.get("custo_total_fornada", 0) or 0)
    custo_un = float(receita.get("custo_por_unidade", 0) or 0)
    preco_sug = float(receita.get("preco_sugerido_unidade", 0) or 0)
    if usuario_pro:
        f1, f2, f3 = st.columns(3)
        f1.metric("💵 Custo Total", f"R$ {custo_tot:.2f}")
        f2.metric("🏷️ Custo / Unidade", f"R$ {custo_un:.2f}")
        f3.metric("💡 Preço Sugerido", f"R$ {preco_sug:.2f}", f"Margem: {receita.get('margem_lucro_pct', 0)}%")
    else:
        st.info("🔒 A análise de **Custos & Precificação** faz parte do Plano PRO.")

    # ==========================================
    # 11. EXPORTAÇÃO: PDF & WHATSAPP
    # ==========================================
    st.markdown("#### 📤 Exportar & Compartilhar")
    if usuario_pro:
        bytes_pdf = b""
        peso_total_int = int(receita.get("peso_total_g", 0) or 0)
        nome_formato_limpo = str(receita.get("nome_formato", "pao")).lower().replace(" ", "_")

        try:
            pdf = FPDF()
            pdf.add_page()
            largura_util = pdf.w - 2 * pdf.l_margin

            if caminho_logo:
                pdf.image(caminho_logo, x=10, y=10, w=24)
            pdf.set_font("Arial", "B", 18)
            espaco = "          " if caminho_logo else ""
            pdf.cell(largura_util, 12, txt=limpar_texto_pdf(f"{espaco}MASSA TRADICIONAL - FICHA DE BANCADA"), ln=True)
            pdf.ln(10)

            pdf.set_font("Arial", "", 11)
            r1 = f"Farinha: {dados_ia.get('marca')} | Massa Total: {peso_total_int}g | Hidratacao: {receita.get('hidratacao_pct')}%"
            r2 = f"Rendimento: {receita.get('qtd_unidades')} un. de {receita.get('peso_porcao_g')}g ({receita.get('nome_formato')})"
            r3 = f"Custo Total: R$ {custo_tot:.2f} | Custo/Un: R$ {custo_un:.2f} | Preco Sugerido: R$ {preco_sug:.2f}"
            pdf.cell(largura_util, 8, txt=limpar_texto_pdf(r1), ln=True)
            pdf.cell(largura_util, 8, txt=limpar_texto_pdf(r2), ln=True)
            pdf.cell(largura_util, 8, txt=limpar_texto_pdf(r3), ln=True)
            pdf.ln(5)

            col_w = largura_util / 2.0
            pdf.set_fill_color(35, 31, 30)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(col_w, 10, " Insumo", border=1, fill=True)
            pdf.cell(col_w, 10, " Quantidade (Balanca / Caseira)", border=1, fill=True, ln=True)

            pdf.set_text_color(0, 0, 0)
            linhas = []
            if integral_pct > 0:
                if farinha_bra_g > 0:
                    linhas.append(("Farinha Branca", f"{farinha_bra_g} g ({converter_medida_caseira(farinha_bra_g, 'farinha')})"))
                linhas.append((f"Farinha Integral ({integral_pct}%)", f"{farinha_int_g} g ({converter_medida_caseira(farinha_int_g, 'farinha')})"))
            else:
                linhas.append(("Farinha Base", f"{int(farinha_g)} g ({converter_medida_caseira(farinha_g, 'farinha')})"))

            linhas.extend([
                ("Água Filtrada", f"{agua_ml} ml ({converter_medida_caseira(agua_ml, 'agua')}) a {receita.get('temp_agua_c')}C"),
                ("Sal", f"{sal_g} g ({converter_medida_caseira(sal_g, 'sal')})"),
                (f"Fermento ({receita.get('tipo_fermento')})", f"{fermento_g} g ({converter_medida_caseira(fermento_g, chave_ferm)})"),
            ])
            if acucar_g > 0:
                linhas.append(("Açúcar", f"{acucar_g} g ({converter_medida_caseira(acucar_g, 'acucar')})"))
            if gordura_g > 0:
                linhas.append(("Manteiga / Óleo", f"{gordura_g} g ({converter_medida_caseira(gordura_g, 'gordura')})"))
            if ovos_g > 0:
                linhas.append(("Ovos", f"{ovos_g} g (~{ovos_un} un.)"))
            if not contem_gluten and "goma_xantana_g" in receita:
                linhas.append(("Goma Xantana", f"{receita.get('goma_xantana_g')} g"))

            for ins, qtd in linhas:
                pdf.cell(col_w, 10, limpar_texto_pdf(f" {ins}"), border=1)
                pdf.cell(col_w, 10, limpar_texto_pdf(f" {qtd}"), border=1, ln=True)

            pdf.ln(6)
            pdf.set_x(pdf.l_margin)
            pdf.set_font("Arial", "B", 12)
            pdf.cell(largura_util, 8, txt="MODO DE PREPARO", ln=True)
            pdf.set_font("Arial", "", 10)
            for p in passos_preparo:
                pdf.set_x(pdf.l_margin)
                pdf.multi_cell(largura_util, 6, txt=limpar_texto_pdf(p.replace("**", "")))

            saida_pdf = pdf.output(dest="S")
            bytes_pdf = saida_pdf.encode("latin-1", errors="ignore") if isinstance(saida_pdf, str) else bytes(saida_pdf)
        except Exception as e:
            bytes_pdf = b""
            st.error(f"Erro ao gerar o PDF: {e}")

        texto_wpp = montar_texto_whatsapp(dados_ia, receita, usar_caseira, chave_ferm, passos_preparo, integral_pct)
        url_wpp = "https://wa.me/?text=" + quote(texto_wpp)

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if len(bytes_pdf) > 0:
                st.download_button(
                    label="📄 Baixar Ficha Técnica em PDF",
                    data=bytes_pdf,
                    file_name=f"ficha_tecnica_{nome_formato_limpo}_{peso_total_int}g.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
        with col_btn2:
            st.link_button("📲 Enviar Ficha pelo WhatsApp", url_wpp, use_container_width=True)

        with st.expander("📋 Copiar texto pronto para WhatsApp"):
            st.code(texto_wpp, language="text")
    else:
        st.info("🔒 A exportação em **PDF** e o envio direto para **WhatsApp** fazem parte do Plano PRO.")
