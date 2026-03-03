import streamlit as st
import pandas as pd
import math
from fpdf import FPDF
from datetime import date
import io

# --- FUNÇÕES DE CÁLCULO ---

def calcular_dimensionamento(p_kw, fp_atual, fp_alvo, tensao):
    # 1. Cálculo da Potência Reativa Necessária (kVAr)
    # Evita erro de domínio se FP for 1.0
    phi_atual = math.acos(min(fp_atual, 0.9999))
    phi_alvo = math.acos(min(fp_alvo, 0.9999))
    kvar_total = p_kw * (math.tan(phi_atual) - math.tan(phi_alvo))
    kvar_total = max(0.0, float(kvar_total))

    # 2. Cálculo de Corrente e Bitola (NBR 5410 - Cobre/PVC/70°C)
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
            
    return {
        "kvar_total": round(kvar_total, 2),
        "i_nom": round(corrente_nominal, 2),
        "i_proj": round(corrente_projeto, 2),
        "bitola": bitola_sugerida,
        "estagios": 6 if kvar_total <= 100 else 12,
        "pot_estagio": round(kvar_total / 5, 2) if kvar_total <= 100 else round(kvar_total / 11, 2)
    }

# --- CLASSE PARA GERAÇÃO DO PDF ---

class RelatorioPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'RELATORIO TECNICO DE CORRECAO DE FATOR DE POTENCIA', 0, 1, 'C')
        self.ln(5)

# --- INTERFACE STREAMLIT ---

st.set_page_config(page_title="Dimensionamento Elétrico", page_icon="⚡")
st.title("⚡ Calculador de Banco de Capacitores")

with st.form("form_calculo"):
    col_a, col_b = st.columns(2)
    with col_a:
        cliente = st.text_input("Cliente", "EMPRESA TESTE")
        p_kw = st.number_input("Potencia Ativa (kW)", min_value=0.1, value=150.0)
        tensao = st.selectbox("Tensao (V)", [220, 380, 440], index=1)
    with col_b:
        # Inputs digitáveis conforme solicitado
        fp_atual = st.number_input("Fator de Potencia Atual (ex: 0.82)", min_value=0.50, max_value=0.99, value=0.82, step=0.01)
        fp_alvo = st.number_input("Fator de Potencia Alvo (ex: 0.95)", min_value=0.92, max_value=1.00, value=0.95, step=0.01)
    
    btn_calcular = st.form_submit_button("Calcular e Preparar Relatório")

if btn_calcular:
    res = calcular_dimensionamento(p_kw, fp_atual, fp_alvo, tensao)
    
    st.success("Cálculo realizado com sucesso!")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total kVAr", f"{res['kvar_total']} kVAr")
    c2.metric("Corrente Projeto", f"{res['i_proj']} A")
    c3.metric("Cabo Sugerido", f"{res['bitola']} mm²")

    # Geração do PDF em memória
    pdf = RelatorioPDF()
    pdf.add_page()
    pdf.set_font("Arial", '', 10)
    
    # Seção 1: Identificação
    pdf.cell(0, 8, f"CLIENTE: {cliente.upper()}", ln=True)
    pdf.cell(0, 8, f"EQUIPAMENTO: BANCO DE CAPACITORES {tensao}V", ln=True)
    pdf.cell(0, 8, f"DATA: {date.today().strftime('%d/%m/%Y')}", ln=True)
    pdf.ln(5)

    # Seção 2: Memorial
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 10, "1. MEMORIAL DE CALCULO E PARAMETROS", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 7, f"- Potencia Ativa: {p_kw} kW", ln=True)
    pdf.cell(0, 7, f"- FP Atual: {fp_atual} / FP Alvo: {fp_alvo}", ln=True)
    pdf.cell(0, 7, f"- Potencia Reativa: {res['kvar_total']} kVAr", ln=True)
    pdf.ln(5)

    # Seção 3: Condutores
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 10, "2. ESPECIFICACAO DE CONDUTORES (NBR 5410)", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.multi_cell(0, 7, f"Corrente de projeto considerada (1.35x In): {res['i_proj']} A. Bitola do cabo de cobre sugerida: {res['bitola']} mm2.")
    pdf.ln(5)

    # Seção 4: Tabela de Estágios
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 10, "3. COMPONENTES DO SISTEMA", ln=True)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(60, 8, "Item", 1); pdf.cell(60, 8, "Capacidade", 1); pdf.cell(60, 8, "Qtd", 1, ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(60, 8, "Controlador FP", 1); pdf.cell(60, 8, f"{res['estagios']} Estagios", 1); pdf.cell(60, 8, "1 un", 1, ln=True)
    pdf.cell(60, 8, "Celulas Capacitivas", 1); pdf.cell(60, 8, f"{res['pot_estagio']} kVAr", 1); pdf.cell(60, 8, f"{res['estagios']-1} un", 1, ln=True)

    # Assinatura
    pdf.ln(20)
    pdf.cell(0, 10, "________________________________________________", ln=True, align='C')
    pdf.cell(0, 5, "Engenheiro Eletricista", ln=True, align='C')

    # Output do PDF para o Streamlit
    pdf_output = pdf.output(dest='S').encode('latin-1', errors='replace')
    
    st.download_button(
        label="📥 Baixar Relatório (PDF)",
        data=pdf_output,
        file_name=f"Relatorio_{cliente}.pdf",
        mime="application/pdf"
    )
