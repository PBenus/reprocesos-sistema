"""
schemas/vehiculo.py
Modelos Pydantic para vehículos y sus daños de pintura/repuesto.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────────────────────
# Daños
# ─────────────────────────────────────────────────────────────────────────────

class DanoPintura(BaseModel):
    """Representa un registro de daño de pintura asociado a un vehículo."""

    id: str
    vin: str
    fecha_hora: Optional[datetime] = None
    marca: Optional[str] = None
    modelo: Optional[str] = None
    procedencia: Optional[str] = None
    seccion: str = Field(..., description="Sección del vehículo afectada")
    diagnostico_esum: Optional[str] = None
    validacion: Optional[str] = None
    num_panos: Optional[float] = None
    comentario: Optional[str] = None
    colaborador: Optional[str] = None
    sincronizado_en: Optional[datetime] = None

    model_config = {"from_attributes": True}


class DanoRepuesto(BaseModel):
    """Representa un registro de daño de repuesto asociado a un vehículo."""

    id: str
    vin: str
    taller: Optional[str] = None
    marca: Optional[str] = None
    modelo: Optional[str] = None
    anio: Optional[str] = None
    color: Optional[str] = None
    procedencia: Optional[str] = None
    seccion: str = Field(..., description="Sección / pieza afectada")
    diagnostico: Optional[str] = None
    num_pedido: Optional[str] = None
    fecha_registro: Optional[str] = None  # es DATE en BD
    validado_por: Optional[str] = None
    validacion_cliente: Optional[str] = None
    fecha_val_cliente: Optional[str] = None
    comentario_val_cliente: Optional[str] = None
    fecha_termino: Optional[str] = None
    link_evidencia_1: Optional[str] = None
    link_evidencia_2: Optional[str] = None
    link_evidencia_3: Optional[str] = None
    link_evidencia_4: Optional[str] = None
    link_evidencia_5: Optional[str] = None
    link_evidencia_6: Optional[str] = None
    link_evidencia_7: Optional[str] = None
    sincronizado_en: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────────────────────────────────────
# Vehículo base
# ─────────────────────────────────────────────────────────────────────────────

class VehiculoBase(BaseModel):
    """
    Campos principales de la tabla 'vehiculos'.
    Mapea directamente las columnas de Supabase.
    """

    id: str
    vin: str = Field(..., description="Número de identificación del vehículo (VIN)")
    taller: Optional[str] = None
    color: Optional[str] = None
    fecha_planificada: Optional[str] = None  # DATE
    fecha_ingreso_flujo: Optional[str] = None  # DATE
    dias_transcurridos: Optional[int] = None
    modelo: Optional[str] = Field(None, description="Modelo del vehículo")
    marca: Optional[str] = None
    proceso: Optional[str] = Field(None, description="Zona actual del vehículo")
    estado: Optional[str] = Field(None, description="EN PROCESO | PENDIENTE")
    concesionario: Optional[str] = None
    observaciones: Optional[str] = None
    sincronizado_en: Optional[datetime] = None

    model_config = {"from_attributes": True, "populate_by_name": True}


# ─────────────────────────────────────────────────────────────────────────────
# Vehículo con daños (ficha completa)
# ─────────────────────────────────────────────────────────────────────────────

class VehiculoConDanos(VehiculoBase):
    """Vehículo con todos sus daños de pintura y repuesto adjuntos."""

    danos_pintura: List[DanoPintura] = Field(
        default_factory=list,
        description="Lista de daños de pintura registrados para este VIN",
    )
    danos_repuesto: List[DanoRepuesto] = Field(
        default_factory=list,
        description="Lista de daños de repuesto registrados para este VIN",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Agrupación por proceso
# ─────────────────────────────────────────────────────────────────────────────

class VehiculosPorProceso(BaseModel):
    """
    Respuesta agrupada de vehículos por proceso.
    Ejemplo: {"PINTURA": [...], "REPUESTO": [...], "CONTROL": [...]}
    """

    vehiculos: Dict[str, List[VehiculoBase]] = Field(
        default_factory=dict,
        description="Diccionario donde la clave es el proceso y el valor es la lista de vehículos",
    )
