import streamlit as st
import pandas as pd
from database.supabase import ZoraDatabase
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Zora Sentinel",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. UI: CSS REFORZADO ---
def apply_custom_ui():
    css = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');

        .stApp { background-color: #0b0e14 !important; }
        h1, h2, h3, p, span, label { color: #e6edf3 !important; font-family: 'Inter', sans-serif; }

        /* Estilo Botón Primario (Amarillo con Fuente Negra) */
        button[kind="primary"] {
            background-color: #FFD700 !important;
            color: #000000 !important; /* Fuente Negra */
            border: none !important;
            border-radius: 12px !important;
            height: 3.5rem !important;
            font-weight: 900 !important; /* Texto Grueso */
            text-transform: uppercase;
            width: 100%;
        }
        
        /* Forzar color negro incluso en hover/focus */
        button[kind="primary"]:hover, button[kind="primary"]:focus, button[kind="primary"]:active {
            color: #000000 !important;
            background-color: #FFC400 !important;
        }

        /* Ocultar elementos de Streamlit */
        header, footer, #MainMenu { visibility: hidden; }
        .block-container { padding-top: 2rem !important; }

        /* Ticker Tape */
        .ticker-wrapper {
            background: #161b22;
            padding: 10px 0;
            border-bottom: 1px solid #30363d;
            overflow: hidden;
            position: fixed;
            top: 0; left: 0; width: 100%; z-index: 999;
        }
        .ticker-text {
            display: inline-block;
            white-space: nowrap;
            animation: ticker 30s linear infinite;
            color: #FFD700;
            font-family: monospace;
        }
        @keyframes ticker {
            0% { transform: translateX(100%); }
            100% { transform: translateX(-100%); }
        }

        /* Feature Box */
        .feature-box {
            background: #161b22;
            padding: 20px;
            border-radius: 15px;
            border: 1px solid #30363d;
            margin-bottom: 15px;
            text-align: center;
        }
        .feature-icon { font-size: 30px; margin-bottom: 10px; display: block; }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
    
    # Ticker Tape Superior
    st.markdown("""
        <div class="ticker-wrapper">
            <div class="ticker-text">
                BTC/USD: $42,650.20 (+1.4%) &nbsp;&nbsp;&nbsp; ETH/USD: $2,541.10 (-0.2%) &nbsp;&nbsp;&nbsp; 
                SOL/USD: $94.50 (+5.1%) &nbsp;&nbsp;&nbsp; ZORA SENTINEL: SCANNING MARKET IN REAL-TIME...
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- 3. COMPONENTE TRADINGVIEW ---
def render_tv_chart(symbol):
    cleaned = symbol.replace("/", "").replace("-", "")
    tv_html = f"""
    <iframe src="https://s.tradingview.com/widgetembed/?symbol=BINANCE:{cleaned}&interval=15&theme=dark" 
    width="100%" height="300" frameborder="0"></iframe>
    """
    components.html(tv_html, height=300)

# --- 4. LÓGICA DE SESIÓN ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user_id': None, 'user_email': None})

def render_login(db):
    apply_custom_ui()
    
    # Hero Section
    st.markdown("<h1 style='text-align: center; margin-top: 40px; color: #FFD700;'>🛡️ ZORA SENTINEL</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Tu Radar Inteligente de Trading</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #8b949e;'>No persigas el precio. Deja que Zora encuentre la entrada perfecta por ti.</p>", unsafe_allow_html=True)

    st.write("---")

    # Sección Informativa (Por qué registrarse)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="feature-box"><span class="feature-icon">🛰️</span><b>Escaneo 24/7</b><br><small>Analizamos +200 activos cada 5 min.</small></div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="feature-box"><span class="feature-icon">🧬</span><b>Estrategia ADN</b><br><small>Filtros de RSI y Bollinger personalizados.</small></div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="feature-box"><span class="feature-icon">📝</span><b>Trading Journal</b><br><small>Registro automático de tus operaciones.</small></div>', unsafe_allow_html=True)

    st.write("")

    # Login Form
    _, log_col, _ = st.columns([1, 2, 1])
    with log_col:
        with st.container(border=True):
            st.markdown("<p style='text-align: center; font-weight: bold;'>ACCESO AL TERMINAL</p>", unsafe_allow_html=True)
            e = st.text_input("Email", placeholder="tu@email.com")
            p = st.text_input("Password", type="password", placeholder="••••••••")
            if st.button("ENTRAR AL RADAR", type="primary"):
                success, user = db.login_user(e, p)
                if success:
                    st.session_state.update({'logged_in': True, 'user_id': user.id, 'user_email': user.email})
                    st.rerun()
            st.markdown("<p style='text-align: center; font-size: 12px; color: #8b949e;'>¿No tienes cuenta? Contacta a un administrador.</p>", unsafe_allow_html=True)

def render_dashboard(db):
    apply_custom_ui()
    st_autorefresh(interval=30000, key="refresh")
    u_id = st.session_state.user_id

    st.markdown(f"🔋 **Terminal Conectada:** {st.session_state.user_email}")

    t_scan, t_jou, t_adn = st.tabs(["🛰️ SCANNER", "📝 JOURNAL", "🧬 ADN"])

    with t_scan:
        signals = db.supabase.table("signals_today").select("*").eq("user_id", u_id).execute()
        if not signals.data:
            st.info("Buscando patrones Sniper en el mercado...")
        else:
            for s in signals.data:
                with st.container(border=True):
                    st.subheader(f"{s['symbol']}")
                    st.write(f"RSI: {s['rsi']} | Precio: ${s['entry_price']}")
                    with st.expander("Ver Análisis Técnico"):
                        render_tv_chart(s['symbol'])
                    if st.button(f"EJECUTAR COMPRA {s['symbol']}", key=f"go_{s['symbol']}", type="primary"):
                        db.save_trade(u_id, s['symbol'], "LONG", s['entry_price'], 0, "Signal")
                        st.toast("Trade enviado al diario.")

    # (Las demás pestañas JOURNAL y ADN se mantienen igual...)

# --- RUN ---
db_instance = ZoraDatabase()
if not st.session_state.logged_in:
    render_login(db_instance)
else:
    render_dashboard(db_instance)