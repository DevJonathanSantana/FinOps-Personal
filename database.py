import streamlit as st
from supabase import create_client, Client
import pandas as pd
def gerar_pdf(df_para_pdf):
        from fpdf import FPDF
        import unicodedata


# CONNECTION AND AUTHENTICATION
@st.cache_resource
def get_supabase_client() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

# Global instance to be used in other files
supabase = get_supabase_client()

# USER ROLES (SUPABASE AUTH)
def login_user(email, senha):
    try:
        resposta = supabase.auth.sign_in_with_password({"email": email, "password": senha})
        return True, resposta.user
    except Exception as e:
        return False, None

def register_user(email, senha):
    try:
        resposta = supabase.auth.sign_up({"email": email, "password": senha})
        return True, resposta.user
    except Exception as e:
        return False, None


#  READING FUNCTIONS (DATA FETCHING)
def carregar_contas(user_id):
    resposta = supabase.table("contas").select("*").eq("user_id", user_id).execute()
    return pd.DataFrame(resposta.data)

def carregar_financas(user_id):
    resposta = supabase.table("financas").select("*").eq("user_id", user_id).execute()
    return pd.DataFrame(resposta.data)

def inserir_lancamentos(dados_insert):
    return supabase.table("financas").insert(dados_insert).execute()

def atualizar_lancamento(id_lancamento, dados_update):
    return supabase.table('financas').update(dados_update).eq('id', int(id_lancamento)).execute()

def deletar_lancamento(id_lancamento):
    return supabase.table('financas').delete().eq('id', int(id_lancamento)).execute()


# ACCOUNT/CARD AND SESSION MANAGEMENT
def fazer_logout_db():
    return supabase.auth.sign_out()

def inserir_conta_db(dados_conta):
    return supabase.table("contas").insert(dados_conta).execute()

def atualizar_conta_db(id_conta, dados_update):
    return supabase.table("contas").update(dados_update).eq("id", id_conta).execute()

def deletar_conta_db(id_conta):
    return supabase.table("contas").delete().eq("id", id_conta).execute()

def pagar_fatura_lote_db(lista_ids):
    return supabase.table("financas").update({"status": "Realizado"}).in_("id", lista_ids).execute()

def recuperar_senha(email):
    try:
        supabase.auth.reset_password_email(email)
        return True, "E-mail de recuperação enviado! Verifique sua caixa de entrada (e o Spam)."
    except Exception as e:
        return False, f"Erro ao enviar: {str(e)}"
    
def redefinir_senha_com_token(email, token, nova_senha):
    try:
        supabase.auth.verify_otp({"email": email, "token": token, "type": "recovery"})
        
        supabase.auth.update_user({"password": nova_senha})
        
        supabase.auth.sign_out()
        
        return True, "Senha atualizada com sucesso! Faça seu login."
    except Exception as e:
        return False, "Código inválido ou expirado. Solicite um novo."