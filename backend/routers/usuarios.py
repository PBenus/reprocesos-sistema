"""
routers/usuarios.py
Endpoints para gestión de usuarios del sistema.
Solo accesible para el rol control_calidad.
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from auth.models import UserInfo
from auth.utils import hash_password, require_role
from database import get_supabase
from schemas.usuario import UsuarioActualiza, UsuarioCrea, UsuarioDB

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

_cc = require_role("control_calidad")

ROLES_VALIDOS = {"control_calidad", "operario_pintura", "operario_repuesto"}


# ─────────────────────────────────────────────────────────────────────────────
# GET /usuarios
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=List[UsuarioDB],
    summary="Listar usuarios",
)
def listar_usuarios(_user: UserInfo = Depends(_cc)) -> List[UsuarioDB]:
    db = get_supabase()
    result = db.table("usuarios").select("id, nombre, usuario, rol, activo, creado_en").order("nombre").execute()
    return [UsuarioDB(**u) for u in (result.data or [])]


# ─────────────────────────────────────────────────────────────────────────────
# POST /usuarios
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/",
    response_model=UsuarioDB,
    status_code=status.HTTP_201_CREATED,
    summary="Crear usuario",
)
def crear_usuario(
    body: UsuarioCrea,
    _user: UserInfo = Depends(_cc),
) -> UsuarioDB:
    db = get_supabase()

    if body.rol not in ROLES_VALIDOS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Rol inválido. Opciones: {', '.join(ROLES_VALIDOS)}",
        )

    # Verificar unicidad del nombre de usuario
    existing = db.table("usuarios").select("id").eq("usuario", body.usuario).execute()
    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El usuario '{body.usuario}' ya existe",
        )

    nuevo = {
        "nombre": body.nombre,
        "usuario": body.usuario,
        "password_hash": hash_password(body.password),
        "rol": body.rol,
        "activo": True,
    }
    result = db.table("usuarios").insert(nuevo).execute()
    if not result.data:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al crear usuario")

    return UsuarioDB(**result.data[0])


# ─────────────────────────────────────────────────────────────────────────────
# PATCH /usuarios/{id}
# ─────────────────────────────────────────────────────────────────────────────

@router.patch(
    "/{usuario_id}",
    response_model=UsuarioDB,
    summary="Actualizar datos del usuario",
)
def actualizar_usuario(
    usuario_id: str,
    body: UsuarioActualiza,
    _user: UserInfo = Depends(_cc),
) -> UsuarioDB:
    db = get_supabase()

    cambios = body.model_dump(exclude_none=True)

    if not cambios:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se enviaron campos a actualizar")

    if "rol" in cambios and cambios["rol"] not in ROLES_VALIDOS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Rol inválido. Opciones: {', '.join(ROLES_VALIDOS)}",
        )

    # Si se actualiza la contraseña, hashearla
    if "password" in cambios:
        cambios["password_hash"] = hash_password(cambios.pop("password"))

    # Si se actualiza el nombre de usuario, verificar unicidad
    if "usuario" in cambios:
        existing = (
            db.table("usuarios")
            .select("id")
            .eq("usuario", cambios["usuario"])
            .neq("id", usuario_id)
            .execute()
        )
        if existing.data:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"El nombre de usuario '{cambios['usuario']}' ya está en uso",
            )

    result = db.table("usuarios").update(cambios).eq("id", usuario_id).execute()
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Usuario '{usuario_id}' no encontrado")

    return UsuarioDB(**result.data[0])


# ─────────────────────────────────────────────────────────────────────────────
# PATCH /usuarios/{id}/toggle-activo
# ─────────────────────────────────────────────────────────────────────────────

@router.patch(
    "/{usuario_id}/toggle-activo",
    response_model=UsuarioDB,
    summary="Activar / desactivar usuario",
    description="Invierte el estado activo del usuario. No se puede desactivar a uno mismo.",
)
def toggle_activo(
    usuario_id: str,
    current_user: UserInfo = Depends(_cc),
) -> UsuarioDB:
    db = get_supabase()

    # Evitar que el usuario se desactive a sí mismo
    if usuario_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes desactivar tu propio usuario",
        )

    # Obtener estado actual
    result = db.table("usuarios").select("*").eq("id", usuario_id).single().execute()
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Usuario '{usuario_id}' no encontrado")

    nuevo_estado = not result.data["activo"]
    updated = db.table("usuarios").update({"activo": nuevo_estado}).eq("id", usuario_id).execute()

    return UsuarioDB(**updated.data[0])
