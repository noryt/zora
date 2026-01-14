import streamlit as st
import pandas as pd
from database.supabase import ZoraDatabase
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components
from datetime import datetime

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Zora Sentinel",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. UI: CSS MOBILE-FIRST REFORZADO ---
def apply_custom_ui():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
        
        /* Reset y Fondo */
        .stApp { background-color: #05070a !important; }
        h1, h2, h3, p, span, label { color: #ffffff !important; font-family: 'Inter', sans-serif; }

        /* Contenedor Responsivo (Optimizado para Móvil) */
        .block-container {
            padding-top: 4.5rem !important;
            padding-left: 0.8rem !important;
            padding-right: 0.8rem !important;
            max-width: 100% !important;
        }
        
        /* EL NUEVO BOTÓN ZORA PREMUM */
        div.stButton > button, .stFormSubmitButton > button {
            background: linear-gradient(135deg, #FFD700 0%, #b8860b 100%) !important;
            color: #000000 !important;
            border: 1px solid rgba(0,0,0,0.1) !important;
            border-radius: 16px !important; /* Más redondeado y moderno */
            height: 4.2rem !important;
            font-weight: 900 !important;
            font-size: 1.1rem !important;
            letter-spacing: 1px !important;
            text-transform: uppercase;
            width: 100% !important;
            
            /* Efecto de Elevación y Brillo */
            box-shadow: 0 4px 15px rgba(255, 215, 0, 0.3), 
                        inset 0 2px 2px rgba(255,255,255,0.5) !important;
            transition: all 0.2s ease-in-out !important;
        }

        /* Efecto al pasar el mouse (PC) */
        div.stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(255, 215, 0, 0.5) !important;
            filter: brightness(1.1);
        }

        /* Efecto al presionar (Móvil y PC) */
        div.stButton > button:active {
            transform: translateY(1px) !important;
            box-shadow: 0 2px 10px rgba(255, 215, 0, 0.2) !important;
            background: linear-gradient(135deg, #b8860b 0%, #FFD700 100%) !important;
        }

        /* Forzar color de texto negro en todo momento */
        div.stButton > button p {
            color: #000000 !important;
            font-weight: 900 !important;
        }
        /* 2. DISEÑO RESPONSIVO DE COLUMNAS (Apilado Vertical) */
        @media (max-width: 768px) {
            div[data-testid="column"] {
                width: 100% !important;
                flex: 1 1 100% !important;
                min-width: 100% !important;
                margin-bottom: 12px !important;
            }
            h1 { font-size: 2.2rem !important; }
        }

        /* Tarjetas Informativas (Landing) */
        .feature-card {
            background: #111827;
            padding: 22px;
            border-radius: 15px;
            border: 1px solid #1f2937;
            text-align: center;
            height: 100%;
        }
        .feature-card h3 { color: #FFD700 !important; font-size: 1.1rem !important; margin-bottom: 12px; }
        .feature-card p { font-size: 0.85rem !important; color: #94a3b8 !important; line-height: 1.5; }

        /* Botones Zora (Gigantes para Tocar en Móvil) */
        div.stButton > button, .stFormSubmitButton > button {
            background-color: #FFD700 !important;
            color: #000000 !important;
            border: none !important;
            border-radius: 14px !important;
            height: 4rem !important;
            font-weight: 900 !important;
            font-size: 1.1rem !important;
            text-transform: uppercase;
            width: 100% !important;
            box-shadow: 0 4px 15px rgba(255, 215, 0, 0.2) !important;
        }
        div.stButton > button p { color: #000000 !important; font-weight: 900 !important; }

        /* Pestañas (Tabs) Estilo App Nativa */
        div[data-testid="stTabs"] [data-baseweb="tab-list"] {
            background-color: #161b22 !important;
            padding: 6px !important;
            border-radius: 14px !important;
            gap: 8px !important;
        }
        div[data-testid="stTabs"] button {
            flex: 1 !important;
            height: 60px !important;
            font-size: 0.9rem !important;
            font-weight: 700 !important;
            color: #8b949e !important;
            background-color: transparent !important;
            border: none !important;
        }
        div[data-testid="stTabs"] button[aria-selected="true"] {
            color: #FFD700 !important;
            border-bottom: 4px solid #FFD700 !important;
        }

        /* Blindaje Anti-Blanco (Toast, Expander, Details) */
        div[data-testid="stToast"] { background-color: #111827 !important; border: 1px solid #FFD700 !important; }
        div[data-testid="stExpander"], details { 
            background-color: #111827 !important; 
            border: 1px solid #1f2937 !important; 
            border-radius: 12px !important; 
        }
        summary { color: #FFD700 !important; font-weight: bold !important; padding: 12px !important; }

        header, footer, #MainMenu { visibility: hidden; }
        </style>
    """, unsafe_allow_html=True)

    # Ticker Tape Real de Coinbase (Z-Index alto para flotar)
    ticker_html = """
    <div style="position: fixed; top: 0; left: 0; width: 100%; z-index: 1001; height: 46px; background: #161b22;">
        <iframe scrolling="no" allowtransparency="true" frameborder="0" 
            src="https://s.tradingview.com/embed-widget/ticker-tape/?symbols%5B%5D%7B%22proName%22%3A%22COINBASE%3ABTCUSD%22%2C%22title%22%3A%22BTC%22%7D%2C%7B%22proName%22%3A%22COINBASE%3AETHUSD%22%2C%22title%22%3A%22ETH%22%7D%2C%7B%22proName%22%3A%22COINBASE%3ASOLUSD%22%2C%22title%22%3A%22SOL%22%7D&colorTheme=dark&isTransparent=false&displayMode=adaptive&locale=es" 
            width="100%" height="46">
        </iframe>
    </div>
    """
    components.html(ticker_html, height=46)

# --- 3. GRÁFICOS COINBASE ---
def render_tv_chart(symbol):
    cleaned = symbol.upper().replace("/", "").replace("-", "").replace(" ", "")
    tv_symbol = f"COINBASE:{cleaned}"
    tv_html = f'<iframe src="https://s.tradingview.com/widgetembed/?symbol={tv_symbol}&interval=15&theme=dark" width="100%" height="400" frameborder="0"></iframe>'
    components.html(tv_html, height=400)

# --- 4. RENDER LANDING PAGE ---
def render_auth(db):
    apply_custom_ui()
    st.markdown("<h1 style='text-align: center; color: #FFD700; font-weight: 900; margin-bottom: 30px;'>ZORA SENTINEL</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="feature-card"><h3>🛰️ SCANNER</h3><p>Vigilancia en tiempo real que identifica confluencias técnicas exactas y niveles de sobreventa.</p></div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="feature-card"><h3>🧬 CONFIGURACIÓN</h3><p>Cerebro algorítmico donde defines niveles de RSI y volumen para personalizar tu estrategia.</p></div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="feature-card"><h3>📝 EXPORT</h3><p>Auditoría de datos para descargar tu historial en CSV/Excel y analizar tu PnL fuera de la nube.</p></div>', unsafe_allow_html=True)

    st.write("")
    _, auth_box, _ = st.columns([0.02, 1, 0.02])
    with auth_box:
        t1, t2 = st.tabs(["🔑 ACCESO", "✨ REGISTRO"])
        with t1:
            with st.form("login_form"):
                e = st.text_input("Email")
                p = st.text_input("Contraseña", type="password")
                if st.form_submit_button("ENTRAR AL TERMINAL"):
                    if e and p:
                        success, user = db.login_user(e, p)
                        if success:
                            st.session_state.update({'logged_in': True, 'user_id': user.id, 'user_email': user.email})
                            st.rerun()
                        else: st.error("Credenciales incorrectas.")
        with t2:
            with st.form("reg_form"):
                ne = st.text_input("Nuevo Email")
                np = st.text_input("Nueva Contraseña", type="password")
                if st.form_submit_button("CREAR CUENTA"):
                    try:
                        db.supabase.auth.sign_up({"email": ne, "password": np})
                        st.success("Verifica tu email para activar.")
                    except Exception as ex: st.error(f"Error: {ex}")

# --- 5. RENDER DASHBOARD ---
def render_dashboard(db):
    apply_custom_ui()
    st_autorefresh(interval=30000, key="ref_dash")
    u_id = st.session_state.user_id

    if st.sidebar.button("Cerrar Sesión", type="primary"):
        st.session_state.logged_in = False
        st.rerun()

    t_scan, t_jou, t_adn = st.tabs(["🛰️ RADAR", "📝 DIARIO", "🧬 ADN"])

    with t_scan:
        st.markdown("""
            <div style="display: flex; align-items: center; gap: 10px; margin: 10px 0;">
                <div style="width: 12px; height: 12px; background-color: #00ff88; border-radius: 50%; box-shadow: 0 0 10px #00ff88;"></div>
                <span style="color: #00ff88; font-weight: bold; font-size: 0.9rem;">SISTEMA ACTIVO - COINBASE LIVE</span>
            </div>
        """, unsafe_allow_html=True)
        
        signals = db.supabase.table("signals_today").select("*").eq("user_id", u_id).execute()
        if not signals.data:
            st.info("Esperando señales que cumplan tu ADN...")
        else:
            for s in signals.data:
                with st.container(border=True):
                    st.markdown(f"#### {s['symbol']} | RSI: <span style='color:#FFD700'>{s['rsi']}</span>", unsafe_allow_html=True)
                    with st.expander("📊 VER GRÁFICO REALTIME"):
                        render_tv_chart(s['symbol'])
                    if st.button(f"EJECUTAR {s['symbol']}", key=f"g_{s['symbol']}", type="primary"):
                        db.save_trade(u_id, s['symbol'], "LONG", s['entry_price'], 0, "Signal")
                        st.toast(f"Trade {s['symbol']} iniciado", icon='🛡️')

    with t_jou:
        res = db.get_trade_history(u_id)
        if res.data:
            df = pd.DataFrame(res.data)
            pnl = df[df['status'] == 'CLOSED']['profit'].sum() if not df.empty else 0
            
            # 1. Dashboard de PnL
            st.markdown(f'<div style="background:#111827; padding:20px; border-radius:15px; border:2px solid #FFD700; text-align:center;"><p style="margin:0; color:#8b949e;">PNL TOTAL ACUMULADO</p><h1 style="color:{"#00ff88" if pnl >= 0 else "#ff4b4b"}; margin:0; font-size:2.5rem;">${pnl:,.2f}</h1></div>', unsafe_allow_html=True)
            
            # 2. LÓGICA DE CIERRE (FORMULARIO DINÁMICO)
            if 'closing_id' in st.session_state:
                with st.container(border=True):
                    st.warning(f"🛡️ FINALIZAR OPERACIÓN")
                    exit_price = st.number_input("Precio de Salida (Coinbase)", value=float(st.session_state.entry_p))
                    
                    c_col1, c_col2 = st.columns(2)
                    if c_col1.button("CONFIRMAR CIERRE", type="primary"):
                        try:
                            # 1. Aseguramos que los números sean float puros y la fecha sea ISO
                            final_profit = float(exit_price) - float(st.session_state.entry_p)
                            ahora = datetime.now().isoformat()

                            # 2. Ejecutamos la actualización
                            db.supabase.table("journal").update({
                                "exit_price": float(exit_price),
                                "status": "CLOSED",
                                "profit": float(final_profit),
                                "created_at": ahora
                            }).eq("id", st.session_state.closing_id).execute()
                            
                            # 3. Limpieza de estado exitosa
                            del st.session_state['closing_id']
                            st.toast("Trade Cerrado", icon="✅")
                            st.rerun()

                        except Exception as e:
                            # Esto te dirá exactamente qué columna está fallando
                            st.error(f"Error de Base de Datos: {str(e)}")
                        
                    if c_col2.button("CANCELAR"):
                        del st.session_state['closing_id']
                        st.rerun()
                st.divider()

            # 3. LISTA DE TRADES
            st.write("")
            st.download_button("📥 EXPORTAR CSV", df.to_csv(index=False), "trades.csv", "text/csv", use_container_width=True)
            
            for _, trade in df.sort_values('created_at', ascending=False).iterrows():
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.write(f"**{trade['symbol']}**")
                        st.caption(f"ENTRADA: ${trade['entry_price']} | {trade['status']}")
                    with c2:
                        if trade['status'] == 'OPEN':
                            # Al hacer click, guardamos los datos en session_state para activar el form de arriba
                            if st.button("CERRAR", key=f"btn_close_{trade['id']}", type="primary"):
                                st.session_state.closing_id = trade['id']
                                st.session_state.entry_p = trade['entry_price']
                                st.rerun()
                        else:
                            clr = "#00ff88" if trade['profit'] > 0 else "#ff4b4b"
                            st.markdown(f"<p style='color:{clr}; font-weight:bold; text-align:right; margin:0;'>${trade['profit']:,.2f}</p>", unsafe_allow_html=True)
        else:
            st.info("No hay registros en el diario.")

    with t_adn:
        conf = db.get_user_strategy(u_id)
        with st.form("adn_form"):
            rsi_val = st.slider("RSI Umbral Sniper", 10, 50, int(conf.get('rsi_limit', 30)))
            if st.form_submit_button("GUARDAR ADN"):
                db.supabase.table("strategies").upsert({"user_id": u_id, "rsi_limit": rsi_val}).execute()
                st.success("Estrategia sincronizada.")

# --- 6. LÓGICA DE CONTROL ---
db_instance = ZoraDatabase()
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    render_auth(db_instance)
else:
    render_dashboard(db_instance)