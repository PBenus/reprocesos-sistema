"""
schemas/trabajo.py
Modelos Pydantic para trabajos de operarios (pintura y repuesto).
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────────────────────
# Requests
# ─────────────────────────────────────────────────────────────────────────────

class TrabajoCrea(BaseModel):
    """Body para iniciar un trabajo en un ítem de reproceso."""

    item_id: str = Field(..., description="UUID del ítem (pintura o repuesto) a trabajar")


class TrabajoCierra(BaseModel):
    """Body para cerrar (completar) un trabajo."""

    foto_url: Optional[str] = Field(
        None,
        description="URL del archivo en Google Drive con la foto de evidencia",
    )
    notas: Optional[str] = Field(None, description="Notas del operario al cerrar el trabajo")


# ─────────────────────────────────────────────────────────────────────────────
# Base de datos
# ─────────────────────────────────────────────────────────────────────────────

class TrabajoDB(BaseModel):
    """Campos completos de la tabla 'trabajos_pintura' o 'trabajos_repuesto'."""

    id: str
    item_id: str = Field(..., description="UUID del ítem asociado")
    operario_id: str = Field(..., description="UUID del operario que realiza el trabajo")
    abierto_en: Optional[datetime] = Field(None, description="Timestamp de inicio del trabajo")
    cerrado_en: Optional[datetime] = Field(None, description="Timestamp de cierre del trabajo")
    foto_url: Optional[str] = None
    notas: Optional[str] = None
    estado: str = Field(
        default="abierto",
        description="Estado del trabajo: abierto | cerrado",
    )
    nombre_operario: Optional[str] = Field(None, description="Nombre del operario (join con usuarios)")

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────────────────
# Trabajo con contexto completo (histórico)
# ─────────────────────────────────────────────────────────────────────────────

class TrabajoHistorico(TrabajoDB):
    """
    Trabajo enriquecido con información del ítem, vehículo y creador del reproceso.
    Útil para historial y reportes.
    """

    # Datos del ítem de reproceso
    seccion: Optional[str] = Field(None, description="Sección del ítem asociado")
    observacion_item: Optional[str] = Field(None, description="Observación del ítem")

    # Datos del vehículo
    vin: Optional[str] = Field(None, description="VIN del vehículo")
    modelo: Optional[str] = Field(None, description="Modelo del vehículo")

    # Datos del creador del reproceso
    nombre_creador: Optional[str] = Field(
        None,
        description="Nombre del inspector de calidad que creó el reproceso",
    )

    # Nombre del operario
    nombre_operario: Optional[str] = Field(None, description="Nombre del operario")
