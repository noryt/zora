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

# --- 2. MOTOR DE ESCANEO Y RECOMENDACIÓN (CEREBRO) ---
def run_market_scan(user_config):
    """Escanea Coinbase y otorga un Score de inversión basado en el ADN"""
    try:
        rsi_limit = user_config.get('rsi_limit', 30)
        ema_period = user_config.get('ema_period', 200)
        use_ema = user_config.get('use_ema', True)

        # Conexión a Coinbase
        exchange = ccxt.coinbase()
        markets = exchange.load_markets()
        
        # Definición de símbolos (Solución al NameError)
        symbols = [s for s in markets.keys() if '/USD' in s and markets[s]['active']]
        
        found_signals = []
        progress_bar = st.progress(0)
        
        # Analizamos los top 40 pares para optimizar velocidad
        for i, sym in enumerate(symbols[:40]):
            try:
                limit_needed = int(ema_period * 1.2) if use_ema else 50
                ohlcv = exchange.fetch_ohlcv(sym, timeframe='15m', limit=limit_needed)
                
                if len(ohlcv) < 30: continue

                df = pd.DataFrame(ohlcv, columns=['t', 'o', 'h', 'l', 'c', 'v'])
                
                # Indicadores Técnicos
                df['RSI'] = ta.rsi(df['c'], length=14)
                df['EMA200'] = ta.ema(df['c'], length=200)
                
                last = df.iloc[-1]
                prev = df.iloc[-2]

                # --- SISTEMA DE SCORE DE INVERSIÓN (0-100) ---
                score = 0
                # Regla 1: RSI bajo (Hasta 40 pts)
                if last['RSI'] <= rsi_limit: score += 40
                elif last['RSI'] <= 45: score += 20
                
                # Regla 2: Tendencia Alcista (Hasta 30 pts)
                if last['c'] > last['EMA200']: score += 30
                
                # Regla 3: Volumen Creciente (Hasta 30 pts)
                if last['v'] > prev['v']: score += 30

                # Filtrar solo oportunidades reales (Score >= 50)
                if score >= 50:
                    found_signals.append({
                        'symbol': sym,
                        'score': score,
                        'confidence': "ALTA 💎" if score >= 80 else "MEDIA ⚖️",
                        'price': last['c'],
                        'rsi': round(last['RSI'], 2),
                        'action': "COMPRAR" if score >= 80 else "OBSERVAR"
                    })
            except: continue
            progress_bar.progress((i + 1) / 40)
            
        progress_bar.empty()
        return found_signals
    except Exception as e:
        st.error(f"Error en el motor: {e}")
        return []

# --- 3. UI: CSS Y COMPONENTES ---
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
            height: 3.5rem !important;
            text-transform: uppercase;
            box-shadow: 0 4px 15px rgba(255, 215, 0, 0.3) !important;
            width: 100% !important;
        }
        div.stButton > button p { color: #000000 !important; }
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
    tv_html = f'<iframe src="https://s.tradingview.com/widgetembed/?symbol=COINBASE:{cleaned}&interval=15&theme=dark" width="100%" height="400" frameborder="0"></iframe>'
    components.html(tv_html, height=400)

# --- 4. RENDER DASHBOARD ---
def render_dashboard(db):
    apply_custom_ui()
    st_autorefresh(interval=60000, key="refresh_sync")
    u_id = st.session_state.user_id

    t_scan, t_jou, t_adn = st.tabs(["🛰️ RADAR", "📝 DIARIO", "🧬 ADN"])

    with t_scan:
        st.markdown("<h3 style='color: #00ff88; margin-top:10px;'>RECOMENDACIONES DE INVERSIÓN</h3>", unsafe_allow_html=True)
        conf = db.get_user_strategy(u_id)
        
        if st.button("🚀 ANALIZAR OPORTUNIDADES", width="stretch"):
            with st.spinner("Escaneando confluencias Sniper..."):
                results = run_market_scan(conf)
                st.session_state.radar_results = results

        data = st.session_state.get('radar_results', [])
        if not data:
            st.info(f"Radar listo. Escaneando activos con RSI < {conf.get('rsi_limit', 30)}")
        else:
            for s in data:
                with st.container(border=True):
                    c1, c2 = st.columns([2, 1])
                    with c1:
                        st.markdown(f"#### {s['symbol']} | Score: <span style='color:#FFD700;'>{s['score']}</span>", unsafe_allow_html=True)
                        st.write(f"Confianza: **{s['confidence']}** | RSI: **{s['rsi']}**")
                    with c2:
                        label = f"{s['action']} {s['symbol']}"
                        if st.button(label, key=f"btn_{s['symbol']}", width="stretch"):
                            db.save_trade(u_id, s['symbol'], "LONG", s['price'], 0, "Radar Signal")
                            st.toast(f"Orden de {s['action']} registrada", icon='🛡️')
                    with st.expander("📊 VER GRÁFICO REALTIME"):
                        render_tv_chart(s['symbol'])

    with t_jou:
        res = db.get_trade_history(u_id)
        if res.data:
            df = pd.DataFrame(res.data)
            st.dataframe(df, width="stretch")
        else:
            st.info("No hay trades en el historial.")

    with t_adn:
        st.subheader("🧬 Configuración de ADN")
        with st.form("adn_form_final"):
            rsi_limit = st.slider("Umbral RSI Sniper", 10, 60, int(conf.get('rsi_limit', 30)))
            if st.form_submit_button("GUARDAR ADN", width="stretch"):
                db.supabase.table("strategies").upsert({
                    "user_id": u_id, "rsi_limit": rsi_limit
                }).execute()
                st.success("ADN Sincronizado.")
                st.rerun()

# --- 5. LÓGICA DE CONTROL ---
def main():
    db = ZoraDatabase()
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        apply_custom_ui()
        st.markdown("<h1 style='text-align:center; color:#FFD700;'>ZORA CRYPTO</h1>", unsafe_allow_html=True)
        with st.form("login_ui"):
            e = st.text_input("Email")
            p = st.text_input("Pass", type="password")
            if st.form_submit_button("ACCEDER", width="stretch"):
                success, user = db.login_user(e, p)
                if success:
                    st.session_state.update({'logged_in': True, 'user_id': user.id})
                    st.rerun()
                else: st.error("Error de acceso.")
    else:
        render_dashboard(db)

if __name__ == "__main__":
    main()