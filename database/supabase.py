import os
from supabase import create_client, Client
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

class ZoraDatabase:
    def __init__(self):
        # Intentar obtener de Streamlit Secrets (Nube)
        # Si no existe (Local), intentar obtener de variables de entorno
        self.url = st.secrets.get("SUPABASE_URL") or os.environ.get("SUPABASE_URL")
        self.key = st.secrets.get("SUPABASE_KEY") or os.environ.get("SUPABASE_KEY")

        if not self.url or not self.key:
            # Si llegamos aquí, es que no están en ningún lado
            raise ValueError("Error: SUPABASE_URL o SUPABASE_KEY no encontrados.")

        self.supabase = create_client(self.url, self.key)

    def create_user(self, email, password, full_name):
        """Crea un nuevo usuario y su perfil inicial."""
        try:
            auth_res = self.supabase.auth.sign_up({
                "email": email,
                "password": password,
            })
            
            if auth_res.user:
                user_data = {
                    "id": auth_res.user.id,
                    "username": email.split('@')[0],
                    "full_name": full_name,
                    "is_pro": False
                }
                self.supabase.table("profiles").insert(user_data).execute()
                
                self.supabase.table("strategies").insert({"user_id": auth_res.user.id}).execute()
                
                return True, "Registro exitoso. Revisa tu email."
            return False, "No se pudo crear el usuario."
        except Exception as e:
            return False, str(e)

    def login_user(self, email, password):
        """Autentica al usuario en Supabase."""
        try:
            res = self.supabase.auth.sign_in_with_password({
                "email": email, 
                "password": password
            })
            if res.user:
                return True, res.user
            return False, None
        except Exception as e:
            print(f"Error en login: {e}")
            return False, None

    def get_user_strategy(self, user_id):
        try:
            response = self.supabase.table("strategies").select("*").eq("user_id", user_id).execute()
            if response.data:
                return response.data[0]
            return {"rsi_limit": 30, "use_bb": True, "ema_period": 20}
        except Exception as e:
            print(f"Error cargando estrategia: {e}")
            return {"rsi_limit": 30, "use_bb": True, "ema_period": 20}

    def update_strategy(self, user_id, rsi_limit, use_bb):
        data = {"user_id": user_id, "rsi_limit": rsi_limit, "use_bb": use_bb}
        return self.supabase.table("strategies").upsert(data).execute()

    def save_trade(self, user_id, symbol, trade_type, entry, exit, notes):
        profit = exit - entry if trade_type == "LONG" else entry - exit
        data = {
            "user_id": user_id,
            "symbol": symbol,
            "trade_type": trade_type,
            "entry_price": entry,
            "exit_price": exit,
            "profit": profit,
            "notes": notes
        }
        return self.supabase.table("journal").insert(data).execute()

    def get_trade_history(self, user_id):
        return self.supabase.table("journal").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()