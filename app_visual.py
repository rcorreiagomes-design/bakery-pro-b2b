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
    h1, h2, h3, h4, p, span, label {
        font-family: 'Plus Jakarta Sans', sans-serif;
        color: #2B2118;
    }
    h1, h2, h3, h4 {
        font-family: 'Playfair Display', serif !important;
        color: #231F1E !important;
    }

    /* CABEÇALHO PRINCIPAL - Cores forçadas para contraste perfeito no fundo escuro */
    .cabecalho-titulo {
        color: #F5EFE6 !important;
    }
    .cabecalho-sub {
        color: #D6C7B2 !important;
    }

    /* CORREÇÃO DO CONTRASTE DAS ABAS (TABS) NO CORPO PRINCIPAL */
    button[data-baseweb="tab"] {
        color: #231F1E !important;
        font-weight: 600 !important;
        font-size: 1.05rem !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #C87D32 !important;
        border-bottom-color: #C87D32 !important;
    }

    /* CORREÇÃO DA CAIXA DE UPLOAD DE ARQUIVOS */
    [data-testid="stFileUploader"] section {
        background-color: #F4ECE1 !important;
        border: 2px dashed #C87D32 !important;
    }
    [data-testid="stFileUploader"] section * {
        color: #231F1E !important;
    }

    /* BARRA LATERAL - Cores corrigidas para total legibilidade */
    section[data-testid="stSidebar"] {
        background-color: #231F1E !important;
        border-right: 2px solid #C87D32;
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
    section[data-testid="stSidebar"] [data-baseweb="tag"] * {
        color: #FFFFFF !important;
    }

    /* Cartões e Métricas */
    [data-testid="stMetric"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E6D7C3 !important;
        border-left: 5px solid #C87D32 !important;
        border-radius: 10px !important;
        padding: 16px !important;
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
# 4. CABEÇALHO & BARRA LATERAL
# ==========================================
if logo_b64:
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #231F1E 0%, #362C28 100%); padding: 22px 28px; border-radius: 12px; border-bottom: 4px solid #C87D32; display: flex; align-items: center; gap: 20px; margin-bottom: 20px;">
        <div style="width: 85px; height: 85px; flex-shrink: 0;"><img src="data:image/png;base64,{logo_b64}" style="width: 100%; height: 100%; object-fit: contain;"></div>
        <div>
            <h1 class="cabecalho-titulo" style="margin: 0; font-size: 2rem;">Massa Tradicional</h1>
            <p class="cabecalho-sub" style="font-size: 0.95rem; margin: 4px 0 0 0;">Painel Profissional de Panificação & B2B Intelligence</p>
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
        st.markdown(f'<div style="text-align: center; margin-bottom: 10px;"><img src="data:image/png;base64,{logo_b64}" style="width: 80px;"></div>', unsafe_allow_html=True)

    st.markdown("### 🥖 Planeamento de Produção")
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
        c_farinha = st.number_input("Farinha (R$/kg)", 2.0, 20.0, 5.50, 0.5)
        c_fermento = st.number_input("Fermento (R$/kg)", 10.0, 100.0, 35.0, 1.0)
        c_acucar = st.number_input("Açúcar (R$/kg)", 2.0, 15.0, 4.50, 0.5)
        c_sal = st.number_input("Sal (R$/kg)", 1.0, 10.0, 3.0, 0.5)
    with cc2:
        c_gordura = st.number_input("Manteiga / Gordura (R$/kg)", 5.0, 60.0, 18.0, 1.0)
        c_leite = st.number_input("Leite em Pó (R$/kg)", 10.0, 80.0, 30.0, 1.0)
        c_ovo_unidade = st.number_input("Ovo (R$ por UNIDADE)", 0.20, 2.00, 0.75, 0.05)
        margem_lucro = st.slider("Margem de Lucro Desejada (%)", 20.0, 300.0, 100.0, 10.0)

with aba_calc:
    col_up, col_prev = st.columns([2, 1])
    with col_up:
        st.subheader("Scanner de Rótulo & Simulação Manual")
        foto_upload = st.file_uploader("Enviar foto da tabela nutricional da farinha (Opcional)", type=["jpg", "jpeg", "png"])
        b_acao = st.button("✨ Calcular Ficha de Produção Completa")

    if foto_upload is not None:
        img = Image.open(foto_upload)
        with col_prev:
            st.image(img, caption="Rótulo", use_container_width=True)

    if b_acao:
        with st.spinner("Processando cálculo matemático e inteligência..."):
            dados_ia = {"marca": "Farinha Padrão / Manual", "proteina_g_por_50g": 6.0, "forca_estimada": "Alta", "hidratacao_minima": 60, "contem_gluten": True}
            
            if foto_upload is not None:
                if not chave_api:
                    st.error("⚠️ Chave API Gemini não configurada nas Secrets do Streamlit.")
                else:
                    res_ia = analisar_imagem_farinha(Image.open(foto_upload), chave_api)
                    if "erro" not in res_ia:
                        dados_ia = res_ia

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
                ovos_pct=ovos_pct,
                custo_farinha_kg=c_farinha,
                custo_fermento_kg=c_fermento,
                custo_acucar_kg=c_acucar,
                custo_gordura_kg=c_gordura,
                custo_leite_po_kg=c_leite,
                custo_ovo_unidade=c_ovo_unidade,
                custo_sal_kg=c_sal,
                margem_lucro_pct=margem_lucro
            )
            st.session_state["resultado_atual"] = {"dados_ia": dados_ia, "receita": calc.calcular()}
            st.success("Ficha calculada com sucesso!")

# ==========================================
# 6. EXIBIÇÃO DOS RESULTADOS & PDF
# ==========================================
if "resultado_atual" in st.session_state:
    res = st.session_state["resultado_atual"]
    dados_ia = res["dados_ia"]
    receita = res["receita"]
    contem_gluten = dados_ia.get("contem_gluten", True)

    st.markdown("---")
    if not contem_gluten:
        st.warning("⚠️ **PROTOCOLO SEM GLÚTEN:** Adicionado 2% de Goma Xantana.")

    st.subheader(f"📋 Ficha Técnica — {dados_ia.get('marca')} ({receita.get('peso_total_g')}g de Massa)")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("🌾 Farinha Base", f"{receita.get('farinha_g')} g")
    m2.metric("💧 Água", f"{receita.get('agua_ml')} ml", f"Ideal: {receita.get('temp_agua_c')} °C")
    m3.metric("🧂 Sal", f"{receita.get('sal_g')} g")
    m4.metric("🦠 Fermento", f"{receita.get('fermento_g')} g")

    if receita.get("massa_enriquecida"):
        e1, e2, e3, e4 = st.columns(4)
        e1.metric("🍬 Açúcar", f"{receita.get('acucar_g')} g")
        e2.metric("🧈 Manteiga", f"{receita.get('gordura_g')} g")
        e3.metric("🥛 Leite Pó", f"{receita.get('leite_po_g')} g")
        e4.metric("🥚 Ovos", f"{receita.get('ovos_g')} g", f"~{receita.get('unidades_ovos_inteiras')} unidades")

    p1, p2, p3 = st.columns(3)
    p1.metric("🥖 Formato", receita.get("nome_formato"), f"{receita.get('peso_porcao_g')}g/un")
    p2.metric("📦 Rendimento", f"{receita.get('qtd_unidades')} unidades")
    p3.metric("✂️ Sobra", f"{receita.get('sobra_massa_g')} g")

    st.markdown("#### 💰 Custos & Precificação Comercial")
    f1, f2, f3 = st.columns(3)
    f1.metric("💵 Custo Total", f"R$ {receita.get('custo_total_fornada'):.2f}")
    f2.metric("🏷️ Custo / Unidade", f"R$ {receita.get('custo_por_unidade'):.2f}")
    f3.metric("💡 Preço Sugerido", f"R$ {receita.get('preco_sugerido_unidade'):.2f}", f"Margem: {receita.get('margem_lucro_pct')}%")

    pdf = FPDF()
    pdf.add_page()
    if caminho_logo:
        pdf.image(caminho_logo, x=10, y=10, w=24)
    pdf.set_font("Arial", "B", 18)
    espaco = "          " if caminho_logo else ""
    pdf.cell(0, 12, txt=limpar_texto_pdf(f"{espaco}MASSA TRADICIONAL - FICHA DE BANCADA"), ln=True)
    pdf.ln(10)

    pdf.set_font("Arial", "", 11)
    peso_total_int = int(receita.get('peso_total_g', 0))
    nome_formato_limpo = str(receita.get('nome_formato', 'pao')).lower().replace(' ', '_')
    pdf.cell(0, 8, txt=limpar_texto_pdf(f"Farinha: {dados_ia.get('marca')} | Massa Total: {receita.get('peso_total_g')}g | Hidratacao: {receita.get('hidratacao_pct')}%"), ln=True)
    pdf.cell(0, 8, txt=limpar_texto_pdf(f"Rendimento: {receita.get('qtd_unidades')} un. de {receita.get('peso_porcao_g')}g ({receita.get('nome_formato')})"), ln=True)
    pdf.cell(0, 8, txt=limpar_texto_pdf(f"Custo Total: R$ {receita.get('custo_total_fornada')} | Custo/Un: R$ {receita.get('custo_por_unidade')} | Preco Sugerido: R$ {receita.get('preco_sugerido_unidade')} ({receita.get('margem_lucro_pct')}%)"), ln=True)
    pdf.ln(5)

    pdf.set_fill_color(35, 31, 30)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(95, 10, " Insumo", border=1, fill=True)
    pdf.cell(95, 10, " Quantidade / Custo", border=1, fill=True, ln=True)

    pdf.set_text_color(0, 0, 0)
    linhas = [
        ("Farinha Base", f"{receita.get('farinha_g')} g"),
        ("Água Filtrada", f"{receita.get('agua_ml')} ml (a {receita.get('temp_agua_c')}C)"),
        ("Sal", f"{receita.get('sal_g')} g"),
        (f"Fermento ({receita.get('tipo_fermento')})", f"{receita.get('fermento_g')} g"),
    ]
    if receita.get("acucar_g", 0) > 0: linhas.append(("Açúcar", f"{receita.get('acucar_g')} g"))
    if receita.get("gordura_g", 0) > 0: linhas.append(("Manteiga / Gordura", f"{receita.get('gordura_g')} g"))
    if receita.get('leite_po_g', 0) > 0: linhas.append(("Leite em Pó", f"{receita.get('leite_po_g')} g"))
    if receita.get("ovos_g", 0) > 0: linhas.append(("Ovos", f"{receita.get('ovos_g')} g (~{receita.get('unidades_ovos_inteiras')} un.)"))
    if not contem_gluten and "goma_xantana_g" in receita:
        linhas.append(("Goma Xantana", f"{receita.get('goma_xantana_g')} g"))

    for ins, qtd in linhas:
        pdf.cell(95, 10, limpar_texto_pdf(f" {ins}"), border=1)
        pdf.cell(95, 10, limpar_texto_pdf(f" {qtd}"), border=1, ln=True)

    saida_pdf = pdf.output(dest="S")
    bytes_pdf = saida_pdf.encode("latin-1") if isinstance(saida_pdf, str) else FPDF.output(pdf, dest="S").encode("latin-1")

    st.download_button(
        label="📄 Baixar Ficha Técnica em PDF",
        data=bytes_pdf,
        file_name=f"ficha_tecnica_{nome_formato_limpo}_{peso_total_int}g.pdf",
        mime="application/pdf"
    )

with aba_b2b:
    st.subheader("📊 Telemetria B2B")
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