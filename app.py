import streamlit as st
import pandas as pd
import pandas_ta as ta
import ccxt
import os
import numpy as np
from database.supabase import ZoraDatabase
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components
from datetime import datetime

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Zora Crypto Terminal",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. MOTOR DE ESCANEO OPTIMIZADO PARA COINBASE ---
def run_market_scan(user_config):
    """Escanea Coinbase usando el ADN personalizado del usuario"""
    try:
        rsi_limit = user_config.get('rsi_limit', 30)
        ema_period = user_config.get('ema_period', 200)
        min_vol = user_config.get('min_vol', 1000000)
        use_ema = user_config.get('use_ema', True)

        # Conexión a Coinbase (Data Pública)
        exchange = ccxt.coinbase()
        markets = exchange.load_markets()
        
        # Filtramos pares USD (Estándar de Coinbase)
        symbols = [s for s in markets.keys() if '/USD' in s and markets[s]['active']]
        
        # Priorizamos los top 50 pares por volumen para velocidad
        found_signals = []
        
        # Barra de progreso para feedback visual
        progress_bar = st.progress(0)
        
        for i, sym in enumerate(symbols[:50]):
            try:
                # Pedimos suficientes velas para los indicadores
                limit_needed = int(ema_period + 20) if use_ema else 50
                ohlcv = exchange.fetch_ohlcv(sym, timeframe='15m', limit=limit_needed)
                
                if len(ohlcv) < limit_needed:
                    continue

                df = pd.DataFrame(ohlcv, columns=['t', 'o', 'h', 'l', 'c', 'v'])
                
                # Indicadores Técnicos
                df['RSI'] = ta.rsi(df['c'], length=14)
                if use_ema:
                    df['EMA_DYN'] = ta.ema(df['c'], length=ema_period)
                
                last = df.iloc[-1]
                vol_usd = last['v'] * last['c'] # Estimación de volumen de la última vela

                # LÓGICA DE VALIDACIÓN (ADN)
                cond_rsi = last['RSI'] <= rsi_limit
                cond_vol = vol_usd >= (min_vol / 100) # Ajuste de volumen por timeframe
                cond_ema = (last['c'] > last['EMA_DYN']) if use_ema else True

                if cond_rsi and cond_ema:
                    found_signals.append({
                        'symbol': sym,
                        'rsi': round(last['RSI'], 2),
                        'price': last['c'],
                        'vol': f"${vol_usd:,.0f}",
                        'trend': "ALCISTA ✅" if (not use_ema or last['c'] > last['EMA_DYN']) else "N/A"
                    })
            except:
                continue
            progress_bar.progress((i + 1) / 50)
            
        progress_bar.empty()
        return found_signals
    except Exception as e:
        st.error(f"Error en el motor de escaneo: {e}")
        return []

# --- 3. COMPONENTES DE INTERFAZ (UI) ---
def apply_custom_ui():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
        .stApp { background-color: #05070a !important; }
        h1, h2, h3, p, span, label { color: #ffffff !important; font-family: 'Inter', sans-serif; }
        .block-container { padding-top: 4.5rem !important; }
        
        /* Botón Estilo Zora Gold */
        div.stButton > button {
            background: linear-gradient(135deg, #FFD700 0%, #b8860b 100%) !important;
            color: #000000 !important;
            border-radius: 12px !important;
            font-weight: 900 !important;
            height: 3.8rem !important;
            text-transform: uppercase;
            box-shadow: 0 4px 15px rgba(255, 215, 0, 0.3) !important;
            width: 100% !important;
        }
        
        /* Estilo de Tarjetas */
        .stAlert { background-color: #111827 !important; border: 1px solid #1f2937 !important; }
        </style>
    """, unsafe_allow_html=True)

    ticker_html = """
    <div style="position: fixed; top: 0; left: 0; width: 100%; z-index: 1001; height: 46px; background: #161b22; border-bottom: 1px solid #FFD700;">
        <iframe scrolling="no" src="https://s.tradingview.com/embed-widget/ticker-tape/?symbols%5B%5D%7B%22proName%22%3A%22COINBASE%3ABTCUSD%22%2C%22title%22%3A%22BTC%22%7D%2C%7B%22proName%22%3A%22COINBASE%3AETHUSD%22%2C%22title%22%3A%22ETH%22%7D&colorTheme=dark" width="100%" height="46" frameborder="0"></iframe>
    </div>
    """
    components.html(ticker_html, height=46)

def render_tv_chart(symbol):
    cleaned = symbol.replace("/", "").replace(" ", "")
    tv_html = f'<iframe src="https://s.tradingview.com/widgetembed/?symbol=COINBASE:{cleaned}&interval=15&theme=dark" width="100%" height="450" frameborder="0"></iframe>'
    components.html(tv_html, height=450)

# --- 4. DASHBOARD PRINCIPAL ---
def render_dashboard(db):
    apply_custom_ui()
    st_autorefresh(interval=60000, key="radar_refresh")
    u_id = st.session_state.user_id

    t_scan, t_jou, t_adn = st.tabs(["🛰️ RADAR SNIPER", "📝 DIARIO", "🧬 ADN"])

    with t_scan:
        st.markdown("<h3 style='color: #00ff88; margin-top:10px;'>VIGILANCIA EN TIEMPO REAL</h3>", unsafe_allow_html=True)
        
        conf = db.get_user_strategy(u_id)
        
        if st.button("🚀 INICIAR ESCANEO COINBASE"):
            with st.spinner("Filtrando mercado según tu ADN..."):
                results = run_market_scan(conf)
                st.session_state.radar_results = results

        data = st.session_state.get('radar_results', [])
        
        if not data:
            st.info(f"Radar en espera. Filtro actual: RSI < {conf.get('rsi_limit', 30)}")
        else:
            for s in data:
                with st.container(border=True):
                    c1, c2 = st.columns([2, 1])
                    with c1:
                        st.markdown(f"#### {s['symbol']} | <span style='color:#FFD700;'>RSI: {s['rsi']}</span>", unsafe_allow_html=True)
                        st.write(f"Precio: ${s['price']} | {s['trend']}")
                    with c2:
                        if st.button("EJECUTAR", key=f"btn_{s['symbol']}"):
                            db.save_trade(u_id, s['symbol'], "LONG", s['price'], 0, "Radar")
                            st.toast(f"Orden registrada: {s['symbol']}")
                    with st.expander("VER ANÁLISIS"):
                        render_tv_chart(s['symbol'])

    with t_jou:
        res = db.get_trade_history(u_id)
        if res.data:
            df = pd.DataFrame(res.data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No hay registros en el diario.")

    with t_adn:
        st.subheader("🧬 ADN Algorítmico")
        with st.form("adn_form_final"):
            col1, col2 = st.columns(2)
            with col1:
                rsi_limit = st.slider("Umbral RSI Sniper", 10, 60, int(conf.get('rsi_limit', 30)))
                ema_p = st.selectbox("Media Móvil (EMA)", [50, 100, 200], index=2)
            with col2:
                m_vol = st.number_input("Volumen Mínimo Diario (USD)", value=int(conf.get('min_vol', 1000000)))
                use_ema = st.toggle("Activar Filtro de Tendencia", value=conf.get('use_ema', True))
            
            if st.form_submit_button("GUARDAR Y SINCRONIZAR"):
                try:
                    db.supabase.table("strategies").upsert({
                        "user_id": u_id, "rsi_limit": rsi_limit, "ema_period": ema_p, 
                        "min_vol": m_vol, "use_ema": use_ema
                    }).execute()
                    st.success("ADN Actualizado Correctamente.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error de base de datos: {e}")

# --- 5. LÓGICA DE CONTROL ---
def main():
    db = ZoraDatabase()
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        apply_custom_ui()
        st.markdown("<h1 style='text-align:center; color:#FFD700; font-weight:900;'>ZORA CRYPTO</h1>", unsafe_allow_html=True)
        with st.form("login_box"):
            e = st.text_input("Email")
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("ACCEDER AL TERMINAL"):
                success, user = db.login_user(e, p)
                if success:
                    st.session_state.update({'logged_in': True, 'user_id': user.id})
                    st.rerun()
                else: st.error("Credenciales incorrectas.")
    else:
        render_dashboard(db)

if __name__ == "__main__":
    main()