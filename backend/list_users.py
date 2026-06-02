from database import get_supabase
db = get_supabase()
res = db.table("usuarios").select("id, nombre, usuario, rol, activo").execute()
print("\n=== USUARIOS EN SUPABASE ===")
for u in res.data:
    estado = "ACTIVO" if u["activo"] else "INACTIVO"
    print(f"  usuario: {u['usuario']:<20} rol: {u['rol']:<25} nombre: {u['nombre']} [{estado}]")
print(f"\nTotal: {len(res.data)} usuario(s)\n")
