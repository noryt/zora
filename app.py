import streamlit as st
import pandas as pd
from database.supabase import ZoraDatabase
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components
from datetime import datetime
from io import BytesIO

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Zora Sentinel",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. UI: CSS DE ALTO CONTRASTE (Botón Amarillo + Texto Negro) ---
def apply_custom_ui():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
        
        /* Fondo Negro y Tipografía */
        .stApp { background-color: #05070a !important; }
        h1, h2, h3, p, span, label { color: #ffffff !important; font-family: 'Inter', sans-serif; }

        /* BOTÓN AMARILLO ZORA (Letras Negras 900) */
        div.stButton > button, .stDownloadButton > button {
            background-color: #FFD700 !important;
            color: #000000 !important;
            border: none !important;
            border-radius: 12px !important;
            height: 3.5rem !important;
            font-weight: 900 !important;
            font-size: 1.1rem !important;
            text-transform: uppercase;
            width: 100%;
        }
        /* Forzado de color negro para el texto del botón */
        div.stButton > button p, .stDownloadButton > button p {
            color: #000000 !important;
            font-weight: 900 !important;
        }

        /* TICKER TAPE ANIMADO */
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
            font-size: 1rem;
        }
        @keyframes ticker { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }

        /* BADGE PNL */
        .pnl-badge {
            background: #111827;
            padding: 25px;
            border-radius: 15px;
            border: 2px solid #FFD700;
            text-align: center;
            margin-bottom: 20px;
        }
        
        .stButton > button[kind="primary"] p {
        color: #000000 !important;
        font-weight: 900 !important;
        }

        .stButton > button {
        border: 1px solid #FFD700 !important; /* Añade un borde dorado para que no se pierda */
        }

        /* LANDING CARDS */
        .feature-box {
            background: #111827;
            padding: 20px;
            border-radius: 12px;
            border: 1px solid #1f2937;
            text-align: center;
            height: 100%;
        }

        header, footer, #MainMenu { visibility: hidden; }
        .block-container { padding-top: 5rem !important; }
        </style>

        <div class="ticker-wrapper">
            <div class="ticker-text">
                ZORA SENTINEL: MARKET SCANNER ACTIVE &nbsp;&nbsp;&nbsp; BTC/USD: $43,120 &nbsp;&nbsp;&nbsp; ETH/USD: $2,580 &nbsp;&nbsp;&nbsp; SOL/USD: $98.40 &nbsp;&nbsp;&nbsp; SNIPER MODE: ON
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- 3. COMPONENTES ---
def render_tv_chart(symbol):
    cleaned = symbol.replace("/", "").replace("-", "")
    tv_html = f'<iframe src="https://s.tradingview.com/widgetembed/?symbol=BINANCE:{cleaned}&interval=15&theme=dark" width="100%" height="400" frameborder="0"></iframe>'
    components.html(tv_html, height=400)

# --- 4. LANDING PAGE & AUTH ---
def render_auth(db):
    apply_custom_ui()
    st.markdown("<h1 style='text-align: center; color: #FFD700; font-size: 3rem; font-weight: 900;'>ZORA SENTINEL</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.2rem; color: #cbd5e0;'>Algorithmic Trading Terminal</p>", unsafe_allow_html=True)
    
    st.write("")
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown('<div class="feature-box"><h3>🛰️</h3><b>SCANNER</b><br><small>Escaneo real de confluencias técnicas.</small></div>', unsafe_allow_html=True)
    with c2: st.markdown('<div class="feature-box"><h3>🧬</h3><b>ADN</b><br><small>Configura tu propio radar de entrada.</small></div>', unsafe_allow_html=True)
    with c3: st.markdown('<div class="feature-box"><h3>📝</h3><b>EXPORT</b><br><small>Descarga tu historial en CSV/Excel.</small></div>', unsafe_allow_html=True)
    
    st.divider()

    _, auth_col, _ = st.columns([1, 1.5, 1])
    with auth_col:
        m = st.tabs(["🔑 LOGIN", "✨ REGISTRO"])
        with m[0]:
            el = st.text_input("Email", key="l_e")
            pl = st.text_input("Password", type="password", key="l_p")
            if st.button("ENTRAR AL TERMINAL", key="btn_login", type="primary"):
                success, user = db.login_user(el, pl)
                if success:
                    st.session_state.update({'logged_in': True, 'user_id': user.id, 'user_email': user.email})
                    st.rerun()
        with m[1]:
            er = st.text_input("Nuevo Email", key="r_e")
            pr = st.text_input("Nueva Contraseña", type="password", key="r_p")
            if st.button("CREAR CUENTA", key="btn_reg", type="primary"):
                try:
                    db.supabase.auth.sign_up({"email": er, "password": pr})
                    st.success("Verifica tu email para activar la cuenta.")
                except Exception as e: st.error(f"Error: {e}")

# --- 5. DASHBOARD ---
def render_dashboard(db):
    apply_custom_ui()
    st_autorefresh(interval=30000, key="ref_dash")
    u_id = st.session_state.user_id

    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.logged_in = False
        st.rerun()

    t_scan, t_jou, t_adn = st.tabs(["🛰️ RADAR", "📝 DIARIO", "🧬 ADN"])

    # --- SCANNER ---
    with t_scan:
        st.markdown("### 🔭 Señales en Vivo")
        signals = db.supabase.table("signals_today").select("*").eq("user_id", u_id).execute()
        if not signals.data:
            st.info("Sentinel está escaneando el mercado...")
        else:
            for s in signals.data:
                with st.container(border=True):
                    st.markdown(f"#### {s['symbol']} | RSI: <span style='color:#FFD700'>{s['rsi']}</span>", unsafe_allow_html=True)
                    st.write(f"Entrada: **${s['entry_price']:,}**")
                    with st.expander("Ver Gráfico"): render_tv_chart(s['symbol'])
                    if st.button(f"EJECUTAR {s['symbol']}", key=f"g_{s['symbol']}", type="primary"):
                        db.save_trade(u_id, s['symbol'], "LONG", s['entry_price'], s.get('take_profit', 0), "Signal")
                        st.toast("Trade guardado en el Diario.")

    # --- JOURNAL ---
    with t_jou:
        res = db.get_trade_history(u_id)
        if res.data:
            df = pd.DataFrame(res.data)
            closed = df[df['status'] == 'CLOSED']
            pnl_total = closed['profit'].sum() if not closed.empty else 0.0
            pnl_color = "#00ff88" if pnl_total >= 0 else "#ff4b4b"
            
            st.markdown(f'<div class="pnl-badge"><p style="margin:0; color:#8b949e;">PNL TOTAL ACUMULADO</p><h1 style="color:{pnl_color}; margin:0;">${pnl_total:,.2f}</h1></div>', unsafe_allow_html=True)
            
            st.download_button(label="📥 EXPORTAR HISTORIAL (CSV)", data=df.to_csv(index=False), file_name='zora_trades.csv', mime='text/csv', use_container_width=True)
            
            # LÓGICA DE CIERRE PROTEGIDA
            if 'closing_id' in st.session_state and 'closing_symbol' in st.session_state:
                with st.form("f_close"):
                    st.markdown(f"### Cerrar {st.session_state.closing_symbol}")
                    entry_p_float = float(st.session_state.entry_p) if st.session_state.entry_p else 0.0
                    exit_p = st.number_input("Precio de Salida Real", format="%.4f", value=entry_p_float)
                    
                    c_f1, c_f2 = st.columns(2)
                    if c_f1.form_submit_button("CONFIRMAR CIERRE", type="primary"):
                        profit = exit_p - st.session_state.entry_p
                        db.supabase.table("journal").update({
                            "exit_price": exit_p, 
                            "status": "CLOSED", 
                            "profit": profit, 
                            "closed_at": datetime.now().isoformat()
                        }).eq("id", st.session_state.closing_id).execute()
                        
                        del st.session_state['closing_id']
                        del st.session_state['closing_symbol']
                        st.rerun()
                    
                    if c_f2.form_submit_button("CANCELAR", type="primary"):
                        del st.session_state['closing_id']
                        del st.session_state['closing_symbol']
                        st.rerun()

            st.write("---")
            for _, trade in df.sort_values('created_at', ascending=False).iterrows():
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.write(f"**{trade['symbol']}**")
                        e, tp = trade.get('entry_price', 0), trade.get('take_profit', 0)
                        ex = f"${trade.get('exit_price', 0):,.2f}" if trade['status'] == 'CLOSED' else "---"
                        st.markdown(f"<small>IN: **${e:,.2f}** | TP: <span style='color:#FFD700'>**${tp:,.2f}**</span> | OUT: **{ex}**</small>", unsafe_allow_html=True)
                    with c2:
                        if trade['status'] == 'OPEN':
                            if st.button("CERRAR", key=f"c_{trade['id']}", type="primary"):
                                st.session_state.update({
                                    'closing_id': trade['id'], 
                                    'closing_symbol': trade['symbol'], 
                                    'entry_p': trade['entry_price']
                                })
                                st.rerun()
                        else:
                            clr = "#00ff88" if trade['profit'] > 0 else "#ff4b4b"
                            st.markdown(f"<p style='color:{clr}; font-weight:bold; text-align:right; margin:0;'>${trade['profit']:,.2f}</p>", unsafe_allow_html=True)
        else: st.info("No hay registros aún.")

    # --- ADN ---
    with t_adn:
        st.markdown("### 🧬 Configuración del Radar")
        conf = db.get_user_strategy(u_id)
        with st.form("f_adn"):
            col1, col2 = st.columns(2)
            with col1:
                rsi = st.slider("RSI Límite (Sobrevendido)", 10, 50, int(conf.get('rsi_limit', 30)))
                bb = st.number_input("Multiplicador Bollinger", 1.0, 3.0, float(conf.get('bb_mult', 2.0)))
            with col2:
                tf = st.selectbox("Timeframe", ["5m", "15m", "1h"], index=1)
                vol = st.number_input("Volumen Mínimo", 0, 1000000, int(conf.get('min_vol', 50000)))
            
            if st.form_submit_button("GUARDAR CONFIGURACIÓN ADN", type="primary"):
                db.supabase.table("strategies").upsert({
                    "user_id": u_id, "rsi_limit": rsi, "bb_mult": bb, "timeframe": tf, "min_vol": vol
                }).execute()
                st.success("Sincronizado con el motor.")

# --- EJECUCIÓN ---
db_instance = ZoraDatabase()
if not st.session_state.get('logged_in'):
    render_auth(db_instance)
else:
    render_dashboard(db_instance)