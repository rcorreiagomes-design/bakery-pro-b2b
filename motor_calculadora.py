class CalculadoraPanificacao:
    """
    Motor central para cálculo de porcentagem do padeiro reverso.
    Recebe o peso final desejado da massa e retorna a gramatura exata dos insumos.
    """
    def __init__(self, peso_total_massa, hidratacao_pct, sal_pct=2.0, fermento_seco_pct=1.0):
        # Recebe os valores do usuário (ex: 3500g, 65%)
        self.peso_total = peso_total_massa
        
        # Converte as porcentagens para decimais para o motor matemático (ex: 65 vira 0.65)
        self.hidratacao = hidratacao_pct / 100
        self.sal = sal_pct / 100
        self.fermento_seco = fermento_seco_pct / 100

    def calcular_receita(self):
        # A farinha é sempre a base 100% (1.0)
        soma_percentuais = 1.0 + self.hidratacao + self.sal + self.fermento_seco
        
        # Cálculo reverso da base de farinha
        farinha_g = self.peso_total / soma_percentuais
        
        # Proporções dos demais ingredientes
        agua_ml = farinha_g * self.hidratacao # ml = g na conversão de água
        sal_g = farinha_g * self.sal
        fermento_seco_g = farinha_g * self.fermento_seco
        
        # Regra universal: Fermento fresco é 3x o volume do fermento seco
        fermento_fresco_g = fermento_seco_g * 3
        
        return {
            "Farinha_g": round(farinha_g, 1),
            "Agua_ml": round(agua_ml, 1),
            "Sal_g": round(sal_g, 1),
            "Fermento_Seco_g": round(fermento_seco_g, 1),
            "Fermento_Fresco_g": round(fermento_fresco_g, 1)
        }

# ==========================================
# ÁREA DE TESTE (Rode no seu terminal)
# ==========================================
if __name__ == "__main__":
    print("--- INICIANDO MOTOR DE CÁLCULO ---")
    
    # Simulando a fornada de 3,5 kg com a Venturelli (65% de hidratação)
    minha_fornada = CalculadoraPanificacao(
        peso_total_massa=3500, 
        hidratacao_pct=65.0, 
        sal_pct=2.0, 
        fermento_seco_pct=1.0
    )
    
    ficha_tecnica = minha_fornada.calcular_receita()
    
    print(f"\nReceita para {minha_fornada.peso_total}g de massa total:")
    for ingrediente, quantidade in ficha_tecnica.items():
        # Formatação simples para o console ficar amigável
        unidade = "ml" if "ml" in ingrediente else "g"
        nome_limpo = ingrediente.replace("_ml", "").replace("_g", "").replace("_", " ")
        print(f"> {nome_limpo}: {quantidade} {unidade}")