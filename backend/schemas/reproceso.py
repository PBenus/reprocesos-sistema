"""
schemas/reproceso.py
Modelos Pydantic para reprocesos e ítems de reproceso (pintura y repuesto).
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────────────────────
# Ítems de reproceso
# ─────────────────────────────────────────────────────────────────────────────

class ItemCrea(BaseModel):
    """Datos para crear un ítem de reproceso (pintura o repuesto)."""

    seccion: Optional[str] = Field(None, description="Sección o pieza a reprocesar (opcional para pintura)")
    observacion: Optional[str] = Field(None, description="Observación del inspector")
    foto_url: Optional[str] = Field(None, description="URL de la foto de la evidencia")


class ItemPintura(BaseModel):
    """Campos completos de la tabla 'items_reproceso_pintura', opcionalmente enriquecidos con datos del trabajo."""

    id: str
    reproceso_id: str
    seccion: Optional[str] = None
    observacion: Optional[str] = None
    estado: str = Field(default="pendiente", description="pendiente | en_proceso | subsanado")
    foto_url: Optional[str] = None
    creado_en: Optional[datetime] = None
    # Campos del trabajo del operario (enriquecidos al consultar por VIN)
    trabajo_foto: Optional[str] = Field(None, description="Foto del operario al subsanar")
    trabajo_notas: Optional[str] = Field(None, description="Observación del operario")
    trabajo_cerrado_en: Optional[datetime] = Field(None, description="Fecha de cierre del trabajo")
    nombre_operario: Optional[str] = Field(None, description="Nombre del operario que subsanó")

    model_config = {"from_attributes": True}


class ItemRepuesto(BaseModel):
    """Campos completos de la tabla 'items_reproceso_repuesto', opcionalmente enriquecidos con datos del trabajo."""

    id: str
    reproceso_id: str
    seccion: Optional[str] = None
    observacion: Optional[str] = None
    estado: str = Field(default="pendiente", description="pendiente | en_proceso | subsanado")
    foto_url: Optional[str] = None
    creado_en: Optional[datetime] = None
    # Campos del trabajo del operario (enriquecidos al consultar por VIN)
    trabajo_foto: Optional[str] = Field(None, description="Foto del operario al subsanar")
    trabajo_notas: Optional[str] = Field(None, description="Observación del operario")
    trabajo_cerrado_en: Optional[datetime] = Field(None, description="Fecha de cierre del trabajo")
    nombre_operario: Optional[str] = Field(None, description="Nombre del operario que subsanó")

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────────────────
# Reproceso
# ─────────────────────────────────────────────────────────────────────────────

class ReprocesoCrea(BaseModel):
    """Body para crear un nuevo reproceso."""

    vin: str = Field(..., description="VIN del vehículo a reprocesar")
    notas_cc: Optional[str] = Field(
        None,
        description="Notas del inspector de control de calidad",
    )
    items_pintura: List[ItemCrea] = Field(
        default_factory=list,
        description="Ítems de pintura a incluir en el reproceso",
    )
    items_repuesto: List[ItemCrea] = Field(
        default_factory=list,
        description="Ítems de repuesto a incluir en el reproceso",
    )


class ReprocesoDB(BaseModel):
    """Campos completos de la tabla 'reprocesos' tal como vienen de Supabase."""

    id: str
    vin: str
    notas_cc: Optional[str] = None
    estado: str = Field(
        default="pendiente",
        description="Estado global del reproceso: pendiente | por_validar | cerrado",
    )
    creado_por: Optional[str] = Field(None, description="UUID del usuario que creó el reproceso")
    creado_en: Optional[datetime] = None
    actualizado_en: Optional[datetime] = None
    vehiculos: Optional[dict] = Field(None, description="Información del vehículo si se usó select('*, vehiculos(*)')")

    model_config = {"from_attributes": True}


class ReprocesoDetalle(ReprocesoDB):
    """
    Reproceso con todos sus ítems (enriquecidos con datos del trabajo) y nombre del creador.
    Retornado por GET /reprocesos/{id} y GET /reprocesos?vin=...
    """

    items_pintura: List[ItemPintura] = Field(default_factory=list)
    items_repuesto: List[ItemRepuesto] = Field(default_factory=list)
    nombre_creador: Optional[str] = Field(None, description="Nombre del usuario que creó el reproceso")


class ReprocesoActualiza(BaseModel):
    """Body para actualizar parcialmente un reproceso (PATCH)."""

    notas_cc: Optional[str] = None
    estado: Optional[str] = Field(
        None,
        description="Nuevo estado: pendiente | cerrado",
    )
