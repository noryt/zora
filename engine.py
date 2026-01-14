import time
import sys
import os

# Aseguramos que Python encuentre los módulos locales
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.scanner import ScalinityEliteScanner
from database.supabase import ZoraDatabase # Asegúrate de que el nombre del archivo sea supabase_db.py

def run_engine():
    db = ZoraDatabase()
    scanner = ScalinityEliteScanner()
    
    print("🛡️ Zora Sentinel Engine: INICIADO")
    
    while True:
        try:
            # 1. Obtener todos los usuarios de la tabla profiles
            profiles_res = db.supabase.table("profiles").select("id").execute()
            
            if not profiles_res.data:
                print("⚠️ No se encontraron perfiles para escanear.")
            
            for profile in profiles_res.data:
                u_id = profile['id']
                
                # 2. Obtener la estrategia completa (ADN)
                config = db.get_user_strategy(u_id)
                print(f"DEBUG: Escaneando para {u_id[:8]} | RSI Gatillo: {config.get('rsi_limit')} | TF: {config.get('timeframe')}")
                
                # 3. Escanear
                found_signals = scanner.scan_market(u_id, config)
                
                if not found_signals:
                    print(f"ℹ️ Mercado tranquilo para {u_id[:8]}. Ningún activo cumple criterios.")
                else:
                    # 4. Limpiar señales previas del día para este usuario
                    db.supabase.table("signals_today").delete().eq("user_id", u_id).execute()
                    
                    # 5. Insertar nuevas señales
                    db.supabase.table("signals_today").insert(found_signals).execute()
                    print(f"✅ {len(found_signals)} SEÑALES DETECTADAS para usuario {u_id[:8]}")
            
            print(f"🛰️ Ciclo finalizado ({time.strftime('%H:%M:%S')}). Esperando 5 minutos...")
            time.sleep(60) 
            
        except Exception as e:
            print(f"❌ Error en el motor: {e}")
            time.sleep(60) 

if __name__ == "__main__":
    run_engine()