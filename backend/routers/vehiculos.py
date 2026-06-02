"""
routers/vehiculos.py
Endpoints para consulta de vehículos y sus daños.
Solo accesible para el rol control_calidad.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth.models import UserInfo
from auth.utils import require_role
from database import get_supabase
from schemas.vehiculo import DanoPintura, DanoRepuesto, VehiculoBase, VehiculoConDanos

router = APIRouter(prefix="/vehiculos", tags=["Vehículos"])

# Dependencia reutilizable para control_calidad
_cc = require_role("control_calidad")


# ─────────────────────────────────────────────────────────────────────────────
# GET /vehiculos
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/",
    summary="Listar vehículos agrupados por proceso",
    description=(
        "Retorna todos los vehículos agrupados por proceso. "
        "Filtrable por 'proceso' y por búsqueda libre (VIN o modelo)."
    ),
    response_model=Dict[str, List[VehiculoBase]],
)
def listar_vehiculos(
    proceso: Optional[str] = Query(None, description="Filtrar por proceso específico"),
    buscar: Optional[str] = Query(None, description="Buscar por VIN o modelo"),
    _user: UserInfo = Depends(_cc),
) -> Dict[str, List[VehiculoBase]]:
    db = get_supabase()

    # Supabase limita a 1000 filas por consulta — paginamos para obtener todo
    PAGE_SIZE = 1000
    all_rows: list = []
    offset = 0

    while True:
        q = db.table("vehiculos").select("*")

        if proceso:
            q = q.eq("proceso", proceso.upper())

        if buscar:
            buscar_like = f"%{buscar}%"
            q = q.or_(f"vin.ilike.{buscar_like},modelo.ilike.{buscar_like}")

        result = (
            q.order("fecha_ingreso_flujo", desc=True)
            .range(offset, offset + PAGE_SIZE - 1)
            .execute()
        )

        if result.data is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al consultar vehículos",
            )

        all_rows.extend(result.data)

        # Si devolvió menos de PAGE_SIZE, ya no hay más páginas
        if len(result.data) < PAGE_SIZE:
            break

        offset += PAGE_SIZE

    # Agrupar por proceso
    agrupados: Dict[str, List[VehiculoBase]] = defaultdict(list)
    for row in all_rows:
        proc = row.get("proceso") or "SIN_PROCESO"
        agrupados[proc].append(VehiculoBase(**row))

    return dict(agrupados)


# ─────────────────────────────────────────────────────────────────────────────
# GET /vehiculos/{vin}
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/{vin}",
    summary="Ficha completa del vehículo",
    description="Retorna el vehículo con todos sus daños de pintura y repuesto.",
    response_model=VehiculoConDanos,
)
def detalle_vehiculo(
    vin: str,
    _user: UserInfo = Depends(_cc),
) -> VehiculoConDanos:
    db = get_supabase()

    # Datos del vehículo
    veh_result = (
        db.table("vehiculos")
        .select("*")
        .eq("vin", vin.upper())
        .single()
        .execute()
    )

    if not veh_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehículo con VIN '{vin}' no encontrado",
        )

    vehiculo_data = veh_result.data

    # Daños de pintura
    pin_result = (
        db.table("danos_pintura")
        .select("*")
        .eq("vin", vin.upper())
        .execute()
    )
    danos_pintura = [DanoPintura(**d) for d in (pin_result.data or [])]

    # Daños de repuesto
    rep_result = (
        db.table("danos_repuesto")
        .select("*")
        .eq("vin", vin.upper())
        .execute()
    )
    danos_repuesto = [DanoRepuesto(**d) for d in (rep_result.data or [])]

    return VehiculoConDanos(
        **vehiculo_data,
        danos_pintura=danos_pintura,
        danos_repuesto=danos_repuesto,
    )
