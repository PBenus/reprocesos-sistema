"""
auth/utils.py
Utilidades de autenticación: hashing de contraseñas, JWT y dependencias FastAPI.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from auth.models import UserInfo
from config import settings

# ── Configuración de bcrypt ───────────────────────────────────────────────────
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── Esquema OAuth2 (extrae el token del header Authorization: Bearer <token>) ─
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ─────────────────────────────────────────────────────────────────────────────
# Hashing de contraseñas
# ─────────────────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Genera un hash bcrypt de la contraseña en texto plano."""
    return _pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verifica si la contraseña en texto plano coincide con el hash bcrypt."""
    return _pwd_context.verify(plain, hashed)


# ─────────────────────────────────────────────────────────────────────────────
# JWT
# ─────────────────────────────────────────────────────────────────────────────

def create_jwt_token(data: dict) -> str:
    """
    Crea un JWT firmado con la clave secreta.

    Args:
        data: Payload del token (se recomienda incluir 'sub', 'rol', 'nombre').

    Returns:
        Token JWT como string.
    """
    payload = data.copy()
    expire = datetime.now(tz=timezone.utc) + timedelta(hours=settings.JWT_EXPIRE_HOURS)
    payload.update({"exp": expire})

    return jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_jwt_token(token: str) -> dict:
    """
    Decodifica y valida un JWT.

    Args:
        token: Token JWT como string.

    Returns:
        Payload decodificado como dict.

    Raises:
        HTTPException 401 si el token es inválido o expirado.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError:
        raise credentials_exception


# ─────────────────────────────────────────────────────────────────────────────
# Dependencias FastAPI
# ─────────────────────────────────────────────────────────────────────────────

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInfo:
    """
    Dependencia FastAPI que extrae y valida el usuario del JWT.

    Uso en un endpoint:
        @router.get("/ruta")
        def mi_ruta(user: UserInfo = Depends(get_current_user)):
            ...
    """
    payload = decode_jwt_token(token)

    user_id: str | None = payload.get("sub")
    usuario: str | None = payload.get("usuario")
    nombre: str | None = payload.get("nombre")
    rol: str | None = payload.get("rol")

    if not all([user_id, usuario, nombre, rol]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token con datos incompletos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return UserInfo(id=user_id, nombre=nombre, usuario=usuario, rol=rol)  # type: ignore[arg-type]


def require_role(*roles: str) -> Callable:
    """
    Fábrica de dependencias que verifica que el usuario tenga uno de los roles indicados.

    Uso:
        @router.get("/admin", dependencies=[Depends(require_role("control_calidad"))])
        def admin_only():
            ...

        # O cuando también necesitas el objeto user:
        @router.get("/ruta")
        def ruta(user: UserInfo = Depends(require_role("control_calidad", "operario_pintura"))):
            ...

    Args:
        *roles: Roles permitidos (ej. "control_calidad", "operario_pintura").

    Returns:
        Función de dependencia que retorna el UserInfo si el rol es válido.
    """

    async def _check(user: UserInfo = Depends(get_current_user)) -> UserInfo:
        if user.rol not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado. Se requiere uno de los roles: {', '.join(roles)}",
            )
        return user

    return _check
