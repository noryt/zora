import streamlit as st
import pandas as pd
from database.supabase import ZoraDatabase
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components

# --- 1. CONFIGURACIÓN (Ocultar barras laterales innecesarias en móvil) ---
st.set_page_config(
    page_title="Zora Sentinel",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. CSS MOBILE-FRIENDLY REFORZADO ---
def apply_custom_ui():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
        
        /* Reset para Móvil */
        .stApp { background-color: #05070a !important; }
        
        /* 1. Ajuste de Contenedor Principal (Quitar márgenes laterales en móvil) */
        .block-container {
            padding-top: 4rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            max-width: 100% !important;
        }

        /* 2. Tarjetas de la Landing (Forzar una debajo de otra en móvil) */
        @media (max-width: 640px) {
            div[data-testid="column"] {
                width: 100% !important;
                flex: 1 1 100% !important;
                min-width: 100% !important;
                margin-bottom: 15px !important;
            }
            h1 { font-size: 2.2rem !important; }
            .feature-card { padding: 15px !important; }
        }

        .feature-card {
            background: #111827;
            padding: 20px;
            border-radius: 15px;
            border: 1px solid #1f2937;
            text-align: center;
            margin-bottom: 10px;
        }
        .feature-card h3 { color: #FFD700 !important; font-size: 1.1rem !important; }
        .feature-card p { font-size: 0.85rem !important; color: #94a3b8 !important; }

        /* 3. Botones Gigantes para Pulgares */
        div.stButton > button {
            width: 100% !important;
            height: 3.8rem !important;
            font-size: 1.1rem !important;
            border-radius: 14px !important;
            background-color: #FFD700 !important;
            color: #000 !important;
            font-weight: 900 !important;
        }

        /* 4. Pestañas (Tabs) Estilo Mobile Bar */
        div[data-testid="stTabs"] [data-baseweb="tab-list"] {
            display: flex !important;
            justify-content: space-around !important;
            background-color: #161b22 !important;
            position: sticky;
            top: 46px; /* Justo debajo del ticker */
            z-index: 999;
            padding: 5px !important;
        }
        div[data-testid="stTabs"] button {
            font-size: 0.8rem !important; /* Más pequeño para que quepan 3 en línea */
            flex: 1 !important;
        }

        /* Ocultar elementos de escritorio */
        #MainMenu, footer, header { visibility: hidden; }
        </style>
    """, unsafe_allow_html=True)

    # Ticker optimizado para no romperse en pantallas pequeñas
    ticker_html = """
    <div style="position: fixed; top: 0; left: 0; width: 100%; z-index: 1001; height: 46px; background: #161b22;">
        <iframe scrolling="no" allowtransparency="true" frameborder="0" 
            src="https://s.tradingview.com/embed-widget/ticker-tape/?symbols%5B%5D%7B%22proName%22%3A%22COINBASE%3ABTCUSD%22%7D%2C%7B%22proName%22%3A%22COINBASE%3AETHUSD%22%7D&colorTheme=dark&isTransparent=false&displayMode=adaptive&locale=es" 
            width="100%" height="46">
        </iframe>
    </div>
    """
    components.html(ticker_html, height=46)

# --- 3. RENDER LANDING (MOBILE FIRST) ---
def render_auth(db):
    apply_custom_ui()
    
    st.markdown("<h1 style='text-align: center; color: #FFD700; font-weight: 900;'>ZORA SENTINEL</h1>", unsafe_allow_html=True)
    
    # En móvil, estas columnas se verán una debajo de otra gracias al CSS media query
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="feature-card"><h3>🛰️ SCANNER</h3><p>Vigilancia en tiempo real de confluencias técnicas.</p></div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="feature-card"><h3>🧬 ADN</h3><p>Configuración de algoritmos y límites de RSI.</p></div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="feature-card"><h3>📝 EXPORT</h3><p>Auditoría de PnL y descarga de historial.</p></div>', unsafe_allow_html=True)

    st.write("---")
    
    _, auth_box, _ = st.columns([0.1, 1, 0.1]) # En móvil ocupará casi todo el ancho
    with auth_box:
        tab_login, tab_reg = st.tabs(["🔑 ACCESO", "✨ REGISTRO"])
        with tab_login:
            st.text_input("Email", key="m_email")
            st.text_input("Password", type="password", key="m_pass")
            st.button("ENTRAR AL TERMINAL", type="primary", use_container_width=True)

# --- INICIO ---
db_instance = ZoraDatabase()
if not st.session_state.get('logged_in'):
    render_auth(db_instance)
else:
    # render_dashboard(db_instance)
    pass