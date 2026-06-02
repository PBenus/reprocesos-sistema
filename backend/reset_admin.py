"""
Reset password del usuario admin en Supabase.
"""
from database import get_supabase
from auth.utils import hash_password

db = get_supabase()

nueva_password = "Admin2026!"
nuevo_hash = hash_password(nueva_password)

res = db.table("usuarios").update({"password_hash": nuevo_hash}).eq("usuario", "admin").execute()

if res.data:
    print(f"✓ Contraseña del usuario 'admin' actualizada a: {nueva_password}")
else:
    print("! No se pudo actualizar. Verifica que el usuario 'admin' existe.")

# Mostrar todos los usuarios
print("\n=== USUARIOS EN EL SISTEMA ===")
todos = db.table("usuarios").select("usuario, nombre, rol, activo").execute()
for u in todos.data:
    estado = "ACTIVO" if u["activo"] else "INACTIVO"
    print(f"  {u['usuario']:<20} {u['rol']:<25} [{estado}]")
