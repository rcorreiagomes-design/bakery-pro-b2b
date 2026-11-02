import streamlit as st
from PIL import Image
import io
import os
import base64
import pandas as pd
from fpdf import FPDF
import firebase_admin
from firebase_admin import credentials, firestore

from motor_calculadora import CalculadoraPanificacao
from leitor_rotulos import analisar_imagem_farinha

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA E ESTÉTICA ARTESANAL ("PÃO DA CASA" + B2B)
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
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 15px rgba(140, 74, 39, 0.35) !important;
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
# 2. INICIALIZAÇÃO DO FIREBASE E LOGO
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
# 3. CABEÇALHO ARTESANAL & TECNOLÓGICO
# ==========================================
if logo_b64:
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #231F1E 0%, #362C28 100%); padding: 24px 30px; border-radius: 14px; border-bottom: 4px solid #C87D32; display: flex; align-items: center; gap: 24px; margin-bottom: 24px; box-shadow: 0 8px 20px rgba(35,31,30,0.12);">
        <div style="width: 95px; height: 95px; flex-shrink: 0;">
            <img src="data:image/png;base64,{logo_b64}" style="width: 100%; height: 100%; object-fit: contain; filter: drop-shadow(0 4px 10px rgba(0,0,0,0.5));">
        </div>
        <div>
            <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
                <h1 style="margin: 0; font-size: 2.1rem; color: #F5EFE6 !important; letter-spacing: -0.01em;">Massa Tradicional</h1>
                <span style="background: rgba(14, 165, 233, 0.18); color: #38BDF8; border: 1px solid rgba(56, 189, 248, 0.4); font-size: 0.72rem; padding: 3px 10px; border-radius: 20px; font-weight: 600; text-transform: uppercase;">Tecnologia de Panificação • B2B</span>
            </div>
            <p style="color: #D6C7B2; font-size: 1rem; margin: 6px 0 0 0;">Resgatando a panificação autoral com precisão matemática, enriquecimento de massa e visão computacional</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.title("🌾 Massa Tradicional | Tecnologia de Panificação B2B")

# ==========================================
# 4. BARRA LATERAL (PARÂMETROS, PORÇÕES E ENRIQUECIMENTO)
# ==========================================
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
        st.markdown(
            f'<div style="text-align: center; margin-bottom: 12px;"><img src="data:image/png;base64,{logo_b64}" style="width: 95px;"></div>',
            unsafe_allow_html=True
        )

    st.markdown("### 🥖 1. Formato & Divisão")
    modo_planeamento = st.radio(
        "Modo de cálculo da fornada:",
        ["Pelo Peso Total da Massa (g)", "Pela Quantidade de Pães (Unidades)"]
    )

    formato_escolhido = st.selectbox("Formato do Pão / Boleamento", list(FORMATOS_PADARIA.keys()))
    peso_padrao = FORMATOS_PADARIA[formato_escolhido]

    if peso_padrao == 0:
        peso_porcao_g = st.number_input("Peso de cada unidade (g)", min_value=20, max_value=3000, value=100, step=5)
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
        qtd_encomenda = st.number_input("Quantidade de Pães Desejada", min_value=1, max_value=500, value=50, step=1)
        peso_desejado = int(qtd_encomenda * peso_porcao_g)
        st.info(f"⚖️ **Massa Total Calculada:** {peso_desejado} g")

    st.markdown("---")
    st.markdown("### 🧈 2. Enriquecimento da Massa")
    perfil_escolhido = st.selectbox("Perfil de Receita", list(PERFIS_ENRIQUECIMENTO.keys()), index=1)
    valores_perfil = PERFIS_ENRIQUECIMENTO[perfil_escolhido]

    with st.expander("Ajustar Percentagens de Enriquecimento (%)", expanded=(valores_perfil is None)):
        acucar_pct = st.slider(
            "Açúcar (%)", 0.0, 25.0,
            valores_perfil["acucar"] if valores_perfil else 6.0, 0.5
        )
        gordura_pct = st.slider(
            "Manteiga / Banha / Óleo (%)", 0.0, 30.0,
            valores_perfil["gordura"] if valores_perfil else 5.0, 0.5
        )
        leite_po_pct = st.slider(
            "Leite em Pó (%)", 0.0, 15.0,
            valores_perfil["leite_po"] if valores_perfil else 3.0, 0.5
        )
        ovos_pct = st.slider(
            "Ovos Líquidos (%)", 0.0, 30.0,
            valores_perfil["ovos"] if valores_perfil else 0.0, 1.0
        )

    st.markdown("---")
    st.markdown("### ⚙️ 3. Fermentação & Ambiente")
    tipo_fermento = st.selectbox("Método de Fermentação", ["Seco (1%)", "Fresco (3%)", "Levain (20%)"])
    fermento_limpo = tipo_fermento.split(" ")[0]
    sal_pct = st.slider("Percentagem de Sal (%)", 1.0, 3.5, 2.0, 0.1)
    temp_ambiente = st.number_input("Temperatura Ambiente (°C)", 10.0, 40.0, 24.0, 0.5)

    st.markdown("---")
    st.markdown("### 🔑 4. Inteligência Artificial")
    chave_padrao = os.environ.get("GEMINI_API_KEY", "")
    chave_api = st.text_input("Chave API Google Gemini", value=chave_padrao, type="password")

# ==========================================
# 5. ABAS DE NAVEGAÇÃO
# ==========================================
aba_ia, aba_manual, aba_b2b = st.tabs([
    "📷 Scanner de Rótulo (IA)",
    "🥖 Bancada Manual (Rápida)",
    "📊 Telemetria B2B"
])

# --- ABA 1: SCANNER DE RÓTULO COM IA ---
with aba_ia:
    col_up, col_prev = st.columns([2, 1])
    with col_up:
        st.subheader("1. Leitura Óptica da Matéria-Prima")
        st.write("Envie a foto da tabela nutricional da farinha para calibrar a hidratação automaticamente pela proteína.")
        foto_upload = st.file_uploader("Selecione a foto do pacote/tabela nutricional", type=["jpg", "jpeg", "png"])
        btn_ia = st.button("✨ Analisar Farinha & Calcular Fornada")

    if foto_upload is not None:
        img = Image.open(foto_upload)
        with col_prev:
            st.image(img, caption="Rótulo carregado", use_container_width=True)

        if btn_ia:
            if not chave_api:
                st.error("⚠️ Insira a sua Chave Google Gemini na barra lateral esquerda para usar o leitor óptico.")
            else:
                with st.spinner("Lendo tabela nutricional com Visão Computacional e calculando matriz..."):
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
                        receita = calc.calcular()
                        st.session_state["resultado_atual"] = {
                            "dados_ia": dados_ia,
                            "receita": receita
                        }
                        if db is not None:
                            try:
                                db.collection("scans_farinha").add({
                                    "marca_detectada": dados_ia.get("marca"),
                                    "proteina_50g": dados_ia.get("proteina_g_por_50g"),
                                    "hidratacao_aplicada": dados_ia.get("hidratacao_minima"),
                                    "peso_fornada": peso_desejado,
                                    "formato_pao": nome_formato,
                                    "qtd_unidades": receita.get("qtd_unidades"),
                                    "massa_enriquecida": receita.get("massa_enriquecida"),
                                    "tipo_fermento": fermento_limpo,
                                    "contem_gluten": dados_ia.get("contem_gluten", True),
                                    "timestamp": firestore.SERVER_TIMESTAMP
                                })
                            except Exception:
                                pass

# --- ABA 2: CALCULADORA MANUAL DIRETA ---
with aba_manual:
    st.subheader("Simulador Rápido de Fornada, Enriquecimento & Porcionamento")
    st.write("Ideal para quando já conhece a força da sua farinha e quer gerar a ficha de bancada rapidamente.")
    c1, c2, c3 = st.columns(3)
    marca_manual = c1.text_input("Nome da Farinha / Receita", value="Venturelli Especial")
    hidratacao_manual = c2.slider("Hidratação de Água/Líquido (%)", 45, 90, 60, 1)
    gluten_manual = c3.selectbox("Presença de Glúten", ["Com Glúten (Trigo)", "Sem Glúten (+2% Goma Xantana)"])

    if st.button("🥖 Calcular Receita & Divisão de Bancada"):
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
# 6. EXIBIÇÃO DA FICHA TÉCNICA, ENRIQUECIMENTO, PORÇÕES E PDF
# ==========================================
if "resultado_atual" in st.session_state:
    dados_ia = st.session_state["resultado_atual"]["dados_ia"]
    receita = st.session_state["resultado_atual"]["receita"]
    contem_gluten = dados_ia.get("contem_gluten", True)
    texto_gluten = "Com Glúten" if contem_gluten else "SEM GLÚTEN"

    st.markdown("---")
    if not contem_gluten:
        st.warning("⚠️ **PROTOCOLO SEM GLÚTEN ATIVADO:** Adicionado 2% de Goma Xantana na formulação para estrutura da rede.")

    st.subheader(f"📋 Ficha de Bancada — {dados_ia.get('marca')} ({receita.get('peso_total_g')}g de Massa Total)")
    st.markdown(
        f"**Força Estimada:** `{dados_ia.get('forca_estimada', 'Padrão')}` &nbsp;|&nbsp; "
        f"**Proteína (50g):** `{dados_ia.get('proteina_g_por_50g')}g` &nbsp;|&nbsp; "
        f"**Hidratação Base:** `{receita.get('hidratacao_pct')}%` &nbsp;|&nbsp; "
        f"**Classificação:** `{texto_gluten}`"
    )

    # Linha 1: Base da Massa
    st.markdown("#### 🌾 1. Base de Panificação")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("🌾 Farinha Base (100%)", f"{receita.get('farinha_g')} g")
    m2.metric("💧 Água Filtrada", f"{receita.get('agua_ml')} ml", f"Temp. Ideal: {receita.get('temp_agua_c')} °C", delta_color="off")
    m3.metric("🧂 Sal Marinho", f"{receita.get('sal_g')} g", f"{sal_pct}% sobre a farinha", delta_color="off")
    m4.metric(f"🦠 Fermento ({receita.get('tipo_fermento')})", f"{receita.get('fermento_g')} g", f"Equiv. Fresco: {receita.get('fermento_fresco_equivalente_g')} g", delta_color="off")

    # Linha 2: Ingredientes de Enriquecimento (Exibe se houver pelo menos um > 0)
    if receita.get("massa_enriquecida"):
        st.markdown("#### 🧈 2. Ingredientes de Enriquecimento (Maciez, Cor e Sabor)")
        e1, e2, e3, e4 = st.columns(4)
        e1.metric("🍬 Açúcar", f"{receita.get('acucar_g')} g", f"{receita.get('acucar_pct')}% sobre a farinha", delta_color="off")
        e2.metric("🧈 Manteiga / Banha", f"{receita.get('gordura_g')} g", f"{receita.get('gordura_pct')}% sobre a farinha", delta_color="off")
        e3.metric("🥛 Leite em Pó", f"{receita.get('leite_po_g')} g", f"{receita.get('leite_po_pct')}% sobre a farinha", delta_color="off")
        e4.metric("🥚 Ovos", f"{receita.get('ovos_g')} g", f"~{receita.get('unidades_ovos_aprox')} un. ({receita.get('ovos_pct')}%)", delta_color="off")

    # Linha 3: Divisão de Porções / Boleamento
    st.markdown("#### ⚖️ 3. Rendimento & Boleamento na Bancada")
    p1, p2, p3 = st.columns(3)
    p1.metric("🥖 Formato Escolhido", receita.get("nome_formato"), f"{receita.get('peso_porcao_g')} g por unidade", delta_color="off")
    p2.metric("📦 Rendimento da Fornada", f"{receita.get('qtd_unidades')} unidades", f"Peso Total: {receita.get('peso_total_g')} g", delta_color="off")

    sobra = receita.get("sobra_massa_g", 0.0)
    if not contem_gluten and "goma_xantana_g" in receita:
        p3.metric("🧬 Goma Xantana (2%)", f"{receita.get('goma_xantana_g')} g", f"Sobra de corte: {sobra} g", delta_color="off")
    else:
        p3.metric("✂️ Sobra de Bancada (Retalho)", f"{sobra} g", "Divisão exata!" if sobra == 0 else "Distribuir nos pães", delta_color="off")

    # Geração segura do PDF com Base + Enriquecimento + Rendimento
    pdf = FPDF()
    pdf.add_page()
    if caminho_logo:
        pdf.image(caminho_logo, x=10, y=10, w=24)

    pdf.set_font("Arial", "B", 20)
    pdf.set_text_color(35, 31, 30)
    espaco = "          " if caminho_logo else ""
    pdf.cell(0, 12, txt=limpar_texto_pdf(f"{espaco}MASSA TRADICIONAL - FICHA TECNICA"), ln=True)
    pdf.set_font("Arial", "I", 11)
    pdf.set_text_color(140, 74, 39)
    pdf.cell(0, 6, txt=limpar_texto_pdf(f"{espaco}Tecnologia de Panificacao Artesanal & B2B"), ln=True)
    pdf.ln(14)

    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(35, 31, 30)
    pdf.cell(0, 8, txt=limpar_texto_pdf(f"Farinha: {dados_ia.get('marca')} | Massa Total: {receita.get('peso_total_g')}g | Hidratacao: {receita.get('hidratacao_pct')}%"), ln=True)
    pdf.cell(0, 8, txt=limpar_texto_pdf(f"Rendimento: {receita.get('qtd_unidades')} unidades de {receita.get('peso_porcao_g')}g ({receita.get('nome_formato')}) | Sobra: {sobra}g"), ln=True)
    pdf.ln(4)

    pdf.set_fill_color(35, 31, 30)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(95, 10, " Insumo / Etapa", border=1, fill=True)
    pdf.cell(95, 10, " Quantidade Exata", border=1, fill=True, ln=True)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "", 11)
    linhas_pdf = [
        ("Farinha Base (100%)", f"{receita.get('farinha_g')} g"),
        ("Agua Filtrada", f"{receita.get('agua_ml')} ml (Temp. ideal: {receita.get('temp_agua_c')} C)"),
        ("Sal Marinho", f"{receita.get('sal_g')} g ({sal_pct}%)"),
        (f"Fermento ({receita.get('tipo_fermento')})", f"{receita.get('fermento_g')} g (Equiv. Fresco: {receita.get('fermento_fresco_equivalente_g')} g)"),
    ]

    if receita.get("acucar_g", 0) > 0:
        linhas_pdf.append((f"Acucar ({receita.get('acucar_pct')}%)", f"{receita.get('acucar_g')} g"))
    if receita.get("gordura_g", 0) > 0:
        linhas_pdf.append((f"Manteiga / Banha ({receita.get('gordura_pct')}%)", f"{receita.get('gordura_g')} g"))
    if receita.get("leite_po_g", 0) > 0:
        linhas_pdf.append((f"Leite em Po ({receita.get('leite_po_pct')}%)", f"{receita.get('leite_po_g')} g"))
    if receita.get("ovos_g", 0) > 0:
        linhas_pdf.append((f"Ovos ({receita.get('ovos_pct')}%)", f"{receita.get('ovos_g')} g (~{receita.get('unidades_ovos_aprox')} un.)"))
    if not contem_gluten and "goma_xantana_g" in receita:
        linhas_pdf.append(("Goma Xantana (Sem Gluten)", f"{receita.get('goma_xantana_g')} g"))

    linhas_pdf.append(("Divisao de Bancada (Boleamento)", f"{receita.get('qtd_unidades')} un. x {receita.get('peso_porcao_g')} g ({receita.get('nome_formato')})"))

    for idx, (insumo, qtd) in enumerate(linhas_pdf):
        pdf.set_fill_color(248, 244, 238) if idx % 2 == 1 else pdf.set_fill_color(255, 255, 255)
        pdf.cell(95, 10, limpar_texto_pdf(f" {insumo}"), border=1, fill=True)
        pdf.cell(95, 10, limpar_texto_pdf(f" {qtd}"), border=1, fill=True, ln=True)

    saida_pdf = pdf.output(dest="S")
    bytes_pdf = saida_pdf.encode("latin-1") if isinstance(saida_pdf, str) else bytes(saida_pdf)

    st.markdown("<br>", unsafe_allow_html=True)
    st.download_button(
        label="📄 Baixar Ficha Técnica Completa (PDF)",
        data=bytes_pdf,
        file_name=f"ficha_tecnica_{receita.get('nome_formato').lower().replace(' ', '_')}_{int(receita.get('peso_total_g'))}g.pdf",
        mime="application/pdf"
    )

# --- ABA 3: PAINEL ANALÍTICO B2B ---
with aba_b2b:
    st.subheader("📊 Inteligência de Categoria & Volume de Fornadas")
    if db is None:
        st.info("💡 Para ativar a gravação em nuvem de todas as fornadas, adicione o ficheiro `firebase_key.json` na raiz do projeto.")
    else:
        try:
            docs = db.collection("scans_farinha").stream()
            lista_dados = [doc.to_dict() for doc in docs]
            if lista_dados:
                df = pd.DataFrame(lista_dados)
                k1, k2, k3 = st.columns(3)
                k1.metric("Fornadas Processadas", len(df))
                k2.metric("Volume Total de Massa", f"{df['peso_fornada'].sum():,.0f} g")
                k3.metric("Marcas Mapeadas", df["marca_detectada"].nunique())
                st.dataframe(df.drop(columns=["receita_gerada"], errors="ignore"), use_container_width=True)
            else:
                st.info("Nenhum lote registado na base de dados ainda.")
        except Exception as e:
            st.error(f"Erro ao ler telemetria: {e}")