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
            f"2. **Hidratação:** Adicione água (a {temp_agua} °C) e líquidos aos poucos, batendo por 4-5 min.",
            "3. **Modelagem Direta:** Transfira direto para a forma untada e alise com espátula molhada.",
            "4. **Crescimento:** Cubra e deixe crescer por 35 a 50 min até atingir a borda da forma.",
            "5. **Forno:** Asse a 190 °C por 35 a 45 min. Espere esfriar totalmente antes de fatiar.",
        ]
    if tipo_massa == "focaccia":
        return [
            f"1. **Mistura Inicial:** Misture farinha, fermento e água (a {temp_agua} °C). Descanse 15 min e junte sal e azeite.",
            "2. **Dobras:** Faça 3 séries de dobras (Stretch & Fold) na tigela com intervalos de 30 min.",
            "3. **Fermentação na Forma:** Transfira para assadeira bem untada com azeite e descanse 45 a 60 min.",
            "4. **Cobertura:** Regue com azeite, faça covinhas com os dedos e salpique sal grosso e alecrim.",
            "5. **Forno:** Asse em forno preaquecido a 220 °C por 20 a 25 min até dourar bem.",
        ]
    if tipo_massa == "rustico":
        return [
            f"1. **Autólise:** Misture apenas farinha e água (a {temp_agua} °C) e descanse coberto por 30 min.",
            "2. **Incorporação:** Adicione o fermento e o sal, misturando até homogeneizar.",
            "3. **Dobras:** Faça 3 a 4 séries de dobras a cada 30 min. Fermente até crescer cerca de 60%.",
            f"4. **Divisão e Modelagem:** Divida em {qtd_un} porção(ões) de {peso_un}g, pré-modele, descanse 15 min e modele com tensão.",
            "5. **Forno com Vapor:** Preaqueça a 240 °C com assadeira vazia embaixo. Faça o corte e use vapor nos primeiros 15 min. Asse por 25-35 min.",
        ]
    return [
        f"1. **Mistura Inicial:** Misture farinha, fermento, açúcar e leite em pó. Junte água (a {temp_agua} °C) e ovos aos poucos.",
        "2. **Sova e Ponto de Véu:** Sove por 8 min. Adicione o sal e, por último, a manteiga em pomada até ficar lisa.",
        "3. **Primeira Fermentação:** Cubra a massa e deixe descansar por 40 a 60 min até dobrar de volume.",
        f"4. **Divisão e Modelagem:** Divida em {qtd_un} un. de {peso_un}g, boleie, descanse 10 min e modele ({nome_formato}).",
        "5. **Segunda Fermentação e Forno:** Deixe dobrar na assadeira (35-50 min). Asse a 180 °C por 18-25 min (pequenos) ou 30-35 min (grandes).",
    ]

def gerar_cronograma_reverso(hora_pronto: datetime.time, nome_formato: str, receita: dict, contem_gluten: bool) -> list:
    tipo_massa = classificar_massa(nome_formato, receita, contem_gluten)
    base_dt = datetime.datetime.combine(datetime.date.today(), hora_pronto)

    if tipo_massa == "sem_gluten":
        etapas_min = [
            (95, "🥣 Pesagem e mistura na batedeira"),
            (85, "🍞 Transferir para a forma untada"),
            (40, "🔥 Preaquecer forno a 190 °C"),
            (35, "⏲️ Colocar no forno"),
            (0, "✅ Pão pronto! Esfriar na grade"),
        ]
    elif tipo_massa == "focaccia":
        etapas_min = [
            (195, "🥣 Mistura inicial e descanso (15 min)"),
            (180, "🧂 Incorporar sal/azeite e 1ª dobra"),
            (150, "🔄 2ª dobra (Stretch & Fold)"),
            (120, "🔄 3ª dobra (Stretch & Fold)"),
            (90, "🫒 Transferir para forma untada com azeite"),
            (40, "🔥 Preaquecer forno a 220 °C"),
            (25, "✨ Covinhas, sal grosso/alecrim e forno"),
            (0, "✅ Focaccia dourada e pronta!"),
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
            (25, "🥚 Pincelar gema/leite e levar ao forno"),
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
    leite_po = float(receita.get("leite_po_g", 0) or 0)
    ovos = float(receita.get("ovos_g", 0) or 0)
    sal = float(receita.get("sal_g", 0) or 0)
    fermento = float(receita.get("fermento_g", 0) or 0)

    kcal = farinha * 3.60 + acucar * 3.87 + gordura * 7.17 + leite_po * 4.96 + ovos * 1.43 + fermento * 2.95
    carb = farinha * 0.75 + acucar * 1.00 + leite_po * 0.38 + ovos * 0.01 + fermento * 0.38
    prot = farinha * 0.11 + gordura * 0.01 + leite_po * 0.26 + ovos * 0.13 + fermento * 0.38
    gord = farinha * 0.014 + gordura * 0.81 + leite_po * 0.27 + ovos * 0.095 + fermento * 0.04
    sodio_mg = sal * 388.0 + leite_po * 3.7 + ovos * 1.4

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

def montar_texto_whatsapp(dados_ia: dict, receita: dict, usar_caseira: bool, chave_ferm: str, passos: list) -> str:
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

    linhas.append(f"• Farinha: {fmt(receita.get('farinha_g', 0), 'farinha')}")
    linhas.append(f"• Água ({receita.get('temp_agua_c')}°C): {fmt(receita.get('agua_ml', 0), 'agua', 'ml')}")
    linhas.append(f"• Sal: {fmt(receita.get('sal_g', 0), 'sal')}")
    linhas.append(f"• Fermento ({receita.get('tipo_fermento')}): {fmt(receita.get('fermento_g', 0), chave_ferm)}")

    if (receita.get("acucar_g", 0) or 0) > 0:
        linhas.append(f"• Açúcar: {fmt(receita.get('acucar_g', 0), 'acucar')}")
    if (receita.get("gordura_g", 0) or 0) > 0:
        linhas.append(f"• Manteiga/Gordura: {fmt(receita.get('gordura_g', 0), 'gordura')}")
    if (receita.get("leite_po_g", 0) or 0) > 0:
        linhas.append(f"• Leite em Pó: {fmt(receita.get('leite_po_g', 0), 'leite_po')}")
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
# 3. IA / LEITOR DE RÓTULOS
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

# ==========================================
# 4. FIREBASE, ACESSO PRO & LOGO
# ==========================================
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
# 5. CABEÇALHO & BARRA LATERAL
# ==========================================
if logo_b64:
    logo_html = '<img src="data:image/png;base64,' + logo_b64 + '" style="width: 100%; height: 100%; object-fit: contain;">'
else:
    logo_html = "🌾"

banner_html = (
    '<div id="banner-topo">'
    f'<div style="width: 80px; height: 80px; flex-shrink: 0;">{logo_html}</div>'
    '<div>'
    '<div class="titulo-principal">Massa Tradicional</div>'
    '<div class="subtitulo-principal">Painel Profissional de Panificação & B2B Intelligence</div>'
    '</div></div>'
)
st.markdown(banner_html, unsafe_allow_html=True)

FORMATOS_PADARIA = {
    "Pão de Cachorro-Quente (70g)": 70,
    "Pão de Hambúrguer / Brioche (90g)": 90,
    "Pão Francês / Mini Baguete (120g)": 120,
    "Focaccia Individual (250g)": 250,
    "Pão de Forma Tradicional (550g)": 550,
    "Pão de Forma Grande (650g)": 650,
    "Pão Rústico / Campagne (800g)": 800,
    "Personalizado (Definir gramas)": 0,
    "Peça Única (Sem divisão)": -1,
}

with st.sidebar:
    if caminho_logo:
        st.image(caminho_logo, width=65)

    st.markdown("### 🔑 Acesso PRO")
    credencial_pro = st.text_input("E-mail ou Chave PRO", placeholder="seu@email.com")
    usuario_pro = verificar_acesso_pro(credencial_pro)
    if not ATIVAR_PAYWALL:
        st.caption("🟢 Modo Teste: Recursos PRO liberados")
    elif usuario_pro:
        st.success("✅ Plano PRO Ativo")
    else:
        st.warning("🔒 Modo Gratuito (Scanner IA, PDF e Custos bloqueados)")

    st.markdown("---")
    st.markdown("### 🥖 Planejamento")
    st.caption("Configure os parâmetros base:")

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

    st.markdown("---")
    tipo_fermento = st.selectbox("Fermento", ["Seco (1%)", "Fresco (3%)", "Levain (20%)"])
    fermento_limpo = tipo_fermento.split(" ")[0]
    sal_pct = st.slider("Sal (%)", 1.0, 3.5, 2.0, 0.1)
    temp_ambiente = st.number_input("Temp. Ambiente (°C)", min_value=10.0, max_value=40.0, value=24.0, step=0.5)

# ==========================================
# 6. ABAS CENTRAIS
# ==========================================
aba_calc, aba_extras, aba_custos, aba_sos, aba_b2b = st.tabs([
    "🚀 Calculadora & IA",
    "🧈 Enriquecimento da Massa",
    "💰 Custos & Precificação",
    "🆘 SOS Padeiro",
    "📊 Telemetria B2B",
])

with aba_extras:
    st.info(
        "🧈 **Para que serve esta aba?**\n\n"
        "Defina ingredientes complementares em **percentagem (%) sobre o peso da farinha**.\n"
        "• Escolha um *Perfil Rápido* ou ajuste os controles deslizantes conforme sua receita."
    )
    st.subheader("Ingredientes de Enriquecimento (% sobre a Farinha)")
    opcoes_perfil = [
        "Cachorro-Quente / Forma (Macio)",
        "Hambúrguer / Brioche (Rico)",
        "Pão Rústico (0%)",
        "Personalizado",
    ]
    perfil = st.selectbox("Perfil Rápido", opcoes_perfil)

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
    st.info(
        "💰 **Para que serve esta aba?**\n\n"
        "Insira o preço de compra dos insumos por quilo (ou por unidade nos ovos) para calcular "
        "o **custo total**, **custo por unidade** e **preço sugerido de venda**."
    )
    st.subheader("Tabela de Custos dos Insumos & Margem Comercial")
    cc1, cc2 = st.columns(2)
    with cc1:
        c_farinha = st.number_input("Farinha (R$/kg)", min_value=2.0, max_value=20.0, value=5.50, step=0.5)
        c_fermento = st.number_input("Fermento (R$/kg)", min_value=10.0, max_value=100.0, value=35.0, step=1.0)
        c_acucar = st.number_input("Açúcar (R$/kg)", min_value=2.0, max_value=15.0, value=4.50, step=0.5)
        c_sal = st.number_input("Sal (R$/kg)", min_value=1.0, max_value=10.0, value=3.0, step=0.5)
    with cc2:
        c_gordura = st.number_input("Manteiga / Gordura (R$/kg)", min_value=5.0, max_value=60.0, value=18.0, step=1.0)
        c_leite = st.number_input("Leite em Pó (R$/kg)", min_value=10.0, max_value=80.0, value=30.0, step=1.0)
        c_ovo_unidade = st.number_input("Ovo (R$ por UNIDADE)", min_value=0.20, max_value=2.00, value=0.75, step=0.05)
        margem_lucro = st.slider("Margem de Lucro Desejada (%)", 20.0, 300.0, 100.0, 10.0)

with aba_sos:
    st.info("🆘 **SOS Padeiro:** Clique no problema abaixo para ver a causa provável e como corrigir.")
    with st.expander("💧 A massa ficou muito mole ou grudenta"):
        st.markdown(
            "- **Causa:** Farinha com menos proteína, excesso de água ou falta de glúten.\n"
            "- **Solução:** Descanse 15 min coberta e faça 2 séries de dobras com mãos untadas. Se precisar, adicione farinha aos poucos (1 col. sopa por vez)."
        )
    with st.expander("🧱 O pão ficou pesado, duro ou com miolo fechado"):
        st.markdown(
            "- **Causa:** Falta de fermentação, excesso de farinha na bancada ou fermento inativo.\n"
            "- **Solução:** Teste o fermento em água morna com açúcar (deve espumar em 10 min) e aguarde a massa dobrar de volume."
        )
    with st.expander("🌋 O pão rachou na lateral ou abriu fora do corte"):
        st.markdown(
            "- **Causa:** Fermentação insuficiente na 2ª etapa ou falta de vapor no início.\n"
            "- **Solução:** Fermente mais 10-15 min antes de assar e faça o corte em ângulo de 45°."
        )
    with st.expander("📉 O pão cresceu muito e murchou no forno"):
        st.markdown(
            "- **Causa:** Superfermentação (passou do ponto).\n"
            "- **Solução:** Faça o teste do dedo: aperte leve; se voltar devagar deixando leve marca, leve ao forno. Em dias quentes (>28 °C), use água gelada."
        )
    with st.expander("🥖 A casca ficou pálida ou seca demais"):
        st.markdown(
            "- **Causa:** Forno frio ou tempo excessivo em temperatura baixa.\n"
            "- **Solução:** Preaqueça o forno por 20 min. Use gema + leite em pães macios ou vapor nos primeiros 15 min em pães rústicos."
        )

with aba_calc:
    st.info(
        "👋 **Como usar:** 1) Configure o planejamento na barra lateral. "
        "2) Opcional: envie foto do rótulo da farinha para análise por IA. "
        "3) Clique em **Calcular Ficha de Produção Completa**."
    )
    col_up, col_prev = st.columns([2, 1])
    with col_up:
        st.subheader("Scanner de Rótulo & Simulação Manual")
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
                margem_lucro_pct=margem_lucro,
            )
            st.session_state["resultado_atual"] = {"dados_ia": dados_ia, "receita": calc.calcular()}
            st.success("Ficha calculada com sucesso!")

# ==========================================
# 7. EXIBIÇÃO DOS RESULTADOS
# ==========================================
if "resultado_atual" in st.session_state:
    res = st.session_state["resultado_atual"]
    dados_ia = res["dados_ia"]
    receita = res["receita"]
    contem_gluten = dados_ia.get("contem_gluten", True)

    st.markdown("---")
    if not contem_gluten:
        st.warning("⚠️ **PROTOCOLO SEM GLÚTEN:** Adicionado 2% de Goma Xantana.")

    st.subheader(f"📋 Ficha Técnica — {dados_ia.get('marca')} ({receita.get('peso_total_g', 0)}g de Massa)")

    unidade_exibicao = st.radio(
        "Escolha como deseja visualizar os ingredientes:",
        ["⚖️ Balança (gramas / ml)", "🥄 Medidas Caseiras (Xícaras / Colheres)"],
        horizontal=True,
    )
    usar_caseira = "Caseiras" in unidade_exibicao

    tipo_ferm = str(receita.get("tipo_fermento", "Seco")).lower()
    chave_ferm = "fermento_seco"
    if "fresco" in tipo_ferm:
        chave_ferm = "fermento_fresco"
    elif "levain" in tipo_ferm:
        chave_ferm = "levain"

    farinha_g = receita.get("farinha_g", 0) or 0
    agua_ml = receita.get("agua_ml", 0) or 0
    sal_g = receita.get("sal_g", 0) or 0
    fermento_g = receita.get("fermento_g", 0) or 0

    m1, m2, m3, m4 = st.columns(4)
    if usar_caseira:
        m1.metric("🌾 Farinha Base", converter_medida_caseira(farinha_g, "farinha"), f"{farinha_g} g")
        m2.metric("💧 Água", converter_medida_caseira(agua_ml, "agua"), f"{agua_ml} ml | {receita.get('temp_agua_c')} °C")
        m3.metric("🧂 Sal", converter_medida_caseira(sal_g, "sal"), f"{sal_g} g")
        m4.metric("🦠 Fermento", converter_medida_caseira(fermento_g, chave_ferm), f"{fermento_g} g")
    else:
        m1.metric("🌾 Farinha Base", f"{farinha_g} g")
        m2.metric("💧 Água", f"{agua_ml} ml", f"Ideal: {receita.get('temp_agua_c')} °C")
        m3.metric("🧂 Sal", f"{sal_g} g")
        m4.metric("🦠 Fermento", f"{fermento_g} g")

    if receita.get("massa_enriquecida"):
        acucar_g = receita.get("acucar_g", 0) or 0
        gordura_g = receita.get("gordura_g", 0) or 0
        leite_po_g = receita.get("leite_po_g", 0) or 0
        ovos_g = receita.get("ovos_g", 0) or 0
        ovos_un = receita.get("unidades_ovos_inteiras", 0) or 0

        e1, e2, e3, e4 = st.columns(4)
        if usar_caseira:
            e1.metric("🍬 Açúcar", converter_medida_caseira(acucar_g, "acucar"), f"{acucar_g} g")
            e2.metric("🧈 Manteiga", converter_medida_caseira(gordura_g, "gordura"), f"{gordura_g} g")
            e3.metric("🥛 Leite Pó", converter_medida_caseira(leite_po_g, "leite_po"), f"{leite_po_g} g")
            e4.metric("🥚 Ovos", f"{ovos_un} un.", f"{ovos_g} g")
        else:
            e1.metric("🍬 Açúcar", f"{acucar_g} g")
            e2.metric("🧈 Manteiga", f"{gordura_g} g")
            e3.metric("🥛 Leite Pó", f"{leite_po_g} g")
            e4.metric("🥚 Ovos", f"{ovos_g} g", f"~{ovos_un} unidades")

    p1, p2, p3 = st.columns(3)
    p1.metric("🥖 Formato", receita.get("nome_formato", "-"), f"{receita.get('peso_porcao_g', 0)}g/un")
    p2.metric("📦 Rendimento", f"{receita.get('qtd_unidades', 0)} unidades")
    p3.metric("✂️ Sobra", f"{receita.get('sobra_massa_g', 0)} g")

    passos_preparo = gerar_modo_preparo(receita.get("nome_formato", ""), receita, contem_gluten)
    with st.expander("👨‍🍳 Modo de Preparo Profissional (Passo a Passo)", expanded=True):
        for passo in passos_preparo:
            st.markdown(passo)

    with st.expander("⏰ Cronograma Reverso da Fornada (Planeje o Horário)"):
        hora_alvo = st.time_input("Que horas você quer o pão saindo do forno?", value=datetime.time(18, 0))
        agenda_fornada = gerar_cronograma_reverso(hora_alvo, receita.get("nome_formato", ""), receita, contem_gluten)
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
    # 8. EXPORTAÇÃO: PDF & WHATSAPP
    # ==========================================
    st.markdown("#### 📤 Exportar & Compartilhar")
    if usuario_pro:
        bytes_pdf = b""
        peso_total_int = int(receita.get("peso_total_g", 0) or 0)
        nome_formato_limpo = str(receita.get("nome_formato", "pao")).lower().replace(" ", "_")

        try:
            pdf = FPDF()
            pdf.add_page()
            if caminho_logo:
                pdf.image(caminho_logo, x=10, y=10, w=24)
            pdf.set_font("Arial", "B", 18)
            espaco = "          " if caminho_logo else ""
            pdf.cell(0, 12, txt=limpar_texto_pdf(f"{espaco}MASSA TRADICIONAL - FICHA DE BANCADA"), ln=True)
            pdf.ln(10)

            pdf.set_font("Arial", "", 11)
            r1 = f"Farinha: {dados_ia.get('marca')} | Massa Total: {peso_total_int}g | Hidratacao: {receita.get('hidratacao_pct')}%"
            r2 = f"Rendimento: {receita.get('qtd_unidades')} un. de {receita.get('peso_porcao_g')}g ({receita.get('nome_formato')})"
            r3 = f"Custo Total: R$ {custo_tot:.2f} | Custo/Un: R$ {custo_un:.2f} | Preco Sugerido: R$ {preco_sug:.2f}"
            pdf.cell(0, 8, txt=limpar_texto_pdf(r1), ln=True)
            pdf.cell(0, 8, txt=limpar_texto_pdf(r2), ln=True)
            pdf.cell(0, 8, txt=limpar_texto_pdf(r3), ln=True)
            pdf.ln(5)

            pdf.set_fill_color(35, 31, 30)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(95, 10, " Insumo", border=1, fill=True)
            pdf.cell(95, 10, " Quantidade (Balanca / Caseira)", border=1, fill=True, ln=True)

            pdf.set_text_color(0, 0, 0)
            linhas = [
                ("Farinha Base", f"{farinha_g} g ({converter_medida_caseira(farinha_g, 'farinha')})"),
                ("Água Filtrada", f"{agua_ml} ml ({converter_medida_caseira(agua_ml, 'agua')}) a {receita.get('temp_agua_c')}C"),
                ("Sal", f"{sal_g} g ({converter_medida_caseira(sal_g, 'sal')})"),
                (f"Fermento ({receita.get('tipo_fermento')})", f"{fermento_g} g ({converter_medida_caseira(fermento_g, chave_ferm)})"),
            ]
            if (receita.get("acucar_g", 0) or 0) > 0:
                v = receita.get("acucar_g")
                linhas.append(("Açúcar", f"{v} g ({converter_medida_caseira(v, 'acucar')})"))
            if (receita.get("gordura_g", 0) or 0) > 0:
                v = receita.get("gordura_g")
                linhas.append(("Manteiga / Gordura", f"{v} g ({converter_medida_caseira(v, 'gordura')})"))
            if (receita.get("leite_po_g", 0) or 0) > 0:
                v = receita.get("leite_po_g")
                linhas.append(("Leite em Pó", f"{v} g ({converter_medida_caseira(v, 'leite_po')})"))
            if (receita.get("ovos_g", 0) or 0) > 0:
                linhas.append(("Ovos", f"{receita.get('ovos_g')} g (~{receita.get('unidades_ovos_inteiras')} un.)"))
            if not contem_gluten and "goma_xantana_g" in receita:
                linhas.append(("Goma Xantana", f"{receita.get('goma_xantana_g')} g"))

            for ins, qtd in linhas:
                pdf.cell(95, 10, limpar_texto_pdf(f" {ins}"), border=1)
                pdf.cell(95, 10, limpar_texto_pdf(f" {qtd}"), border=1, ln=True)

            pdf.ln(6)
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 8, txt="MODO DE PREPARO", ln=True)
            pdf.set_font("Arial", "", 10)
            for p in passos_preparo:
                pdf.multi_cell(0, 6, txt=limpar_texto_pdf(p.replace("**", "")))

            saida_pdf = pdf.output(dest="S")
            bytes_pdf = saida_pdf.encode("latin-1", errors="ignore") if isinstance(saida_pdf, str) else bytes(saida_pdf)
        except Exception as e:
            bytes_pdf = b""
            st.error(f"Erro ao gerar o PDF: {e}")

        texto_wpp = montar_texto_whatsapp(dados_ia, receita, usar_caseira, chave_ferm, passos_preparo)
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

with aba_b2b:
    st.info("📊 **Telemetria B2B:** Histórico de farinhas escaneadas e simulações salvas no Firebase.")
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
