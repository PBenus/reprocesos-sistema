"""
auth/models.py
Modelos Pydantic para autenticación y gestión de usuarios.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Cuerpo de la petición de login."""

    usuario: str = Field(..., min_length=3, description="Nombre de usuario")
    password: str = Field(..., min_length=6, description="Contraseña")


class TokenResponse(BaseModel):
    """Respuesta exitosa del login con el JWT y datos del usuario."""

    access_token: str = Field(..., description="JSON Web Token")
    token_type: str = Field(default="bearer", description="Tipo de token")
    rol: str = Field(..., description="Rol del usuario en el sistema")
    nombre: str = Field(..., description="Nombre completo del usuario")
    id: str = Field(..., description="UUID del usuario en Supabase")


class UserInfo(BaseModel):
    """Información del usuario actualmente autenticado."""

    id: str = Field(..., description="UUID del usuario")
    nombre: str = Field(..., description="Nombre completo")
    usuario: str = Field(..., description="Nombre de usuario para login")
    rol: str = Field(..., description="Rol del usuario: control_calidad | operario_pintura | operario_repuesto")
