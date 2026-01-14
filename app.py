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

# --- 2. UI: CSS DE APP NATIVA Y LANDING ---
def apply_custom_ui():
    css = """
    <style>
        /* Estética General Dark Mode */
        .stApp { background-color: #0b0e14 !important; }
        h1, h2, h3, p, span, label { color: #e6edf3 !important; font-family: 'Inter', sans-serif; }

        /* Ocultar elementos de Web */
        header, footer, #MainMenu { visibility: hidden; }
        .block-container { padding-top: 0rem !important; padding-bottom: 5rem !important; }

        /* Ticker Tape Animation */
        .ticker-wrapper {
            background: #161b22;
            padding: 10px 0;
            border-bottom: 1px solid #30363d;
            overflow: hidden;
            white-space: nowrap;
        }
        .ticker-text {
            display: inline-block;
            padding-left: 100%;
            animation: ticker 25s linear infinite;
            color: #FFD700;
            font-family: monospace;
            font-size: 0.9rem;
        }
        @keyframes ticker {
            0% { transform: translate3d(0, 0, 0); }
            100% { transform: translate3d(-100%, 0, 0); }
        }

        /* Signal Cards */
        .signal-card {
            background: #1f242c;
            border-radius: 15px;
            padding: 20px;
            border-left: 5px solid #FFD700;
            margin-bottom: 15px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.5);
        }

        /* Botones Pro */
        .stButton>button {
            border-radius: 12px !important;
            height: 3rem !important;
            font-weight: bold !important;
            border: none !important;
        }
        button[kind="primary"] { background-color: #FFD700 !important; color: #000 !important; }

        /* Radar Pulse */
        .radar-pulse {
            width: 10px; height: 10px; border-radius: 50%;
            background: #00ff88; box-shadow: 0 0 0 rgba(0,255,136, 0.4);
            animation: pulse 2s infinite; display: inline-block; margin-right: 8px;
        }
        @keyframes pulse { 0% { box-shadow: 0 0 0 0px rgba(0,255,136, 0.4); } 70% { box-shadow: 0 0 0 10px rgba(0,255,136, 0); } 100% { box-shadow: 0 0 0 0px rgba(0,255,136, 0); } }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
    
    # Ticker  HTML
    st.markdown("""
        <div class="ticker-wrapper">
            <div class="ticker-text">
                BTC/USD: $42,650.20 (+1.4%) &nbsp;&nbsp;&nbsp; ETH/USD: $2,541.10 (-0.2%) &nbsp;&nbsp;&nbsp; 
                SOL/USD: $94.50 (+5.1%) &nbsp;&nbsp;&nbsp; LINK/USD: $18.20 (+2.3%) &nbsp;&nbsp;&nbsp; 
                ZORA SENTINEL: SCANNING MARKET...
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- 3. WIDGET DE TRADINGVIEW ---
def render_tv_chart(symbol):
    cleaned_symbol = symbol.replace("/", "").replace("-", "")
    tv_html = f"""
    <div style="height:300px;">
        <iframe src="https://s.tradingview.com/widgetembed/?frameElementId=tradingview_76d0d&symbol=BINANCE:{cleaned_symbol}&interval=15&hidesidetoolbar=1&symboledit=1&saveimage=1&toolbarbg=f1f3f6&studies=[]&theme=dark&style=1&timezone=Etc%2FUTC&studies_overrides=%7B%7D&overrides=%7B%7D&enabled_features=[]&disabled_features=[]&locale=es" 
        width="100%" height="300" frameborder="0" allowtransparency="true" scrolling="no" allowfullscreen></iframe>
    </div>
    """
    components.html(tv_html, height=300)

# --- 4. LÓGICA DE SESIÓN ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user_id': None, 'user_email': None})

def render_login(db):
    apply_custom_ui()
    st.markdown("<h1 style='text-align: center; margin-top: 50px;'>🛡️ ZORA SENTINEL</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #8b949e;'>Algorithmic Sniper Terminal</p>", unsafe_allow_html=True)
    
    _, col, _ = st.columns([1, 2, 1])
    with col:
        with st.container(border=True):
            e = st.text_input("Email")
            p = st.text_input("Password", type="password")
            if st.button("ACCEDER AL TERMINAL", use_container_width=True, type="primary"):
                success, user = db.login_user(e, p)
                if success:
                    st.session_state.update({'logged_in': True, 'user_id': user.id, 'user_email': user.email})
                    st.rerun()

def render_dashboard(db):
    apply_custom_ui()
    st_autorefresh(interval=30000, key="global_refresh")
    u_id = st.session_state.user_id

    # Header con Radar
    st.markdown(f'<p><span class="radar-pulse"></span> Sistema Activo: {st.session_state.user_email}</p>', unsafe_allow_html=True)

    t_scan, t_jou, t_adn = st.tabs(["🛰️ SCANNER", "📝 JOURNAL", "🧬 ADN"])

    with t_scan:
        signals = db.supabase.table("signals_today").select("*").eq("user_id", u_id).execute()
        
        if not signals.data:
            st.info("Esperando confirmación de indicadores...")
        else:
            for s in signals.data:
                # Signal Card
                st.markdown(f"""
                <div class="signal-card">
                    <div style="display: flex; justify-content: space-between;">
                        <span style="font-size: 22px; font-weight: bold;">{s['symbol']}</span>
                        <span style="color: #00ff88; font-weight: bold;">RSI: {s['rsi']}</span>
                    </div>
                    <p style="color: #8b949e; font-size: 14px; margin-bottom: 10px;">Entrada Detectada: ${s['entry_price']:,}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Gráfico de TradingView colapsable
                with st.expander("Ver Gráfico en Vivo"):
                    render_tv_chart(s['symbol'])
                
                if st.button(f"EJECUTAR TRADE {s['symbol']}", key=f"go_{s['symbol']}", type="primary", use_container_width=True):
                    db.save_trade(u_id, s['symbol'], "LONG", s['entry_price'], 0, "Signal")
                    st.toast(f"Trade {s['symbol']} abierto.")

    with t_jou:
        res = db.get_trade_history(u_id)
        if res.data:
            df = pd.DataFrame(res.data)
            
            # Métricas Pro
            closed = df[df['status'] == 'CLOSED']
            pnl = closed['profit'].sum() if not closed.empty else 0.0
            
            c1, c2 = st.columns(2)
            c1.metric("PnL Acumulado", f"${pnl:,.2f}", delta=f"{pnl:.2f}")
            c2.metric("Trades Abiertos", len(df[df['status'] == 'OPEN']))

            st.divider()

            for _, trade in df.iterrows():
                with st.container(border=True):
                    col_info, col_btn = st.columns([3, 1])
                    with col_info:
                        st.write(f"**{trade['symbol']}**")
                        if trade['status'] == 'OPEN':
                            st.caption(f"Entrada: ${trade['entry_price']:,} 🟢")
                        else:
                            color = "green" if trade['profit'] > 0 else "red"
                            st.markdown(f"Profit: :{color}[${trade['profit']:,.2f}]")
                    
                    with col_btn:
                        if trade['status'] == 'OPEN':
                            if st.button("CERRAR", key=f"cl_{trade['id']}", use_container_width=True):
                                st.session_state.update({'closing_id': trade['id'], 'entry_p': trade['entry_price']})
                                st.rerun()

            if 'closing_id' in st.session_state:
                with st.form("close_form"):
                    exit_p = st.number_input("Precio de Salida", format="%.4f")
                    if st.form_submit_button("CONFIRMAR CIERRE", type="primary"):
                        profit = exit_p - st.session_state.entry_p
                        db.supabase.table("journal").update({"exit_price": exit_p, "status": "CLOSED", "profit": profit}).eq("id", st.session_state.closing_id).execute()
                        del st.session_state['closing_id']
                        st.rerun()

    with t_adn:
        st.subheader("Configuración de ADN")
        conf = db.get_user_strategy(u_id)
        with st.form("adn"):
            rsi = st.slider("Límite RSI (Sobrevendido)", 10, 40, int(conf.get('rsi_limit', 25)))
            if st.form_submit_button("ACTUALIZAR ESTRATEGIA", type="primary"):
                db.supabase.table("strategies").upsert({"user_id": u_id, "rsi_limit": rsi}).execute()
                st.success("ADN Sincronizado.")

db_instance = ZoraDatabase()
if not st.session_state.logged_in:
    render_login(db_instance)
else:
    render_dashboard(db_instance)