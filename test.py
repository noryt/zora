import os
from supabase import create_client
from dotenv import load_dotenv

# Forzamos la carga del .env buscando en la carpeta actual
load_dotenv()

def test_connection():
    url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    key = os.getenv("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY")
   
    print(f"--- Diagnóstico de Conexión Zora ---")
    
    # Verificamos si las variables están vacías antes de intentar conectar
    if not url or not key:
        print("❌ Error: No se encontraron las variables en el archivo .env")
        print(f"Ruta actual de trabajo: {os.getcwd()}")
        print(f"¿Existe el archivo .env?: {os.path.exists('.env')}")
        return

    print(f"URL detectada: {url[:20]}...")
    
    try:
        supabase = create_client(url, key)
        # Intentamos una operación simple
        print("✅ Cliente creado. Intentando handshake...")
        res = supabase.table("profiles").select("*").limit(1).execute()
        print("✅ Conexión total exitosa.")
    except Exception as e:
        print("❌ Error de conexión con el servidor.")
        print(f"Detalle: {e}")

if __name__ == "__main__":
    test_connection()