"""
schemas/usuario.py
Modelos Pydantic para gestión de usuarios del sistema.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UsuarioCrea(BaseModel):
    """Body para crear un nuevo usuario."""

    nombre: str = Field(..., min_length=2, description="Nombre completo del usuario")
    usuario: str = Field(..., min_length=3, description="Nombre de usuario para login")
    password: str = Field(..., min_length=6, description="Contraseña en texto plano (se hasheará)")
    rol: str = Field(
        ...,
        description="Rol: control_calidad | operario_pintura | operario_repuesto",
    )


class UsuarioActualiza(BaseModel):
    """Body para actualizar datos de un usuario (PATCH)."""

    nombre: Optional[str] = Field(None, min_length=2)
    usuario: Optional[str] = Field(None, min_length=3)
    password: Optional[str] = Field(None, min_length=6, description="Si se envía, se rehashea")
    rol: Optional[str] = None


class UsuarioDB(BaseModel):
    """Representación de un usuario tal como está en la base de datos (sin password_hash)."""

    id: str
    nombre: str
    usuario: str
    rol: str
    activo: bool = True
    creado_en: Optional[datetime] = None

    model_config = {"from_attributes": True}
