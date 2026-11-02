class CalculadoraPanificacao:
    """
    Motor central para cálculo de percentagem de padeiro reversa, enriquecimento de massa,
    divisão de bancada e custos unitários (tratando ovos por unidade).
    """
    def __init__(
        self,
        peso_total_massa: float,
        hidratacao_pct: float,
        sal_pct: float = 2.0,
        tipo_fermento: str = "Seco",
        temp_ambiente: float = 25.0,
        contem_gluten: bool = True,
        peso_porcao_g: float = 0.0,
        nome_formato: str = "Massa Única",
        acucar_pct: float = 0.0,
        gordura_pct: float = 0.0,
        leite_po_pct: float = 0.0,
        ovos_pct: float = 0.0,
        # Custos dos insumos
        custo_farinha_kg: float = 5.0,
        custo_sal_kg: float = 3.0,
        custo_fermento_kg: float = 35.0,
        custo_acucar_kg: float = 4.5,
        custo_gordura_kg: float = 18.0,
        custo_leite_po_kg: float = 30.0,
        custo_ovo_unidade: float = 0.75,  # Preço por unidade de ovo (ex: R$ 0,75 cada)
        margem_lucro_pct: float = 100.0
    ):
        self.peso_total = float(peso_total_massa)
        self.hidratacao = float(hidratacao_pct) / 100.0
        self.sal = float(sal_pct) / 100.0
        self.tipo_fermento = tipo_fermento.strip().capitalize()
        self.temp_ambiente = float(temp_ambiente)
        self.contem_gluten = bool(contem_gluten)
        self.peso_porcao_g = float(peso_porcao_g)
        self.nome_formato = nome_formato

        self.acucar = float(acucar_pct) / 100.0
        self.gordura = float(gordura_pct) / 100.0
        self.leite_po = float(leite_po_pct) / 100.0
        self.ovos = float(ovos_pct) / 100.0

        self.c_farinha = custo_farinha_kg
        self.c_sal = custo_sal_kg
        self.c_fermento = custo_fermento_kg
        self.c_acucar = custo_acucar_kg
        self.c_gordura = custo_gordura_kg
        self.c_leite_po = custo_leite_po_kg
        self.c_ovo_unidade = custo_ovo_unidade
        self.margem_lucro = float(margem_lucro_pct) / 100.0

        if self.tipo_fermento.lower() == "levain":
            self.fermento_pct = 0.20
        elif self.tipo_fermento.lower() == "fresco":
            self.fermento_pct = 0.03
        else:
            self.fermento_pct = 0.01

        self.goma_xantana_pct = 0.00 if self.contem_gluten else 0.02

    def calcular(self) -> dict:
        soma_percentuais = (
            1.0
            + self.hidratacao
            + self.sal
            + self.fermento_pct
            + self.goma_xantana_pct
            + self.acucar
            + self.gordura
            + self.leite_po
            + self.ovos
        )

        farinha_g = self.peso_total / soma_percentuais
        agua_ml = farinha_g * self.hidratacao
        sal_g = farinha_g * self.sal
        fermento_g = farinha_g * self.fermento_pct

        acucar_g = farinha_g * self.acucar
        gordura_g = farinha_g * self.gordura
        leite_po_g = farinha_g * self.leite_po
        ovos_g = farinha_g * self.ovos

        # Consideramos um ovo médio sem casca com aprox. 50g
        unidades_ovos_aprox = (ovos_g / 50.0) if ovos_g > 0 else 0.0
        unidades_ovos_inteiras = max(1, round(unidades_ovos_aprox)) if ovos_g > 0 else 0

        temp_alvo = 25.0
        fator_friccao = 5.0
        temp_agua = (temp_alvo * 3.0) - (self.temp_ambiente * 2.0) - fator_friccao

        if self.peso_porcao_g > 0:
            qtd_unidades = int(self.peso_total // self.peso_porcao_g)
            sobra_massa_g = round(self.peso_total % self.peso_porcao_g, 1)
        else:
            qtd_unidades = 1
            sobra_massa_g = 0.0

        # Custos
        custo_farinha = (farinha_g / 1000.0) * self.c_farinha
        custo_sal = (sal_g / 1000.0) * self.c_sal
        custo_fermento = (fermento_g / 1000.0) * self.c_fermento
        custo_acucar = (acucar_g / 1000.0) * self.c_acucar
        custo_gordura = (gordura_g / 1000.0) * self.c_gordura
        custo_leite_po = (leite_po_g / 1000.0) * self.c_leite_po
        custo_ovos = unidades_ovos_inteiras * self.c_ovo_unidade

        custo_total_fornada = (
            custo_farinha + custo_sal + custo_fermento + 
            custo_acucar + custo_gordura + custo_leite_po + custo_ovos
        )

        unidades_efetivas = qtd_unidades if qtd_unidades > 0 else 1
        custo_por_unidade = custo_total_fornada / unidades_efetivas
        preco_sugerido_unidade = custo_por_unidade * (1.0 + self.margem_lucro)

        massa_enriquecida = any(x > 0 for x in [self.acucar, self.gordura, self.leite_po, self.ovos])

        return {
            "peso_total_g": round(self.peso_total, 1),
            "farinha_g": round(farinha_g, 1),
            "agua_ml": round(agua_ml, 1),
            "sal_g": round(sal_g, 1),
            "fermento_g": round(fermento_g, 1),
            "fermento_fresco_equivalente_g": round(farinha_g * 0.03, 1),
            "tipo_fermento": self.tipo_fermento,
            "temp_agua_c": round(temp_agua, 1),
            "contem_gluten": self.contem_gluten,
            "hidratacao_pct": round(self.hidratacao * 100, 1),
            "nome_formato": self.nome_formato,
            "peso_porcao_g": round(self.peso_porcao_g, 1) if self.peso_porcao_g > 0 else round(self.peso_total, 1),
            "qtd_unidades": qtd_unidades,
            "sobra_massa_g": sobra_massa_g,
            "massa_enriquecida": massa_enriquecida,
            "acucar_g": round(acucar_g, 1),
            "acucar_pct": round(self.acucar * 100, 1),
            "gordura_g": round(gordura_g, 1),
            "gordura_pct": round(self.gordura * 100, 1),
            "leite_po_g": round(leite_po_g, 1),
            "leite_po_pct": round(self.leite_po * 100, 1),
            "ovos_g": round(ovos_g, 1),
            "ovos_pct": round(self.ovos * 100, 1),
            "unidades_ovos_inteiras": unidades_ovos_inteiras,
            "custo_total_fornada": round(custo_total_fornada, 2),
            "custo_por_unidade": round(custo_por_unidade, 2),
            "preco_sugerido_unidade": round(preco_sugerido_unidade, 2),
            "margem_lucro_pct": round(self.margem_lucro * 100, 1),
            "goma_xantana_g": round(farinha_g * self.goma_xantana_pct, 1) if not self.contem_gluten else 0.0
        }