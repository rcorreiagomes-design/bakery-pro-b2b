from fastapi import FastAPI, UploadFile, File, Form
from google import genai
from PIL import Image
import io
import json
import os
import firebase_admin
from firebase_admin import credentials, firestore

# ==========================================
# INICIALIZAÇÃO DO BANCO DE DADOS (FIREBASE)
# ==========================================
if not firebase_admin._apps:
    caminho_credencial = os.path.join(os.path.dirname(__file__), "firebase_key.json")
    cred = credentials.Certificate(caminho_credencial)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ==========================================
# CONFIGURAÇÃO DA API E MATEMÁTICA AVANÇADA
# ==========================================
app = FastAPI(title="Motor API - Panificação PRO & B2B Intelligence")

class CalculadoraPanificacao:
    def __init__(self, peso_total, hidratacao_pct, sal_pct, tipo_fermento, temp_ambiente, contem_gluten):
        self.peso_total = peso_total
        self.hidratacao = hidratacao_pct / 100
        self.sal = sal_pct / 100
        self.tipo_fermento = tipo_fermento
        self.temp_ambiente = temp_ambiente
        self.contem_gluten = contem_gluten
        
        # Regra de negócio do fermento
        if self.tipo_fermento.lower() == "levain":
            self.fermento = 0.20 # 20% de Fermento Natural
        else:
            self.fermento = 0.01 # 1% de Fermento Seco
            
        # Regra de negócio do Glúten (Agente Ligante)
        self.goma_xantana = 0.00
        if not self.contem_gluten:
            self.goma_xantana = 0.02 # 2% de Goma Xantana para dar estrutura à massa

    def calcular(self):
        # 1. Cálculo dos Pesos (Soma total dos percentuais)
        soma = 1.0 + self.hidratacao + self.sal + self.fermento + self.goma_xantana
        farinha_g = self.peso_total / soma
        
        # 2. Cálculo da Temperatura da Água
        temp_alvo = 25
        fator_friccao = 5
        temp_agua = (temp_alvo * 3) - self.temp_ambiente - self.temp_ambiente - fator_friccao
        
        resultado = {
            "farinha_g": round(farinha_g, 1),
            "agua_ml": round(farinha_g * self.hidratacao, 1),
            "sal_g": round(farinha_g * self.sal, 1),
            "fermento_g": round(farinha_g * self.fermento, 1),
            "tipo_fermento": self.tipo_fermento.capitalize(),
            "temp_agua_c": round(temp_agua, 1),
            "contem_gluten": self.contem_gluten
        }
        
        # Se for sem glúten, adiciona a Goma Xantana à ficha técnica final
        if not self.contem_gluten:
            resultado["goma_xantana_g"] = round(farinha_g * self.goma_xantana, 1)
            
        return resultado

@app.post("/analisar_e_calcular/")
async def analisar_fornada(
    peso_desejado: int = Form(...),
    chave_api: str = Form(...),
    tipo_fermento: str = Form("Seco"),
    temp_ambiente: float = Form(25.0),
    foto_rotulo: UploadFile = File(...)
):
    try:
        conteudo_imagem = await foto_rotulo.read()
        img = Image.open(io.BytesIO(conteudo_imagem))

        client = genai.Client(api_key=chave_api)
        
        # PROMPT ATUALIZADO: IA agora deteta se há glúten
        prompt = """
        Retorne APENAS um JSON:
        - "marca": Nome da farinha.
        - "proteina_g_por_50g": Proteína para 50g (float).
        - "hidratacao_minima": Se proteina >= 6.0 retorne 65, se >= 5.0 retorne 60, senao 55.
        - "contem_gluten": Booleano (true/false). Leia os ingredientes ou alertas alergénicos da imagem. Se o rótulo disser 'Não contém glúten', 'Gluten-free', ou for farinha de arroz/amêndoa, retorne false. Caso contrário, retorne true.
        """
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=[prompt, img]
        )
        
        dados_ia = json.loads(response.text.replace("```json", "").replace("```", "").strip())
        
        calc = CalculadoraPanificacao(
            peso_total=peso_desejado,
            hidratacao_pct=dados_ia.get("hidratacao_minima"),
            sal_pct=2.0,
            tipo_fermento=tipo_fermento,
            temp_ambiente=temp_ambiente,
            contem_gluten=dados_ia.get("contem_gluten", True)
        )
        receita_final = calc.calcular()

        # Adicionamos a flag de glúten no payload do Firestore (B2B Intelligence)
        registro_b2b = {
            "marca_detectada": dados_ia.get("marca"),
            "proteina_50g": dados_ia.get("proteina_g_por_50g"),
            "hidratacao_aplicada": dados_ia.get("hidratacao_minima"),
            "peso_fornada": peso_desejado,
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