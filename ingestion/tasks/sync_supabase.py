"""
tasks/sync_supabase.py
=======================
Sincroniza los datos parseados de los reportes eSUM hacia Supabase.

Estrategias de sincronización:
  - vehiculos:      UPSERT por VIN (siempre actualiza si ya existe)
  - danos_pintura:  DELETE del mes actual + INSERT (reemplaza datos del mes)
  - danos_repuesto: DELETE desde inicio del mes anterior hasta hoy + INSERT

Todas las operaciones se ejecutan en batches de 500 registros para evitar
timeouts y respetar los límites de la API de Supabase.

Variables de entorno requeridas:
    SUPABASE_URL         URL del proyecto Supabase
    SUPABASE_SERVICE_KEY Clave de servicio (service_role) con acceso completo

Uso:
    from tasks.sync_supabase import sync_vehiculos, sync_danos_pintura, sync_danos_repuesto, log_sync

    result = sync_vehiculos(records)
    result = sync_danos_pintura(records)
    result = sync_danos_repuesto(records)
    log_sync("PINTURA", "OK", 150, "Sync exitoso")
"""

import os
import logging
from datetime import datetime, date
from typing import Optional

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo  # type: ignore

from supabase import create_client, Client

logger = logging.getLogger(__name__)

BATCH_SIZE = 500
LIMA_TZ = ZoneInfo("America/Lima")

# ──────────────────────────────────────────────
# Cliente Supabase (singleton por proceso)
# ──────────────────────────────────────────────
_supabase_client: Optional[Client] = None


def _get_client() -> Client:
    """
    Retorna el cliente Supabase, creándolo si no existe.
    Usa SUPABASE_URL y SUPABASE_SERVICE_KEY del entorno.
    """
    global _supabase_client
    if _supabase_client is None:
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_KEY")

        if not url or not key:
            raise EnvironmentError(
                "Variables SUPABASE_URL y SUPABASE_SERVICE_KEY son requeridas."
            )

        _supabase_client = create_client(url, key)
        logger.info("Cliente Supabase inicializado para URL: %s", url[:40] + "...")

    return _supabase_client


def _chunk(lst: list, size: int):
    """Divide una lista en chunks de tamaño 'size'."""
    for i in range(0, len(lst), size):
        yield lst[i: i + size]


def _now_lima_iso() -> str:
    """Retorna el datetime actual en Lima como string ISO."""
    return datetime.now(LIMA_TZ).isoformat()


def _today_lima() -> date:
    """Retorna la fecha actual en Lima."""
    return datetime.now(LIMA_TZ).date()


# ──────────────────────────────────────────────
# Funciones de sincronización
# ──────────────────────────────────────────────

def sync_vehiculos(records: list[dict]) -> dict:
    """
    UPSERT de vehículos en la tabla 'vehiculos' de Supabase.

    Conflicto resuelto por la columna 'vin'. Si el VIN ya existe,
    actualiza todos los campos. Agrega 'sincronizado_en' con timestamp actual.

    Args:
        records: Lista de dicts con campos del reporte de Ubicación.

    Returns:
        dict con claves 'procesados' (int) y 'errores' (int).
    """
    if not records:
        logger.warning("sync_vehiculos: no hay registros para procesar.")
        return {"procesados": 0, "errores": 0}

    client = _get_client()
    now_iso = _now_lima_iso()
    procesados = 0
    errores = 0

    # Agregar timestamp de sincronización a cada registro
    enriched = [{**rec, "sincronizado_en": now_iso} for rec in records]

    logger.info("sync_vehiculos: iniciando UPSERT de %d registros en batches de %d",
                len(enriched), BATCH_SIZE)

    for batch_num, batch in enumerate(_chunk(enriched, BATCH_SIZE), start=1):
        try:
            response = (
                client.table("vehiculos")
                .upsert(batch, on_conflict="vin")
                .execute()
            )
            procesados += len(batch)
            logger.debug(
                "sync_vehiculos: batch %d — %d registros insertados/actualizados",
                batch_num, len(batch),
            )
        except Exception as exc:
            errores += len(batch)
            logger.error(
                "sync_vehiculos: error en batch %d: %s", batch_num, exc
            )

    logger.info(
        "sync_vehiculos finalizado — procesados: %d, errores: %d",
        procesados, errores,
    )
    return {"procesados": procesados, "errores": errores}


def sync_danos_pintura(records: list[dict]) -> dict:
    """
    Reemplaza los registros de daños de pintura del mes actual.

    Estrategia:
      1. DELETE de 'danos_pintura' donde fecha_hora esté en el mes actual.
      2. INSERT de los nuevos registros en batches.

    Args:
        records: Lista de dicts con campos del reporte de Pintura.

    Returns:
        dict con claves 'procesados' (int) y 'errores' (int).
    """
    client = _get_client()
    today = _today_lima()

    # Rango del mes actual
    inicio_mes = date(today.year, today.month, 1)
    fin_mes = date(today.year, today.month + 1, 1) if today.month < 12 \
        else date(today.year + 1, 1, 1)

    inicio_iso = inicio_mes.strftime("%Y-%m-%dT00:00:00")
    fin_iso = fin_mes.strftime("%Y-%m-%dT00:00:00")

    logger.info(
        "sync_danos_pintura: DELETE en danos_pintura de %s a %s",
        inicio_iso, fin_iso,
    )

    try:
        client.table("danos_pintura") \
            .delete() \
            .gte("fecha_hora", inicio_iso) \
            .lt("fecha_hora", fin_iso) \
            .execute()
        logger.info("sync_danos_pintura: DELETE completado.")
    except Exception as exc:
        logger.error("sync_danos_pintura: error en DELETE: %s", exc)
        return {"procesados": 0, "errores": len(records)}

    if not records:
        logger.warning("sync_danos_pintura: no hay registros para insertar.")
        return {"procesados": 0, "errores": 0}

    procesados = 0
    errores = 0

    logger.info(
        "sync_danos_pintura: INSERT de %d registros en batches de %d",
        len(records), BATCH_SIZE,
    )

    for batch_num, batch in enumerate(_chunk(records, BATCH_SIZE), start=1):
        try:
            client.table("danos_pintura").insert(batch).execute()
            procesados += len(batch)
            logger.debug(
                "sync_danos_pintura: batch %d — %d registros insertados",
                batch_num, len(batch),
            )
        except Exception as exc:
            errores += len(batch)
            logger.error(
                "sync_danos_pintura: error en batch %d: %s", batch_num, exc
            )

    logger.info(
        "sync_danos_pintura finalizado — procesados: %d, errores: %d",
        procesados, errores,
    )
    return {"procesados": procesados, "errores": errores}


def sync_danos_repuesto(records: list[dict]) -> dict:
    """
    Reemplaza los registros de daños de repuesto del período actual.

    Período: desde el primer día del mes anterior hasta hoy.

    Estrategia:
      1. DELETE de 'danos_repuesto' en el rango de fechas.
      2. INSERT de los nuevos registros en batches.

    Args:
        records: Lista de dicts con campos del reporte de Repuestos.

    Returns:
        dict con claves 'procesados' (int) y 'errores' (int).
    """
    client = _get_client()
    today = _today_lima()

    # Calcular primer día del mes anterior
    if today.month == 1:
        inicio = date(today.year - 1, 12, 1)
    else:
        inicio = date(today.year, today.month - 1, 1)

    # Fin: mañana para incluir todos los registros de hoy
    from datetime import timedelta
    fin = today + timedelta(days=1)

    inicio_iso = inicio.strftime("%Y-%m-%d")
    fin_iso = fin.strftime("%Y-%m-%d")

    logger.info(
        "sync_danos_repuesto: DELETE en danos_repuesto de %s a %s",
        inicio_iso, fin_iso,
    )

    try:
        client.table("danos_repuesto") \
            .delete() \
            .gte("fecha_registro", inicio_iso) \
            .lt("fecha_registro", fin_iso) \
            .execute()
        logger.info("sync_danos_repuesto: DELETE completado.")
    except Exception as exc:
        logger.error("sync_danos_repuesto: error en DELETE: %s", exc)
        return {"procesados": 0, "errores": len(records)}

    if not records:
        logger.warning("sync_danos_repuesto: no hay registros para insertar.")
        return {"procesados": 0, "errores": 0}

    procesados = 0
    errores = 0

    logger.info(
        "sync_danos_repuesto: INSERT de %d registros en batches de %d",
        len(records), BATCH_SIZE,
    )

    for batch_num, batch in enumerate(_chunk(records, BATCH_SIZE), start=1):
        try:
            client.table("danos_repuesto").insert(batch).execute()
            procesados += len(batch)
            logger.debug(
                "sync_danos_repuesto: batch %d — %d registros insertados",
                batch_num, len(batch),
            )
        except Exception as exc:
            errores += len(batch)
            logger.error(
                "sync_danos_repuesto: error en batch %d: %s", batch_num, exc
            )

    logger.info(
        "sync_danos_repuesto finalizado — procesados: %d, errores: %d",
        procesados, errores,
    )
    return {"procesados": procesados, "errores": errores}


def log_sync(reporte: str, estado: str, filas: int, mensaje: str) -> None:
    """
    Registra el resultado de una sincronización en la tabla 'sync_log'.

    Args:
        reporte: Nombre del reporte ('UBICACION', 'PINTURA', 'REPUESTO').
        estado:  Estado de la operación ('OK', 'ERROR', 'PARCIAL').
        filas:   Cantidad de filas procesadas.
        mensaje: Mensaje descriptivo del resultado o error.
    """
    client = _get_client()

    log_entry = {
        "reporte": reporte,
        "estado": estado,
        "filas": filas,
        "mensaje": mensaje,
        "ejecutado_en": _now_lima_iso(),
    }

    try:
        client.table("sync_log").insert(log_entry).execute()
        logger.info(
            "log_sync: registrado — reporte=%s, estado=%s, filas=%d",
            reporte, estado, filas,
        )
    except Exception as exc:
        # No propagar: el log no debe romper el flujo principal
        logger.error("log_sync: error al insertar en sync_log: %s", exc)
