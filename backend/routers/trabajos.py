"""
routers/trabajos.py
Endpoints para gestión de trabajos de operarios.
- operario_pintura: trabaja sobre items_reproceso_pintura / trabajos_pintura
- operario_repuesto: trabaja sobre items_reproceso_repuesto / trabajos_repuesto
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from auth.models import UserInfo
from auth.utils import require_role, get_current_user
from database import get_supabase
from schemas.trabajo import TrabajoCierra, TrabajoCrea, TrabajoDB, TrabajoHistorico

router = APIRouter(prefix="/trabajos", tags=["Trabajos"])

_pin = require_role("operario_pintura")
_rep = require_role("operario_repuesto")


def _now_iso() -> str:
    """Retorna la fecha/hora actual en ISO 8601 UTC."""
    return datetime.now(tz=timezone.utc).isoformat()


# ═════════════════════════════════════════════════════════════════════════════
# PINTURA
# ═════════════════════════════════════════════════════════════════════════════

@router.post(
    "/pintura",
    response_model=TrabajoDB,
    status_code=status.HTTP_201_CREATED,
    summary="Iniciar trabajo de pintura",
    description="El operario toma un ítem de pintura pendiente y lo pone en proceso.",
)
def iniciar_trabajo_pintura(
    body: TrabajoCrea,
    current_user: UserInfo = Depends(_pin),
) -> TrabajoDB:
    db = get_supabase()

    # Verificar que el ítem exista y esté pendiente
    item = (
        db.table("items_reproceso_pintura")
        .select("id, estado")
        .eq("id", body.item_id)
        .single()
        .execute()
    )
    if not item.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ítem de pintura no encontrado")
    if item.data["estado"] != "pendiente":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El ítem ya está en estado '{item.data['estado']}'",
        )

    # Verificar que no exista ya un trabajo abierto para este ítem
    trabajo_existente = (
        db.table("trabajos_pintura")
        .select("id")
        .eq("item_id", body.item_id)
        .eq("estado", "abierto")
        .execute()
    )
    if trabajo_existente.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un trabajo abierto para este ítem",
        )

    # Crear el trabajo
    nuevo = {
        "item_id": body.item_id,
        "operario_id": current_user.id,
        "abierto_en": _now_iso(),
        "estado": "abierto",
    }
    result = db.table("trabajos_pintura").insert(nuevo).execute()
    if not result.data:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al crear el trabajo")

    # Cambiar estado del ítem a en_proceso
    db.table("items_reproceso_pintura").update({"estado": "en_proceso"}).eq("id", body.item_id).execute()

    return TrabajoDB(**result.data[0])


def _check_and_update_reproceso_status(db, reproceso_id: str):
    """
    Verifica si todos los ítems del reproceso están subsanados.
    Si todos lo están (y hay al menos 1), cambia el estado a 'por_validar'.
    """
    pin_items = db.table("items_reproceso_pintura").select("estado").eq("reproceso_id", reproceso_id).execute()
    rep_items = db.table("items_reproceso_repuesto").select("estado").eq("reproceso_id", reproceso_id).execute()

    pin_data = pin_items.data or []
    rep_data = rep_items.data or []
    total    = len(pin_data) + len(rep_data)

    # Debe haber al menos 1 ítem y todos deben estar subsanados
    if total == 0:
        return

    todos_subsanados = (
        all(i["estado"] == "subsanado" for i in pin_data) and
        all(i["estado"] == "subsanado" for i in rep_data)
    )

    if todos_subsanados:
        db.table("reprocesos").update({"estado": "por_validar"}).eq("id", reproceso_id).execute()


@router.patch(
    "/pintura/{trabajo_id}/cerrar",
    response_model=TrabajoDB,
    summary="Cerrar trabajo de pintura",
    description="El operario cierra el trabajo con foto de evidencia y notas.",
)
def cerrar_trabajo_pintura(
    trabajo_id: str,
    body: TrabajoCierra,
    current_user: UserInfo = Depends(_pin),
) -> TrabajoDB:
    db = get_supabase()

    # Verificar que el trabajo exista y pertenezca al operario
    # Traemos item_id en la misma query para evitar un round-trip extra
    trabajo = (
        db.table("trabajos_pintura")
        .select("id, estado, item_id, operario_id")
        .eq("id", trabajo_id)
        .eq("operario_id", current_user.id)
        .single()
        .execute()
    )
    if not trabajo.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trabajo no encontrado o no pertenece a este operario",
        )
    if trabajo.data["estado"] == "cerrado":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El trabajo ya fue cerrado")

    item_id = trabajo.data["item_id"]

    # Obtener reproceso_id del ítem (necesario para verificar estado global)
    item_data = (
        db.table("items_reproceso_pintura")
        .select("reproceso_id")
        .eq("id", item_id)
        .single()
        .execute()
    )
    reproceso_id = item_data.data.get("reproceso_id") if item_data.data else None

    # Cerrar el trabajo y marcar ítem como subsanado en paralelo (dos updates)
    cambios = {
        "cerrado_en": _now_iso(),
        "estado": "cerrado",
        "foto_url": body.foto_url,
        "notas": body.notas,
    }
    result = db.table("trabajos_pintura").update(cambios).eq("id", trabajo_id).execute()
    db.table("items_reproceso_pintura").update({"estado": "subsanado"}).eq("id", item_id).execute()

    # Verificar estado global del reproceso
    if reproceso_id:
        _check_and_update_reproceso_status(db, reproceso_id)

    return TrabajoDB(**result.data[0])

@router.get(
    "/pintura/mis-trabajos",
    response_model=List[TrabajoHistorico],
    summary="Mis trabajos de pintura",
    description="Lista todos los trabajos (abiertos y cerrados) del operario actual.",
)
def mis_trabajos_pintura(
    current_user: UserInfo = Depends(_pin),
) -> List[TrabajoHistorico]:
    db = get_supabase()

    trabajos_result = (
        db.table("trabajos_pintura")
        .select("*")
        .eq("operario_id", current_user.id)
        .order("abierto_en", desc=True)
        .execute()
    )
    trabajos = trabajos_result.data or []

    resultado: List[TrabajoHistorico] = []
    for t in trabajos:
        # Obtener info del ítem
        item_r = db.table("items_reproceso_pintura").select("*").eq("id", t["item_id"]).single().execute()
        item = item_r.data or {}

        # Obtener info del reproceso → VIN
        reproceso_id = item.get("reproceso_id")
        vin = None
        modelo = None
        nombre_creador = None
        if reproceso_id:
            rep_r = db.table("reprocesos").select("*").eq("id", reproceso_id).single().execute()
            rep = rep_r.data or {}
            vin = rep.get("vin")
            creado_por = rep.get("creado_por")
            if vin:
                veh_r = db.table("vehiculos").select("modelo").eq("vin", vin).single().execute()
                if veh_r.data:
                    modelo = veh_r.data.get("modelo")
            if creado_por:
                usr_r = db.table("usuarios").select("nombre").eq("id", creado_por).single().execute()
                if usr_r.data:
                    nombre_creador = usr_r.data.get("nombre")

        resultado.append(
            TrabajoHistorico(
                **t,
                seccion=item.get("seccion"),
                observacion_item=item.get("observacion"),
                vin=vin,
                modelo=modelo,
                nombre_creador=nombre_creador,
                nombre_operario=current_user.nombre,
            )
        )

    return resultado


# ═════════════════════════════════════════════════════════════════════════════
# REPUESTO
# ═════════════════════════════════════════════════════════════════════════════

@router.post(
    "/repuesto",
    response_model=TrabajoDB,
    status_code=status.HTTP_201_CREATED,
    summary="Iniciar trabajo de repuesto",
)
def iniciar_trabajo_repuesto(
    body: TrabajoCrea,
    current_user: UserInfo = Depends(_rep),
) -> TrabajoDB:
    db = get_supabase()

    item = (
        db.table("items_reproceso_repuesto")
        .select("id, estado")
        .eq("id", body.item_id)
        .single()
        .execute()
    )
    if not item.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ítem de repuesto no encontrado")
    if item.data["estado"] != "pendiente":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El ítem ya está en estado '{item.data['estado']}'",
        )

    trabajo_existente = (
        db.table("trabajos_repuesto")
        .select("id")
        .eq("item_id", body.item_id)
        .eq("estado", "abierto")
        .execute()
    )
    if trabajo_existente.data:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe un trabajo abierto para este ítem")

    nuevo = {
        "item_id": body.item_id,
        "operario_id": current_user.id,
        "abierto_en": _now_iso(),
        "estado": "abierto",
    }
    result = db.table("trabajos_repuesto").insert(nuevo).execute()
    if not result.data:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al crear el trabajo")

    db.table("items_reproceso_repuesto").update({"estado": "en_proceso"}).eq("id", body.item_id).execute()

    return TrabajoDB(**result.data[0])


@router.patch(
    "/repuesto/{trabajo_id}/cerrar",
    response_model=TrabajoDB,
    summary="Cerrar trabajo de repuesto",
)
def cerrar_trabajo_repuesto(
    trabajo_id: str,
    body: TrabajoCierra,
    current_user: UserInfo = Depends(_rep),
) -> TrabajoDB:
    db = get_supabase()

    trabajo = (
        db.table("trabajos_repuesto")
        .select("id, estado, item_id, operario_id")
        .eq("id", trabajo_id)
        .eq("operario_id", current_user.id)
        .single()
        .execute()
    )
    if not trabajo.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trabajo no encontrado o no pertenece a este operario",
        )
    if trabajo.data["estado"] == "cerrado":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El trabajo ya fue cerrado")

    item_id = trabajo.data["item_id"]

    # Obtener reproceso_id antes de marcar subsanado
    item_data = (
        db.table("items_reproceso_repuesto")
        .select("reproceso_id")
        .eq("id", item_id)
        .single()
        .execute()
    )
    reproceso_id = item_data.data.get("reproceso_id") if item_data.data else None

    cambios = {
        "cerrado_en": _now_iso(),
        "estado": "cerrado",
        "foto_url": body.foto_url,
        "notas": body.notas,
    }
    result = db.table("trabajos_repuesto").update(cambios).eq("id", trabajo_id).execute()
    db.table("items_reproceso_repuesto").update({"estado": "subsanado"}).eq("id", item_id).execute()

    if reproceso_id:
        _check_and_update_reproceso_status(db, reproceso_id)

    return TrabajoDB(**result.data[0])


@router.get(
    "/repuesto/mis-trabajos",
    response_model=List[TrabajoHistorico],
    summary="Mis trabajos de repuesto",
)
def mis_trabajos_repuesto(
    current_user: UserInfo = Depends(_rep),
) -> List[TrabajoHistorico]:
    db = get_supabase()

    trabajos_result = (
        db.table("trabajos_repuesto")
        .select("*")
        .eq("operario_id", current_user.id)
        .order("abierto_en", desc=True)
        .execute()
    )
    trabajos = trabajos_result.data or []

    resultado: List[TrabajoHistorico] = []
    for t in trabajos:
        item_r = db.table("items_reproceso_repuesto").select("*").eq("id", t["item_id"]).single().execute()
        item = item_r.data or {}

        reproceso_id = item.get("reproceso_id")
        vin = None
        modelo = None
        nombre_creador = None
        if reproceso_id:
            rep_r = db.table("reprocesos").select("*").eq("id", reproceso_id).single().execute()
            rep = rep_r.data or {}
            vin = rep.get("vin")
            creado_por = rep.get("creado_por")
            if vin:
                veh_r = db.table("vehiculos").select("modelo").eq("vin", vin).single().execute()
                if veh_r.data:
                    modelo = veh_r.data.get("modelo")
            if creado_por:
                usr_r = db.table("usuarios").select("nombre").eq("id", creado_por).single().execute()
                if usr_r.data:
                    nombre_creador = usr_r.data.get("nombre")

        resultado.append(
            TrabajoHistorico(
                **t,
                seccion=item.get("seccion"),
                observacion_item=item.get("observacion"),
                vin=vin,
                modelo=modelo,
                nombre_creador=nombre_creador,
                nombre_operario=current_user.nombre,
            )
        )

    return resultado


# ═════════════════════════════════════════════════════════════════════════════
# GET por ítem — Para que CC vea las fotos/operarios en ValidarReproceso
# ═════════════════════════════════════════════════════════════════════════════

@router.get(
    "/pintura/item/{item_id}",
    response_model=List[TrabajoDB],
    summary="Trabajos de pintura de un ítem",
    description="Retorna todos los trabajos asociados a un ítem de pintura (para CC).",
)
def trabajos_pintura_por_item(
    item_id: str,
    current_user: UserInfo = Depends(get_current_user),
) -> List[TrabajoDB]:
    db = get_supabase()
    result = (
        db.table("trabajos_pintura")
        .select("*, usuarios(nombre)")
        .eq("item_id", item_id)
        .order("abierto_en", desc=True)
        .execute()
    )
    trabajos = []
    for t in (result.data or []):
        nombre_operario = t.pop("usuarios", {}) or {}
        t["nombre_operario"] = nombre_operario.get("nombre") if isinstance(nombre_operario, dict) else None
        trabajos.append(TrabajoDB(**t))
    return trabajos


@router.get(
    "/repuesto/item/{item_id}",
    response_model=List[TrabajoDB],
    summary="Trabajos de repuesto de un ítem",
    description="Retorna todos los trabajos asociados a un ítem de repuesto (para CC).",
)
def trabajos_repuesto_por_item(
    item_id: str,
    current_user: UserInfo = Depends(get_current_user),
) -> List[TrabajoDB]:
    db = get_supabase()
    result = (
        db.table("trabajos_repuesto")
        .select("*, usuarios(nombre)")
        .eq("item_id", item_id)
        .order("abierto_en", desc=True)
        .execute()
    )
    trabajos = []
    for t in (result.data or []):
        nombre_operario = t.pop("usuarios", {}) or {}
        t["nombre_operario"] = nombre_operario.get("nombre") if isinstance(nombre_operario, dict) else None
        trabajos.append(TrabajoDB(**t))
    return trabajos
