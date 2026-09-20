import streamlit as st
from PIL import Image
import requests
import io
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore
import os
import base64  # <-- Nova biblioteca para forçar o tamanho da imagem
from fpdf import FPDF

# ==========================================
# CONFIGURAÇÃO DE INTERFACE & CSS PREMIUM
# ==========================================
st.set_page_config(page_title="Bakery Pro | Intelligence", page_icon="🌾", layout="wide")

st.markdown("""
    <style>
    [data-testid="stMetricDelta"] > div:nth-child(1) {
        color: #555555 !important;
        font-weight: 500;
    }
    [data-testid="stMetric"] {
        background-color: #FFFFFF;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        border: 1px solid #E2E8F0;
    }
    .stButton>button {
        background-color: #0F172A;
        color: white;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: bold;
        border: none;
        transition: all 0.3s ease;
    }
    </style>
""", unsafe_allow_html=True)

# Inicializa o Firebase
if not firebase_admin._apps:
    caminho_cred = os.path.join(os.path.dirname(__file__), "firebase_key.json")
    if os.path.exists(caminho_cred):
        cred = credentials.Certificate(caminho_cred)
        firebase_admin.initialize_app(cred)

db = firestore.client() if firebase_admin._apps else None

# ==========================================
# CABEÇALHO B2B (PROPORCIONAL & HARMONIOSO)
# ==========================================
caminho_logo = os.path.join(os.path.dirname(__file__), "logo.png")
tem_logo = os.path.exists(caminho_logo)

# Converte a imagem para Base64 recortando automaticamente bordas vazias/transparentes
def obter_base64_da_imagem(caminho):
    from PIL import Image
    import io, base64
    img = Image.open(caminho)
    # Recorta o excesso de transparência para que o logo ocupe 100% da sua área útil
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()

if tem_logo:
    logo_b64 = obter_base64_da_imagem(caminho_logo)
    cabecalho_html = f"""
    <div style="display: flex; align-items: center; gap: 22px; padding: 10px 0 22px 0; margin-bottom: 18px; border-bottom: 1px solid rgba(255, 255, 255, 0.08);">
        <div style="width: 88px; min-width: 88px; height: 88px; flex-shrink: 0; display: flex; align-items: center; justify-content: center;">
            <img src="data:image/png;base64,{logo_b64}" style="width: 100%; height: 100%; object-fit: contain; filter: drop-shadow(0 4px 12px rgba(0,0,0,0.35));">
        </div>
        <div>
            <div style="display: flex; align-items: center; flex-wrap: wrap; gap: 10px;">
                <h1 style='margin: 0; padding: 0; font-size: 2.2rem; font-weight: 700; letter-spacing: -0.02em; line-height: 1.15; color: #F8FAFC;'>Profissional de Padaria</h1>
                <span style="background: rgba(217, 119, 6, 0.15); color: #F59E0B; border: 1px solid rgba(217, 119, 6, 0.35); font-size: 0.72rem; padding: 2px 8px; border-radius: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em;">B2B Engine</span>
            </div>
            <p style='color: #94A3B8; font-size: 1.02rem; margin: 4px 0 0 0; font-weight: 400; letter-spacing: -0.01em;'>Motor de IA & Produção Artesanal B2B</p>
        </div>
    </div>
    """
    st.markdown(cabecalho_html, unsafe_allow_html=True)
else:
    st.markdown("<h1 style='font-size: 2.2rem; margin-bottom: 20px;'>🌾 Profissional de Padaria</h1>", unsafe_allow_html=True)

aba_app, aba_b2b = st.tabs(["🚀 Calculadora de Produção", "📊 Painel Analítico B2B"])

with aba_app:
    # BARRA LATERAL
    with st.sidebar:
        if tem_logo:
            st.markdown(
                f"""
                <div style="display: flex; justify-content: center; margin-bottom: 20px; padding: 10px 0;">
                    <img src="data:image/png;base64,{logo_b64}" style="width: 110px; height: 110px; object-fit: contain; filter: drop-shadow(0 4px 10px rgba(0,0,0,0.4));">
                </div>
                """,
                unsafe_allow_html=True
            )
        
        st.markdown("### Centro de Controlo")
        with st.expander("🔑 Credenciais da API", expanded=True):
            chave_api = st.text_input("Chave Google Gemini", type="password")
            
        with st.expander("📏 Parâmetros da Fornada", expanded=True):
            peso_desejado = st.slider("Peso Total (g)", 500, 5000, 2000, 100)
            tipo_fermento = st.selectbox("Tipo de Fermento", ["Seco", "Levain"])
            temp_ambiente = st.number_input("Temp. Ambiente (°C)", 10.0, 40.0, 25.0, 0.5)

    # CORPO PRINCIPAL
    col_upload, col_preview = st.columns([2, 1])
    
    with col_upload:
        st.subheader("1. Escaneamento Inteligente")
        foto_upload = st.file_uploader("Arraste ou selecione a foto da tabela nutricional", type=["jpg", "jpeg", "png"])
        
        processar = st.button("✨ Processar Receita com IA")

    if foto_upload is not None:
        img = Image.open(foto_upload)
        with col_preview:
            st.image(img, caption="Rótulo em análise", use_container_width=True)
        
        if processar:
            if not chave_api:
                st.error("⚠️ Falta a chave da API na barra lateral.")
            else:
                with st.spinner('A extrair inteligência do rótulo e a calcular matriz matemática...'):
                    try:
                        # Define a URL base dependendo se estamos no PC ou na Nuvem
                        URL_BACKEND = "https://bakery-pro-b2b.onrender.com"
                        url_api = f"{URL_BACKEND}/analisar_e_calcular/"
                        img_byte_arr = io.BytesIO()
                        img.save(img_byte_arr, format=img.format if img.format else 'JPEG')
                        img_byte_arr = img_byte_arr.getvalue()
                        
                        files = {'foto_rotulo': ('rotulo.jpg', img_byte_arr, 'image/jpeg')}
                        data = {
                            'peso_desejado': peso_desejado, 
                            'chave_api': chave_api,
                            'tipo_fermento': tipo_fermento,
                            'temp_ambiente': temp_ambiente
                        }
                        
                        response = requests.post(url_api, data=data, files=files)
                        resultado = response.json()
                        
                        if resultado.get("status") == "sucesso":
                            st.session_state['resultado_api'] = resultado
                        else:
                            st.error(f"Erro na API: {resultado.get('mensagem')}")
                    except Exception as e:
                        st.error(f"Erro de ligação com a API local: {e}")

    # EXIBIÇÃO E EXPORTAÇÃO PDF
    if 'resultado_api' in st.session_state:
        res = st.session_state['resultado_api']
        dados_ia = res.get('inteligencia_extraida', {})
        receita = res.get('receita_calculada', {})
        
        contem_gluten = dados_ia.get('contem_gluten', True)
        texto_gluten = "Com Glúten" if contem_gluten else "SEM GLÚTEN"
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if not contem_gluten:
            st.markdown("""
            <div style="background-color: #FEF2F2; color: #991B1B; padding: 16px; border-radius: 8px; border-left: 6px solid #EF4444; margin-bottom: 20px;">
                <strong>⚠️ PROTOCOLO SEM GLÚTEN ATIVADO:</strong> A IA detetou uma base sem glúten. O motor injetou automaticamente 2% de Goma Xantana na ficha técnica para atuar como agente estrutural.
            </div>
            """, unsafe_allow_html=True)
            
        st.subheader("2. Matriz de Produção Calculada")
        
        st.info(f"🏷️ **Marca:** {dados_ia.get('marca')} &nbsp;|&nbsp; 🌾 **Proteína:** {dados_ia.get('proteina_g_por_50g')}g &nbsp;|&nbsp; 💧 **Hidratação:** {dados_ia.get('hidratacao_minima')}% &nbsp;|&nbsp; 🧬 **Alergénios:** {texto_gluten}")
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Farinha Base", f"{receita.get('farinha_g')} g")
        m2.metric("Água Purificada", f"{receita.get('agua_ml')} ml", f"Ideal a {receita.get('temp_agua_c')} °C", delta_color="off")
        m3.metric("Sal", f"{receita.get('sal_g')} g")
        
        m4, m5, m6 = st.columns(3)
        m4.metric("Fermento", f"{receita.get('fermento_g')} g", f"({receita.get('tipo_fermento')})", delta_color="off")
        
        if not contem_gluten and 'goma_xantana_g' in receita:
            m5.metric("Goma Xantana", f"{receita.get('goma_xantana_g')} g", "Agente Ligante", delta_color="off")
        
        # ==========================================
        # GERAÇÃO DE PDF
        # ==========================================
        def gerar_pdf():
            pdf = FPDF()
            pdf.add_page()
            
            cor_primaria = (15, 23, 42)
            cor_destaque = (217, 119, 6)
            cor_cinza = (100, 116, 139)
            
            if tem_logo:
                pdf.image(caminho_logo, x=10, y=10, w=22)
            
            pdf.set_font("Arial", 'B', 22)
            pdf.set_text_color(*cor_primaria)
            espaco = "        " if tem_logo else ""
            pdf.cell(0, 12, txt=f"{espaco}BAKERY PRO", ln=True, align='L')
            
            pdf.set_font("Arial", 'I', 11)
            pdf.set_text_color(*cor_cinza)
            pdf.cell(0, 6, txt=f"{espaco} Ficha Técnica de Produção Artesanal", ln=True, align='L')
            
            pdf.set_draw_color(*cor_destaque)
            pdf.set_line_width(0.8)
            pdf.line(10, 32, 200, 32)
            pdf.ln(12)
            
            if not contem_gluten:
                pdf.set_fill_color(254, 242, 242)
                pdf.set_text_color(185, 28, 28)
                pdf.set_font("Arial", 'B', 11)
                pdf.cell(0, 10, txt="  PROTOCOLO DE SEGURANCA: MASSA SEM GLUTEN DETETADA", border=1, fill=True, ln=True, align='C')
                pdf.ln(5)
                
            pdf.set_text_color(*cor_primaria)
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 10, txt="1. Especificações da Matéria-Prima", ln=True)
            
            pdf.set_font("Arial", '', 11)
            pdf.set_text_color(0, 0, 0)
            
            y_atual = pdf.get_y()
            pdf.text(10, y_atual + 5, f"Marca da Farinha: {dados_ia.get('marca')}")
            pdf.text(100, y_atual + 5, f"Hidratação Base: {dados_ia.get('hidratacao_minima')}%")
            
            pdf.text(10, y_atual + 12, f"Proteína (50g): {dados_ia.get('proteina_g_por_50g')}g")
            pdf.text(100, y_atual + 12, f"Alergénios: {texto_gluten}")
            
            pdf.text(10, y_atual + 19, f"Temperatura Ambiente: {temp_ambiente} C")
            pdf.text(100, y_atual + 19, f"Volume Total Previsto: {peso_desejado} g")
            
            pdf.ln(25)
            
            pdf.set_text_color(*cor_primaria)
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 10, txt="2. Matriz de Formulação (Pesos e Medidas)", ln=True)
            
            pdf.set_fill_color(*cor_primaria)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(95, 10, " Ingrediente", border=1, fill=True)
            pdf.cell(95, 10, " Quantidade Específica", border=1, fill=True, ln=True)
            
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Arial", '', 11)
            
            def adicionar_linha(ingrediente, quantidade, fundo_cinza=False):
                if fundo_cinza:
                    pdf.set_fill_color(248, 250, 252)
                pdf.cell(95, 10, f" {ingrediente}", border=1, fill=fundo_cinza)
                pdf.cell(95, 10, f" {quantidade}", border=1, fill=fundo_cinza, ln=True)
                
            adicionar_linha("Farinha Base", f"{receita.get('farinha_g')} g", False)
            adicionar_linha("Agua Purificada", f"{receita.get('agua_ml')} ml (Alvo: {receita.get('temp_agua_c')} C)", True)
            adicionar_linha("Sal Refinado", f"{receita.get('sal_g')} g", False)
            adicionar_linha(f"Fermento ({receita.get('tipo_fermento')})", f"{receita.get('fermento_g')} g", True)
            
            if not contem_gluten and 'goma_xantana_g' in receita:
                pdf.set_text_color(185, 28, 28)
                adicionar_linha("Goma Xantana (Agente Ligante)", f"{receita.get('goma_xantana_g')} g", False)
                pdf.set_text_color(0, 0, 0)
                
            pdf.set_y(-25)
            pdf.set_font("Arial", 'I', 8)
            pdf.set_text_color(*cor_cinza)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.cell(0, 10, "Gerado automaticamente por Bakery Pro | Intelligence Engine B2B", align='L')
            
            # Finaliza a função e devolve o PDF empacotado em bytes
    return bytes(pdf.output())

# --- AQUI TERMINA A FUNÇÃO E COMEÇA A INTERFACE ---

# Cria o botão de download limpo chamando a função
st.download_button(
    label="📄 Exportar Ficha Técnica de Produção (PDF)",
    data=gerar_pdf(),
    file_name="ficha_tecnica_producao.pdf",
    mime="application/pdf"
)
with aba_b2b:
    st.subheader("📊 Inteligência de Categoria & Tracking de Volume")
    if db:
        docs = db.collection("scans_farinha").stream()
        lista_dados = [doc.to_dict() for doc in docs]
        
        if lista_dados:
            df = pd.DataFrame(lista_dados)
            m1, m2, m3 = st.columns(3)
            m1.metric("Entradas de Telemetria", len(df))
            m2.metric("Volume Produzido (Global)", f"{df['peso_fornada'].sum():,.0f} g")
            m3.metric("Cobertura de Marcas", df['marca_detectada'].nunique())
            
            st.markdown("---")
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Aguardando sincronização de telemetria com a nuvem...")