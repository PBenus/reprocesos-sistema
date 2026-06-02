import os
from database import get_supabase
from auth.utils import hash_password

def create_users():
    db = get_supabase()
    users = [
        {"nombre": "Operario Pintura", "usuario": "op_pintura", "password_hash": hash_password("123456"), "rol": "operario_pintura", "activo": True},
        {"nombre": "Operario Repuesto", "usuario": "op_repuesto", "password_hash": hash_password("123456"), "rol": "operario_repuesto", "activo": True}
    ]
    
    for u in users:
        # check if exists
        res = db.table("usuarios").select("id").eq("usuario", u["usuario"]).execute()
        if not res.data:
            print(f"Creando usuario {u['usuario']}...")
            db.table("usuarios").insert(u).execute()
        else:
            print(f"El usuario {u['usuario']} ya existe.")
            
if __name__ == "__main__":
    create_users()
