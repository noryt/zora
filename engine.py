import os
import pandas as pd
from supabase import create_client
from coinbase.rest import RESTClient

def get_engine():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    api_key = os.environ.get("CB_API_KEY")
    api_secret = os.environ.get("CB_API_SECRET")
    
    supabase = create_client(url, key)
    client = RESTClient(api_key=api_key, api_secret=api_secret)
    return supabase, client

def calculate_indicators(df):
    # EMA 200
    df['ema200'] = df['close'].ewm(span=200, adjust=False).mean()
    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    # Bollinger Bands
    df['ma20'] = df['close'].rolling(window=20).mean()
    df['std'] = df['close'].rolling(window=20).std()
    df['upper'] = df['ma20'] + (2.5 * df['std'])
    df['lower'] = df['ma20'] - (2.5 * df['std'])
    return df

def run_scan():
    db, cb = get_engine()
    print("🚀 Iniciando escaneo...")
    
    users = db.table("strategies").select("*").execute()
    
    # 2. Obtener lista de activos (Top pares USD)
    products = cb.get_products()
    pairs = [p['product_id'] for p in products['products'] if p['quote_currency_id'] == 'USD' and p['status'] == 'online']
    
    # Limitamos a los primeros 50 para no exceder el tiempo de GitHub si hay muchos
    for symbol in pairs[:50]:
        try:
            # Obtener velas (Timeframe 15m por defecto o dinámico)
            candles = cb.get_candles(symbol, start="1705230000", end="1705250000", granularity="NINE_HUNDRED")
            df = pd.DataFrame(candles['candles'], columns=['start', 'low', 'high', 'open', 'close', 'volume'])
            df['close'] = df['close'].astype(float)
            
            if len(df) < 200: continue
            
            df = calculate_indicators(df)
            last = df.iloc[-1]
            
            # Lógica Sniper para cada usuario
            for user in users.data:
                u_id = user['user_id']
                rsi_limit = user.get('rsi_limit', 25)
                
                # CONDICIONES: Precio > EMA200 Y RSI < Límite Y Precio < Bollinger Inferior
                if last['close'] > last['ema200'] and last['rsi'] < rsi_limit and last['close'] <= last['lower']:
                    # Insertar señal
                    db.table("signals_today").upsert({
                        "user_id": u_id,
                        "symbol": symbol,
                        "entry_price": last['close'],
                        "rsi": round(last['rsi'], 2),
                        "stop_loss": last['lower'] * 0.98,
                        "take_profit": last['upper']
                    }).execute()
                    print(f"✅ Señal detectada para {u_id}: {symbol}")
                    
        except Exception as e:
            print(f"❌ Error en {symbol}: {e}")

if __name__ == "__main__":
    run_scan()