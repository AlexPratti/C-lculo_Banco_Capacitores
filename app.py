import streamlit as st
import pandas as pd
import math
from fpdf import FPDF
from datetime import date
import io

# --- FUNÇÕES DE CÁLCULO ---

def calcular_dimensionamento(p_kw, fp_atual, fp_alvo, tensao):
    # 1. Cálculo da Potência Reativa Necessária (kVAr)
    phi_atual = math.acos(fp_atual)
    phi_alvo = math.acos(fp_alvo)
    kvar_total = p_kw * (math.tan(phi_atual) - math.tan(phi_alvo))
    kvar_total = max(0, float(kvar_total))

    # 2. Cálculo de Corrente e Bitola (NBR 5410 - Cobre/PVC/70°C)
    # Fator de 1.35x para sobrecorrente em capacitores
    corrente_nominal = (kvar_total * 1000) / (math.sqrt(3) * tensao) if kvar_total > 0 else 0
    corrente_projeto = corrente_nominal * 1.35
    
    tabela_cabos = [
        (1.5, 15.5), (2.5, 21), (4, 28), (6, 36), (10, 50), 
        (16, 68), (25, 89), (35, 110), (50, 134), (70, 171), (95, 207), (120, 239)
    ]
    
    bitola_sugerida = 1.5
    for b, amp in tabela_cabos:
        if amp >= corrente_projeto:
            bitola_sugerida = b
            break
    
    # 3. Definição de Estágios e Controlador
    num_estagios = 6 if kvar_total <= 100 else 12
    pot_por_estagio = round(kvar_total / (num_estagios - 1), 2) if kvar_total > 0 else 0
    
    return {
        "kvar_total": round(kvar_total, 2),
        "i_nom": round(corrente_nominal, 2),
        "i_proj": round(corrente_projeto, 2),
        "bitola": bitola_sugerida,
        "estagios": num_estagios,
        "pot_estagio": pot_por_estagio
    }

# --- CLASSE PARA GERAÇÃO DO PDF ---

class RelatorioPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'RELATÓRIO TÉCNICO DE CORREÇÃO DE FATOR DE POTÊNCIA', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

# --- INTERFACE STREAMLIT ---

st.title("⚡ Dimensionamento de Banco de Capacitores")
st.markdown("Cálculo de correção de FP e especificação de condutores (NBR 5410/NBR 17227).")

with st.sidebar:
    st.header("Dados da Instalação")
    cliente = st.text_input("Cliente", "EMPRESA TESTE")
    p_kw = st.number_input("Potência Ativa (kW)", min_value=1.0, value=150.0)
    tensao = st.selectbox("Tensão de Operação (V)", [220, 380, 440], index=1)
    fp_atual = st.slider("Fator de Potência Atual", 0.50, 0.91, 0.82)
    fp_alvo = st.slider("Fator de Potência Desejado", 0.92, 1.00, 0.95)

res = calcular_dimensionamento(p_kw, fp_atual, fp_alvo, tensao)

# Exibição de Resultados na Tela
c1, c2, c3 = st.columns(3)
c1.metric("Total kVAr", f"{res['kvar_total']} kVAr")
c2.metric("Corrente Projeto", f"{res['i_proj']} A")
c3.metric("Bitola do Cabo", f"{res['bitola']} mm²")

if st.button("Gerar Relatório Técnico Completo"):
    pdf = RelatorioPDF()
    pdf.add_page()
    
    # Seção 1: Identificação (Baseado no modelo PDF enviado)
    pdf.set_font("Arial", '', 11)
    pdf.cell(0, 8, f"CLIENTE: {cliente.upper()}", ln=True)
    pdf.cell(0, 8, f"LOCAL: INSTALAÇÃO INDUSTRIAL", ln=True)
    pdf.cell(0, 8, f"EQUIPAMENTO: BANCO DE CAPACITORES {tensao}V", ln=True)
    pdf.cell(0, 8, f"Data de Emissão: {date.today().strftime('%d/%m/%Y')}", ln=True)
    pdf.ln(10)

    # Seção 2: Memorial de Cálculo
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "1. MEMORIAL DE CÁLCULO E PARÂMETROS", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 7, f"- Potência Ativa Instalada: {p_kw} kW", ln=True)
    pdf.cell(0, 7, f"- Fator de Potência Atual: {fp_atual} / Alvo: {fp_alvo}", ln=True)
    pdf.cell(0, 7, f"- Necessidade de Compensação: {res['kvar_total']} kVAr", ln=True)
    pdf.cell(0, 7, f"- Corrente Nominal de Operação: {res['i_nom']} A", ln=True)
    pdf.ln(5)

    # Seção 3: Recomendações Técnicas (Inspirado na Seção 3 do PDF)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "2. RECOMENDAÇÃO E JUSTIFICATIVA TÉCNICA", ln=True)
    pdf.set_font("Arial", '', 10)
    justificativa = (
        f"Com base na NBR 5410, os condutores foram dimensionados com fator de segurança de 1.35 "
        f"sobre a corrente nominal para suportar sobretensões e efeitos harmônicos. "
        f"A bitola mínima exigida para os cabos de cobre (PVC 70°C) é de {res['bitola']} mm²."
    )
    pdf.multi_cell(0, 6, justificativa)
    pdf.ln(5)

    # Seção 4: Tabela de Cargas e Estágios (Inspirado na Seção 5 do PDF)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "3. TABELA DE COMPONENTES E ESTÁGIOS", ln=True)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(45, 10, "Componente", 1)
    pdf.cell(45, 10, "Capacidade", 1)
    pdf.cell(90, 10, "Detalhes Adicionais", 1, ln=True)
    
    pdf.set_font("Arial", '', 9)
    pdf.cell(45, 8, "Controlador FP", 1)
    pdf.cell(45, 8, f"{res['estagios']} Estágios", 1)
    pdf.cell(90, 8, "Automático Digital", 1, ln=True)
    
    pdf.cell(45, 8, "Proteção Geral", 1)
    pdf.cell(45, 8, f"In > {res['i_proj']}A", 1)
    pdf.cell(90, 8, "Disjuntor Termomagnético", 1, ln=True)

    for i in range(1, res['estagios']):
        pdf.cell(45, 8, f"Estágio {i}", 1)
        pdf.cell(45, 8, f"{res['pot_estagio']} kVAr", 1)
        pdf.cell(90, 8, "Célula Capacitiva Trifásica", 1, ln=True)

    # Rodapé de Assinatura
    pdf.ln(15)
    pdf.cell(0, 10, "________________________________________________", ln=True, align='C')
    pdf.cell(0, 5, "Engenheiro Eletricista Responsável", ln=True, align='C')

    # Preparar download
    pdf_bytes = pdf.output(dest='S').encode('latin-1')
    st.download_button(
        label="📥 Baixar Relatório Técnico (PDF)",
        data=pdf_bytes,
        file_name=f"Relatorio_Banco_{cliente}.pdf",
        mime="application/pdf"
    )

st.info("Nota: Este código assume instalação em eletroduto embutido em alvenaria (Método B1 - NBR 5410).")
