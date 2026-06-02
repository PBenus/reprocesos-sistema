"""
tasks/parse_ubicacion.py
=========================
Parsea el reporte CSV de Ubicación/Flujo de Trabajo de eSUM.

El archivo CSV tiene las siguientes características:
  - Encoding: latin-1
  - Delimitador: ';'
  - Primera fila: encabezados
  - Columna de días transcurridos: nombre dinámico que incluye la fecha actual,
    empieza con 'D' y contiene 'TRANSCURRIDOS' (ej: "DÍAS TRANSCURRIDOS AL 20/05/2026")

Columnas esperadas (con posible variación de mayúsculas/tildes):
    TALLER, VIN, COLOR, FECHA PLANIFICADA, FECHA DE INGRESO A FLUJO,
    DÍAS TRANSCURRIDOS... (dinámica), MODELO, MARCA, PROCESO, ESTADO,
    CONCESIONARIO, OBSERVACIONES

Uso:
    from tasks.parse_ubicacion import parse_ubicacion
    records = parse_ubicacion(csv_bytes)
"""

import csv
import logging
from datetime import datetime
from io import StringIO
from typing import Optional

logger = logging.getLogger(__name__)

DATE_FORMATS = ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%y"]


def _parse_date(value: str) -> Optional[str]:
    """
    Convierte una cadena de fecha a formato ISO (YYYY-MM-DD).

    Intenta múltiples formatos comunes en eSUM.
    Retorna None si el valor está vacío o no puede parsearse.
    """
    if not value or not value.strip():
        return None
    val = value.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(val, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    logger.warning("No se pudo parsear fecha: '%s'", val)
    return None


def _parse_int(value: str) -> Optional[int]:
    """
    Convierte una cadena a entero. Retorna None si está vacío o no es numérico.
    """
    if not value or not value.strip():
        return None
    try:
        return int(value.strip())
    except (ValueError, TypeError):
        logger.warning("No se pudo convertir a entero: '%s'", value)
        return None


def _find_dias_key(row_keys) -> Optional[str]:
    """
    Busca la columna de días transcurridos (nombre dinámico con fecha).
    La columna empieza con 'D' y contiene 'TRANSCURRIDOS' en mayúsculas.

    Args:
        row_keys: Iterable con los nombres de columnas del DictReader.

    Returns:
        Nombre de la columna encontrada, o None si no existe.
    """
    for key in row_keys:
        key_upper = key.upper()
        if key_upper.startswith("D") and "TRANSCURRIDOS" in key_upper:
            return key
    return None


def parse_ubicacion(content: bytes) -> list[dict]:
    """
    Parsea el contenido CSV del reporte de Ubicación de eSUM.

    Args:
        content: Bytes del archivo CSV (encoding latin-1, delimitador ';').

    Returns:
        Lista de diccionarios con los registros parseados y normalizados.
        Cada diccionario contiene:
            taller, vin, color, fecha_planificada, fecha_ingreso_flujo,
            dias_transcurridos, modelo, marca, proceso, estado,
            concesionario, observaciones

    Raises:
        ValueError: Si el contenido está vacío o no tiene las columnas esperadas.
    """
    if not content:
        raise ValueError("El contenido del reporte de Ubicación está vacío.")

    # Decodificar con latin-1 (encoding nativo de eSUM)
    try:
        text = content.decode("latin-1")
    except UnicodeDecodeError as exc:
        logger.error("Error decodificando CSV de Ubicación: %s", exc)
        raise ValueError(f"No se pudo decodificar el CSV de Ubicación: {exc}") from exc

    records = []
    reader = csv.DictReader(StringIO(text), delimiter=";")

    # Obtener nombres de columnas del primer registro (o del fieldnames)
    dias_key = None  # Se determina en la primera fila

    row_count = 0
    for row in reader:
        row_count += 1

        # Determinar la columna dinámica de días en la primera fila
        if dias_key is None:
            dias_key = _find_dias_key(row.keys())
            if dias_key is None:
                logger.warning(
                    "No se encontró columna 'DÍAS TRANSCURRIDOS'. "
                    "Columnas disponibles: %s",
                    list(row.keys()),
                )

        # Mapeo de columnas con .get() seguro para evitar KeyError
        record = {
            "taller": (row.get("TALLER") or "").strip() or None,
            "vin": (row.get("VIN") or "").strip() or None,
            "color": (row.get("COLOR") or "").strip() or None,
            "fecha_planificada": _parse_date(row.get("FECHA PLANIFICADA", "")),
            "fecha_ingreso_flujo": _parse_date(row.get("FECHA DE INGRESO A FLUJO", "")),
            "dias_transcurridos": _parse_int(row.get(dias_key, "") if dias_key else ""),
            "modelo": (row.get("MODELO") or "").strip() or None,
            "marca": (row.get("MARCA") or "").strip() or None,
            "proceso": (row.get("PROCESO") or "").strip() or None,
            "estado": (row.get("ESTADO") or "").strip() or None,
            "concesionario": (row.get("CONCESIONARIO") or "").strip() or None,
            "observaciones": (row.get("OBSERVACIONES") or "").strip() or None,
        }

        # Filtrar filas donde el VIN está vacío (filas de totales o vacías)
        if not record["vin"]:
            logger.debug("Fila %d ignorada (VIN vacío)", row_count)
            continue

        records.append(record)

    logger.info(
        "Parse de Ubicación completado — %d filas leídas, %d registros válidos",
        row_count, len(records),
    )
    return records
