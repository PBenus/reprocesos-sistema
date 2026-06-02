"""
routers/items.py
Endpoints para agregar/eliminar ítems de reproceso (pintura y repuesto).
Solo accesible para control_calidad.
Prefijo: /reprocesos/{reproceso_id}/items
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from auth.models import UserInfo
from auth.utils import require_role
from database import get_supabase
from schemas.reproceso import ItemCrea, ItemPintura, ItemRepuesto

router = APIRouter(
    prefix="/reprocesos/{reproceso_id}/items",
    tags=["Ítems de Reproceso"],
)

_cc = require_role("control_calidad")


def _verificar_reproceso(reproceso_id: str) -> None:
    """Lanza 404 si el reproceso no existe."""
    db = get_supabase()
    existing = db.table("reprocesos").select("id").eq("id", reproceso_id).single().execute()
    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reproceso '{reproceso_id}' no encontrado",
        )


# ─────────────────────────────────────────────────────────────────────────────
# POST /reprocesos/{reproceso_id}/items/pintura
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/pintura",
    response_model=ItemPintura,
    status_code=status.HTTP_201_CREATED,
    summary="Agregar ítem de pintura",
)
def agregar_item_pintura(
    reproceso_id: str,
    body: ItemCrea,
    _user: UserInfo = Depends(_cc),
) -> ItemPintura:
    _verificar_reproceso(reproceso_id)
    db = get_supabase()

    nuevo = {
        "reproceso_id": reproceso_id,
        "seccion": body.seccion,
        "observacion": body.observacion,
        "estado": "pendiente",
    }
    result = db.table("items_reproceso_pintura").insert(nuevo).execute()
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al agregar el ítem de pintura",
        )
    return ItemPintura(**result.data[0])


# ─────────────────────────────────────────────────────────────────────────────
# POST /reprocesos/{reproceso_id}/items/repuesto
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/repuesto",
    response_model=ItemRepuesto,
    status_code=status.HTTP_201_CREATED,
    summary="Agregar ítem de repuesto",
)
def agregar_item_repuesto(
    reproceso_id: str,
    body: ItemCrea,
    _user: UserInfo = Depends(_cc),
) -> ItemRepuesto:
    _verificar_reproceso(reproceso_id)
    db = get_supabase()

    nuevo = {
        "reproceso_id": reproceso_id,
        "seccion": body.seccion,
        "observacion": body.observacion,
        "estado": "pendiente",
    }
    result = db.table("items_reproceso_repuesto").insert(nuevo).execute()
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al agregar el ítem de repuesto",
        )
    return ItemRepuesto(**result.data[0])


# ─────────────────────────────────────────────────────────────────────────────
# DELETE /reprocesos/{reproceso_id}/items/pintura/{item_id}
# ─────────────────────────────────────────────────────────────────────────────

@router.delete(
    "/pintura/{item_id}",
    status_code=status.HTTP_200_OK,
    summary="Eliminar ítem de pintura",
)
def eliminar_item_pintura(
    reproceso_id: str,
    item_id: str,
    _user: UserInfo = Depends(_cc),
) -> dict:
    db = get_supabase()

    existing = (
        db.table("items_reproceso_pintura")
        .select("id")
        .eq("id", item_id)
        .eq("reproceso_id", reproceso_id)
        .single()
        .execute()
    )
    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ítem de pintura '{item_id}' no encontrado en este reproceso",
        )

    db.table("items_reproceso_pintura").delete().eq("id", item_id).execute()
    return {"detail": "Ítem eliminado"}


# ─────────────────────────────────────────────────────────────────────────────
# DELETE /reprocesos/{reproceso_id}/items/repuesto/{item_id}
# ─────────────────────────────────────────────────────────────────────────────

@router.delete(
    "/repuesto/{item_id}",
    status_code=status.HTTP_200_OK,
    summary="Eliminar ítem de repuesto",
)
def eliminar_item_repuesto(
    reproceso_id: str,
    item_id: str,
    _user: UserInfo = Depends(_cc),
) -> dict:
    db = get_supabase()

    existing = (
        db.table("items_reproceso_repuesto")
        .select("id")
        .eq("id", item_id)
        .eq("reproceso_id", reproceso_id)
        .single()
        .execute()
    )
    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ítem de repuesto '{item_id}' no encontrado en este reproceso",
        )

    db.table("items_reproceso_repuesto").delete().eq("id", item_id).execute()
    return {"detail": "Ítem eliminado"}
