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
    page_title="Zora Crypto Premium",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. MOTOR DE ESCANEO (LÓGICA CORE) ---
def run_market_scan(rsi_limit):
    """Escanea Coinbase buscando RSI bajo y precio sobre EMA 200 (Tendencia alcista)"""
    try:
        exchange = ccxt.coinbase()
        markets = exchange.load_markets()
        # Filtramos solo pares en USD activos
        symbols = [s for s in markets.keys() if '/USD' in s and markets[s]['active']]
        
        found_signals = []
        # Escaneamos los top 40 para mantener velocidad en Streamlit
        for sym in symbols[:40]:
            try:
                ohlcv = exchange.fetch_ohlcv(sym, timeframe='15m', limit=210)
                df = pd.DataFrame(ohlcv, columns=['t', 'o', 'h', 'l', 'c', 'v'])
                
                # Indicadores
                df['RSI'] = ta.rsi(df['c'], length=14)
                df['EMA200'] = ta.ema(df['c'], length=200)
                
                last_price = df['c'].iloc[-1]
                last_rsi = df['RSI'].iloc[-1]
                last_ema = df['EMA200'].iloc[-1]

                # LÓGICA SNIPER: RSI bajo Y Precio sobre EMA 200 (Filtro de Tendencia)
                if last_rsi <= rsi_limit and last_price > last_ema:
                    found_signals.append({
                        'symbol': sym,
                        'rsi': round(last_rsi, 2),
                        'price': last_price,
                        'trend': "ALCISTA ✅"
                    })
            except: continue
        return found_signals
    except Exception as e:
        st.error(f"Error en Scanner: {e}")
        return []

# --- 3. UI: CSS Y COMPONENTES ---
def apply_custom_ui():
    st.markdown("""
        <style>
        .stApp { background-color: #05070a !important; }
        h1, h2, h3, p, span { color: #ffffff !important; font-family: 'Inter', sans-serif; }
        .block-container { padding-top: 4rem !important; }
        
        /* Botón Zora Estilo Dorado */
        div.stButton > button {
            background: linear-gradient(135deg, #FFD700 0%, #b8860b 100%) !important;
            color: #000000 !important;
            border-radius: 12px !important;
            font-weight: 900 !important;
            text-transform: uppercase;
            width: 100% !important;
            height: 3.5rem !important;
            box-shadow: 0 4px 15px rgba(255, 215, 0, 0.3) !important;
        }

        /* Tarjetas de Señal */
        .signal-card {
            background: #111827;
            padding: 15px;
            border-radius: 12px;
            border: 1px solid #1f2937;
            margin-bottom: 10px;
        }
        </style>
    """, unsafe_allow_html=True)

    ticker_html = """
    <div style="position: fixed; top: 0; left: 0; width: 100%; z-index: 1001; height: 40px; background: #161b22;">
        <iframe scrolling="no" frameborder="0" src="https://s.tradingview.com/embed-widget/ticker-tape/?symbols%5B%5D%7B%22proName%22%3A%22COINBASE%3ABTCUSD%22%2C%22title%22%3A%22BTC%22%7D%2C%7B%22proName%22%3A%22COINBASE%3AETHUSD%22%2C%22title%22%3A%22ETH%22%7D&colorTheme=dark" width="100%" height="40"></iframe>
    </div>
    """
    components.html(ticker_html, height=40)

def render_tv_chart(symbol):
    cleaned = symbol.replace("/", "").replace(" ", "")
    tv_html = f'<iframe src="https://s.tradingview.com/widgetembed/?symbol=COINBASE:{cleaned}&interval=15&theme=dark" width="100%" height="450" frameborder="0"></iframe>'
    components.html(tv_html, height=450)

# --- 4. RENDER DASHBOARD PRINCIPAL ---
def render_dashboard(db):
    apply_custom_ui()
    st_autorefresh(interval=60000, key="global_ref")
    u_id = st.session_state.user_id

    t_scan, t_jou, t_adn = st.tabs(["🛰️ RADAR SNIPER", "📝 DIARIO", "🧬 ADN"])

    with t_scan:
        st.markdown("<h3 style='color: #00ff88;'>SISTEMA DE CONFLUENCIA ACTIVO</h3>", unsafe_allow_html=True)
        
        conf = db.get_user_strategy(u_id)
        rsi_limit = int(conf.get('rsi_limit', 30))

        if st.button("🚀 INICIAR ESCANEO DE MERCADO"):
            with st.spinner("Filtrando tendencia y RSI..."):
                signals = run_market_scan(rsi_limit)
                st.session_state.last_radar = signals

        data = st.session_state.get('last_radar', [])
        
        if not data:
            st.info(f"Radar listo. Buscando RSI < {rsi_limit} a favor de EMA 200.")
        else:
            for s in data:
                with st.container(border=True):
                    c1, c2 = st.columns([2, 1])
                    with c1:
                        st.markdown(f"### {s['symbol']}")
                        st.write(f"RSI: **{s['rsi']}** | Tendencia: **{s['trend']}**")
                    with c2:
                        if st.button("EJECUTAR", key=f"ex_{s['symbol']}"):
                            db.save_trade(u_id, s['symbol'], "LONG", s['price'], 0, "Algo Signal")
                            st.toast(f"Orden enviada: {s['symbol']}")
                    
                    with st.expander("VER ANÁLISIS"):
                        render_tv_chart(s['symbol'])

    with t_jou:
        # Lógica de historial y PnL (Mantiene tu código original de Journal)
        res = db.get_trade_history(u_id)
        if res.data:
            df = pd.DataFrame(res.data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Diario vacío.")

    with t_adn:
        st.subheader("Configuración de Cerebro")
        with st.form("adn_form"):
            new_rsi = st.slider("Umbral RSI", 10, 50, rsi_limit)
            if st.form_submit_button("ACTUALIZAR ESTRATEGIA"):
                db.supabase.table("strategies").upsert({"user_id": u_id, "rsi_limit": new_rsi}).execute()
                st.success("ADN Sincronizado.")

# --- 5. CONTROL DE ACCESO Y MAIN ---
def main():
    db = ZoraDatabase()
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        # Aquí iría tu función render_auth original
        apply_custom_ui()
        st.title("ZORA CRYPTO")
        with st.form("login"):
            e = st.text_input("Email")
            p = st.text_input("Pass", type="password")
            if st.form_submit_button("ENTRAR"):
                success, user = db.login_user(e, p)
                if success:
                    st.session_state.update({'logged_in': True, 'user_id': user.id})
                    st.rerun()
    else:
        render_dashboard(db)

if __name__ == "__main__":
    main()