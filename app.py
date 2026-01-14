import streamlit as st
import pandas as pd
from database.supabase import ZoraDatabase
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components
from datetime import datetime
from io import BytesIO

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Zora Sentinel", page_icon="🛡️", layout="wide", initial_sidebar_state="collapsed")

# --- 2. UI: CSS BLINDADO (FUERZA BRUTA CONTRA ELEMENTOS BLANCOS) ---
def apply_custom_ui():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
        
        /* 1. FONDO GLOBAL */
        .stApp, div[data-testid="stAppViewContainer"] { 
            background-color: #05070a !important; 
        }

        /* 2. BOTONES AMARILLOS (PRIMARY) */
        button[kind="primary"] {
            background-color: #FFD700 !important;
            color: #000000 !important;
            border: none !important;
            font-weight: 900 !important;
            text-transform: uppercase;
        }
        button[kind="primary"] p {
            color: #fff !important;
            font-weight: 900 !important;
        }

        /* 3. BOTONES SECUNDARIOS (COMO CANCELAR O EXPANDER) */
        /* Forzamos que CUALQUIER botón que no sea primario tenga fondo oscuro */
        button[kind="secondary"], .stButton > button {
            background-color: #161b22 !important;
            color: #FFD700 !important;
            border: 1px solid #FFD700 !important;
        }

        /* 4. ELIMINAR RECUADRO BLANCO DEL EXPANDER (ESTO ES LO QUE TE FALLA) */
        /* El 'summary' es la barra del expander */
        div[data-testid="stExpander"] {
            background-color: #161b22 !important;
            border: 1px solid #30363d !important;
            border-radius: 10px !important;
        }
        
        div[data-testid="stExpander"] details summary {
            background-color: #161b22 !important;
            color: #FFD700 !important;
        }

        div[data-testid="stExpander"] details summary:hover {
            color: #ffffff !important;
        }

        /* Eliminar el borde blanco/gris al hacer focus o abrirlo */
        div[data-testid="stExpander"] details {
            border: none !important;
        }

        /* 5. TICKER TAPE */
        .ticker-wrapper {
            background: #161b22;
            padding: 12px 0;
            border-bottom: 2px solid #FFD700;
            overflow: hidden;
            position: fixed;
            top: 0; left: 0; width: 100%; z-index: 1000;
        }
        .ticker-text {
            display: inline-block;
            white-space: nowrap;
            animation: ticker 30s linear infinite;
            color: #FFD700;
            font-family: monospace;
        }
        @keyframes ticker { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }

        /* OCULTAR INTERFAZ POR DEFECTO */
        header, footer, #MainMenu { visibility: hidden; }
        .block-container { padding-top: 5rem !important; }
        </style>

        <div class="ticker-wrapper"><div class="ticker-text">
            ZORA SENTINEL: MARKET RADAR ACTIVE &nbsp;&nbsp;&nbsp; BTC/USD: $43,120 &nbsp;&nbsp;&nbsp; ETH/USD: $2,580 &nbsp;&nbsp;&nbsp; SOL/USD: $98.40
        </div></div>
    """, unsafe_allow_html=True)

# --- 3. COMPONENTES ---
def render_tv_chart(symbol):
    cleaned = symbol.replace("/", "").replace("-", "")
    tv_html = f'<iframe src="https://s.tradingview.com/widgetembed/?symbol=BINANCE:{cleaned}&interval=15&theme=dark" width="100%" height="400" frameborder="0"></iframe>'
    components.html(tv_html, height=400)

# --- 4. LANDING & AUTH ---
def render_auth(db):
    apply_custom_ui()
    st.markdown("<h1 style='text-align: center; color: #FFD700; font-size: 3rem; font-weight: 900;'>ZORA SENTINEL</h1>", unsafe_allow_html=True)
    
    _, auth_col, _ = st.columns([1, 1.5, 1])
    with auth_col:
        m = st.tabs(["🔑 LOGIN", "✨ REGISTRO"])
        with m[0]:
            el = st.text_input("Email", key="l_e")
            pl = st.text_input("Password", type="password", key="l_p")
            if st.button("ENTRAR AL TERMINAL", type="primary"):
                success, user = db.login_user(el, pl)
                if success:
                    st.session_state.update({'logged_in': True, 'user_id': user.id, 'user_email': user.email})
                    st.rerun()
        with m[1]:
            er = st.text_input("Nuevo Email", key="r_e")
            pr = st.text_input("Nueva Contraseña", type="password", key="r_p")
            if st.button("CREAR CUENTA", type="primary"):
                try:
                    db.supabase.auth.sign_up({"email": er, "password": pr})
                    st.success("Verifica tu email.")
                except Exception as e: st.error(f"Error: {e}")

# --- 5. DASHBOARD ---
def render_dashboard(db):
    apply_custom_ui()
    st_autorefresh(interval=30000, key="ref_dash")
    u_id = st.session_state.user_id

    t_scan, t_jou, t_adn = st.tabs(["🛰️ RADAR", "📝 DIARIO", "🧬 ADN"])

    # --- PESTAÑA SCANNER ---
    with t_scan:
        st.markdown("### 🔭 Radar de Oportunidades")
        signals = db.supabase.table("signals_today").select("*").eq("user_id", u_id).execute()
        if not signals.data:
            st.info("Buscando confluencias...")
        else:
            for s in signals.data:
                with st.container(border=True):
                    st.markdown(f"#### {s['symbol']} | RSI: <span style='color:#FFD700'>{s['rsi']}</span>", unsafe_allow_html=True)
                    st.write(f"Entrada: **${s['entry_price']:,}**")
                    
                    # Expander con selectores CSS forzados (data-testid)
                    with st.expander("📊 VER GRÁFICO TÉCNICO"):
                        render_tv_chart(s['symbol'])
                    
                    if st.button(f"EJECUTAR {s['symbol']}", key=f"g_{s['symbol']}", type="primary"):
                        db.save_trade(u_id, s['symbol'], "LONG", s['entry_price'], s.get('take_profit', 0), "Signal")
                        st.toast("Trade guardado.")

    # --- PESTAÑA JOURNAL ---
    with t_jou:
        res = db.get_trade_history(u_id)
        if res.data:
            df = pd.DataFrame(res.data)
            closed = df[df['status'] == 'CLOSED']
            pnl_total = closed['profit'].sum() if not closed.empty else 0.0
            pnl_color = "#00ff88" if pnl_total >= 0 else "#ff4b4b"
            
            st.markdown(f'<div style="background:#111827; padding:20px; border-radius:15px; border:2px solid #FFD700; text-align:center;"><p style="margin:0; color:#8b949e;">PNL ACUMULADO</p><h1 style="color:{pnl_color}; margin:0;">${pnl_total:,.2f}</h1></div>', unsafe_allow_html=True)
            
            # Formulario de Cierre Protegido
            if 'closing_id' in st.session_state:
                with st.form("f_close"):
                    st.markdown(f"### Cerrar {st.session_state.get('closing_symbol', 'Trade')}")
                    exit_p = st.number_input("Precio Salida", format="%.4f", value=float(st.session_state.get('entry_p', 0)))
                    c1, c2 = st.columns(2)
                    if c1.form_submit_button("CONFIRMAR", type="primary"):
                        p = exit_p - st.session_state.entry_p
                        db.supabase.table("journal").update({"exit_price": exit_p, "status": "CLOSED", "profit": p, "closed_at": datetime.now().isoformat()}).eq("id", st.session_state.closing_id).execute()
                        del st.session_state['closing_id']
                        st.rerun()
                    if c2.form_submit_button("CANCELAR"): # Este botón ya no será blanco por el CSS de arriba
                        del st.session_state['closing_id']
                        st.rerun()

            st.write("---")
            for _, trade in df.sort_values('created_at', ascending=False).iterrows():
                with st.container(border=True):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**{trade['symbol']}**")
                        st.markdown(f"<small>IN: {trade['entry_price']} | STATUS: {trade['status']}</small>", unsafe_allow_html=True)
                    with col2:
                        if trade['status'] == 'OPEN':
                            if st.button("CERRAR", key=f"c_{trade['id']}", type="primary"):
                                st.session_state.update({'closing_id': trade['id'], 'closing_symbol': trade['symbol'], 'entry_p': trade['entry_price']})
                                st.rerun()
                        else:
                            clr = "#00ff88" if trade['profit'] > 0 else "#ff4b4b"
                            st.markdown(f"<p style='color:{clr}; font-weight:bold; text-align:right;'>${trade['profit']:,.2f}</p>", unsafe_allow_html=True)

    # --- PESTAÑA ADN ---
    with t_adn:
        conf = db.get_user_strategy(u_id)
        with st.form("f_adn"):
            rsi = st.slider("RSI Umbral", 10, 50, int(conf.get('rsi_limit', 30)))
            if st.form_submit_button("GUARDAR ADN", type="primary"):
                db.supabase.table("strategies").upsert({"user_id": u_id, "rsi_limit": rsi}).execute()
                st.success("Sincronizado.")

# --- EJECUCIÓN ---
db_instance = ZoraDatabase()
if not st.session_state.get('logged_in'):
    render_auth(db_instance)
else:
    render_dashboard(db_instance)