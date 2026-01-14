import streamlit as st
import pandas as pd
from database.supabase import ZoraDatabase
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Zora by Scalinity",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def apply_custom_ui():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
        
        /* Fondo Negro Profundo */
        .stApp { background-color: #05070a !important; }
        h1, h2, h3, p, span, label { color: #ffffff !important; font-family: 'Inter', sans-serif; }

        /* EL BOTÓN AMARILLO PERFECTO */
        div.stButton > button:first-child {
            background-color: #FFD700 !important;
            color: #000000 !important;
            border: none !important;
            border-radius: 12px !important;
            height: 3.5rem !important;
            font-weight: 900 !important;
            font-size: 1.2rem !important;
            text-transform: uppercase;
            box-shadow: 0 4px 15px rgba(255, 215, 0, 0.3);
        }
        /* Forzar texto negro en el botón */
        div.stButton > button:first-child p {
            color: #000000 !important;
            font-weight: 900 !important;
        }

        /* TICKER TAPE RECUPERADO */
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
            animation: ticker 25s linear infinite;
            color: #FFD700;
            font-family: monospace;
            font-size: 1rem;
            font-weight: bold;
        }
        @keyframes ticker {
            0% { transform: translateX(100%); }
            100% { transform: translateX(-100%); }
        }

        /* FEATURES LANDING */
        .feature-box {
            background: #111827;
            padding: 25px;
            border-radius: 15px;
            border: 1px solid #1f2937;
            text-align: center;
            margin-top: 10px;
            color: #fff;
        }

        /* UI CLEANUP */
        header, footer, #MainMenu { visibility: hidden; }
        .block-container { padding-top: 4rem !important; }
        </style>

        <div class="ticker-wrapper">
            <div class="ticker-text">
                BTC/USD: $43,120.50 (+2.1%) &nbsp;&nbsp;&nbsp; ETH/USD: $2,580.15 (+1.4%) &nbsp;&nbsp;&nbsp; 
                SOL/USD: $98.40 (+4.8%) &nbsp;&nbsp;&nbsp; ZORA SENTINEL: SCANNING 247 ASSETS IN REAL-TIME...
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- 3. COMPONENTE TRADINGVIEW ---
def render_tv_chart(symbol):
    cleaned = symbol.replace("/", "").replace("-", "")
    tv_html = f'<iframe src="https://s.tradingview.com/widgetembed/?symbol=BINANCE:{cleaned}&interval=15&theme=dark" width="100%" height="400" frameborder="0"></iframe>'
    components.html(tv_html, height=400)

# --- 4. LANDING PAGE + AUTH ---
def render_auth(db):
    apply_custom_ui()
    st.markdown("<h1 style='text-align: center; color: #FFD700; font-size: 3.5rem; font-weight: 900;'>ZORA SENTINEL</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Tu Terminal de Inteligencia Algorítmica</h3>", unsafe_allow_html=True)
    
    st.write("")
    
    # Grid Informativo
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown('<div class="feature-box"><h1 style="margin:0;">🛰️</h1><b>SCANNER PRO</b><br>Escaneo de confluencias en tiempo real.</div>', unsafe_allow_html=True)
    with c2: st.markdown('<div class="feature-box"><h1 style="margin:0;">🧬</h1><b>ADN PERSONAL</b><br>Ajusta el radar a tu gestión de riesgo.</div>', unsafe_allow_html=True)
    with c3: st.markdown('<div class="feature-box"><h1 style="margin:0;">📝</h1><b>JOURNAL</b><br>Métricas de win-rate y PnL automático.</div>', unsafe_allow_html=True)

    st.write("---")

    _, auth_col, _ = st.columns([1, 1.5, 1])
    with auth_col:
        mode = st.tabs(["🔑 LOGIN", "✨ REGISTRO"])
        with mode[0]:
            el = st.text_input("Email", key="l_email")
            pl = st.text_input("Password", type="password", key="l_pass")
            if st.button("ACCEDER AHORA", type="primary", key="btn_login"):
                success, user = db.login_user(el, pl)
                if success:
                    st.session_state.update({'logged_in': True, 'user_id': user.id, 'user_email': user.email})
                    st.rerun()
        
        with mode[1]:
            er = st.text_input("Nuevo Email", key="r_email")
            pr = st.text_input("Nueva Contraseña", type="password", key="r_pass")
            if st.button("CREAR MI CUENTA", type="primary", key="btn_reg"):
                try:
                    db.supabase.auth.sign_up({"email": er, "password": pr})
                    st.success("¡Listo! Verifica tu correo.")
                except Exception as e: st.error(f"Error: {e}")

# --- 5. DASHBOARD COMPLETO ---
def render_dashboard(db):
    apply_custom_ui()
    st_autorefresh(interval=30000, key="refresh_dashboard")
    u_id = st.session_state.user_id

    with st.sidebar:
        st.markdown(f"📡 **Online:** {st.session_state.user_email}")
        if st.button("SALIR"):
            st.session_state.logged_in = False
            st.rerun()

    t_scan, t_jou, t_adn = st.tabs(["🛰️ RADAR", "📝 DIARIO", "🧬 ADN"])

    with t_scan:
        signals = db.supabase.table("signals_today").select("*").eq("user_id", u_id).execute()
        if not signals.data:
            st.info("Sentinel está buscando oportunidades...")
        else:
            for s in signals.data:
                with st.container(border=True):
                    st.markdown(f"### {s['symbol']} <span style='color:#FFD700; float:right;'>RSI: {s['rsi']}</span>", unsafe_allow_html=True)
                    st.write(f"Precio de Entrada: **${s['entry_price']:,}**")
                    with st.expander("Ver Gráfico"): render_tv_chart(s['symbol'])
                    if st.button(f"EJECUTAR {s['symbol']}", key=f"go_{s['symbol']}", type="primary"):
                        db.save_trade(u_id, s['symbol'], "LONG", s['entry_price'], 0, "Signal")
                        st.toast("Trade guardado.")

    with t_jou:
        res = db.get_trade_history(u_id)
        if res.data:
            df = pd.DataFrame(res.data)
            closed = df[df['status'] == 'CLOSED']
            pnl = closed['profit'].sum() if not closed.empty else 0
            
            c1, c2 = st.columns(2)
            c1.metric("PnL TOTAL", f"${pnl:,.2f}", delta=f"{pnl:.2f}")
            c2.metric("ABIERTOS", len(df[df['status'] == 'OPEN']))

            for _, trade in df.iterrows():
                with st.container(border=True):
                    col_t, col_b = st.columns([3, 1])
                    col_t.write(f"**{trade['symbol']}**")
                    if trade['status'] == 'OPEN':
                        col_t.caption("🟢 POSICIÓN ABIERTA")
                        if col_b.button("CERRAR", key=f"cl_{trade['id']}"):
                            st.session_state.update({'closing_id': trade['id'], 'entry_p': trade['entry_price']})
                            st.rerun()
                    else:
                        color = "green" if trade['profit'] > 0 else "red"
                        col_t.markdown(f"Resultado: :{color}[${trade['profit']:,.2f}]")

            if 'closing_id' in st.session_state:
                with st.form("f_close"):
                    exit_p = st.number_input("Precio de Salida", format="%.4f")
                    if st.form_submit_button("CONFIRMAR CIERRE", type="primary"):
                        profit = exit_p - st.session_state.entry_p
                        db.supabase.table("journal").update({"exit_price": exit_p, "status": "CLOSED", "profit": profit}).eq("id", st.session_state.closing_id).execute()
                        del st.session_state['closing_id']
                        st.rerun()

    with t_adn:
        conf = db.get_user_strategy(u_id)
        with st.form("f_adn"):
            new_rsi = st.slider("RSI Límite", 10, 40, int(conf.get('rsi_limit', 25)))
            if st.form_submit_button("ACTUALIZAR ADN", type="primary"):
                db.supabase.table("strategies").upsert({"user_id": u_id, "rsi_limit": new_rsi}).execute()
                st.success("Sincronizado.")

# --- INICIO ---
db_instance = ZoraDatabase()
if not st.session_state.get('logged_in'):
    render_auth(db_instance)
else:
    render_dashboard(db_instance)