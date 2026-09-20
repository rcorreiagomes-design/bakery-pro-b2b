import os
import sys
import json
from pathlib import Path
from PIL import Image
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

# Garante suporte a UTF-8 e acentuação no terminal Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ==============================================================================
# 1. CONFIGURAÇÃO DA CHAVE E CLIENTE GEMINI
# ==============================================================================
CHAVE_API = os.environ.get("GEMINI_API_KEY", "")
client = genai.Client(api_key=CHAVE_API)

# ==============================================================================
# 2. ESQUEMA DE DADOS ESTRUTURADOS (Garante JSON perfeito e tipado)
# ==============================================================================
class RotuloFarinha(BaseModel):
    marca: str = Field(description="Nome comercial ou fabricante da farinha")
    proteina_g_por_50g: float = Field(description="Proteína em gramas para porção de 50g (se tabela for 100g, dividir por 2)")
    forca_estimada: str = Field(description="Força da farinha: 'Alta' se proteína >= 6.0, 'Média' se >= 5.0, senão 'Baixa'")
    hidratacao_minima: int = Field(description="Percentual de hidratação mínima recomendada: 65 se Alta, 60 se Média, 55 se Baixa")


def analisar_rotulo_farinha(caminho_imagem: str | Path) -> dict:
    caminho = Path(caminho_imagem)
    print(f"\n[1/3] Carregando a imagem: {caminho.name}...")

    if not caminho.is_file():
        return {"erro": f"Arquivo não encontrado: {caminho}"}

    try:
        img = Image.open(caminho)
    except Exception as e:
        return {"erro": f"Erro ao abrir arquivo de imagem: {e}"}

    prompt = (
        "Você é um sistema especialista em visão computacional para panificação artesanal. "
        "Analise com atenção a imagem da embalagem e a tabela nutricional desta farinha de trigo. "
        "Extraia a marca e calcule a quantidade exata de proteína por porção de 50g. "
        "Avalie a força estimada ('Alta', 'Média' ou 'Baixa') e a hidratação mínima recomendada (65, 60 ou 55)."
    )

    print("[2/3] Analisando rótulo com Visão Computacional do Gemini...")

    configuracao = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=RotuloFarinha,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
    )

    # Modelos suportados com failover automático em caso de sobrecarga temporária
    modelos = ["gemini-3.6-flash", "gemini-3.8-flash", "gemini-flash-latest"]
    ultimo_erro = None

    for modelo in modelos:
        try:
            response = client.models.generate_content(
                model=modelo,
                contents=[prompt, img],
                config=configuracao
            )
            dados = json.loads(response.text)
            return dados
        except Exception as e:
            ultimo_erro = str(e)
            continue

    return {"erro": f"Falha na comunicação com a API: {ultimo_erro}"}


# ==============================================================================
# 3. TESTE INDIVIDUAL DO MÓDULO
# ==============================================================================
if __name__ == "__main__":
    print("=" * 55)
    print("    MOTOR DE VISÃO COMPUTACIONAL - PANIFICAÇÃO")
    print("=" * 55)

    diretorio_atual = Path(__file__).parent
    foto_teste = diretorio_atual / "foto_venturelli.jpeg"

    resultado = analisar_rotulo_farinha(foto_teste)

    print("\n--- RESULTADO DA ANÁLISE ---")
    if "erro" in resultado:
        print(f"❌ ERRO: {resultado['erro']}")
    else:
        print(f"🌾 Marca Detectada:               {resultado.get('marca')}")
        print(f"💪 Proteína (por 50g):             {resultado.get('proteina_g_por_50g')} g")
        print(f"⚡ Força Estimada:                {resultado.get('forca_estimada')}")
        print(f"💧 Hidratação Mínima Sugerida:    {resultado.get('hidratacao_minima')}%")
        print("=" * 55)

    input("\nPressione ENTER para encerrar...")