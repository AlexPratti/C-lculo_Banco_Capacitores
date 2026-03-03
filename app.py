import streamlit as st
import pandas as pd
import math
from fpdf import FPDF
from datetime import date

# Configuração da página Streamlit
st.set_page_config(page_title="Dimensionamento de Banco de Capacitores", layout="wide")

def calcular_kvar(p_kw, fp_atual, fp_alvo):
    # Cálculo da potência reativa necessária
    phi_atual = math.acos(fp_atual)
    phi_alvo = math.acos(fp_alvo)
    kvar_necessario = p_kw * (math.tan(phi_atual) - math.tan(phi_alvo))
    return max(0, kvar_necessario)

def sugerir_estagios(kvar_total):
    # Lógica simplificada para divisão de estágios e componentes
    estagios = 6 if kvar_total < 100 else 12
    potencia_estagio = round(kvar_total / (estagios - 1), 2)
    return estagios, potencia_estagio

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'RELATÓRIO TÉCNICO DE CORREÇÃO DE FATOR DE POTÊNCIA', 0, 1, 'C')
        self.ln(10)

# UI do Streamlit
st.title("⚡ Calculador de Banco de Capacitores")

with st.sidebar:
    st.header("Parâmetros de Entrada")
    p_kw = st.number_input("Potência Ativa Total (kW)", min_value=1.0, value=100.0)
    tensao = st.selectbox("Tensão do Sistema (V)", [220, 380, 440])
    fp_atual = st.number_input("Fator de Potência Atual", min_value=0.5, max_value=0.99, value=0.80)
    fp_alvo = st.number_input("Fator de Potência Desejado", min_value=0.92, max_value=1.0, value=0.95)
    cliente = st.text_input("Nome do Cliente", "EMPRESA EXEMPLO")

if st.button("Calcular e Gerar Relatório"):
    kvar_total = calcular_kvar(p_kw, fp_atual, fp_alvo)
    num_estagios, cap_unitario = sugerir_estagios(kvar_total)
    
    # Exibição dos resultados na tela
    st.subheader("Resultados do Dimensionamento")
    col1, col2, col3 = st.columns(3)
    col1.metric("Potência Necessária", f"{kvar_total:.2f} kVAr")
    col2.metric("Total de Estágios", num_estagios)
    col3.metric("Controlador Sugerido", f"{num_estagios} Estágios")

    # Tabela de Componentes
    df_dados = pd.DataFrame({
        "Componente": ["Banco de Capacitores", "Controlador de FP", "Estágios Individuais"],
        "Especificação": [f"{kvar_total:.2f} kVAr", f"Automático {num_estagios} est.", f"{num_estagios-1} x {cap_unitario} kVAr"]
    })
    st.table(df_dados)

    # Geração do PDF seguindo o modelo das imagens
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    
    # Cabeçalho Identificação (Baseado na pág 1)
    pdf.cell(0, 10, f"CLIENTE: {cliente.upper()}", ln=True)
    pdf.cell(0, 10, f"EQUIPAMENTO: BANCO DE CAPACITORES {tensao}V", ln=True)
    pdf.cell(0, 10, f"Data de Emissão: {date.today().strftime('%d/%m/%Y')}", ln=True)
    pdf.ln(10)

    # Memorial de Cálculo (Baseado na pág 3)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "1. MEMORIAL DE CÁLCULO E PARÂMETROS", ln=True)
    pdf.set_font("Arial", size=11)
    pdf.cell(0, 8, f"- Potência Ativa: {p_kw} kW", ln=True)
    pdf.cell(0, 8, f"- FP Atual: {fp_atual} / FP Alvo: {fp_alvo}", ln=True)
    pdf.cell(0, 8, f"- Potência Reativa Total Necessária: {kvar_total:.2f} kVAr", ln=True)
    
    # Tabela de Estágios (Baseado na pág 4)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "2. TABELA DE CARGAS INDIVIDUAIS", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.cell(60, 10, "Estágio", 1)
    pdf.cell(60, 10, "Potência (kVAr)", 1)
    pdf.cell(60, 10, "Tipo", 1, ln=True)
    
    for i in range(1, num_estagios):
        pdf.cell(60, 10, f"Estágio {i}", 1)
        pdf.cell(60, 10, f"{cap_unitario}", 1)
        pdf.cell(60, 10, "Fixa/Automática", 1, ln=True)

    # Rodapé Profissional
    pdf.ln(20)
    pdf.cell(0, 10, "________________________________________________", ln=True, align='C')
    pdf.cell(0, 10, "Responsável Técnico - Engenharia Elétrica", ln=True, align='C')

    # Download do PDF
    pdf_output = pdf.output(dest='S').encode('latin-1')
    st.download_button(label="📥 Baixar Relatório Técnico (PDF)", data=pdf_output, file_name="Relatorio_Capacitores.pdf", mime="application/pdf")
