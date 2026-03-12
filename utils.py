import streamlit as st

CARTOES_PERMITIDOS = [
    "Banco do Brasil", "Banrisul", "Bradesco", "BS2", "BTG", "BV", 
    "C6", "Caixa", "Inter", "Itaú", "Iti", "Mercado Pago", "Neon", "Next", "Nubank", 
    "Original", "PagBank", "Pan", "PicPay", "Porto Seguro", "Santander", "Sicoob", 
    "Sicredi", "Will Bank", "XP", "Black (Genérico)"
]

def formata_moeda(valor): 
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def injetar_css_global():
    # CSS para forçar o conteúdo central a preencher toda a largura e adicionar micro-interações
    st.markdown("""
    <style>
        /* Expands the central content and removes standard margins */
        .block-container { padding: 2rem 1rem !important; max-width: 100% !important; margin: 0 !important; }
        .element-container { padding-left: 0 !important; padding-right: 0 !important; }
        
        /* Global Text Styles */
        p, label, input, select, div[data-baseweb="select"] { font-size: 16px !important; }
        button[data-baseweb="tab"] * { font-size: 18px !important; font-weight: 600 !important; }
        
        /* =========================================
                METRIC CARD ANIMATIONS
           ========================================= */
        .card-container { display: flex; gap: 15px; justify-content: space-between; margin-bottom: 20px; flex-wrap: wrap; }
        .metric-card { 
            flex: 1; min-width: 200px; padding: 20px; border-radius: 12px; display: flex; flex-direction: column; justify-content: center; 
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); 
            cursor: default;
        }
        .metric-card:hover { 
            transform: translateY(-8px) scale(1.02); 
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.4); 
            filter: brightness(1.1); 
        }
        
        .card-title { font-size: 16px; font-weight: 600; margin-bottom: 8px; opacity: 0.8; }
        .card-value { font-size: 30px; font-weight: 800; }
        
        .card-receita { background-color: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.2); color: #10b981; }
        .card-gasto { background-color: rgba(244, 63, 94, 0.1); border: 1px solid rgba(244, 63, 94, 0.2); color: #f43f5e; }
        .card-saldo { background-color: rgba(14, 165, 233, 0.1); border: 1px solid rgba(14, 165, 233, 0.2); color: #0ea5e9; }
        .card-caixinha { background-color: rgba(168, 85, 247, 0.1); border: 1px solid rgba(168, 85, 247, 0.2); color: #a855f7; }
        
        /* =========================================
                CREDIT CARD ANIMATIONS
           ========================================= */
        .credit-card { 
            width: 300px; height: 185px; border-radius: 14px; padding: 22px; color: white; display: flex; flex-direction: column; justify-content: space-between; 
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.4); font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; flex-shrink: 0; 
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            cursor: pointer;
        }
        .credit-card:hover { 
            transform: translateY(-12px) scale(1.03); 
            box-shadow: 0 25px 30px -5px rgba(0, 0, 0, 0.7); 
            z-index: 10; 
        }
        
        /* =========================================
                GRAPH AND TABLE ANIMATIONS
           ========================================= */
        [data-testid="stPlotlyChart"], 
        [data-testid="stDataFrame"],
        div[data-testid="stVerticalBlockBorderWrapper"] {
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            border-radius: 12px !important;
        }
        
        /* Hover Effect: Charts and Tables float and gain shadow */
        [data-testid="stPlotlyChart"]:hover, 
        [data-testid="stDataFrame"]:hover,
        div[data-testid="stVerticalBlockBorderWrapper"]:hover {
            transform: translateY(-6px) !important;
            box-shadow: 0 15px 30px -5px rgba(0, 0, 0, 0.5) !important;
            border-color: #0ea5e9 !important;
        }
        
        /* Table Styles */
        [data-testid="stDataFrame"] { font-size: 16px !important; }
        
        /* Login/Register Form Styles */
        .login-box { padding: 30px; border-radius: 16px; background-color: rgba(31, 41, 55, 0.8); border: 1px solid rgba(55, 65, 81, 0.5); box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.4); }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
#    SVG ICON DICTIONARY 
ic_card = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="1" y="4" width="22" height="16" rx="2" ry="2"></rect><line x1="1" y1="10" x2="23" y2="10"></line></svg>'
ic_add = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>'
ic_trash = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>'
ic_calendar = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>'
ic_money = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="1" x2="12" y2="23"></line><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>'
ic_bar = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>'
ic_pie = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.21 15.89A10 10 0 1 1 8 2.83"></path><path d="M22 12A10 10 0 0 0 12 2v10z"></path></svg>'
ic_list = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line></svg>'
ic_up = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="7" y1="17" x2="17" y2="7"></line><polyline points="7 7 17 7 17 17"></polyline></svg>'
ic_down = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="7" y1="7" x2="17" y2="17"></line><polyline points="17 7 17 17 7 17"></polyline></svg>'
ic_wallet = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12V7H5a2 2 0 0 1 0-4h14v4"></path><path d="M3 5v14a2 2 0 0 0 2 2h16v-5"></path><path d="M18 12a2 2 0 0 0 0 4h4v-4Z"></path></svg>'
ic_safe = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>'
ic_lock = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>'
ic_user = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>'