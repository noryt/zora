import os
import time
import pandas as pd
from coinbase.rest import RESTClient
from dotenv import load_dotenv

load_dotenv()

class ScalinityEliteScanner:
    def __init__(self):
        self.client = RESTClient(
            api_key=os.getenv('CB_API_KEY'), 
            api_secret=os.getenv('CB_API_SECRET')
        )

    def get_all_usd_products(self):
        """Obtiene todos los pares activos en USD de Coinbase."""
        try:
            products = self.client.get_products()
            return [p.product_id for p in products.products 
                    if p.quote_currency_id == 'USD' and p.status == 'online']
        except:
            return ['BTC-USD', 'ETH-USD', 'SOL-USD']

    def _get_indicators(self, symbol, timeframe='15m'):
        tf_map = {'1m': (60, 'ONE_MINUTE'), '5m': (300, 'FIVE_MINUTE'), 
                  '15m': (900, 'FIFTEEN_MINUTE'), '1h': (3600, 'ONE_HOUR')}
        
        seconds, granularity = tf_map.get(timeframe, (900, 'FIFTEEN_MINUTE'))

        try:
            end_ts = int(time.time())
            start_ts = end_ts - (300 * seconds)
            
            response = self.client.get_candles(
                product_id=symbol, start=str(start_ts), end=str(end_ts), granularity=granularity
            )
            
            if not response.candles or len(response.candles) < 200: return None

            df = pd.DataFrame([{'c': float(c.close)} for c in response.candles])
            df = df.iloc[::-1].reset_index(drop=True)

            # RSI 14
            delta = df['c'].diff()
            gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14, adjust=False).mean()
            loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
            rsi = 100 - (100 / (1 + (gain / (loss + 1e-9))))
            
            return {'precio': df['c'].iloc[-1], 'rsi': rsi.iloc[-1], 'df': df}
        except:
            return None

    def scan_market(self, user_id, config):
        all_assets = self.get_all_usd_products()
        signals = []
        
        rsi_limit = config.get('rsi_limit', 25)
        std_dev_mult = float(config.get('boll_std_dev', 2.5))
        timeframe = config.get('timeframe', '15m')

        for asset in all_assets:
            data = self._get_indicators(asset, timeframe)
            if not data: continue
            
            df = data['df']
            precio = data['precio']
            
        
            ema200 = df['c'].ewm(span=200, adjust=False).mean().iloc[-1]
            if precio < ema200: continue 

            if data['rsi'] > rsi_limit: continue

            ma20 = df['c'].rolling(20).mean().iloc[-1]
            std = df['c'].rolling(20).std().iloc[-1]
            lower_band = ma20 - (std * std_dev_mult)

            if precio <= lower_band:
                atr_mult = float(config.get('atr_multiplier', 2.0))
                buffer = max(std * atr_mult, precio * 0.005)
                
                signals.append({
                    "user_id": user_id,
                    "symbol": asset,
                    "rsi": round(data['rsi'], 2),
                    "entry_price": round(precio, 4),
                    "stop_loss": round(precio - buffer, 4),
                    "take_profit": round(precio + (buffer * 2.5), 4),
                    "net_est": f"Sniper {timeframe}"
                })
            
            time.sleep(0.05) 
        return signals