import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import calendar
import streamlit as st

from utils import *
from database import carregar_contas, carregar_financas, login_user, register_user
from controllers import (
    registrar_novo_lancamento, pagar_lancamento, excluir_lancamento, editar_lancamento_controller,
    gerar_relatorio_csv, gerar_relatorio_pdf, fechar_fatura_cartao_controller, verificar_alertas_vencimento,
    logout_usuario, adicionar_cartao_controller, atualizar_cartao_controller, excluir_cartao_controller
)

# Authentication state management
if 'user_id' not in st.session_state: st.session_state.user_id = None
if 'show_register' not in st.session_state: st.session_state.show_register = False
if 'show_forgot_password' not in st.session_state: st.session_state.show_forgot_password = False
if 'msg_sucesso' not in st.session_state: st.session_state.msg_sucesso = None

# Auth Routing UI
if st.session_state.user_id is None:
    bg_image_url = "https://i.imgur.com/piWdBst.jpeg"
    
    st.markdown(f"""
    <style>
        .stApp {{
            background-image: linear-gradient(rgba(15, 23, 42, 0.75), rgba(15, 23, 42, 0.95)), url('{bg_image_url}');
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        [data-testid="stHeader"] {{
            background-color: transparent !important;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"],
        div[data-testid="stForm"] {{
            background-color: #0f172a !important; 
            border-radius: 12px !important;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            border: 1px solid #1e293b !important;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5) !important;
        }}
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <h1 style='text-align: center; font-weight: 1000; letter-spacing: -2px; 
                   background: -webkit-linear-gradient(45deg, #2dd4bf, #0ea5e9); 
                   -webkit-background-clip: text; 
                   -webkit-text-fill-color: transparent; 
                   margin-bottom: 20px;'>
            FinOps Personal
        </h1>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        if st.session_state.show_forgot_password:
            with st.container(border=True):
                st.markdown(f'<div style="display: flex; align-items: center; justify-content: center; gap: 10px; margin-bottom: 20px;">{ic_lock}<h3 style="margin: 0; color: #f8fafc;">Recuperar Senha</h3></div>', unsafe_allow_html=True)

                aba1, aba2 = st.tabs(["1. Solicitar Código", "2. Redefinir Senha"])
                
                with aba1:
                    st.info("Digite seu e-mail. Você receberá um código de 6 dígitos.", icon=":material/info:")
                    with st.form("form_recover", clear_on_submit=False):
                        email_rec = st.text_input("Seu E-mail cadastrado")
                        if st.form_submit_button("Enviar Código", use_container_width=True):
                            from database import recuperar_senha
                            sucesso, msg = recuperar_senha(email_rec)
                            if sucesso: st.success(msg, icon=":material/mark_email_read:")
                            else: st.error(msg, icon=":material/error:")
                            
                with aba2:
                    with st.form("form_reset", clear_on_submit=True):
                        email_reset = st.text_input("Confirme seu E-mail")
                        codigo_otp = st.text_input("Código de 6 dígitos (recebido no e-mail)")
                        nova_senha = st.text_input("Nova Senha", type="password")
                        if st.form_submit_button("Atualizar Senha", type="primary", use_container_width=True):
                            from database import redefinir_senha_com_token
                            suc, m = redefinir_senha_com_token(email_reset, codigo_otp, nova_senha)
                            if suc:
                                st.session_state.msg_sucesso = m
                                st.session_state.show_forgot_password = False
                                st.rerun()
                            else:
                                st.error(m, icon=":material/error:")
                
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Voltar para o Login", use_container_width=True):
                    st.session_state.show_forgot_password = False
                    st.rerun()

        elif st.session_state.show_register:
            with st.container(border=True):
                st.markdown(f'<div style="display: flex; align-items: center; justify-content: center; gap: 10px; margin-bottom: 20px;">{ic_user}<h3 style="margin: 0; color: #f8fafc;">Criar Nova Conta</h3></div>', unsafe_allow_html=True)
                with st.form("form_register", clear_on_submit=False):
                    email = st.text_input("Seu melhor E-mail")
                    senha = st.text_input("Sua Senha Mestra", type="password")
                    if st.form_submit_button("Criar Conta", use_container_width=True):
                        pode_salvar, user = register_user(email, senha)
                        if pode_salvar:
                            st.session_state.msg_sucesso = "Conta criada com sucesso! Faça seu login abaixo."
                            st.session_state.show_register = False
                            st.rerun()
                        else:
                            st.error("Erro ao criar conta. Verifique o e-mail ou tente novamente.", icon=":material/error:")
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Voltar para o Login", use_container_width=True):
                    st.session_state.show_register = False
                    st.rerun()
                    
        else:
            with st.container(border=True):
                st.markdown(f'<div style="display: flex; align-items: center; justify-content: center; gap: 10px; margin-bottom: 20px;">{ic_lock}<h3 style="margin: 0; color: #f8fafc;">Acesso ao Painel</h3></div>', unsafe_allow_html=True)
                if st.session_state.msg_sucesso:
                    st.success(st.session_state.msg_sucesso, icon=":material/check_circle:")
                    st.session_state.msg_sucesso = None 
                    
                with st.form("form_login", clear_on_submit=False):
                    email = st.text_input("E-mail")
                    senha = st.text_input("Senha", type="password")
                    if st.form_submit_button("Entrar", use_container_width=True):
                        pode_entrar, user = login_user(email, senha)
                        if pode_entrar:
                            st.session_state.user_id = user.id
                            st.rerun()
                        else:
                            st.error("E-mail ou senha incorretos.", icon=":material/error:")
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                col_btn1, col_btn2 = st.columns(2)
                if col_btn1.button("Não tem conta?", use_container_width=True):
                    st.session_state.show_register = True
                    st.rerun()
                if col_btn2.button("Esqueceu a senha?", use_container_width=True):
                    st.session_state.show_forgot_password = True
                    st.rerun()
                    
    st.stop()

# Main Application Initialization
injetar_css_global()
df_contas = carregar_contas(st.session_state.user_id)
df_raw = carregar_financas(st.session_state.user_id)

# Robust Pre-processing
if df_raw.empty:
    df = pd.DataFrame(columns=['id', 'Data', 'Tipo', 'Categoria', 'Valor', 'Status', 'Parcela', 'conta_id', 'Conta', 'created_at', 'user_id'])
else:
    df = df_raw.copy()
    if not df_contas.empty:
        df['conta_id'] = pd.to_numeric(df['conta_id'], errors='coerce')
        df_contas_merge = df_contas[['id', 'nome']].rename(columns={'id': 'id_do_cartao'})
        df = df.merge(df_contas_merge, left_on='conta_id', right_on='id_do_cartao', how='left')
        df.rename(columns={'nome': 'Conta'}, inplace=True)
    else: 
        df['Conta'] = pd.NA

df['Conta'] = df['Conta'].fillna("Saldo Geral")
df.rename(columns={'data': 'Data', 'tipo': 'Tipo', 'categoria': 'Categoria', 'valor': 'Valor', 'status': 'Status', 'parcela': 'Parcela'}, inplace=True)
df['Data'] = pd.to_datetime(df['Data'], errors='coerce')

if 'Status' not in df.columns: df['Status'] = 'Realizado'
if 'Parcela' not in df.columns: df['Parcela'] = None

df['Mês'] = df['Data'].dt.strftime('%Y-%m')

# Sidebar: Credit Cards & Transactions
st.sidebar.markdown(f'<h3 style="margin-top:0; color: #f8fafc; display: flex; align-items: center; gap: 8px;">{ic_card} Cartões de Crédito</h3>', unsafe_allow_html=True)

with st.sidebar.expander("Adicionar Novo Cartão", icon=":material/add_card:"):
    with st.form(key="form_nova_conta", clear_on_submit=True):
        nome_conta = st.selectbox("Selecione o Cartão", CARTOES_PERMITIDOS)
        limite_conta = st.number_input("Limite Total (R$)", min_value=0.0, step=100.0, format="%.2f")
        col_f, col_v = st.columns(2)
        dia_fechamento = col_f.number_input("Fechamento", min_value=1, max_value=31, value=None, placeholder="Ex: 25")
        dia_vencimento = col_v.number_input("Vencimento", min_value=1, max_value=31, value=None, placeholder="Ex: 05")
        
        if st.form_submit_button("Salvar Cartão"):
            sucesso, msg = adicionar_cartao_controller(nome_conta, limite_conta, dia_fechamento, dia_vencimento, st.session_state.user_id)
            if sucesso: 
                st.toast("Cartão adicionado com sucesso!", icon=":material/check_circle:")
                st.rerun()
            else: st.warning(msg, icon=":material/warning:")

if not df_contas.empty:
    with st.sidebar.expander("Gerenciar / Excluir Cartões", icon=":material/settings:"):
        cartao_editar = st.selectbox("Selecione o Cartão:", df_contas['nome'].tolist(), key="sel_ed_cartao")
        linha_cartao = df_contas[df_contas['nome'] == cartao_editar].iloc[0]
        id_cartao_editar = int(linha_cartao['id'])
        
        novo_limite = st.number_input("Alterar Limite (R$)", value=float(linha_cartao['limite']), min_value=0.0, step=100.0, format="%.2f", key="num_ed_limite")
        col_f_ed, col_v_ed = st.columns(2)
        novo_fechamento = col_f_ed.number_input("Fechamento", min_value=1, max_value=31, value=int(linha_cartao.get('dia_fechamento', 30)), key="num_ed_fechamento")
        novo_vencimento = col_v_ed.number_input("Vencimento", min_value=1, max_value=31, value=int(linha_cartao.get('dia_vencimento', 7)), key="num_ed_vencimento")
        
        col_up, col_del = st.columns(2)
        if col_up.button("Atualizar", use_container_width=True):
            sucesso, msg = atualizar_cartao_controller(id_cartao_editar, novo_limite, novo_fechamento, novo_vencimento)
            if sucesso: st.rerun()
            else: st.error(msg, icon=":material/error:")
            
        if col_del.button("Excluir", type="primary", use_container_width=True):
            sucesso, msg = excluir_cartao_controller(id_cartao_editar)
            if sucesso: st.rerun()
            else: st.error(msg, icon=":material/error:")

st.sidebar.divider()

# Sidebar: Transaction Input Form
st.sidebar.markdown(f'<h3 style="color: #f8fafc; display: flex; align-items: center; gap: 8px;">{ic_add} Novo Registro</h3>', unsafe_allow_html=True)

with st.sidebar.container(border=True):
    tipo = st.selectbox("O que é isso?", ["Despesa (Gasto)", "Receita (Salário/Entrada)", "Reserva (Caixinha)", "Resgate da Caixinha", "Pagamento de Fatura"])
    opcoes_pagamento = ["Saldo Geral (Dinheiro/Pix)"] + (df_contas['nome'].tolist() if not df_contas.empty else [])
    forma_pagamento = st.selectbox("Forma de Pagamento", opcoes_pagamento)
    categoria = st.text_input("Categoria (ex: Mercado, Luz, Salário)")
    data_lancamento = st.date_input("Data do Lançamento", datetime.today())
    
    is_credito = forma_pagamento != "Saldo Geral (Dinheiro/Pix)"
    is_parcelado, is_fixa, qtd_parcelas = False, False, 1
    
    if tipo == "Despesa (Gasto)":
        modalidade = st.radio("Modalidade:", ["Única (À vista)", "Parcelada", "Assinatura / Fixa"] if is_credito else ["Única (À vista)", "Assinatura / Fixa"], horizontal=True)
            
        if modalidade == "Parcelada":
            is_parcelado = True
            qtd_parcelas = st.number_input("Em quantas vezes?", min_value=2, max_value=24, value=2)
            tipo_juros = st.radio("Cálculo:", ["Sem Juros (Dividir Valor)", "Com Juros (Informar Parcela)"])
            
            if tipo_juros == "Sem Juros (Dividir Valor)":
                valor_total = st.number_input("Valor TOTAL da Compra (R$)", min_value=0.01, step=10.0)
                valor_parcela = valor_total / qtd_parcelas
                st.info(f"Serão {qtd_parcelas}x de R$ {valor_parcela:,.2f}", icon=":material/info:")
            else:
                valor_parcela = st.number_input("Valor de CADA Parcela (R$)", min_value=0.01, step=10.0)
                valor_total = valor_parcela * qtd_parcelas
                st.info(f"O Custo Total será R$ {valor_total:,.2f}", icon=":material/info:")
                
        elif modalidade == "Assinatura / Fixa":
            is_fixa, qtd_parcelas = True, 12
            valor_parcela = st.number_input("Valor Mensal (R$)", min_value=0.01, step=10.0)
            valor_total = valor_parcela 
            st.info("Serão gerados 12 agendamentos automáticos para o ano.", icon=":material/info:")
            
        else:
            valor_total = st.number_input("Valor (R$)", min_value=0.0, step=1.0)
            valor_parcela = valor_total
            
    else:
        modalidade = st.radio("Modalidade:", ["Único", "Fixo Mensal (12 meses)"], horizontal=True)
        if modalidade == "Fixo Mensal (12 meses)":
            is_fixa, qtd_parcelas = True, 12
            valor_total = st.number_input("Valor Mensal (R$)", min_value=0.01, step=10.0)
            valor_parcela = valor_total
            st.info("Serão gerados 12 agendamentos automáticos.", icon=":material/info:")
        else:
            valor_total = st.number_input("Valor (R$)", min_value=0.0, step=1.0)
            valor_parcela = valor_total


# Form logic...
    # (Maintain the radio buttons logic for 'Parcelada', 'Fixa' as it was)
    if st.button("Adicionar Lançamento", use_container_width=True, type="primary"):
        sucesso, msg = registrar_novo_lancamento(tipo, forma_pagamento, categoria, data_lancamento, is_credito, is_parcelado, is_fixa, qtd_parcelas, valor_total, valor_parcela, df, df_contas, st.session_state.user_id)
        if sucesso:
            st.sidebar.success(msg, icon=":material/check_circle:")
            st.rerun()
        else: 
            st.sidebar.error(msg, icon=":material/error:")

st.sidebar.divider()

# Date Filters & Logout Header
with st.container(border=True):
    col_titulo, col_btn_sair = st.columns([8, 2]) 
    with col_titulo:
        st.markdown(f"<h5 style='color: #f8fafc; margin-bottom: 10px; margin-top: 5px; display: flex; align-items: center; gap: 8px;'>{ic_calendar} Filtro por Período</h5>", unsafe_allow_html=True)
    with col_btn_sair:
        if st.button("Sair do Sistema", use_container_width=True, type="primary"):
            logout_usuario()
            st.session_state.user_id = None
            st.session_state.show_register = False
            st.rerun()

    hoje = datetime.today().date()
    primeiro_dia_mes = hoje.replace(day=1)
    ultimo_dia_mes = hoje.replace(day=calendar.monthrange(hoje.year, hoje.month)[1])

    atalho_selecionado = st.selectbox("Selecione o período:", ["Mês Atual", "Últimos 30 dias", "Últimos 6 meses", "Este Ano", "Período Livre (Calendário)"], label_visibility="collapsed")
        
    if atalho_selecionado == "Mês Atual": 
        data_inicio, data_fim = primeiro_dia_mes, ultimo_dia_mes
    elif atalho_selecionado == "Últimos 30 dias": 
        data_inicio, data_fim = (hoje - timedelta(days=30)), hoje
    elif atalho_selecionado == "Últimos 6 meses": 
        data_inicio, data_fim = (hoje - timedelta(days=180)), hoje
    elif atalho_selecionado == "Este Ano": 
        data_inicio, data_fim = hoje.replace(month=1, day=1), hoje.replace(month=12, day=31)
    else:
        datas_selecionadas = st.date_input("Escolha a data:", value=(primeiro_dia_mes, ultimo_dia_mes), format="DD/MM/YYYY")
        if isinstance(datas_selecionadas, tuple) and len(datas_selecionadas) == 2: data_inicio, data_fim = datas_selecionadas
        elif isinstance(datas_selecionadas, tuple) and len(datas_selecionadas) == 1: data_inicio = data_fim = datas_selecionadas[0]
        else: data_inicio = data_fim = datas_selecionadas

texto_metrica = f"{data_inicio.strftime('%d/%m/%Y')} até {data_fim.strftime('%d/%m/%Y')}"

# Dashboard Core
if not df.empty:
    # Data preprocessing
    df_filtrado = df[(df['Data'].dt.date >= data_inicio) & (df['Data'].dt.date <= data_fim)]
else:
    df_filtrado = df.copy()

# Smart Alerts Processing
alertas = verificar_alertas_vencimento(df, df_contas)
if alertas:
    for alerta in alertas:
        if alerta['tipo'] == 'error': st.error(alerta['mensagem'], icon=alerta['icone'])
        else: st.warning(alerta['mensagem'], icon=alerta['icone'])
    st.markdown("<br>", unsafe_allow_html=True)

# Key Metrics (Matemática segura contra df vazio)
if not df_filtrado.empty:
    df_realizado = df_filtrado[df_filtrado['Status'] == 'Realizado']
    entradas_gerais = df_realizado[df_realizado['Tipo'] == 'Receita (Salário/Entrada)']['Valor'].sum()
    saidas_dinheiro = df_realizado[df_realizado['Tipo'] == 'Despesa (Gasto)']['Valor'].sum()
    faturas_pagas = df_realizado[df_realizado['Tipo'] == 'Pagamento de Fatura']['Valor'].sum()
    caixinha_real = (df_realizado[df_realizado['Tipo'] == 'Reserva (Caixinha)']['Valor'].sum() - 
                     df_realizado[df_realizado['Tipo'] == 'Resgate da Caixinha']['Valor'].sum())
else:
    entradas_gerais = saidas_dinheiro = faturas_pagas = caixinha_real = 0.0

saldo_real = entradas_gerais - saidas_dinheiro - faturas_pagas - caixinha_real

#illustration of balances
with st.container(border=True):
    st.markdown(f"<h4 style='color: #cbd5e1; margin-bottom: 20px; display: flex; align-items: center; gap: 8px;'>{ic_money} Dinheiro na Conta (Saldo Geral): {texto_metrica}</h4>", unsafe_allow_html=True)
    html_cards = f"""
    <div class="card-container">
        <div class="metric-card card-receita"><span class="card-title" style="display: flex; align-items: center; gap: 6px;">Receitas / Salário {ic_up}</span><span class="card-value">{formata_moeda(entradas_gerais)}</span></div>
        <div class="metric-card card-gasto"><span class="card-title" style="display: flex; align-items: center; gap: 6px;">Gastos em Dinheiro/Pix {ic_down}</span><span class="card-value">{formata_moeda(saidas_dinheiro + faturas_pagas)}</span></div>
        <div class="metric-card card-saldo"><span class="card-title" style="display: flex; align-items: center; gap: 6px;">Saldo Disponível (Livre) {ic_wallet}</span><span class="card-value">{formata_moeda(saldo_real)}</span></div>
        <div class="metric-card card-caixinha"><span class="card-title" style="display: flex; align-items: center; gap: 6px;">Na Caixinha {ic_safe}</span><span class="card-value">{formata_moeda(caixinha_real)}</span></div>
    </div>
    """
    st.markdown(html_cards, unsafe_allow_html=True)

    st.markdown("<hr style='border-color: #334155; margin-top: 5px; margin-bottom: 15px;'>", unsafe_allow_html=True)
    st.markdown(f"<h5 style='color: #94a3b8; margin-bottom: 15px; display: flex; align-items: center; gap: 8px;'>{ic_card} Meus Cartões (Limites)</h5>", unsafe_allow_html=True)
    
    if not df_contas.empty:
        html_bancos = '<div style="display: flex; gap: 20px; flex-wrap: wrap; padding-bottom: 10px; justify-content: flex-start;">'
        for index, row_conta in df_contas.iterrows():
            conta_nome = row_conta['nome']
            limite_total = float(row_conta['limite'])
            dia_f = int(row_conta.get('dia_fechamento', 30))
            dia_v = int(row_conta.get('dia_vencimento', 7))
            
            gastos_totais = 0.0
            pagamentos_cartao = 0.0
            if not df.empty:
                gastos_cartao = df[(df['Conta'] == conta_nome) & (df['Tipo'] == 'Despesa (Gasto)') & (df['Status'] == 'Agendado')]
                hoje_date = datetime.today().date()
                gastos_validos = gastos_cartao[~((gastos_cartao['Parcela'] == 'Mensal (Fixa)') & (gastos_cartao['Data'].dt.date > hoje_date))]
                gastos_totais = gastos_validos['Valor'].sum()
                pagamentos_cartao = df[(df['Conta'] == conta_nome) & (df['Tipo'] == 'Pagamento de Fatura')]['Valor'].sum()
                
            limite_disponivel = limite_total - gastos_totais + pagamentos_cartao
            
            nome_lower = str(conta_nome).lower()
            cor_texto = "white"
            dominio_banco = ""
            
            if "nubank" in nome_lower: bg_gradiente, dominio_banco = "linear-gradient(135deg, #8A05BE, #530082)", "nubank.com.br"
            elif "inter" in nome_lower: bg_gradiente, dominio_banco = "linear-gradient(135deg, #FF7A00, #CC5200)", "bancointer.com.br"
            elif "itaú" in nome_lower or "itau" in nome_lower: bg_gradiente, dominio_banco = "linear-gradient(135deg, #EC7000, #B35500)", "itau.com.br"
            elif "iti" in nome_lower: bg_gradiente, dominio_banco = "linear-gradient(135deg, #EC008C, #F05A28)", "iti.itau"
            elif "bradesco" in nome_lower: bg_gradiente, dominio_banco = "linear-gradient(135deg, #CC092F, #8A001A)", "bradesco.com.br"
            elif "santander" in nome_lower: bg_gradiente, dominio_banco = "linear-gradient(135deg, #EC0000, #AA0000)", "santander.com.br"
            elif "caixa" in nome_lower: bg_gradiente, dominio_banco = "linear-gradient(135deg, #005CA9, #003666)", "caixa.gov.br"
            elif "brasil" in nome_lower or "bb" in nome_lower: bg_gradiente, cor_texto, dominio_banco = "linear-gradient(135deg, #FCEB00, #C2B500)", "#0f172a", "bb.com.br"
            elif "c6" in nome_lower: bg_gradiente, dominio_banco = "linear-gradient(135deg, #242424, #000000)", "c6bank.com.br"
            elif "xp" in nome_lower: bg_gradiente, dominio_banco = "linear-gradient(135deg, #000000, #1f1f1f)", "xpi.com.br"
            elif "picpay" in nome_lower: bg_gradiente, dominio_banco = "linear-gradient(135deg, #11C76F, #0E9F59)", "picpay.com"
            elif "mercado pago" in nome_lower or "mercadopago" in nome_lower: bg_gradiente, dominio_banco = "linear-gradient(135deg, #009EE3, #007EB5)", "mercadopago.com.br"
            elif "btg" in nome_lower: bg_gradiente, dominio_banco = "linear-gradient(135deg, #002A54, #00152A)", "btgpactual.com"
            elif "neon" in nome_lower: bg_gradiente, cor_texto, dominio_banco = "linear-gradient(135deg, #00E4C0, #00B396)", "#0f172a", "neon.com.br"
            elif "next" in nome_lower: bg_gradiente, cor_texto, dominio_banco = "linear-gradient(135deg, #00FF5F, #00CC4C)", "#0f172a", "next.me"
            elif "pan" in nome_lower: bg_gradiente, dominio_banco = "linear-gradient(135deg, #0094D9, #0073A8)", "bancopan.com.br"
            elif "porto" in nome_lower: bg_gradiente, dominio_banco = "linear-gradient(135deg, #004691, #002D5E)", "portoseguro.com.br"
            elif "pagbank" in nome_lower or "pagseguro" in nome_lower: bg_gradiente, cor_texto, dominio_banco = "linear-gradient(135deg, #F1D302, #C2A800)", "#0f172a", "pagbank.com.br"
            elif "sicredi" in nome_lower: bg_gradiente, dominio_banco = "linear-gradient(135deg, #006341, #00402A)", "sicredi.com.br"
            elif "sicoob" in nome_lower: bg_gradiente, dominio_banco = "linear-gradient(135deg, #003641, #002027)", "sicoob.com.br"
            elif "will" in nome_lower: bg_gradiente, cor_texto, dominio_banco = "linear-gradient(135deg, #FFD900, #CCAD00)", "#0f172a", "willbank.com.br"
            elif "bv" in nome_lower or "votorantim" in nome_lower: bg_gradiente, dominio_banco = "linear-gradient(135deg, #005CA9, #003B6D)", "bv.com.br"
            elif "ame" in nome_lower: bg_gradiente, dominio_banco = "linear-gradient(135deg, #E31A6B, #B30D4E)", "amedigital.com"
            elif "banrisul" in nome_lower: bg_gradiente, dominio_banco = "linear-gradient(135deg, #00579D, #003865)", "banrisul.com.br"
            elif "original" in nome_lower: bg_gradiente, dominio_banco = "linear-gradient(135deg, #00B634, #008225)", "original.com.br"
            elif "bs2" in nome_lower: bg_gradiente, dominio_banco = "linear-gradient(135deg, #111111, #001E62)", "bancobs2.com.br"
            elif "black" in nome_lower: bg_gradiente, dominio_banco = "linear-gradient(135deg, #18181b, #000000)", ""
            else: bg_gradiente, dominio_banco = "linear-gradient(135deg, #475569, #1e293b)", ""

            if dominio_banco:
                url_logo = f"https://www.google.com/s2/favicons?sz=64&domain={dominio_banco}"
                icone_html = f'<img src="{url_logo}" style="height: 32px; width: 32px; background-color: white; padding: 4px; border-radius: 50%; box-shadow: 0 4px 8px rgba(0,0,0,0.3); object-fit: contain;">'
            else:
                icone_html = '<div style="background: linear-gradient(135deg, #18181b, #000000); height: 32px; width: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 8px rgba(0,0,0,0.5); border: 1px solid #fbbf24; flex-shrink: 0;"><svg width="18" height="18" viewBox="0 0 512 512" fill="#fbbf24" xmlns="http://www.w3.org/2000/svg"><path d="M255.9 14.8l-26.6 42.1-47.5-16.1 1.7 49.9-49 8.9 17.6 46.8-43.2 24.5 32 38.3-33.6 37 42.4 25.8-19.9 46.1 48.3 12.5-2.7 49.8 48.7-10.6 15 47.6 42.2-26.7 26.6 42.1 26.6-42.1 42.2 26.7 15-47.6 48.7 10.6-2.7-49.8 48.3-12.5-19.9-46.1 42.4-25.8-33.6-37 32-38.3-43.2-24.5 17.6-46.8-49-8.9 1.7-49.9-47.5 16.1-26.6-42.1zM256 112c35.3 0 64 28.7 64 64 0 22-11.1 41.4-28 52.4v97.4c0 10.1-5.6 19.4-14.6 24.2l-21.4 11.4-21.4-11.4c-9-4.8-14.6-14.1-14.6-24.2v-97.4c-16.9-11-28-30.4-28-52.4 0-35.3 28.7-64 64-64z"/></svg></div>'

            percentual_gasto_num = ((limite_total - limite_disponivel) / limite_total) * 100 if limite_total > 0 else 0.0
            largura_barra = min(max(percentual_gasto_num, 0.0), 100.0)
            cor_barra = "#ff4b4b" if percentual_gasto_num >= 80 else "#facc15" if percentual_gasto_num >= 60 else "white"
            
            barra_html = f'<div style="width: 100%; background-color: rgba(255, 255, 255, 0.3); border-radius: 4px; height: 6px; margin-top: 6px; margin-bottom: 6px; overflow: hidden;"><div style="width: {largura_barra}%; background-color: {cor_barra}; height: 100%; border-radius: 4px; transition: width 0.5s ease-in-out;"></div></div>'

            cartao_html = f"""
            <div class="credit-card" style="background: {bg_gradiente}; color: {cor_texto};">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        {icone_html}
                        <span style="font-size: 18px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;">{conta_nome}</span>
                    </div>
                    <span style="font-size: 14px; opacity: 0.9; font-weight: 600;">Total: {formata_moeda(limite_total)}</span>
                </div>
                <div>
                    <div style="font-size: 13px; opacity: 0.8; margin-bottom: 2px; text-transform: uppercase; letter-spacing: 0.5px;">Limite Disponível</div>
                    <div style="font-size: 28px; font-weight: bold; margin-bottom: 2px;">{formata_moeda(limite_disponivel)}</div>
                    {barra_html}
                    <div style="font-size: 11px; opacity: 0.6; text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px; margin-top: 4px;">Vence dia {dia_v:02d} • Fecha dia {dia_f:02d}</div>
                </div>
            </div>"""
            html_bancos += cartao_html
        html_bancos += "</div>"
        st.markdown(html_bancos, unsafe_allow_html=True)
    else: 
        st.info("Nenhum cartão cadastrado. Use o menu lateral para adicionar o primeiro.", icon=":material/info:")

    st.markdown("<br>", unsafe_allow_html=True)
    if not df_contas.empty:
        with st.expander("Fechar Fatura (Pagar todos os agendamentos do período selecionado)", icon=":material/credit_card:"):
            col_sel, col_info, col_btn = st.columns([2, 2.5, 1.5])
            with col_sel:
                cartao_fatura = st.selectbox("Selecione o Cartão:", df_contas['nome'].tolist(), key="fatura_cartao", label_visibility="collapsed")
            
            valor_fatura = 0.0
            if not df_filtrado.empty:
                df_fatura = df_filtrado[(df_filtrado['Conta'] == cartao_fatura) & (df_filtrado['Tipo'] == 'Despesa (Gasto)') & (df_filtrado['Status'] == 'Agendado')]
                valor_fatura = df_fatura['Valor'].sum()
                
            str_fatura_tela = f" R\$ {valor_fatura:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            
            with col_info:
                st.markdown(f"<div style='padding-top: 5px; color: #cbd5e1; font-size: 15px;'>Total pendente no mês: <b style='color: #facc15; font-size: 16px;'>{str_fatura_tela}</b></div>", unsafe_allow_html=True)
                
            with col_btn:
                if st.button("Pagar Fatura Completa", type="primary", use_container_width=True, disabled=(valor_fatura == 0)):
                    sucesso, msg = fechar_fatura_cartao_controller(cartao_fatura, df_filtrado, saldo_real)
                    if sucesso:
                        st.toast(msg, icon=":material/check_circle:")
                        st.rerun()
                    else:
                        st.toast(msg, icon=":material/error:")

st.markdown("<br>", unsafe_allow_html=True)

# Historical & Distribution Charts
col_barras, col_pizza = st.columns([1.2, 1]) 
with col_barras:
    with st.container(border=True):
        st.markdown(f"<h4 style='color: #cbd5e1; display: flex; align-items: center; gap: 8px;'>{ic_bar} Evolução Histórica</h4>", unsafe_allow_html=True)
        
        if not df_filtrado.empty:
            df_grafico_puro = df_filtrado[df_filtrado['Tipo'].isin(['Receita (Salário/Entrada)', 'Despesa (Gasto)'])]
            df_grafico = df_grafico_puro.groupby(['Mês', 'Tipo'])['Valor'].sum().reset_index()
            paleta_cores = {'Receita (Salário/Entrada)': '#10b981', 'Despesa (Gasto)': '#f43f5e'}
            
            if not df_grafico.empty:
                fig = px.bar(df_grafico, x='Mês', y='Valor', color='Tipo', barmode='group', color_discrete_map=paleta_cores)
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#94a3b8', size=13),
                    legend=dict(title="", orientation="h", y=-0.2, x=0.5, xanchor="center"), margin=dict(l=10, r=10, t=20, b=10),
                    yaxis=dict(title="", showgrid=True, gridcolor='rgba(51, 65, 85, 0.4)', zeroline=False, tickprefix="R$ "),
                    xaxis=dict(title="", showgrid=False), hovermode="x unified", 
                    hoverlabel=dict(bgcolor="rgba(15, 23, 42, 0.95)", bordercolor="#334155", font=dict(color="white", size=14))
                )
                fig.update_traces(marker_line_width=0)
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            else: 
                st.info("Nenhum dado financeiro no período para gerar o gráfico.", icon=":material/info:")
        else:
            st.info("Aguardando lançamentos para gerar o gráfico de evolução.", icon=":material/info:")

with col_pizza:
    with st.container(border=True):
        st.markdown(f"<h4 style='color: #cbd5e1; display: flex; align-items: center; gap: 8px;'>{ic_pie} Despesas por Categoria</h4>", unsafe_allow_html=True)
        
        if not df_filtrado.empty:
            df_despesas = df_filtrado[df_filtrado['Tipo'] == 'Despesa (Gasto)']
            if not df_despesas.empty:
                dados_pizza = df_despesas.groupby('Categoria')['Valor'].sum().reset_index()
                fig_pizza = px.pie(dados_pizza, values='Valor', names='Categoria', hole=0.7, color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_pizza.update_traces(
                    textposition='inside', textinfo='percent', hovertemplate="<b>%{label}</b><br>R$ %{value:,.2f}<extra></extra>",
                    marker=dict(line=dict(color='#0f172a', width=4)), pull=[0.02] * len(dados_pizza) 
                )
                fig_pizza.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#94a3b8', size=14),
                    margin=dict(l=10, r=10, t=10, b=10), showlegend=False,
                    hoverlabel=dict(bgcolor="rgba(15, 23, 42, 0.95)", bordercolor="#334155", font=dict(color="white", size=14)),
                    annotations=[dict(text="Despesas", x=0.5, y=0.5, font_size=16, font_color="#cbd5e1", showarrow=False)]
                )
                st.plotly_chart(fig_pizza, use_container_width=True, config={'displayModeBar': False})
            else: 
                st.info("Nenhuma despesa registrada neste período.", icon=":material/info:")
        else:
            st.info("Aguardando lançamentos para exibir o gráfico de categorias.", icon=":material/info:")

st.markdown("<br>", unsafe_allow_html=True)

@st.dialog("Editar Lançamento")
def modal_editar_lancamento(id_lancamento, categoria_atual, valor_atual):
    st.markdown(f"Editando: **{categoria_atual}**")
    nova_categoria = st.text_input("Nova Descrição", value=categoria_atual)
    novo_valor = st.number_input("Novo Valor (R$)", value=float(valor_atual), min_value=0.01, step=10.0)
    if st.button("Salvar Alterações", type="primary", use_container_width=True):
        sucesso, msg = editar_lancamento_controller(id_lancamento, nova_categoria, novo_valor)
        if sucesso: st.rerun()
        else: st.error(msg, icon=":material/error:")

with st.container(border=True):
    col_titulo_hist, col_btn_csv, col_btn_pdf = st.columns([5, 2.5, 2.5])
    with col_titulo_hist:
        st.markdown(f"<h4 style='color: #cbd5e1; margin-top: 5px; display: flex; align-items: center; gap: 8px;'>{ic_list} Movimentações Recentes</h4>", unsafe_allow_html=True)
    
    if not df_filtrado.empty:
        df_agendados = df[df['Status'] == 'Agendado']
        df_exibicao = pd.concat([df_filtrado, df_agendados]).drop_duplicates(subset=['id']).sort_values(by='Data', ascending=False)
        df_para_exportar = df_exibicao[['Data', 'Categoria', 'Conta', 'Tipo', 'Valor', 'Status', 'Parcela']]
        
        with col_btn_csv:
            csv_data = gerar_relatorio_csv(df_para_exportar)
            st.download_button(label="Baixar CSV / Excel", data=csv_data, file_name=f"Relatorio_{datetime.today().strftime('%d_%m_%Y')}.csv", mime="text/csv", use_container_width=True, icon=":material/download:")
            
        with col_btn_pdf:
            pdf_data = gerar_relatorio_pdf(df_para_exportar)
            st.download_button(label="Baixar PDF", data=pdf_data, file_name=f"Relatorio_{datetime.today().strftime('%d_%m_%Y')}.pdf", mime="application/pdf", use_container_width=True, icon=":material/picture_as_pdf:")
    else:
        df_exibicao = pd.DataFrame()
    
    col1, col2, col3, col4, col5 = st.columns([1.5, 3, 2, 1.5, 1.5])
    col1.markdown("<span style='color: #94a3b8; font-size: 14px; font-weight: 600;'>DATA</span>", unsafe_allow_html=True)
    col2.markdown("<span style='color: #94a3b8; font-size: 14px; font-weight: 600;'>DESCRIÇÃO / CONTA</span>", unsafe_allow_html=True)
    col3.markdown("<span style='color: #94a3b8; font-size: 14px; font-weight: 600;'>VALOR</span>", unsafe_allow_html=True)
    col4.markdown("<span style='color: #94a3b8; font-size: 14px; font-weight: 600;'>STATUS</span>", unsafe_allow_html=True)
    col5.markdown("<span style='color: #94a3b8; font-size: 14px; font-weight: 600; text-align: right;'>AÇÕES</span>", unsafe_allow_html=True)
    
    st.markdown("<hr style='border-color: #334155; margin: 5px 0 10px 0;'>", unsafe_allow_html=True)

    if df_exibicao.empty:
        st.markdown("<div style='text-align: center; color: #64748b; padding: 30px; font-size: 16px;'>Ainda não há lançamentos para este período. Comece adicionando no menu lateral!</div>", unsafe_allow_html=True)
    else:
        for index, row in df_exibicao.iterrows():
            with st.container():
                c1, c2, c3, c4, c5 = st.columns([1.5, 3, 2, 1.5, 1.5])
                
                str_data = row['Data'].strftime('%d/%m/%Y')
                try: data_entrada = pd.to_datetime(row['created_at']).strftime('%d/%m/%Y')
                except: data_entrada = ""

                if row['Status'] == 'Agendado':
                    info_parcela = row['Parcela'] if pd.notna(row['Parcela']) and str(row['Parcela']).strip() != "" else 'Agendado'
                    texto_data = f"<div style='display: flex; align-items: center; gap: 5px; color: #facc15;'><svg width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><circle cx='12' cy='12' r='10'></circle><polyline points='12 6 12 12 16 14'></polyline></svg> {str_data}</div><span style='font-size: 11.5px; color: #64748b;'>{info_parcela} • Lançado em {data_entrada}</span>"
                else:
                    texto_data = f"{str_data}<br><span style='font-size: 12px; color: #64748b;'>{row['Parcela']}</span>" if pd.notna(row['Parcela']) else str_data
                c1.markdown(f"<span style='color: #cbd5e1;'>{texto_data}</span>", unsafe_allow_html=True)
                
                cor_icone = "#10b981" if row['Tipo'] == "Receita (Salário/Entrada)" else "#f43f5e"
                seta = "↓" if row['Tipo'] == "Despesa (Gasto)" else "↑" if row['Tipo'] == "Receita (Salário/Entrada)" else "→"
                c2.markdown(f"<div style='display: flex; align-items: center; gap: 8px;'><span style='color: {cor_icone}; font-weight: bold;'>{seta}</span> <span style='color: #f8fafc; font-weight: 500;'>{row['Categoria']}</span> <span style='font-size: 12px; color: #64748b;'>({row['Conta']})</span></div>", unsafe_allow_html=True)
                
                cor_valor = cor_icone
                c3.markdown(f"<span style='color: {cor_valor}; font-weight: bold;'>{formata_moeda(row['Valor'])}</span>", unsafe_allow_html=True)
                
                bg_status = "#1e293b" if row['Status'] == 'Agendado' else "rgba(16, 185, 129, 0.1)"
                color_status = "#94a3b8" if row['Status'] == 'Agendado' else "#10b981"
                border_status = "#334155" if row['Status'] == 'Agendado' else "rgba(16, 185, 129, 0.2)"
                c4.markdown(f"<div style='background-color: {bg_status}; border: 1px solid {border_status}; color: {color_status}; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; display: inline-block; text-align: center;'>{row['Status']}</div>", unsafe_allow_html=True)
                
                with c5:
                    col_edit, col_pay, col_del = st.columns(3)
                    with col_edit:
                        if st.button("", icon=":material/edit:", key=f"edit_{row['id']}", help="Editar Valor/Categoria"):
                            modal_editar_lancamento(row['id'], row['Categoria'], row['Valor'])
                            
                    with col_pay:
                        if row['Status'] == 'Agendado':
                            if st.button("", icon=":material/check_circle:", key=f"pay_{row['id']}", help="Pagar hoje (Desconta do Saldo)"):
                                sucesso, msg = pagar_lancamento(
                                    id_lancamento=int(row['id']),
                                    valor_da_conta=float(row['Valor']),
                                    saldo_disponivel_real=saldo_real,
                                    data_original=row['Data'],
                                    texto_parcela_original=row['Parcela']
                                )
                                if sucesso:
                                    st.toast(msg, icon=":material/check_circle:")
                                    st.rerun()
                                else:
                                    st.toast(msg, icon=":material/error:")
                        else: st.write("")
                        
                    with col_del:
                        if st.button("", icon=":material/delete:", type="primary", key=f"del_{row['id']}", help="Excluir lançamento"):
                            sucesso, msg = excluir_lancamento(int(row['id']))
                            if sucesso: st.rerun()
                            else: st.toast(msg, icon=":material/error:")
                
                st.markdown("<hr style='border-color: rgba(51, 65, 85, 0.5); margin: 0;'>", unsafe_allow_html=True)


st.markdown("""
    <div style="text-align: center; margin-top: 50px; padding-top: 20px; border-top: 1px solid rgba(51, 65, 85, 0.4); color: #64748b; font-size: 13px; font-family: sans-serif; padding-bottom: 20px;">
        Desenvolvido por <a href="https://github.com/DevJonathanSantana" target="_blank" style="color: #2dd4bf; text-decoration: none; font-weight: 600;">Jonathan Santana</a><br>
        &copy; 2026 FinOps Personal. Todos os direitos reservados.
    </div>
""", unsafe_allow_html=True)