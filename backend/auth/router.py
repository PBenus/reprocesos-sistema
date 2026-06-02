"""
auth/router.py
Endpoints de autenticación: login, me, register.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from auth.models import LoginRequest, TokenResponse, UserInfo
from auth.utils import (
    create_jwt_token,
    get_current_user,
    hash_password,
    require_role,
    verify_password,
)
from database import get_supabase
from schemas.usuario import UsuarioCrea, UsuarioDB

router = APIRouter(prefix="/auth", tags=["Autenticación"])


# ─────────────────────────────────────────────────────────────────────────────
# POST /auth/login
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Iniciar sesión",
    description="Recibe usuario y contraseña. Retorna un JWT si las credenciales son válidas.",
)
def login(body: LoginRequest) -> TokenResponse:
    db = get_supabase()

    # Buscar usuario activo en la tabla 'usuarios'
    result = (
        db.table("usuarios")
        .select("id, nombre, usuario, password_hash, rol, activo")
        .eq("usuario", body.usuario)
        .eq("activo", True)
        .single()
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado o desactivado",
        )

    user_data = result.data

    # Verificar contraseña
    if not verify_password(body.password, user_data["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Contraseña incorrecta",
        )

    # Crear JWT con datos del usuario
    token = create_jwt_token(
        {
            "sub": user_data["id"],
            "usuario": user_data["usuario"],
            "nombre": user_data["nombre"],
            "rol": user_data["rol"],
        }
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        rol=user_data["rol"],
        nombre=user_data["nombre"],
        id=user_data["id"],
    )


# ─────────────────────────────────────────────────────────────────────────────
# GET /auth/me
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/me",
    response_model=UserInfo,
    summary="Información del usuario actual",
    description="Retorna los datos del usuario autenticado extraídos del JWT.",
)
def me(current_user: UserInfo = Depends(get_current_user)) -> UserInfo:
    return current_user


# ─────────────────────────────────────────────────────────────────────────────
# POST /auth/register  (solo control_calidad)
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/register",
    response_model=UsuarioDB,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nuevo usuario",
    description="Crea un nuevo usuario en el sistema. Solo accesible para control_calidad.",
)
def register(
    body: UsuarioCrea,
    current_user: UserInfo = Depends(require_role("control_calidad")),
) -> UsuarioDB:
    db = get_supabase()

    # Verificar que el nombre de usuario no exista
    existing = (
        db.table("usuarios")
        .select("id")
        .eq("usuario", body.usuario)
        .execute()
    )
    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El usuario '{body.usuario}' ya existe",
        )

    # Validar que el rol sea válido
    roles_validos = {"control_calidad", "operario_pintura", "operario_repuesto"}
    if body.rol not in roles_validos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Rol inválido. Debe ser uno de: {', '.join(roles_validos)}",
        )

    # Insertar nuevo usuario
    nuevo = {
        "nombre": body.nombre,
        "usuario": body.usuario,
        "password_hash": hash_password(body.password),
        "rol": body.rol,
        "activo": True,
    }

    result = db.table("usuarios").insert(nuevo).execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al crear el usuario en la base de datos",
        )

    created = result.data[0]
    return UsuarioDB(**created)
