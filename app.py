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

# --- 2. FUNCIÓN DE DISEÑO (ESTO CONTROLA TODA LA ESTÉTICA) ---
def apply_custom_ui():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
        
        /* FONDO Y TEXTO */
        .stApp { background-color: #05070a !important; }
        h1, h2, h3, p, span, label { color: #ffffff !important; font-family: 'Inter', sans-serif; }

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
            animation: ticker 30s linear infinite;
            color: #FFD700;
            font-family: monospace;
            font-size: 1rem;
        }
        @keyframes ticker { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }

        /* BOTONES AMARILLOS (PRIMARY) */
        div.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {
            background-color: #FFD700 !important;
            color: #000000 !important;
            border: none !important;
            border-radius: 12px !important;
            height: 3.5rem !important;
            font-weight: 900 !important;
            font-size: 1.1rem !important;
            text-transform: uppercase;
        }
        div.stButton > button[kind="primary"] p { color: #000000 !important; font-weight: 900 !important; }

        /* BOTONES SECUNDARIOS (CANCELAR / OTROS) */
        div.stButton > button:not([kind="primary"]) {
            background-color: #161b22 !important;
            color: #ffffff !important;
            border: 1px solid #FFD700 !important;
            border-radius: 12px !important;
        }

        /* PESTAÑAS GIGANTES (REAL TABS) */
        div[data-testid="stTabs"] [data-baseweb="tab-list"] {
            background-color: #161b22 !important;
            gap: 5px !important;
            padding: 5px !important;
            border-radius: 12px !important;
            margin-bottom: 20px !important;
        }
        div[data-testid="stTabs"] button {
            flex: 1 !important;
            height: 65px !important;
            font-size: 1.1rem !important;
            font-weight: 700 !important;
            color: #8b949e !important;
            border: none !important;
            background-color: transparent !important;
        }
        div[data-testid="stTabs"] button[aria-selected="true"] {
            color: #FFD700 !important;
            border-bottom: 4px solid #FFD700 !important;
        }

       /* CORRECCIÓN DEFINITIVA EXPANDER (ABIERTO, CERRADO Y HOVER) */
        /* 1. El contenedor principal */
        div[data-testid="stExpander"], details {
            background-color: #111827 !important;
            border: 1px solid #1f2937 !important;
            border-radius: 12px !important;
        }

        /* 2. La barra del título (Summary) cuando está abierto o cerrado */
        div[data-testid="stExpander"] summary {
            background-color: #111827 !important;
            color: #FFD700 !important; /* Texto siempre Dorado */
            padding: 10px !important;
        }

        /* 3. El contenido de adentro cuando se abre */
        div[data-testid="stExpander"] div[data-testid="stVerticalBlock"] {
            background-color: #111827 !important;
            border: none !important;
        }

        /* 4. Eliminar el efecto blanco al hacer click o estar activo */
        details[open] > summary {
            background-color: #111827 !important;
            color: #FFD700 !important;
            border-bottom: 1px solid #1f2937 !important;
        }

        /* 5. Forzar que no cambie a blanco en Hover */
        div[data-testid="stExpander"]:hover, summary:hover {
            background-color: #111827 !important;
            color: #ffffff !important;
        }
                /* CORRECCIÓN ALERTAS (TOAST) */
        div[data-testid="stToast"] {
            background-color: #111827 !important; /* Fondo azul oscuro Zora */
            border: 1px solid #FFD700 !important; /* Borde dorado Sniper */
            border-radius: 10px !important;
            width: auto !important;
        }

        /* Color del texto y del icono dentro de la alerta */
        div[data-testid="stToast"] [data-testid="stMarkdownContainer"] p {
            color: #ffffff !important;
            font-weight: 700 !important;
        }

        /* Botón de cerrar (X) de la alerta */
        div[data-testid="stToast"] button {
            color: #FFD700 !important;
        }
        /* LIMPIEZA INTERFAZ */
        header, footer, #MainMenu { visibility: hidden; }
        .block-container { padding-top: 5.5rem !important; }
        </style>

        <div class="ticker-wrapper">
            <div class="ticker-text">
                ZORA SENTINEL: MARKET RADAR ACTIVE &nbsp;&nbsp;&nbsp; BTC/USD: $43,120 &nbsp;&nbsp;&nbsp; ETH/USD: $2,580 &nbsp;&nbsp;&nbsp; SNIPER MODE: ON
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- 3. COMPONENTES ---
def render_tv_chart(symbol):
    cleaned = symbol.replace("/", "").replace("-", "")
    tv_html = f'<iframe src="https://s.tradingview.com/widgetembed/?symbol=BINANCE:{cleaned}&interval=15&theme=dark" width="100%" height="400" frameborder="0"></iframe>'
    components.html(tv_html, height=400)

# --- 4. SECCIÓN DE AUTENTICACIÓN ---
def render_auth(db):
    apply_custom_ui()
    st.markdown("<h1 style='text-align: center; color: #FFD700; font-size: 3rem; font-weight: 900; margin-top:20px;'>ZORA SENTINEL</h1>", unsafe_allow_html=True)
    
    # Features informativas
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown('<div style="background:#111827; padding:15px; border-radius:10px; text-align:center;"><b>🛰️ SCANNER</b></div>', unsafe_allow_html=True)
    with c2: st.markdown('<div style="background:#111827; padding:15px; border-radius:10px; text-align:center;"><b>🧬 ADN</b></div>', unsafe_allow_html=True)
    with c3: st.markdown('<div style="background:#111827; padding:15px; border-radius:10px; text-align:center;"><b>📝 EXPORT</b></div>', unsafe_allow_html=True)

    st.divider()
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
            if st.button("CREAR MI CUENTA", type="primary"):
                try:
                    db.supabase.auth.sign_up({"email": er, "password": pr})
                    st.success("Revisa tu correo para activar tu cuenta.")
                except Exception as e: st.error(f"Error: {e}")

# --- 5. DASHBOARD ---
def render_dashboard(db):
    apply_custom_ui()
    st_autorefresh(interval=30000, key="ref_dash")
    u_id = st.session_state.user_id

    # Sidebar
    if st.sidebar.button("Cerrar Sesión", type="primary"):
        st.session_state.logged_in = False
        st.rerun()

    # Tabs Gigantes
    t_scan, t_jou, t_adn = st.tabs(["🛰️ RADAR", "📝 DIARIO", "🧬 ADN"])

    with t_scan:
        st.markdown("### 🔭 Radar de Oportunidades")
        signals = db.supabase.table("signals_today").select("*").eq("user_id", u_id).execute()
        if not signals.data:
            st.info("Buscando señales con tu configuración de ADN...")
        else:
            for s in signals.data:
                with st.container(border=True):
                    st.markdown(f"#### {s['symbol']} | RSI: <span style='color:#FFD700'>{s['rsi']}</span>", unsafe_allow_html=True)
                    st.write(f"Entrada Sugerida: **${s['entry_price']:,}**")
                    with st.expander("📊 VER ANÁLISIS TÉCNICO"):
                        render_tv_chart(s['symbol'])
                    if st.button(f"EJECUTAR {s['symbol']}", key=f"g_{s['symbol']}", type="primary"):
                    db.save_trade(u_id, s['symbol'], "LONG", s['entry_price'], s.get('take_profit', 0), "Signal")
                    # Añadimos un icono de escudo o radar
                    st.toast(f"Trade {s['symbol']} sincronizado", icon='🛡️')

    with t_jou:
        res = db.get_trade_history(u_id)
        if res.data:
            df = pd.DataFrame(res.data)
            closed = df[df['status'] == 'CLOSED']
            pnl_total = closed['profit'].sum() if not closed.empty else 0.0
            pnl_color = "#00ff88" if pnl_total >= 0 else "#ff4b4b"
            
            st.markdown(f'<div style="background:#111827; padding:20px; border-radius:15px; border:2px solid #FFD700; text-align:center;"><p style="margin:0; color:#8b949e;">PNL TOTAL</p><h1 style="color:{pnl_color}; margin:0; font-size:3rem;">${pnl_total:,.2f}</h1></div>', unsafe_allow_html=True)
            st.download_button(label="📥 EXPORTAR CSV", data=df.to_csv(index=False), file_name='trades.csv', mime='text/csv', use_container_width=True)
            
            # Cierre de trades
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
                    if c2.form_submit_button("CANCELAR"):
                        del st.session_state['closing_id']
                        st.rerun()

            st.write("---")
            for _, trade in df.sort_values('created_at', ascending=False).iterrows():
                with st.container(border=True):
                    c_a, c_b = st.columns([3, 1])
                    with c_a:
                        st.write(f"**{trade['symbol']}**")
                        ex = f"${trade['exit_price']}" if trade['status'] == 'CLOSED' else "---"
                        st.markdown(f"<small>IN: {trade['entry_price']} | OUT: {ex}</small>", unsafe_allow_html=True)
                    with c_b:
                        if trade['status'] == 'OPEN':
                            if st.button("CERRAR", key=f"c_{trade['id']}", type="primary"):
                                st.session_state.update({'closing_id': trade['id'], 'closing_symbol': trade['symbol'], 'entry_p': trade['entry_price']})
                                st.rerun()
                        else:
                            clr = "#00ff88" if trade['profit'] > 0 else "#ff4b4b"
                            st.markdown(f"<p style='color:{clr}; font-weight:bold; text-align:right;'>${trade['profit']:,.2f}</p>", unsafe_allow_html=True)

    with t_adn:
        conf = db.get_user_strategy(u_id)
        with st.form("f_adn"):
            rsi = st.slider("RSI Umbral", 10, 50, int(conf.get('rsi_limit', 30)))
            if st.form_submit_button("GUARDAR ADN", type="primary"):
                db.supabase.table("strategies").upsert({"user_id": u_id, "rsi_limit": rsi}).execute()
                st.success("Configuración guardada.")

# --- INICIO ---
db_instance = ZoraDatabase()
if not st.session_state.get('logged_in'):
    render_auth(db_instance)
else:
    render_dashboard(db_instance)