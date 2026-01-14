import streamlit as st
import pandas as pd
from database.supabase import ZoraDatabase
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Zora", page_icon="🛡️", layout="wide", initial_sidebar_state="collapsed")

def apply_custom_ui():
    css_code = '''
    <style>
        .stApp { background-color: #0b0e14 !important; }
        
        /* Forzar texto blanco en toda la app */
        h1, h2, h3, h4, p, span, label, div { color: #e6edf3 !important; }

        button[kind="primary"] {
            background-color: #FFD700 !important;
            border: none !important;
            height: 3rem !important;
        }
        button[kind="primary"] p {
            color: #000000 !important;
            font-weight: 900 !important;
            font-size: 1.2rem !important;
        }

        /* Botón Cerrar/Secundario */
        button[kind="secondary"], button:not([kind="primary"]) {
            background-color: #1f242c !important;
            border: 1px solid #3d444d !important;
            color: #ffffff !important;
        }

        /* UI Clean */
        header, footer, #MainMenu { visibility: hidden; }
        .block-container { padding-top: 2rem !important; }
        
        /* Tabs */
        .stTabs [data-baseweb="tab"] p { color: #8b949e !important; }
        .stTabs [aria-selected="true"] p { color: #FFD700 !important; }
        
        /* Input fields */
        input { background-color: #161b22 !important; color: white !important; }
    </style>
    '''
    st.markdown(css_code, unsafe_allow_html=True)

# --- 1. inicio de sESIÓN ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user_id': None, 'user_email': None})

def render_login(db):
    apply_custom_ui()
    st.markdown("<h1 style='text-align: center; color: #FFD700;'>ZORA</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #8b949e;'>Scanner y diario para Crypto</p>", unsafe_allow_html=True)
    
    _, col, _ = st.columns([1, 1.5, 1])
    with col:
        with st.container(border=True):
            t1, t2 = st.tabs(["🔑 LOGIN", "✨ REGISTRO"])
            with t1:
                e = st.text_input("Email", key="log_e")
                p = st.text_input("Password", type="password", key="log_p")
                if st.button("ENTRAR", use_container_width=True, type="primary"):
                    success, user = db.login_user(e, p)
                    if success:
                        st.session_state.update({'logged_in': True, 'user_id': user.id, 'user_email': user.email})
                        st.rerun()
            with t2:
                st.info("Registro habilitado por invitación.")

def render_dashboard(db):
    apply_custom_ui()
    st_autorefresh(interval=30000, key="refresh")
    u_id = st.session_state.user_id

    t_scan, t_jou, t_adn = st.tabs(["🛰️ SCANNER", "📝 JOURNAL", "🧬 ADN"])

    with t_scan:
        st.subheader("Scanner")
        signals = db.supabase.table("signals_today").select("*").eq("user_id", u_id).execute()
        if not signals.data:
            st.info("Esperando señales...")
        else:
            for s in signals.data:
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    c1.write(f"**{s['symbol']}** | RSI: {s['rsi']}")
                    if c2.button("GO", key=s['symbol'], type="primary"):
                        db.save_trade(u_id, s['symbol'], "LONG", s['entry_price'], 0, "Signal")
                        st.toast("Añadido al Diario")

    with t_jou:
        st.subheader("Tu Rendimiento")
        res = db.get_trade_history(u_id)
        if res.data:
            df = pd.DataFrame(res.data)

            for _, trade in df.iterrows():
                with st.container(border=True):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**{trade['symbol']}** | Entrada: ${trade['entry_price']}")
                        if trade['status'] == 'OPEN':
                            st.caption("Estado: En curso 🟢")
                        else:
                            p_color = "green" if trade['profit'] > 0 else "red"
                            st.markdown(f"Profit: :{p_color}[${trade['profit']:,.2f}]")
                    
                    with col2:
                        if trade['status'] == 'OPEN':
                            if st.button("CERRAR", key=f"cl_{trade['id']}", use_container_width=True):
                                st.session_state.update({'closing_id': trade['id'], 'entry_p': trade['entry_price']})
                                st.rerun()
            
            if 'closing_id' in st.session_state:
                with st.expander("Confirmar Cierre", expanded=True):
                    exit_p = st.number_input("Precio Salida", format="%.4f")
                    if st.button("GUARDAR", type="primary"):
                        pnl = exit_p - st.session_state.entry_p
                        db.supabase.table("journal").update({"exit_price": exit_p, "status": "CLOSED", "profit": pnl}).eq("id", st.session_state.closing_id).execute()
                        del st.session_state['closing_id']
                        st.rerun()
        else:
            st.write("No hay trades.")

    with t_adn:
        st.subheader("Configuración")
        conf = db.get_user_strategy(u_id)
        with st.form("adn_form"):
            new_rsi = st.slider("RSI", 10, 50, int(conf.get('rsi_limit', 25)))
            if st.form_submit_button("SINCRONIZAR", type="primary"):
                db.supabase.table("strategies").upsert({"user_id": u_id, "rsi_limit": new_rsi}).execute()
                db.supabase.table("signals_today").delete().eq("user_id", u_id).execute()
                st.rerun()

# --- RUN ---
db_instance = ZoraDatabase()
if not st.session_state.logged_in:
    render_login(db_instance)
else:
    render_dashboard(db_instance)