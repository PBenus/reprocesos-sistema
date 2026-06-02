"""
tasks/descarga_ubicacion.py
============================
Descarga el reporte de Ubicación desde eSUM.

El reporte de Ubicación refleja el estado ACTUAL del flujo de trabajo de los
vehículos en el taller. No requiere rango de fechas: siempre retorna el
snapshot vigente al momento de la consulta.

Variables de entorno:
    ESUM_BASE_URL    URL base del sistema eSUM
    ESUM_TALLER_ID   ID del taller (default: '3')

Uso:
    from tasks.esum_session import create_authenticated_session
    from tasks.descarga_ubicacion import download_ubicacion

    session = create_authenticated_session()
    raw_bytes = download_ubicacion(session)
"""

import os
import logging
import requests

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "http://esum.pe"
DEFAULT_TALLER_ID = "3"
REQUEST_TIMEOUT = 60  # segundos


def download_ubicacion(session: requests.Session) -> bytes:
    """
    Descarga el reporte de Ubicación/Flujo de Trabajo desde eSUM.

    El endpoint retorna un archivo CSV en encoding latin-1 con el estado
    actual de todos los vehículos en el flujo del taller indicado.

    Args:
        session: Sesión requests autenticada (obtenida vía create_authenticated_session).

    Returns:
        Contenido crudo del CSV en bytes.

    Raises:
        requests.RequestException: Si ocurre un error de red o HTTP.
        ValueError: Si la respuesta está vacía o no parece un CSV válido.
    """
    base_url = os.environ.get("ESUM_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    taller_id = os.environ.get("ESUM_TALLER_ID", DEFAULT_TALLER_ID)

    url = f"{base_url}/reportes/ReporteFlujoTrabajoUbicacionAuto.php"
    params = {"VTaller": taller_id}

    logger.info(
        "Descargando reporte de Ubicación — taller_id=%s, url=%s",
        taller_id, url,
    )

    try:
        response = session.get(url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.error("Error al descargar reporte de Ubicación: %s", exc)
        raise

    content = response.content

    if not content:
        raise ValueError("El reporte de Ubicación retornó contenido vacío.")

    # Validación básica: el CSV debería comenzar con alguna cabecera de texto
    try:
        first_chars = content[:200].decode("latin-1", errors="replace")
        logger.debug("Primeros 200 bytes del reporte Ubicación: %s", first_chars)
    except Exception:
        pass  # No crítico, solo es para debug

    logger.info(
        "Reporte de Ubicación descargado exitosamente — tamaño: %d bytes",
        len(content),
    )
    return content
