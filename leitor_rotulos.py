import os
import json
from pathlib import Path
from PIL import Image
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

class RotuloFarinha(BaseModel):
    marca: str = Field(description="Nome comercial ou fabricante da farinha identificado no rótulo.")
    proteina_g_por_50g: float = Field(description="Quantidade de proteína em gramas ajustada para uma porção de 50g (se a tabela estiver por 100g, divida por 2).")
    forca_estimada: str = Field(description="Classificação da farinha: 'Alta (W >= 300)' se proteína >= 6.0g, 'Média (W 220-290)' se >= 5.0g, senão 'Baixa (W < 220)'.")
    hidratacao_minima: int = Field(description="Percentual de hidratação base recomendada: 68 se proteína >= 6.5, 65 se >= 6.0, 60 se >= 5.0, senão 55.")
    contem_gluten: bool = Field(description="True se contiver trigo/glúten. False se o rótulo indicar 'Não contém glúten', farinha de arroz, amêndoa, mandioca ou milho.")
    observacao_tecnica: str = Field(description="Breve dica de panificação de 1 frase baseada no teor de proteína desta farinha.")

def analisar_imagem_rotulo(img: Image.Image, chave_api: str) -> dict:
    """Analisa uma imagem PIL diretamente usando o Google Gemini e retorna dicionário estruturado."""
    if not chave_api:
        return {"erro": "Chave da API do Gemini não informada."}

    client = genai.Client(api_key=chave_api)

    prompt = (
        "Você é um mestre padeiro e especialista em visão computacional para panificação artesanal. "
        "Analise a imagem da embalagem ou tabela nutricional desta farinha. "
        "Extraia a marca, calcule a proteína exata para uma porção de 50g (atenção: se a tabela mostrar 100g, divida a proteína por 2), "
        "determine se contém glúten, classifique a força da farinha e recomende a hidratação ideal."
    )

    configuracao = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=RotuloFarinha,
        temperature=0.1
    )

    modelos = ["gemini-2.5-flash", "gemini-2.0-flash"]
    ultimo_erro = None

    for modelo in modelos:
        try:
            response = client.models.generate_content(
                model=modelo,
                contents=[prompt, img],
                config=configuracao
            )
            return json.loads(response.text)
        except Exception as e:
            ultimo_erro = str(e)
            continue

    return {"erro": f"Não foi possível processar o rótulo na API Gemini: {ultimo_erro}"}

def analisar_rotulo_farinha(caminho_imagem: str | Path, chave_api: str = "") -> dict:
    """Função auxiliar para testes via terminal."""
    caminho = Path(caminho_imagem)
    if not caminho.is_file():
        return {"erro": f"Arquivo não encontrado: {caminho}"}
    
    chave = chave_api or os.environ.get("GEMINI_API_KEY", "")
    img = Image.open(caminho)
    return analisar_imagem_rotulo(img, chave)