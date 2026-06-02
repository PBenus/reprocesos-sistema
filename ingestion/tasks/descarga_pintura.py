"""
tasks/descarga_pintura.py
==========================
Descarga el reporte de Pintura desde eSUM.

El reporte de Pintura cubre el mes actual completo (desde el día 1 hasta hoy,
hora Lima / America/Lima). El archivo retornado por eSUM tiene extensión .xls
pero en realidad es HTML — debe parsearse como HTML, no como Excel binario.

Variables de entorno:
    ESUM_BASE_URL       URL base del sistema eSUM
    ESUM_USUARIO_ID     ID de usuario interno de eSUM (default: '303')

Uso:
    from tasks.esum_session import create_authenticated_session
    from tasks.descarga_pintura import download_pintura

    session = create_authenticated_session()
    raw_bytes = download_pintura(session)
"""

import os
import logging
from datetime import date, timedelta
import requests

try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except ImportError:
    from backports.zoneinfo import ZoneInfo  # type: ignore

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "http://esum.pe"
DEFAULT_USUARIO_ID = "303"
REQUEST_TIMEOUT = 90  # segundos — el reporte puede demorar


def _get_date_range_current_month() -> tuple[str, str]:
    """
    Retorna (fecha_inicio, fecha_fin) para el mes actual en zona America/Lima.

    fecha_inicio: primer día del mes actual (formato YYYY-MM-DD)
    fecha_fin:    hoy (formato YYYY-MM-DD)
    """
    lima_tz = ZoneInfo("America/Lima")
    from datetime import datetime
    today = datetime.now(lima_tz).date()
    inicio = date(today.year, today.month, 1)
    return inicio.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")


def download_pintura(session: requests.Session) -> bytes:
    """
    Descarga el reporte de Pintura desde eSUM para el mes actual.

    Cubre desde el primer día del mes actual hasta el día de hoy (Lima).
    El reporte se filtra por ESUM_USUARIO_ID para obtener solo los registros
    del usuario correspondiente al taller configurado.

    Args:
        session: Sesión requests autenticada.

    Returns:
        Contenido crudo del reporte en bytes (HTML disfrazado de .xls).

    Raises:
        requests.RequestException: Si ocurre un error de red o HTTP.
        ValueError: Si la respuesta está vacía.
    """
    base_url = os.environ.get("ESUM_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    usuario_id = os.environ.get("ESUM_USUARIO_ID", DEFAULT_USUARIO_ID)

    fecha_inicio, fecha_fin = _get_date_range_current_month()

    url = f"{base_url}/reportes/ReportePintura.php"
    params = {
        "inicio": fecha_inicio,
        "fin": fecha_fin,
        "usuario": usuario_id,
    }

    logger.info(
        "Descargando reporte de Pintura — inicio=%s, fin=%s, usuario=%s",
        fecha_inicio, fecha_fin, usuario_id,
    )

    try:
        response = session.get(url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.error("Error al descargar reporte de Pintura: %s", exc)
        raise

    content = response.content

    if not content:
        raise ValueError("El reporte de Pintura retornó contenido vacío.")

    logger.info(
        "Reporte de Pintura descargado exitosamente — período: %s a %s, tamaño: %d bytes",
        fecha_inicio, fecha_fin, len(content),
    )
    return content
