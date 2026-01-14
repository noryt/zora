import streamlit as st
import pandas as pd
from database.supabase import ZoraDatabase
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components
from io import BytesIO

# --- 1. CONFIGURACIÓN ---
st.set_page_config(
    page_title="Zora Sentinel",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. UI: CSS REFORZADO ---
def apply_custom_ui():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
        .stApp { background-color: #05070a !important; }
        h1, h2, h3, p, span, label { color: #ffffff !important; font-family: 'Inter', sans-serif; }

        /* BOTÓN AMARILLO VIBRANTE CON TEXTO NEGRO */
        div.stButton > button:first-child, .stDownloadButton > button {
            background-color: #FFD700 !important;
            color: #000000 !important;
            border: none !important;
            border-radius: 12px !important;
            height: 3.5rem !important;
            font-weight: 900 !important;
            font-size: 1.1rem !important;
            text-transform: uppercase;
        }
        div.stButton > button:first-child p, .stDownloadButton > button p {
            color: #000000 !important;
            font-weight: 900 !important;
        }

        /* BADGE DE PNL DE ALTO CONTRASTE */
        .pnl-badge {
            background: #1a202c;
            padding: 20px;
            border-radius: 15px;
            border: 2px solid #FFD700;
            text-align: center;
            margin-bottom: 20px;
        }
        .pnl-value {
            font-size: 2.5rem;
            font-weight: 900;
            margin: 0;
        }

        /* TICKER TAPE */
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
        }
        @keyframes ticker { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }

        header, footer, #MainMenu { visibility: hidden; }
        .block-container { padding-top: 4.5rem !important; }
        </style>

        <div class="ticker-wrapper">
            <div class="ticker-text">
                ZORA SENTINEL: LIVE MARKET SCANNER &nbsp;&nbsp;&nbsp; BTC/USD: $43,120 &nbsp;&nbsp;&nbsp; ETH/USD: $2,580 &nbsp;&nbsp;&nbsp; SOL/USD: $98.40
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- 3. FUNCIONES AUXILIARES ---
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Trades')
    return output.getvalue()

def render_tv_chart(symbol):
    cleaned = symbol.replace("/", "").replace("-", "")
    tv_html = f'<iframe src="https://s.tradingview.com/widgetembed/?symbol=BINANCE:{cleaned}&interval=15&theme=dark" width="100%" height="400" frameborder="0"></iframe>'
    components.html(tv_html, height=400)

# --- 4. LANDING & AUTH ---
def render_auth(db):
    apply_custom_ui()
    st.markdown("<h1 style='text-align: center; color: #FFD700; font-size: 3rem; font-weight: 900;'>ZORA SENTINEL</h1>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    c1.markdown('<div style="background:#111827; padding:15px; border-radius:10px; text-align:center;"><b>🛰️ SCANNER</b></div>', unsafe_allow_html=True)
    c2.markdown('<div style="background:#111827; padding:15px; border-radius:10px; text-align:center;"><b>🧬 ADN</b></div>', unsafe_allow_html=True)
    c3.markdown('<div style="background:#111827; padding:15px; border-radius:10px; text-align:center;"><b>📝 EXPORT</b></div>', unsafe_allow_html=True)

    _, auth_col, _ = st.columns([1, 1.5, 1])
    with auth_col:
        m = st.tabs(["🔑 LOGIN", "✨ REGISTRO"])
        with m[0]:
            el = st.text_input("Email", key="l_e")
            pl = st.text_input("Password", type="password", key="l_p")
            if st.button("ACCEDER AL RADAR", type="primary"):
                success, user = db.login_user(el, pl)
                if success:
                    st.session_state.update({'logged_in': True, 'user_id': user.id, 'user_email': user.email})
                    st.rerun()

# --- 5. DASHBOARD ---
def render_dashboard(db):
    apply_custom_ui()
    st_autorefresh(interval=30000, key="ref_dash")
    u_id = st.session_state.user_id

    t_scan, t_jou, t_adn = st.tabs(["🛰️ RADAR", "📝 DIARIO", "🧬 ADN"])

    with t_scan:
        signals = db.supabase.table("signals_today").select("*").eq("user_id", u_id).execute()
        if not signals.data:
            st.info("Buscando oportunidades...")
        else:
            for s in signals.data:
                with st.container(border=True):
                    st.markdown(f"### {s['symbol']} <span style='color:#FFD700; float:right;'>RSI: {s['rsi']}</span>", unsafe_allow_html=True)
                    with st.expander("Gráfico"): render_tv_chart(s['symbol'])
                    if st.button(f"OPEN {s['symbol']}", key=f"g_{s['symbol']}", type="primary"):
                        db.save_trade(u_id, s['symbol'], "LONG", s['entry_price'], 0, "Signal")
                        st.toast("Guardado.")

    with t_jou:
        res = db.get_trade_history(u_id)
        if res.data:
            df = pd.DataFrame(res.data)
            closed = df[df['status'] == 'CLOSED']
            pnl_total = closed['profit'].sum() if not closed.empty else 0.0
            
            # PNL BADGE DE ALTO CONTRASTE
            pnl_color = "#00ff88" if pnl_total >= 0 else "#ff4b4b"
            st.markdown(f"""
                <div class="pnl-badge">
                    <p style="margin:0; color:#8b949e; text-transform:uppercase; letter-spacing:2px;">Profit Total Acumulado</p>
                    <p class="pnl-value" style="color:{pnl_color};">${pnl_total:,.2f}</p>
                </div>
            """, unsafe_allow_html=True)

            # BOTÓN DE EXPORTAR
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 EXPORTAR HISTORIAL (CSV)",
                data=csv,
                file_name=f'zora_trades_{datetime.now().strftime("%Y%m%d")}.csv',
                mime='text/csv',
                use_container_width=True
            )
            
            st.divider()

            for _, trade in df.iterrows():
                with st.container(border=True):
                    c_a, c_b = st.columns([3, 1])
                    c_a.write(f"**{trade['symbol']}**")
                    if trade['status'] == 'OPEN':
                        if c_b.button("CERRAR", key=f"c_{trade['id']}"):
                            st.session_state.update({'closing_id': trade['id'], 'entry_p': trade['entry_price']})
                            st.rerun()
                    else:
                        clr = "green" if trade['profit'] > 0 else "red"
                        c_a.markdown(f"Resultado: :{clr}[${trade['profit']:,.2f}]")

            if 'closing_id' in st.session_state:
                with st.form("f_c"):
                    exit_p = st.number_input("Precio Salida", format="%.4f")
                    if st.form_submit_button("CONFIRMAR", type="primary"):
                        p = exit_p - st.session_state.entry_p
                        db.supabase.table("journal").update({"exit_price": exit_p, "status": "CLOSED", "profit": p}).eq("id", st.session_state.closing_id).execute()
                        del st.session_state['closing_id']
                        st.rerun()

    with t_adn:
        conf = db.get_user_strategy(u_id)
        with st.form("f_a"):
            new_rsi = st.slider("RSI Límite", 10, 40, int(conf.get('rsi_limit', 25)))
            if st.form_submit_button("GUARDAR ADN", type="primary"):
                db.supabase.table("strategies").upsert({"user_id": u_id, "rsi_limit": new_rsi}).execute()
                st.success("ADN Sincronizado.")

# --- INICIO ---
db_instance = ZoraDatabase()
from datetime import datetime
if not st.session_state.get('logged_in'):
    render_auth(db_instance)
else:
    render_dashboard(db_instance)