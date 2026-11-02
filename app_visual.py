import streamlit as st
from PIL import Image
import io
import os
import base64
import json
import pandas as pd
from fpdf import FPDF
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
import firebase_admin
from firebase_admin import credentials, firestore

from motor_calculadora import CalculadoraPanificacao

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA & ESTÉTICA COMPACTA
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
    h1, h2, h3, h4, p, span, label {
        font-family: 'Plus Jakarta Sans', sans-serif;
        color: #2B2118 !important;
    }
    h1, h2, h3, h4 {
        font-family: 'Playfair Display', serif !important;
        color: #231F1E !important;
    }

    /* TÍTULO E SUBTÍTULO DO BANNER ESCURO */
    h1.cabecalho-titulo, span.cabecalho-titulo {
        color: #F5EFE6 !important;
        font-family: 'Playfair Display', serif !important;
    }
    p.cabecalho-sub, div.cabecalho-sub {
        color: #D6C7B2 !important;
    }

    /* CORREÇÃO DEFINITIVA DAS ABAS (TABS) NO TOPO */
    button[data-baseweb="tab"] {
        color: #4A3B32 !important;
        font-weight: 600 !important;
        font-size: 1.05rem !important;
    }
    button[data-baseweb="tab"] * {
        color: #4A3B32 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #C87D32 !important;
        border-bottom-color: #C87D32 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] * {
        color: #C87D32 !important;
    }

    /* CAIXA E BOTÃO DE UPLOAD DE ARQUIVOS */
    [data-testid="stFileUploader"] section {
        background-color: #F4ECE1 !important;
        border: 2px dashed #C87D32 !important;
    }
    [data-testid="stFileUploader"] section * {
        color: #231F1E !important;
    }
    [data-testid="stFileUploader"] button {
        background-color: #231F1E !important;
        color: #FFFFFF !important;
        border: none !important;
    }
    [data-testid="stFileUploader"] button * {
        color: #FFFFFF !important;
    }

    /* OTIMIZAÇÃO DA BARRA LATERAL (Sem rolagem) */
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

    /* Cartões e Métricas */
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
# 2. IA / LEITOR DE RÓTULOS
# ==========================================
class RotuloFarinha(BaseModel):
    marca: str = Field(description="Nome comercial ou fabricante da farinha")
    proteina_g_por_50g: float = Field(description="Proteína em gramas para porção de 50g")
    forca_estimada: str = Field(description="'Alta' se proteína >= 6.0, 'Média' se >= 5.0, senão 'Baixa'")
    hidratacao_minima: int = Field(description="Hidratação recomendada (%): 65 se Alta, 60 se Média, 55 se Baixa")
    contem_gluten: bool = Field(description="True se contiver glúten, False se for sem glúten")

def analisar_imagem_farinha(img: Image.Image, chave_api: str) -> dict:
    if not chave_api:
        return {"erro": "Chave da API Gemini não configurada no servidor."}

    client = genai.Client(api_key=chave_api)
    prompt = "Analise o rótulo/tabela nutricional desta farinha. Extraia a marca, proteína por 50g, força, hidratação mínima e contem_gluten (true/false)."
    configuracao = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=RotuloFarinha,
        temperature=0.1
    )

    for modelo in ["gemini-2.5-flash", "gemini-2.0-flash"]:
        try:
            response = client.models.generate_content(model=modelo, contents=[prompt, img], config=configuracao)
            return json.loads(response.text)
        except Exception:
            continue
    return {"erro": "Falha na análise com a IA Gemini."}

# ==========================================
# 3. FIREBASE & LOGO
# ==========================================
if not firebase_admin._apps:
    caminho_cred = os.path.join(os.path.dirname(__file__), "firebase_key.json")
    if os.path.exists(caminho_cred):
        cred = credentials.Certificate(caminho_cred)
        firebase_admin.initialize_app(cred)

db = firestore.client() if firebase_admin._apps else None

diretorio_atual = os.path.dirname(__file__)
caminho_logo = None
for nome_arq in ["logo_limpo.png", "logo_clean.png", "logo.png"]:
    if os.path.exists(os.path.join(diretorio_atual, nome_arq)):
        caminho_logo = os.path.join(diretorio_atual, nome_arq)
        break

def obter_base64_da_imagem(caminho):
    img = Image.open(caminho)
    bbox = img.getbbox()
    if bbox: img = img.crop(bbox)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()

def limpar_texto_pdf(texto: str) -> str:
    return str(texto).encode('latin-1', 'replace').decode('latin-1')

logo_b64 = obter_base64_da_imagem(caminho_logo) if caminho_logo else None

chave_api = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", ""))

# ==========================================
# 4. CABEÇALHO & BARRA LATERAL COMPACTA
# ==========================================
if logo_b64:
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #231F1E 0%, #362C28 100%); padding: 20px 26px; border-radius: 12px; border-bottom: 4px solid #C87D32; display: flex; align-items: center; gap: 20px; margin-bottom: 16px;">
        <div style="width: 80px; height: 80px; flex-shrink: 0;"><img src="data:image/png;base64,{logo_b64}" style="width: 100%; height: 100%; object-fit: contain;"></div>
        <div>
            <h1 class="cabecalho-titulo" style="margin: 0; font-size: 1.9rem; color: #F5EFE6 !important;">Massa Tradicional</h1>
            <p class="cabecalho-sub" style="color: #D6C7B2 !important; font-size: 0.92rem; margin: 2px 0 0 0;">Painel Profissional de Panificação & B2B Intelligence</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

FORMATOS_PADARIA = {
    "Pão de Cachorro-Quente (70g)": 70,
    "Pão de Hambúrguer / Brioche (90g)": 90,
    "Pão Francês / Mini Baguete (120g)": 120,
    "Focaccia Individual (250g)": 250,
    "Pão de Forma Tradicional (550g)": 550,
    "Pão de Forma Grande (650g)": 650,
    "Pão Rústico / Campagne (800g)": 800,
    "Personalizado (Definir gramas)": 0,
    "Peça Única (Sem divisão)": -1
}

with st.sidebar:
    if logo_b64:
        st.markdown(f'<div style="text-align: center; margin-bottom: 4px;"><img src="data:image/png;base64,{logo_b64}" style="width: 65px;"></div>', unsafe_allow_html=True)

    st.markdown("### 🥖 Planeamento")
    modo_planeamento = st.radio("Modo:", ["Pelo Peso Total da Massa (g)", "Pela Quantidade de Pães"])
    formato_escolhido = st.selectbox("Formato", list(FORMATOS_PADARIA.keys()))
    peso_padrao = FORMATOS_PADARIA[formato_escolhido]

    if peso_padrao == 0:
        peso_porcao_g = st.number_input("Peso por unidade (g)", 20, 3000, 100, 5)
        nome_formato = "Porção Personalizada"
    elif peso_padrao == -1:
        peso_porcao_g = 0
        nome_formato = "Peça Única"
    else:
        peso_porcao_g = peso_padrao
        nome_formato = formato_escolhido.split(" (")[0]

    if modo_planeamento == "Pelo Peso Total da Massa (g)":
        peso_desejado = st.slider("Peso Total (g)", 500, 15000, 3500, 100)
    else:
        if peso_porcao_g <= 0: peso_porcao_g = 70
        qtd_encomenda = st.number_input("Quantidade de Pães", 1, 500, 50, 1)
        peso_desejado = int(qtd_encomenda * peso_porcao_g)
        st.info(f"⚖️ **Massa Total:** {peso_desejado} g")

    st.markdown("---")
    tipo_fermento = st.selectbox("Fermento", ["Seco (1%)", "Fresco (3%)", "Levain (20%)"])
    fermento_limpo = tipo_fermento.split(" ")[0]
    sal_pct = st.slider("Sal (%)", 1.0, 3.5, 2.0, 0.1)
    temp_ambiente = st.number_input("Temp. Ambiente (°C)", 10.0, 40.0, 24.0, 0.5)

# ==========================================
# 5. ABAS CENTRAIS
# ==========================================
aba_calc, aba_extras, aba_custos, aba_b2b = st.tabs([
    "🚀 Calculadora & IA", 
    "🧈 Enriquecimento da Massa", 
    "💰 Custos & Precificação", 
    "📊 Telemetria B2B"
])

with aba_extras:
    st.subheader("Ingredientes de Enriquecimento (Percentagem sobre a Farinha)")
    perfil = st.selectbox("Perfil Rápido", ["Cachorro-Quente / Forma (Macio)", "Hambúrguer / Brioche (Rico)", "Pão Rústico (0%)", "Personalizado"])
    
    if "Cachorro" in perfil:
        def_acucar, def_gord, def_leite, def_ovos = 6.0, 5.0, 3.0, 0.0
    elif "Hambúrguer" in perfil:
        def_acucar, def_gord, def_leite, def_ovos = 10.0, 15.0, 4.0, 10.0
    elif "Rústico" in perfil:
        def_acucar, def_gord, def_leite, def_ovos = 0.0, 0.0, 0.0, 0.0
    else:
        def_acucar, def_gord, def_leite, def_ovos = 5.0, 5.0, 2.0, 0.0

    c1, c2 = st.columns(2)
    with c1:
        acucar_pct = st.slider("Açúcar (%)", 0.0, 25.0, def_acucar, 0.5)
        gordura_pct = st.slider("Manteiga / Óleo (%)", 0.0, 30.0, def_gord, 0.5)
    with c2:
        leite_po_pct = st.slider("Leite em Pó (%)", 0.0, 15.0, def_leite, 0.5)
        ovos_pct = st.slider("Ovos (%)", 0.0, 30.0, def_ovos, 1.0)

with aba_custos:
    st.subheader("Tabela de Custos dos Insumos & Margem Comercial")
    cc1, cc2 = st.columns(2)
    with cc1:
        c_farinha = st.number_input("Farin