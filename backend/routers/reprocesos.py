"""
routers/reprocesos.py
Endpoints CRUD para reprocesos.
- control_calidad: acceso completo.
- operario_pintura: solo reprocesos con ítems de pintura pendientes.
- operario_repuesto: solo reprocesos con ítems de repuesto pendientes.
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from auth.models import UserInfo
from auth.utils import get_current_user, require_role
from database import get_supabase
from schemas.reproceso import (
    ItemPintura,
    ItemRepuesto,
    ReprocesoCrea,
    ReprocesoDB,
    ReprocesoDetalle,
    ReprocesoActualiza,
)

router = APIRouter(prefix="/reprocesos", tags=["Reprocesos"])

_cc = require_role("control_calidad")


# ─────────────────────────────────────────────────────────────────────────────
# POST /reprocesos  — Crear reproceso
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/",
    response_model=ReprocesoDetalle,
    status_code=status.HTTP_201_CREATED,
    summary="Crear reproceso",
    description="Crea un reproceso con sus ítems de pintura y repuesto en una sola operación.",
)
def crear_reproceso(
    body: ReprocesoCrea,
    current_user: UserInfo = Depends(_cc),
) -> ReprocesoDetalle:
    db = get_supabase()

    # Verificar que el VIN exista
    veh = db.table("vehiculos").select("vin").eq("vin", body.vin.upper()).single().execute()
    if not veh.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"VIN '{body.vin}' no encontrado en la base de datos",
        )

    # Crear el reproceso principal
    nuevo_reproceso = {
        "vin": body.vin.upper(),
        "notas_cc": body.notas_cc,
        "estado": "pendiente",
        "creado_por": current_user.id,
    }
    rep_result = db.table("reprocesos").insert(nuevo_reproceso).execute()
    if not rep_result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al crear el reproceso",
        )

    reproceso = rep_result.data[0]
    reproceso_id = reproceso["id"]

    # Insertar ítems de pintura
    items_pintura_db: List[ItemPintura] = []
    if body.items_pintura:
        items_pin = [
            {"reproceso_id": reproceso_id, "seccion": it.seccion, "observacion": it.observacion, "foto_url": it.foto_url, "estado": "pendiente"}
            for it in body.items_pintura
        ]
        pin_result = db.table("items_reproceso_pintura").insert(items_pin).execute()
        items_pintura_db = [ItemPintura(**i) for i in (pin_result.data or [])]

    # Insertar ítems de repuesto
    items_repuesto_db: List[ItemRepuesto] = []
    if body.items_repuesto:
        items_rep = [
            {"reproceso_id": reproceso_id, "seccion": it.seccion, "observacion": it.observacion, "foto_url": it.foto_url, "estado": "pendiente"}
            for it in body.items_repuesto
        ]
        rep_items_result = db.table("items_reproceso_repuesto").insert(items_rep).execute()
        items_repuesto_db = [ItemRepuesto(**i) for i in (rep_items_result.data or [])]

    return ReprocesoDetalle(
        **reproceso,
        items_pintura=items_pintura_db,
        items_repuesto=items_repuesto_db,
        nombre_creador=current_user.nombre,
    )


# ─────────────────────────────────────────────────────────────────────────────
# GET /reprocesos  — Listar reprocesos según rol
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/",
    summary="Listar reprocesos",
    description=(
        "control_calidad: todos (con info del vehículo asociada). "
        "Si se filtra por VIN, devuelve ReprocesoDetalle con ítems y datos del operario. "
        "operario_pintura: con ítems de pintura pendientes/en_proceso. "
        "operario_repuesto: con ítems de repuesto pendientes/en_proceso."
    ),
)
def listar_reprocesos(
    estado: Optional[str] = Query(None, description="Filtrar por estado: pendiente | por_validar | cerrado"),
    vin: Optional[str] = Query(None, description="Filtrar por VIN"),
    current_user: UserInfo = Depends(get_current_user),
):
    db = get_supabase()

    # Filtrar por rol
    if current_user.rol == "operario_pintura":
        items_result = (
            db.table("items_reproceso_pintura")
            .select("reproceso_id")
            .in_("estado", ["pendiente", "en_proceso"])
            .execute()
        )
        ids_con_pintura = list({r["reproceso_id"] for r in (items_result.data or [])})
        if not ids_con_pintura:
            return []
        query = db.table("reprocesos").select("*, vehiculos(*)").in_("id", ids_con_pintura)

    elif current_user.rol == "operario_repuesto":
        items_result = (
            db.table("items_reproceso_repuesto")
            .select("reproceso_id")
            .in_("estado", ["pendiente", "en_proceso"])
            .execute()
        )
        ids_con_repuesto = list({r["reproceso_id"] for r in (items_result.data or [])})
        if not ids_con_repuesto:
            return []
        query = db.table("reprocesos").select("*, vehiculos(*)").in_("id", ids_con_repuesto)

    else:
        # control_calidad: todos con info del vehículo
        query = db.table("reprocesos").select("*, vehiculos(*)")

    # Filtros opcionales comunes
    if estado:
        query = query.eq("estado", estado)
    if vin:
        query = query.eq("vin", vin.upper())

    result = query.order("creado_en", desc=True).limit(5000).execute()
    reprocesos_raw = result.data or []

    # Si se filtra por VIN, enriquecer con ítems y datos del trabajo (para historial del vehículo)
    if vin:
        return _enriquecer_reprocesos(db, reprocesos_raw)

    return [ReprocesoDB(**r) for r in reprocesos_raw]


def _enriquecer_reprocesos(db, reprocesos_raw: list) -> list:
    """Para cada reproceso, trae sus ítems enriquecidos con datos del trabajo del operario."""
    resultado = []
    for rep in reprocesos_raw:
        rid = rep["id"]

        # Ítems de pintura
        pin_items_raw = (
            db.table("items_reproceso_pintura").select("*").eq("reproceso_id", rid).execute()
        ).data or []

        items_pintura = []
        for item in pin_items_raw:
            # Buscar el trabajo cerrado de este ítem
            trabajo = (
                db.table("trabajos_pintura")
                .select("foto_url, notas, cerrado_en, operario_id")
                .eq("item_id", item["id"])
                .eq("estado", "cerrado")
                .order("cerrado_en", desc=True)
                .limit(1)
                .execute()
            ).data
            t = trabajo[0] if trabajo else {}
            nombre_op = None
            if t.get("operario_id"):
                usr = db.table("usuarios").select("nombre").eq("id", t["operario_id"]).single().execute()
                nombre_op = usr.data.get("nombre") if usr.data else None
            items_pintura.append(ItemPintura(
                **item,
                trabajo_foto=t.get("foto_url"),
                trabajo_notas=t.get("notas"),
                trabajo_cerrado_en=t.get("cerrado_en"),
                nombre_operario=nombre_op,
            ))

        # Ítems de repuesto
        rep_items_raw = (
            db.table("items_reproceso_repuesto").select("*").eq("reproceso_id", rid).execute()
        ).data or []

        items_repuesto = []
        for item in rep_items_raw:
            trabajo = (
                db.table("trabajos_repuesto")
                .select("foto_url, notas, cerrado_en, operario_id")
                .eq("item_id", item["id"])
                .eq("estado", "cerrado")
                .order("cerrado_en", desc=True)
                .limit(1)
                .execute()
            ).data
            t = trabajo[0] if trabajo else {}
            nombre_op = None
            if t.get("operario_id"):
                usr = db.table("usuarios").select("nombre").eq("id", t["operario_id"]).single().execute()
                nombre_op = usr.data.get("nombre") if usr.data else None
            items_repuesto.append(ItemRepuesto(
                **item,
                trabajo_foto=t.get("foto_url"),
                trabajo_notas=t.get("notas"),
                trabajo_cerrado_en=t.get("cerrado_en"),
                nombre_operario=nombre_op,
            ))

        # Nombre del creador
        nombre_creador = None
        if rep.get("creado_por"):
            usr = db.table("usuarios").select("nombre").eq("id", rep["creado_por"]).single().execute()
            nombre_creador = usr.data.get("nombre") if usr.data else None

        resultado.append(ReprocesoDetalle(
            **rep,
            items_pintura=items_pintura,
            items_repuesto=items_repuesto,
            nombre_creador=nombre_creador,
        ))

    return resultado


# ─────────────────────────────────────────────────────────────────────────────
# GET /reprocesos/{id}  — Detalle
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/{reproceso_id}",
    response_model=ReprocesoDetalle,
    summary="Detalle del reproceso",
)
def detalle_reproceso(
    reproceso_id: str,
    current_user: UserInfo = Depends(get_current_user),
) -> ReprocesoDetalle:
    db = get_supabase()

    # Join con vehiculos para obtener color, concesionario, marca, taller, etc.
    rep_result = db.table("reprocesos").select("*, vehiculos(*)").eq("id", reproceso_id).single().execute()
    if not rep_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reproceso '{reproceso_id}' no encontrado",
        )
    reproceso = rep_result.data

    # Ítems de pintura
    pin_result = (
        db.table("items_reproceso_pintura")
        .select("*")
        .eq("reproceso_id", reproceso_id)
        .execute()
    )
    items_pintura = [ItemPintura(**i) for i in (pin_result.data or [])]

    # Ítems de repuesto
    rep_items_result = (
        db.table("items_reproceso_repuesto")
        .select("*")
        .eq("reproceso_id", reproceso_id)
        .execute()
    )
    items_repuesto = [ItemRepuesto(**i) for i in (rep_items_result.data or [])]

    # Nombre del creador
    nombre_creador = None
    if reproceso.get("creado_por"):
        usr = (
            db.table("usuarios")
            .select("nombre")
            .eq("id", reproceso["creado_por"])
            .single()
            .execute()
        )
        if usr.data:
            nombre_creador = usr.data["nombre"]

    return ReprocesoDetalle(
        **reproceso,
        items_pintura=items_pintura,
        items_repuesto=items_repuesto,
        nombre_creador=nombre_creador,
    )


# ─────────────────────────────────────────────────────────────────────────────
# PATCH /reprocesos/{id}  — Actualizar
# ─────────────────────────────────────────────────────────────────────────────

@router.patch(
    "/{reproceso_id}",
    response_model=ReprocesoDB,
    summary="Actualizar reproceso",
    description="Actualiza notas_cc o estado. Solo control_calidad.",
)
def actualizar_reproceso(
    reproceso_id: str,
    body: ReprocesoActualiza,
    _user: UserInfo = Depends(_cc),
) -> ReprocesoDB:
    db = get_supabase()

    # Construir dict de cambios (solo campos enviados)
    cambios = body.model_dump(exclude_none=True)
    if not cambios:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se enviaron campos a actualizar",
        )

    result = (
        db.table("reprocesos")
        .update(cambios)
        .eq("id", reproceso_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reproceso '{reproceso_id}' no encontrado",
        )

    return ReprocesoDB(**result.data[0])


# ─────────────────────────────────────────────────────────────────────────────
# DELETE /reprocesos/{id}  — Eliminar
# ─────────────────────────────────────────────────────────────────────────────

@router.delete(
    "/{reproceso_id}",
    status_code=status.HTTP_200_OK,
    summary="Eliminar reproceso",
    description="Elimina el reproceso y sus ítems. Solo control_calidad.",
)
def eliminar_reproceso(
    reproceso_id: str,
    _user: UserInfo = Depends(_cc),
) -> dict:
    db = get_supabase()

    # Verificar que exista
    existing = db.table("reprocesos").select("id").eq("id", reproceso_id).single().execute()
    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reproceso '{reproceso_id}' no encontrado",
        )

    # Eliminar ítems primero (FK constraints)
    db.table("items_reproceso_pintura").delete().eq("reproceso_id", reproceso_id).execute()
    db.table("items_reproceso_repuesto").delete().eq("reproceso_id", reproceso_id).execute()

    # Eliminar reproceso
    db.table("reprocesos").delete().eq("id", reproceso_id).execute()
    return {"detail": "Reproceso eliminado"}
