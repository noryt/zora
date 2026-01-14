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

# --- 2. UI: CSS DE ALTO CONTRASTE ---
def apply_custom_ui():
    css = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');

        /* Fondo base ultra oscuro para resaltar elementos */
        .stApp { background-color: #05070a !important; }
        
        /* Texto principal en blanco puro para máximo contraste */
        h1, h2, h3, p, span, label { color: #ffffff !important; font-family: 'Inter', sans-serif; }
        
        /* Subtextos en gris claro para jerarquía visual */
        .stMarkdown p, .stCaption { color: #cbd5e0 !important; }

        /* BOTÓN AMARILLO: Texto Negro profundo y fondo brillante */
        button[kind="primary"] {
            background-color: #FFD700 !important;
            color: #000000 !important;
            border: none !important;
            border-radius: 8px !important;
            height: 3.5rem !important;
            font-weight: 900 !important;
            font-size: 1.1rem !important;
            text-transform: uppercase;
            width: 100%;
            cursor: pointer;
        }
        
        /* Hover del botón para feedback visual */
        button[kind="primary"]:hover {
            background-color: #ffffff !important;
            color: #000000 !important;
            box-shadow: 0px 0px 15px rgba(255, 215, 0, 0.4);
        }

        /* Inputs con bordes visibles para evitar problemas de contraste */
        .stTextInput input {
            background-color: #1a202c !important;
            color: #ffffff !important;
            border: 1px solid #4a5568 !important;
            border-radius: 8px !important;
        }
        .stTextInput input:focus {
            border-color: #FFD700 !important;
        }

        /* Estilo de las cajas de información */
        .feature-box {
            background: #111827;
            padding: 24px;
            border-radius: 12px;
            border: 1px solid #1f2937;
            text-align: center;
            height: 100%;
        }

        /* Ocultar basura de Streamlit */
        header, footer, #MainMenu { visibility: hidden; }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# --- 3. LOGICA DE REGISTRO Y LOGIN ---
def render_auth_section(db):
    apply_custom_ui()
    
    st.markdown("<h1 style='text-align: center; margin-top: 20px; color: #FFD700; font-size: 3rem;'>ZORA SENTINEL</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.2rem;'>El radar definitivo para traders de precisión.</p>", unsafe_allow_html=True)

    st.write("---")

    # Features informativas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="feature-box"><h3>🛰️</h3><b>Escaneo Real-Time</b><p>Monitoreo constante de indicadores técnicos en +200 pares.</p></div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="feature-box"><h3>⚡</h3><b>Alertas Sniper</b><p>Entradas basadas en confluencia de RSI y Bandas de Bollinger.</p></div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="feature-box"><h3>📊</h3><b>Gestión Total</b><p>Lleva un diario detallado y analiza tu Win Rate automáticamente.</p></div>', unsafe_allow_html=True)

    st.write("---")

    # Tabs de Login y Registro
    _, auth_col, _ = st.columns([1, 2, 1])
    with auth_col:
        tab_login, tab_register = st.tabs(["🔑 ENTRAR AL TERMINAL", "✨ CREAR CUENTA NUEVA"])
        
        with tab_login:
            email_log = st.text_input("Email", key="login_email")
            pass_log = st.text_input("Contraseña", type="password", key="login_pass")
            if st.button("INICIAR SESIÓN", type="primary", key="btn_login"):
                success, user = db.login_user(email_log, pass_log)
                if success:
                    st.session_state.update({'logged_in': True, 'user_id': user.id, 'user_email': user.email})
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")

        with tab_register:
            st.markdown("<p style='color: #FFD700;'>Únete a la red de Zora Sentinel</p>", unsafe_allow_html=True)
            new_email = st.text_input("Tu mejor Email", key="reg_email")
            new_pass = st.text_input("Crea una Contraseña segura", type="password", key="reg_pass")
            confirm_pass = st.text_input("Confirma tu Contraseña", type="password", key="reg_confirm")
            
            if st.button("REGISTRARME AHORA", type="primary", key="btn_reg"):
                if new_pass != confirm_pass:
                    st.warning("Las contraseñas no coinciden.")
                elif len(new_pass) < 6:
                    st.warning("La contraseña debe tener al menos 6 caracteres.")
                else:
                    # Lógica de registro en Supabase
                    try:
                        res = db.supabase.auth.sign_up({"email": new_email, "password": new_pass})
                        st.success("¡Cuenta creada! Revisa tu email para confirmar el registro.")
                    except Exception as e:
                        st.error(f"Error al registrar: {e}")

# --- 4. DASHBOARD (SOLO SI ESTÁ LOGUEADO) ---
def render_dashboard(db):
    apply_custom_ui()
    st_autorefresh(interval=30000, key="refresh")
    # ... (Resto del código del Dashboard: Scanner, Journal, ADN) ...
    st.title("🛰️ Panel de Control")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.logged_in = False
        st.rerun()

# --- EJECUCIÓN ---
db_instance = ZoraDatabase()

if not st.session_state.get('logged_in'):
    render_auth_section(db_instance)
else:
    render_dashboard(db_instance)