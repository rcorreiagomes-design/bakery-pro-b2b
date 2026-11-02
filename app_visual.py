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
# 1. CONFIGURAÇÃO DA PÁGINA E ESTÉTICA
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

    section[data-testid="stSidebar"] {
        background-color: #231F1E !important;
        border-right: 2px solid #C87D32;
    }
    section[data-testid="stSidebar"] * {
        color: #F5EFE6 !important;
    }
    section[data-testid="stSidebar"] input, 
    section[data-testid="stSidebar"] select {
        color: #231F1E !important;
    }

    [data-testid="stMetric"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E6D7C3 !important;
        border-left: 5px solid #C87D32 !important;
        border-radius: 10px !important;
        padding: 16px !important;
        box-shadow: 0 4px 12px rgba(43, 33, 24, 0.05) !important;
    }
    [data-testid="stMetricLabel"] * {
        color: #7A634E !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        font-size: 0.78rem !important;
        letter-spacing: 0.04em;
    }
    [data-testid="stMetricValue"] * {
        color: #231F1E !important;
        font-weight: 700 !important;
    }

    .stButton > button {
        background: linear-gradient(135deg, #C87D32 0%, #8C4A27 100%) !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.6rem 1.4rem !important;
        box-shadow: 0 4px 10px rgba(140, 74, 39, 0.25) !important;
    }

    [data-testid="stDownloadButton"] button {
        background-color: #2E5A44 !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 0.6rem 1.4rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. ESQUEMA DE IA E LEITOR DE RÓTULOS
# ==========================================
class RotuloFarinha(BaseModel):
    marca: str = Field(description="Nome comercial ou fabricante da farinha")
    proteina_g_por_50g: float = Field(description="Proteína em gramas para porção de 50g")
    forca_estimada: str = Field(description="'Alta' se proteína >= 6.0, 'Média' se >= 5.0, senão 'Baixa'")
    hidratacao_minima: int = Field(description="Hidratação recomendada (%): 65 se Alta, 60 se Média, 55 se Baixa")
    contem_gluten: bool = Field(description="True se contiver glúten, False se for sem glúten")

def analisar_imagem_farinha(img: Image.Image, chave_api: str) -> dict:
    api_key = chave_api or os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return {"erro": "Chave da API Gemini não fornecida."}

    client = genai.Client(api_key=api_key)
    prompt = (
        "Analise o rótulo/tabela nutricional desta farinha. Extraia a marca, "
        "calcule a proteína exata para 50g, classifique a força ('Alta', 'Média', 'Baixa'), "
        "defina a hidratação mínima (65, 60 ou 55) e verifique se contém glúten (true/false)."
    )
    configuracao = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=RotuloFarinha,
        temperature=0.1
    )

    for modelo in ["gemini-2.5-flash", "gemini-2.0-flash"]:
        try:
            response = client.models.generate_content(
                model=modelo,
                contents=[prompt, img],
                config=configuracao
            )
            return json.loads(response.text)
        except Exception:
            continue
    return {"erro": "Falha na análise com a IA Gemini."}

# ==========================================
# 3. FIREBASE E LOGO
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
    teste_caminho = os.path.join(diretorio_atual, nome_arq)
    if os.path.exists(teste_caminho):
        caminho_logo = teste_caminho
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
    return str(texto).encode('latin-1', 'replace').decode('latin-1')

logo_b64 = obter_base64_da_imagem(caminho_logo) if caminho_logo else None

# ==========================================
# 4. CABEÇALHO & BARRA LATERAL
# ==========================================
if logo_b64:
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #231F1E 0%, #362C28 100%); padding: 24px 30px; border-radius: 14px; border-bottom: 4px solid #C87D32; display: flex; align-items: center; gap: 24px; margin-bottom: 24px;">
        <div style="width: 95px; height: 95px; flex-shrink: 0;">
            <img src="data:image/png;base64,{logo_b64}" style="width: 100%; height: 100%; object-fit: contain;">
        </div>
        <div>
            <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
                <h1 style="margin: 0; font-size: 2.1rem; color: #F5EFE6 !important;">Massa Tradicional</h1>
                <span style="background: rgba(14, 165, 233, 0.18); color: #38BDF8; border: 1px solid rgba(56, 189, 248, 0.4); font-size: 0.72rem; padding: 3px 10px; border-radius: 20px; font-weight: 600;">Tecnologia de Panificação • B2B</span>
            </div>
            <p style="color: #D6C7B2; font-size: 1rem; margin: 6px 0 0 0;">Panificação autoral com precisão matemática e IA</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.title("🌾 Massa Tradicional | Tecnologia de Panificação B2B")

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

PERFIS_ENRIQUECIMENTO = {
    "Pão Rústico / Magro (0% Extras)": {"acucar": 0.0, "gordura": 0.0, "leite_po": 0.0, "ovos": 0.0},
    "Cachorro-Quente / Pão de Forma (Macio)": {"acucar": 6.0, "gordura": 5.0, "leite_po": 3.0, "ovos": 0.0},
    "Hambúrguer / Brioche (Rico)": {"acucar": 10.0, "gordura": 15.0, "leite_po": 4.0, "ovos": 10.0},
    "Personalizado (Ajuste Livre)": None
}

with st.sidebar:
    if logo_b64:
        st.markdown(f'<div style="text-align: center; margin-bottom: 12px;"><img src="data:image/png;base64,{logo_b64}" style="width: 95px;"></div>', unsafe_allow_html=True)

    st.markdown("### 🥖 1. Formato & Divisão")
    modo_planeamento = st.radio("Modo de cálculo:", ["Pelo Peso Total da Massa (g)", "Pela Quantidade de Pães (Unidades)"])
    formato_escolhido = st.selectbox("Formato do Pão", list(FORMATOS_PADARIA.keys()))
    peso_padrao = FORMATOS_PADARIA[formato_escolhido]

    if peso_padrao == 0:
        peso_porcao_g = st.number_input("Peso de cada unidade (g)", 20, 3000, 100, 5)
        nome_formato = "Porção Personalizada"
    elif peso_padrao == -1:
        peso_porcao_g = 0
        nome_formato = "Peça Única"
    else:
        peso_porcao_g = peso_padrao
        nome_formato = formato_escolhido.split(" (")[0]

    if modo_planeamento == "Pelo Peso Total da Massa (g)":
        peso_desejado = st.slider("Peso Total da Massa (g)", 500, 15000, 3500, 100)
    else:
        if peso_porcao_g <= 0:
            peso_porcao_g = 70
            nome_formato = "Pão de Cachorro-Quente"
        qtd_encomenda = st.number_input("Quantidade de Pães", 1, 500, 50, 1)
        peso_desejado = int(qtd_encomenda * peso_porcao_g)
        st.info(f"⚖️ **Massa Total:** {peso_desejado} g")

    st.markdown("---")
    st.markdown("### 🧈 2. Enriquecimento")
    perfil_escolhido = st.selectbox("Perfil", list(PERFIS_ENRIQUECIMENTO.keys()), index=1)
    vp = PERFIS_ENRIQUECIMENTO[perfil_escolhido]

    with st.expander("Ajustar Percentagens (%)", expanded=(vp is None)):
        acucar_pct = st.slider("Açúcar (%)", 0.0, 25.0, vp["acucar"] if vp else 6.0, 0.5)
        gordura_pct = st.slider("Manteiga/Óleo (%)", 0.0, 30.0, vp["gordura"] if vp else 5.0, 0.5)
        leite_po_pct = st.slider("Leite em Pó (%)", 0.0, 15.0, vp["leite_po"] if vp else 3.0, 0.5)
        ovos_pct = st.slider("Ovos (%)", 0.0, 30.0, vp["ovos"] if vp else 0.0, 1.0)

    st.markdown("---")
    st.markdown("### ⚙️ 3. Fermentação & Ambiente")
    tipo_fermento = st.selectbox("Fermento", ["Seco (1%)", "Fresco (3%)", "Levain (20%)"])
    fermento_limpo = tipo_fermento.split(" ")[0]
    sal_pct = st.slider("Sal (%)", 1.0, 3.5, 2.0, 0.1)
    temp_ambiente = st.number_input("Temp. Ambiente (°C)", 10.0, 40.0, 24.0, 0.5)

    st.markdown("---")
    st.markdown("### 🔑 4. Chave Gemini IA")
    chave_padrao = os.environ.get("GEMINI_API_KEY", "")
    chave_api = st.text_input("Chave API", value=chave_padrao, type="password")

# ==========================================
# 5. ABAS
# ==========================================
aba_ia, aba_manual, aba_b2b = st.tabs(["📷 Scanner de Rótulo (IA)", "🥖 Bancada Manual", "📊 Telemetria B2B"])

with aba_ia:
    col_up, col_prev = st.columns([2, 1])
    with col_up:
        st.subheader("1. Leitura Óptica")
        foto_upload = st.file_uploader("Foto do rótulo/tabela nutricional", type=["jpg", "jpeg", "png"])
        btn_ia = st.button("✨ Analisar Farinha & Calcular")

    if foto_upload is not None:
        img = Image.open(foto_upload)
        with col_prev:
            st.image(img, caption="Rótulo", use_container_width=True)

        if btn_ia:
            if not chave_api:
                st.error("⚠️ Insira a Chave Gemini na barra lateral.")
            else:
                with st.spinner("Analisando com IA..."):
                    dados_ia = analisar_imagem_farinha(img, chave_api)
                    if "erro" in dados_ia:
                        st.error(dados_ia["erro"])
                    else:
                        calc = CalculadoraPanificacao(
                            peso_total_massa=peso_desejado,
                            hidratacao_pct=dados_ia.get("hidratacao_minima", 60),
                            sal_pct=sal_pct,
                            tipo_fermento=fermento_limpo,
                            temp_ambiente=temp_ambiente,
                            contem_gluten=dados_ia.get("contem_gluten", True),
                            peso_porcao_g=peso_porcao_g,
                            nome_formato=nome_formato,
                            acucar_pct=acucar_pct,
                            gordura_pct=gordura_pct,
                            leite_po_pct=leite_po_pct,
                            ovos_pct=ovos_pct
                        )
                        st.session_state["resultado_atual"] = {"dados_ia": dados_ia, "receita": calc.calcular()}

with aba_manual:
    st.subheader("Simulador Rápido")
    c1, c2, c3 = st.columns(3)
    marca_manual = c1.text_input("Farinha", value="Venturelli Especial")
    hidratacao_manual = c2.slider("Hidratação (%)", 45, 90, 60, 1)
    gluten_manual = c3.selectbox("Glúten", ["Com Glúten (Trigo)", "Sem Glúten (+2% Goma Xantana)"])

    if st.button("🥖 Calcular Receita"):
        tem_gluten_bool = "Com Glúten" in gluten_manual
        calc = CalculadoraPanificacao(
            peso_total_massa=peso_desejado,
            hidratacao_pct=hidratacao_manual,
            sal_pct=sal_pct,
            tipo_fermento=fermento_limpo,
            temp_ambiente=temp_ambiente,
            contem_gluten=tem_gluten_bool,
            peso_porcao_g=peso_porcao_g,
            nome_formato=nome_formato,
            acucar_pct=acucar_pct,
            gordura_pct=gordura_pct,
            leite_po_pct=leite_po_pct,
            ovos_pct=ovos_pct
        )
        st.session_state["resultado_atual"] = {
            "dados_ia": {
                "marca": marca_manual,
                "proteina_g_por_50g": 6.0 if hidratacao_manual >= 65 else 5.2,
                "forca_estimada": "Alta" if hidratacao_manual >= 65 else "Média",
                "hidratacao_minima": hidratacao_manual,
                "contem_gluten": tem_gluten_bool
            },
            "receita": calc.calcular()
        }

# ==========================================
# 6. EXIBIÇÃO & PDF
# ==========================================
if "resultado_atual" in st.session_state:
    dados_ia = st.session_state["resultado_atual"]["dados_ia"]
    receita = st.session_state["resultado_atual"]["receita"]
    contem_gluten = dados_ia.get("contem_gluten", True)
    texto_gluten = "Com Glúten" if contem_gluten else "SEM GLÚTEN"

    st.markdown("---")
    if not contem_gluten:
        st.warning("⚠️ **PROTOCOLO SEM GLÚTEN:** Adicionado 2% de Goma Xantana.")

    st.subheader(f"📋 Ficha de Bancada — {dados_ia.get('marca')} ({receita.get('peso_total_g')}g)")
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("🌾 Farinha Base", f"{receita.get('farinha_g')} g")
    m2.metric("💧 Água", f"{receita.get('agua_ml')} ml", f"Ideal: {receita.get('temp_agua_c')} °C")
    m3.metric("🧂 Sal", f"{receita.get('sal_g')} g")
    m4.metric(f"🦠 Fermento", f"{receita.get('fermento_g')} g")

    if receita.get("massa_enriquecida"):
        e1, e2, e3, e4 = st.columns(4)
        e1.metric("🍬 Açúcar", f"{receita.get('acucar_g')} g")
        e2.metric("🧈 Manteiga", f"{receita.get('gordura_g')} g")
        e3.metric("🥛 Leite Pó", f"{receita.get('leite_po_g')} g")
        e4.metric("🥚 Ovos", f"{receita.get('ovos_g')} g")

    p1, p2, p3 = st.columns(3)
    p1.metric("🥖 Formato", receita.get("nome_formato"), f"{receita.get('peso_porcao_g')}g/un")
    p2.metric("📦 Rendimento", f"{receita.get('qtd_unidades')} unidades")
    p3.metric("✂️ Sobra", f"{receita.get('sobra_massa_g')} g")

    # PDF
    pdf = FPDF()
    pdf.add_page()
    if caminho_logo:
        pdf.image(caminho_logo, x=10, y=10, w=24)
    pdf.set_font("Arial", "B", 18)
    espaco = "          " if caminho_logo else ""
    pdf.cell(0, 12, txt=limpar_texto_pdf(f"{espaco}MASSA TRADICIONAL - FICHA TECNICA"), ln=True)
    pdf.ln(10)

    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 8, txt=limpar_texto_pdf(f"Farinha: {dados_ia.get('marca')} | Massa: {receita.get('peso_total_g')}g | Hidratacao: {receita.get('hidratacao_pct')}%"), ln=True)
    pdf.cell(0, 8, txt=limpar_texto_pdf(f"Rendimento: {receita.get('qtd_unidades')} un. de {receita.get('peso_porcao_g')}g ({receita.get('nome_formato')})"), ln=True)
    pdf.ln(5)

    pdf.set_fill_color(35, 31, 30)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(95, 10, " Insumo", border=1, fill=True)
    pdf.cell(95, 10, " Quantidade", border=1, fill=True, ln=True)

    pdf.set_text_color(0, 0, 0)
    linhas = [
        ("Farinha Base", f"{receita.get('farinha_g')} g"),
        ("Água Filtrada", f"{receita.get('agua_ml')} ml (a {receita.get('temp_agua_c')}C)"),
        ("Sal", f"{receita.get('sal_g')} g"),
        (f"Fermento ({receita.get('tipo_fermento')})", f"{receita.get('fermento_g')} g"),
    ]
    if receita.get("acucar_g", 0) > 0: linhas.append(("Açúcar", f"{receita.get('acucar_g')} g"))
    if receita.get("gordura_g", 0) > 0: linhas.append(("Manteiga / Gordura", f"{receita.get('gordura_g')} g"))
    if receita.get("leite_po_g", 0) > 0: linhas.append(("Leite em Pó", f"{receita.get('leite_po_g')} g"))
    if receita.get("ovos_g", 0) > 0: linhas.append(("Ovos", f"{receita.get('ovos_g')} g"))
    if not contem_gluten and "goma_xantana_g" in receita:
        linhas.append(("Goma Xantana", f"{receita.get('goma_xantana_g')} g"))

    for ins, qtd in linhas:
        pdf.cell(95, 10, limpar_texto_pdf(f" {ins}"), border=1)
        pdf.cell(95, 10, limpar_texto_pdf(f" {qtd}"), border=1, ln=True)

    saida_pdf = pdf.output(dest="S")
    bytes_pdf = saida_pdf.encode("latin-1") if isinstance(saida_pdf, str) else bytes(saida_pdf)

    st.download_button(
        label="📄 Baixar Ficha Técnica (PDF)",
        data=bytes_pdf,
        file_name=f"ficha_tecnica_{int(receita.get('peso_total_g'))}g.pdf",
        mime="application/pdf"
    )

with aba_b2b:
    st.subheader("📊 Telemetria B2B")
    if db is None:
        st.info("Firebase não configurado (opcional).")
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