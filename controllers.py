import pandas as pd
import calendar
from datetime import datetime
from datetime import datetime, timedelta
from database import inserir_lancamentos
from database import atualizar_lancamento, deletar_lancamento
from database import fazer_logout_db, inserir_conta_db, atualizar_conta_db, deletar_conta_db
from database import pagar_fatura_lote_db

def registrar_novo_lancamento(tipo, forma_pagamento, categoria, data_lancamento, is_credito, is_parcelado, is_fixa, qtd_parcelas, valor_total, valor_parcela, df, df_contas, user_id):
    """Processes new transactions, validates business rules (savings/credit/balance limits), and prepares batch inserts."""
    if not categoria.strip(): return False, "Digite a Categoria."
    if valor_total <= 0: return False, "O valor deve ser maior que zero."

    # PRE-PROCESSING: Calculates current balances
    if df.empty:
        caixinha_atual = 0
        saldo_atual = 0
    else:
        df_realizado = df[df['Status'] == 'Realizado']
        caixinha_atual = (df_realizado[df_realizado['Tipo'] == 'Reserva (Caixinha)']['Valor'].sum() - 
                        df_realizado[df_realizado['Tipo'] == 'Resgate da Caixinha']['Valor'].sum())
        entradas = df_realizado[df_realizado['Tipo'] == 'Receita (Salário/Entrada)']['Valor'].sum()
        saidas = df_realizado[df_realizado['Tipo'] == 'Despesa (Gasto)']['Valor'].sum()
        faturas = df_realizado[df_realizado['Tipo'] == 'Pagamento de Fatura']['Valor'].sum()
        saldo_atual = entradas - saidas - faturas - caixinha_atual

    # Business Rule: Savings protection (Prevents negative balance and credit card usage)
    if tipo == "Reserva (Caixinha)":
        if is_credito: return False, "Ação Negada: Não é possível guardar dinheiro usando Cartão de Crédito."
        consumo_imediato = valor_parcela if is_fixa else valor_total
        if consumo_imediato > saldo_atual:
            return False, f"Saldo Insuficiente! Disponível: R$ {saldo_atual:,.2f}."

    # Business Rule: Savings withdrawal validation
    elif tipo == "Resgate da Caixinha":
        if is_credito: return False, "Ação Negada: Resgates devem ir para o Saldo Geral."
        consumo_imediato = valor_parcela if is_fixa else valor_total
        if consumo_imediato > caixinha_atual:
            return False, f"Saldo de Caixinha Insuficiente! Guardado: R$ {caixinha_atual:,.2f}."

    id_da_conta = None

    # Business Rule: Expenses validation (Credit Card vs General Balance)
    if tipo == "Despesa (Gasto)":
        consumo_imediato = valor_parcela if is_fixa else valor_total
        
        if is_credito:
            conta_selecionada = df_contas[df_contas['nome'] == forma_pagamento].iloc[0]
            limite_total = float(conta_selecionada['limite'])
            id_da_conta = int(conta_selecionada['id'])
            
            gastos_totais = 0
            if not df.empty:
                gastos_cartao = df[(df['conta_id'] == id_da_conta) & (df['Tipo'] == 'Despesa (Gasto)') & (df['Status'] == 'Agendado')].copy()
                if not gastos_cartao.empty:
                    hoje_date = datetime.today().date()
                    gastos_validos = gastos_cartao[~((gastos_cartao['Parcela'] == 'Mensal (Fixa)') & (gastos_cartao['Data'].dt.date > hoje_date))]
                    gastos_totais = gastos_validos['Valor'].sum()
                
                pagamentos_feitos = df[(df['conta_id'] == id_da_conta) & (df['Tipo'] == 'Pagamento de Fatura')]['Valor'].sum()
            else:
                pagamentos_feitos = 0
                
            limite_disponivel = limite_total - gastos_totais + pagamentos_feitos
            
            if consumo_imediato > limite_disponivel:
                return False, f"Compra Recusada! Limite insuficiente no cartão {forma_pagamento}."
        else:
            # NEW FEATURE: Negative Balance Protection for Cash/Pix
            if consumo_imediato > saldo_atual:
                return False, f"Saldo Insuficiente! Você tentou gastar R\$ {consumo_imediato:,.2f}, mas tem apenas R\$ {saldo_atual:,.2f} disponíveis."
                
    elif not is_credito and forma_pagamento != "Saldo Geral (Dinheiro/Pix)":
        conta_selecionada = df_contas[df_contas['nome'] == forma_pagamento].iloc[0]
        id_da_conta = int(conta_selecionada['id'])

    # Generation of Entries for Insertion into the Database
    lancamentos_para_inserir = []
    for i in range(qtd_parcelas):
        data_parcela = adicionar_meses(data_lancamento, i)
        status_atual = "Agendado" if is_credito or data_parcela.date() > datetime.today().date() else "Realizado"
        texto_parcela = f"{i+1}/{qtd_parcelas}" if is_parcelado else ("Mensal (Fixa)" if is_fixa else None)
        
        dados_insert = {
            "data": data_parcela.strftime('%Y-%m-%d'), "tipo": tipo, "categoria": categoria, 
            "valor": float(valor_parcela), "user_id": user_id,
            "status": status_atual, "parcela": texto_parcela
        }
        if id_da_conta: dados_insert["conta_id"] = id_da_conta
        lancamentos_para_inserir.append(dados_insert)
    
    try:
        inserir_lancamentos(lancamentos_para_inserir)
        return True, "Lançamento salvo com sucesso!"
    except Exception as e:
        return False, f"Database error: {str(e)}"

def adicionar_meses(data_original, meses_para_adicionar):
    """Avança os meses corretamente para gerar as faturas futuras."""
    mes = data_original.month - 1 + meses_para_adicionar
    ano = data_original.year + mes // 12
    mes = mes % 12 + 1
    # Make sure we don't invent a February 31st.
    dia = min(data_original.day, calendar.monthrange(ano, mes)[1])
    return datetime(ano, mes, dia)

def validar_transacao_cartao(df_contas, df_historico_completo, forma_pagamento, valor_tentativa):
    """
    Regra de Negócio: Impede que o usuário gaste mais do que o limite disponível.
    Calcula o limite real e retorna (True/False, limite_disponível).
    """
    # 1. Identify the card and its total limit
    linha_conta = df_contas[df_contas['nome'] == forma_pagamento].iloc[0]
    id_conta = int(linha_conta['id'])
    limite_total = float(linha_conta['limite'])
    
    # 2. Filter all history for this card only
    df_historico_cartao = df_historico_completo[df_historico_completo['conta_id'] == id_conta] if not df_historico_completo.empty else pd.DataFrame()
    
    # 3. Calculate what has already been spent and paid
    if not df_historico_cartao.empty:
        gastos_totais = df_historico_cartao[df_historico_cartao['tipo'] == 'Despesa (Gasto)']['valor'].sum()
        pagamentos_totais = df_historico_cartao[df_historico_cartao['tipo'] == 'Pagamento de Fatura']['valor'].sum()
    else:
        gastos_totais = 0
        pagamentos_totais = 0
        
    limite_real_disponivel = limite_total - gastos_totais + pagamentos_totais
    
    # 4. Validates whether the purchase is allowed
    pode_salvar = valor_tentativa <= limite_real_disponivel
    
    return pode_salvar, limite_real_disponivel



def pagar_lancamento(id_lancamento, valor_da_conta, saldo_disponivel_real, data_original, texto_parcela_original):
    # Business rule: verify that there is sufficient balance
    if valor_da_conta > saldo_disponivel_real:
        str_saldo = f"R\$ {saldo_disponivel_real:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        str_conta = f"R\$ {valor_da_conta:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        mensagem_erro = f" Saldo Insuficiente! Saldo {str_saldo} livres, mas a conta custa {str_conta}."
        return False, mensagem_erro

    # Format the observation of the old date
    data_antiga = data_original.strftime('%d/%m/%Y')
    txt_antigo = str(texto_parcela_original) if pd.notna(texto_parcela_original) and str(texto_parcela_original).strip() != "" else ""
    novo_texto = f"{txt_antigo} (Vencia a {data_antiga})" if txt_antigo else f"Vencia a {data_antiga}"

    dados_update = {
        'status': 'Realizado',
        'data': datetime.today().strftime('%Y-%m-%d'),
        'parcela': novo_texto
    }

    try:
        atualizar_lancamento(id_lancamento, dados_update)
        return True, "Conta paga com sucesso!"
    except Exception as e:
        return False, f"Erro ao atualizar: {str(e)}"

def excluir_lancamento(id_lancamento):
    try:
        deletar_lancamento(id_lancamento)
        return True, "Lançamento excluído com sucesso!"
    except Exception as e:
        return False, f"Erro ao excluir: {str(e)}"

def editar_lancamento_controller(id_lancamento, nova_categoria, novo_valor):
    dados_update = {
        'categoria': nova_categoria,
        'valor': novo_valor
    }
    try:
        atualizar_lancamento(id_lancamento, dados_update)
        return True, "Lançamento editado com sucesso!"
    except Exception as e:
        return False, f"Erro ao editar: {str(e)}"
    
def gerar_relatorio_csv(df_export):
    #Receives the dataframe, formats it to the Brazilian standard, and generates the CSV bytes.
        df_csv = df_export.copy()
        df_csv['Data'] = df_csv['Data'].dt.strftime('%d/%m/%Y')
        df_csv['Valor'] = df_csv['Valor'].apply(lambda x: f"{float(x):.2f}".replace('.', ','))
        
        # encode('utf-8-sig') mantém os acentos funcionando no Excel do Windows
        return df_csv.to_csv(index=False, sep=';').encode('utf-8-sig')


def gerar_relatorio_pdf(df_export):
    #Receives the dataframe, formats it, and draws the PDF file
    from fpdf import FPDF
    import unicodedata
    
    df_pdf = df_export.copy()
    df_pdf['Data'] = df_pdf['Data'].dt.strftime('%d/%m/%Y')
    df_pdf['Valor'] = df_pdf['Valor'].apply(lambda x: f"{float(x):.2f}".replace('.', ','))
    
    def limpar_texto(txt):
        return ''.join(c for c in unicodedata.normalize('NFD', str(txt)) if unicodedata.category(c) != 'Mn')

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Relatorio Financeiro", ln=True, align='C')
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(30, 8, "Data", border=1, align='C')
    pdf.cell(60, 8, "Descricao", border=1)
    pdf.cell(40, 8, "Conta", border=1)
    pdf.cell(30, 8, "Valor (R$)", border=1, align='C')
    pdf.cell(30, 8, "Status", border=1, align='C')
    pdf.ln()
    
    pdf.set_font("Arial", size=9)
    for index, row in df_pdf.iterrows():
        pdf.cell(30, 8, str(row['Data']), border=1, align='C')
        pdf.cell(60, 8, limpar_texto(row['Categoria'])[:30], border=1)
        pdf.cell(40, 8, limpar_texto(row['Conta'])[:20], border=1)
        pdf.cell(30, 8, f"{row['Valor']}", border=1, align='R')
        pdf.cell(30, 8, limpar_texto(row['Status']), border=1, align='C')
        pdf.ln()
        
    return pdf.output(dest='S').encode('latin1')

def logout_usuario():
    try:
        fazer_logout_db()
        return True
    except Exception:
        return False

def adicionar_cartao_controller(nome_conta, limite, fechamento, vencimento, user_id):
    if fechamento is None or vencimento is None:
        return False, "Preencha os dias de fechamento e vencimento."
        
    dados = {
        "nome": nome_conta, 
        "limite": limite,
        "dia_fechamento": int(fechamento), 
        "dia_vencimento": int(vencimento),
        "user_id": user_id
    }
    try:
        inserir_conta_db(dados)
        return True, "Cartão salvo com sucesso!"
    except Exception as e:
        return False, f"Erro ao salvar cartão: {str(e)}"

def atualizar_cartao_controller(id_cartao, novo_limite, novo_fechamento, novo_vencimento):
    dados = {
        "limite": novo_limite, 
        "dia_fechamento": int(novo_fechamento), 
        "dia_vencimento": int(novo_vencimento)
    }
    try:
        atualizar_conta_db(id_cartao, dados)
        return True, "Cartão atualizado!"
    except Exception as e:
        return False, f"Erro ao atualizar: {str(e)}"

def excluir_cartao_controller(id_cartao):
    try:
        deletar_conta_db(id_cartao)
        return True, "Cartão excluído!"
    except Exception as e:
        return False, f"Erro ao excluir: {str(e)}"
    
    
def fechar_fatura_cartao_controller(cartao_nome, df_filtrado, saldo_disponivel_real):
    # Filters the expenses from the selected card that are still ‘Scheduled’ for the month on the screen.
    df_fatura = df_filtrado[(df_filtrado['Conta'] == cartao_nome) & 
                            (df_filtrado['Tipo'] == 'Despesa (Gasto)') & 
                            (df_filtrado['Status'] == 'Agendado')]
                            
    if df_fatura.empty:
        return False, f"Nenhuma despesa pendente para o {cartao_nome} neste período."
        
    # Calculate the total invoice amount
    valor_total = df_fatura['Valor'].sum()
    
    # Security Lock: Insufficient Balance
    if valor_total > saldo_disponivel_real:
        str_saldo = f"R\$ {saldo_disponivel_real:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        str_fatura = f"R\$ {valor_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return False, f"Saldo Insuficiente! A fatura soma {str_fatura} e você tem apenas {str_saldo} livre."
        
    # Take the list with the IDs of all these purchases and send it to the bank.
    lista_ids = df_fatura['id'].tolist()
    
    try:
        pagar_fatura_lote_db(lista_ids)
        str_sucesso = f"R\$ {valor_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return True, f"Fatura do {cartao_nome} ({str_sucesso}) paga com sucesso! Limite liberado."
    except Exception as e:
        return False, f"Erro ao processar fatura: {str(e)}"
    

def verificar_alertas_vencimento(df, df_contas):
    alertas = []
    hoje = datetime.today().date()
    
    agendados = df[df['Status'] == 'Agendado'].copy()
    if agendados.empty:
        return alertas
        
    agendados['Data_Real'] = pd.to_datetime(agendados['Data']).dt.date
    
    atrasadas = agendados[agendados['Data_Real'] < hoje]
    para_hoje = agendados[agendados['Data_Real'] == hoje]
    
    limite_5_dias = hoje + timedelta(days=5)
    proximos_dias = agendados[(agendados['Data_Real'] > hoje) & (agendados['Data_Real'] <= limite_5_dias)]
    
    if not atrasadas.empty:
        valor_total = atrasadas['Valor'].sum()
        str_valor = f"R$ {valor_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        alertas.append({"tipo": "error", "icone": ":rotating_light:", "mensagem": f"Você tem **{len(atrasadas)} conta(s) ATRASADA(S)** (Total: {str_valor})."})
        
    if not para_hoje.empty:
        valor_hoje = para_hoje['Valor'].sum()
        str_valor_hoje = f"R$ {valor_hoje:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        alertas.append({"tipo": "warning", "icone": ":bell:", "mensagem": f"Você tem **{len(para_hoje)} conta(s)** vencendo **HOJE** ({str_valor_hoje})."})
        
    if not proximos_dias.empty:
        valor_prox = proximos_dias['Valor'].sum()
        str_valor_prox = f"R$ {valor_prox:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        alertas.append({"tipo": "warning", "icone": ":calendar:", "mensagem": f"Fique de olho: **{len(proximos_dias)} conta(s)** vencem nos próximos 5 dias ({str_valor_prox})."})

    if not df_contas.empty:
        for _, cartao in df_contas.iterrows():
            dia_venc = cartao.get('dia_vencimento')
            if pd.notna(dia_venc):
                dia_venc = int(dia_venc)
                
                try:
                    data_vencimento_este_mes = hoje.replace(day=dia_venc)
                except ValueError:
                    ultimo_dia = calendar.monthrange(hoje.year, hoje.month)[1]
                    data_vencimento_este_mes = hoje.replace(day=min(dia_venc, ultimo_dia))
                    
                # Filter what is pending on the card BEFORE this month's bill is due.
                gastos_fatura = agendados[(agendados['Conta'] == cartao['nome']) & (agendados['Data_Real'] <= data_vencimento_este_mes)]
                
                if not gastos_fatura.empty:
                    dias_faltantes = (data_vencimento_este_mes - hoje).days
                    valor_fatura = gastos_fatura['Valor'].sum()
                    str_fat = f"R\$ {valor_fatura:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    
                    if dias_faltantes < 0:
                        # The invoice is already past its due date this month and there are still “Scheduled” debits!
                        alertas.append({"tipo": "error", "icone": "material/fire", "mensagem": f"A fatura do **{cartao['nome']}** venceu há **{abs(dias_faltantes)} dia(s)**! (Valor: {str_fat})."})
                    elif 0 <= dias_faltantes <= 5:
                        alertas.append({"tipo": "warning", "icone": "material/credit_card", "mensagem": f"A fatura do **{cartao['nome']}** vence em **{dias_faltantes} dia(s)** (Dia {dia_venc:02d}). Pendente: {str_fat}."})
                        
    return alertas