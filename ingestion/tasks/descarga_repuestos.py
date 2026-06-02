"""
tasks/descarga_repuestos.py
============================
Descarga el reporte de Repuestos desde eSUM.

El reporte de Repuestos cubre desde el primer día del mes ANTERIOR hasta hoy
(hora Lima / America/Lima). Esto asegura capturar registros que puedan haberse
actualizado en los últimos días del mes anterior.

El archivo retornado por eSUM tiene extensión .xls pero es en realidad HTML
con 2 filas de encabezado — debe parsearse como HTML.

Variables de entorno:
    ESUM_BASE_URL    URL base del sistema eSUM

Uso:
    from tasks.esum_session import create_authenticated_session
    from tasks.descarga_repuestos import download_repuestos

    session = create_authenticated_session()
    raw_bytes = download_repuestos(session)
"""

import os
import logging
from datetime import date
import requests

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo  # type: ignore

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "http://esum.pe"
REQUEST_TIMEOUT = 90  # segundos — el reporte puede ser grande


def _get_date_range_prev_month() -> tuple[str, str]:
    """
    Retorna (fecha_inicio, fecha_fin) desde el primer día del mes anterior
    hasta hoy, usando la zona horaria America/Lima.

    fecha_inicio: primer día del mes anterior (YYYY-MM-DD)
    fecha_fin:    hoy (YYYY-MM-DD)
    """
    from datetime import datetime
    lima_tz = ZoneInfo("America/Lima")
    today = datetime.now(lima_tz).date()

    # Calcular el primer día del mes anterior
    if today.month == 1:
        inicio = date(today.year - 1, 12, 1)
    else:
        inicio = date(today.year, today.month - 1, 1)

    return inicio.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")


def download_repuestos(session: requests.Session) -> bytes:
    """
    Descarga el reporte de Repuestos desde eSUM.

    Cubre desde el primer día del mes anterior hasta hoy (Lima).
    Los parámetros VTaller=0 y VInventario=0 indican "todos los talleres"
    y "sin filtro de inventario".

    Args:
        session: Sesión requests autenticada.

    Returns:
        Contenido crudo del reporte en bytes (HTML disfrazado de .xls).

    Raises:
        requests.RequestException: Si ocurre un error de red o HTTP.
        ValueError: Si la respuesta está vacía.
    """
    base_url = os.environ.get("ESUM_BASE_URL", DEFAULT_BASE_URL).rstrip("/")

    fecha_inicio, fecha_fin = _get_date_range_prev_month()

    url = f"{base_url}/reportes/ListaReportesRepuestosGen.php"
    params = {
        "VFecha_Inicio": fecha_inicio,
        "VFecha_Fin": fecha_fin,
        "VTaller": "0",
        "VInventario": "0",
    }

    logger.info(
        "Descargando reporte de Repuestos — inicio=%s, fin=%s",
        fecha_inicio, fecha_fin,
    )

    try:
        response = session.get(url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.error("Error al descargar reporte de Repuestos: %s", exc)
        raise

    content = response.content

    if not content:
        raise ValueError("El reporte de Repuestos retornó contenido vacío.")

    logger.info(
        "Reporte de Repuestos descargado exitosamente — período: %s a %s, tamaño: %d bytes",
        fecha_inicio, fecha_fin, len(content),
    )
    return content
