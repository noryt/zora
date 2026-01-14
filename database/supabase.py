import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

class ZoraDatabase:
    def __init__(self):
        url: str = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        key: str = os.getenv("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY")
        
        if not url or not key:
            raise ValueError("SUPABASE_URL o SUPABASE_KEY no configurados en .env")
            
        self.supabase: Client = create_client(url, key)

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