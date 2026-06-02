"""
Script para crear el usuario de control_calidad (administrador).
Ejecutar desde la carpeta backend/ con el entorno virtual activo.
"""
from database import get_supabase
from auth.utils import hash_password

def create_admin():
    db = get_supabase()

    usuarios = [
        {
            "nombre": "Administrador",
            "usuario": "admin",
            "password_hash": hash_password("Admin2026!"),
            "rol": "control_calidad",
            "activo": True,
        },
    ]

    for u in usuarios:
        res = db.table("usuarios").select("id").eq("usuario", u["usuario"]).execute()
        if not res.data:
            db.table("usuarios").insert(u).execute()
            print(f"✓ Usuario '{u['usuario']}' creado con rol '{u['rol']}'")
        else:
            print(f"! Usuario '{u['usuario']}' ya existe — no se modificó")

    # Mostrar todos los usuarios al final
    print("\n=== USUARIOS EN EL SISTEMA ===")
    todos = db.table("usuarios").select("usuario, nombre, rol, activo").execute()
    for u in todos.data:
        estado = "ACTIVO" if u["activo"] else "INACTIVO"
        print(f"  {u['usuario']:<20} {u['rol']:<25} {u['nombre']} [{estado}]")

if __name__ == "__main__":
    create_admin()
