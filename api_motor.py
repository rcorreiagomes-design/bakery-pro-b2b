from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import io
import os
import firebase_admin
from firebase_admin import credentials, firestore

from motor_calculadora import CalculadoraPanificacao
from leitor_rotulos import analisar_imagem_farinha

db = None
if not firebase_admin._apps:
    caminho_credencial = os.path.join(os.path.dirname(__file__), "firebase_key.json")
    if os.path.exists(caminho_credencial):
        cred = credentials.Certificate(caminho_credencial)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
else:
    db = firestore.client()

app = FastAPI(title="Motor API - Massa Tradicional & Panificação PRO B2B")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "online", "firebase_conectado": db is not None}

@app.post("/analisar_e_calcular/")
async def analisar_fornada(
    peso_desejado: float = Form(...),
    chave_api: str = Form(...),
    tipo_fermento: str = Form("Seco"),
    temp_ambiente: float = Form(25.0),
    sal_pct: float = Form(2.0),
    peso_porcao_g: float = Form(70.0),
    nome_formato: str = Form("Pão de Cachorro-Quente"),
    acucar_pct: float = Form(0.0),
    gordura_pct: float = Form(0.0),
    leite_po_pct: float = Form(0.0),
    ovos_pct: float = Form(0.0),
    foto_rotulo: UploadFile = File(...)
):
    try:
        conteudo_imagem = await foto_rotulo.read()
        img = Image.open(io.BytesIO(conteudo_imagem))

        dados_ia = analisar_imagem_farinha(img, chave_api)
        if "erro" in dados_ia:
            return {"status": "erro", "mensagem": dados_ia["erro"]}

        calc = CalculadoraPanificacao(
            peso_total_massa=peso_desejado,
            hidratacao_pct=dados_ia.get("hidratacao_minima", 60),
            sal_pct=sal_pct,
            tipo_fermento=tipo_fermento,
            temp_ambiente=temp_ambiente,
            contem_gluten=dados_ia.get("contem_gluten", True),
            peso_porcao_g=peso_porcao_g,
            nome_formato=nome_formato,
            acucar_pct=acucar_pct,
            gordura_pct=gordura_pct,
            leite_po_pct=leite_po_pct,
            ovos_pct=ovos_pct
        )
        receita_final = calc.calcular()

        if db is not None:
            registro_b2b = {
                "marca_detectada": dados_ia.get("marca"),
                "proteina_50g": dados_ia.get("proteina_g_por_50g"),
                "forca_estimada": dados_ia.get("forca_estimada"),
                "hidratacao_aplicada": dados_ia.get("hidratacao_minima"),
                "peso_fornada": peso_desejado,
                "formato_pao": nome_formato,
                "qtd_unidades": receita_final.get("qtd_unidades"),
                "massa_enriquecida": receita_final.get("massa_enriquecida"),
                "tipo_fermento": tipo_fermento,
                "temp_ambiente": temp_ambiente,
                "contem_gluten": dados_ia.get("contem_gluten", True),
                "receita_gerada": receita_final,
                "timestamp": firestore.SERVER_TIMESTAMP
            }
            db.collection("scans_farinha").add(registro_b2b)

        return {
            "status": "sucesso",
            "mensagem": "Ficha técnica processada com sucesso.",
            "inteligencia_extraida": dados_ia,
            "receita_calculada": receita_final
        }

    except Exception as e:
        return {"status": "erro", "mensagem": str(e)}