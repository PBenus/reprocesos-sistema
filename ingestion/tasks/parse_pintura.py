"""
tasks/parse_pintura.py
=======================
Parsea el reporte de Pintura de eSUM (HTML disfrazado de .xls).

El archivo que entrega eSUM tiene extensión .xls pero en realidad es una
tabla HTML. Se usa BeautifulSoup para extraer los datos.

Estructura esperada:
  - Una tabla HTML principal
  - Primera fila (índice 0): encabezados
  - Filas siguientes: datos

Encabezados esperados (en orden):
    'Fecha / Hora', 'VIN', 'Marca', 'Modelo', 'Procedencia', 'Sección',
    'Diag. eSUM', 'Validación', 'Núm. Paños', 'Comentario', 'Colaborador'

Mapeo de salida:
    fecha_hora, vin, marca, modelo, procedencia, seccion,
    diagnostico_esum, validacion, num_panos, comentario, colaborador

Uso:
    from tasks.parse_pintura import parse_pintura
    records = parse_pintura(html_bytes)
"""

import logging
from datetime import datetime
from typing import Optional

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Encabezados esperados y su mapeo a nombres de campo normalizados
HEADER_MAP = {
    "Fecha / Hora": "fecha_hora",
    "VIN": "vin",
    "Marca": "marca",
    "Modelo": "modelo",
    "Procedencia": "procedencia",
    "Sección": "seccion",
    "Diag. eSUM": "diagnostico_esum",
    "Validación": "validacion",
    "Núm. Paños": "num_panos",
    "Comentario": "comentario",
    "Colaborador": "colaborador",
}

DATETIME_FORMATS = [
    "%d/%m/%Y %H:%M",
    "%d/%m/%Y %H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%d/%m/%Y",
    "%Y-%m-%d",
]


def _parse_datetime(value: str) -> Optional[str]:
    """
    Convierte una cadena de fecha/hora a formato ISO (YYYY-MM-DDTHH:MM:SS).
    Retorna None si el valor está vacío o no puede parsearse.
    """
    if not value or not value.strip():
        return None
    val = value.strip()
    for fmt in DATETIME_FORMATS:
        try:
            return datetime.strptime(val, fmt).strftime("%Y-%m-%dT%H:%M:%S")
        except ValueError:
            continue
    logger.warning("No se pudo parsear fecha/hora: '%s'", val)
    return None


def _parse_float(value: str) -> Optional[float]:
    """
    Convierte una cadena a float. Acepta comas o puntos como decimal.
    Retorna None si está vacío o no es numérico.
    """
    if not value or not value.strip():
        return None
    val = value.strip().replace(",", ".")
    try:
        return float(val)
    except (ValueError, TypeError):
        logger.warning("No se pudo convertir a float: '%s'", value)
        return None


def _extract_table_rows(soup: BeautifulSoup) -> list[list[str]]:
    """
    Extrae todas las filas de la primera tabla HTML encontrada.

    Returns:
        Lista de listas de strings, donde cada lista interior es una fila.
    """
    table = soup.find("table")
    if not table:
        raise ValueError("No se encontró ninguna tabla HTML en el reporte de Pintura.")

    rows = []
    for tr in table.find_all("tr"):
        cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
        if cells:
            rows.append(cells)
    return rows


def parse_pintura(content: bytes) -> list[dict]:
    """
    Parsea el contenido HTML del reporte de Pintura de eSUM.

    Args:
        content: Bytes del archivo (HTML con extensión .xls, encoding latin-1).

    Returns:
        Lista de diccionarios con los registros parseados y normalizados.
        Cada diccionario contiene:
            fecha_hora, vin, marca, modelo, procedencia, seccion,
            diagnostico_esum, validacion, num_panos, comentario, colaborador

    Raises:
        ValueError: Si el contenido está vacío, no contiene tabla, o los
                    encabezados no coinciden con lo esperado.
    """
    if not content:
        raise ValueError("El contenido del reporte de Pintura está vacío.")

    # Decodificar con latin-1
    try:
        html_text = content.decode("latin-1", errors="replace")
    except Exception as exc:
        raise ValueError(f"No se pudo decodificar el HTML de Pintura: {exc}") from exc

    soup = BeautifulSoup(html_text, "html.parser")
    rows = _extract_table_rows(soup)

    if len(rows) < 2:
        logger.warning(
            "El reporte de Pintura tiene menos de 2 filas (header + data). "
            "Posiblemente no hay datos para el período consultado."
        )
        return []

    # La primera fila es el header
    raw_headers = rows[0]
    logger.debug("Encabezados encontrados en Pintura: %s", raw_headers)

    # Construir mapeo posición → campo normalizado
    field_map = {}
    for idx, raw_header in enumerate(raw_headers):
        header_clean = raw_header.strip()
        if header_clean in HEADER_MAP:
            field_map[idx] = HEADER_MAP[header_clean]
        else:
            # Intentar match insensible a acentos/mayúsculas
            for expected, field_name in HEADER_MAP.items():
                if expected.lower() == header_clean.lower():
                    field_map[idx] = field_name
                    break

    if not field_map:
        logger.error(
            "Ningún encabezado del reporte de Pintura coincidió con los esperados. "
            "Encabezados encontrados: %s. Esperados: %s",
            raw_headers, list(HEADER_MAP.keys()),
        )
        raise ValueError("Los encabezados del reporte de Pintura no coinciden con los esperados.")

    records = []
    data_rows = rows[1:]  # Saltar la fila de encabezados

    for row_idx, row_cells in enumerate(data_rows):
        record = {}

        for col_idx, field_name in field_map.items():
            cell_value = row_cells[col_idx].strip() if col_idx < len(row_cells) else ""
            record[field_name] = cell_value

        # Conversiones de tipo
        record["fecha_hora"] = _parse_datetime(record.get("fecha_hora", ""))
        record["num_panos"] = _parse_float(record.get("num_panos", ""))

        # Limpiar strings vacíos a None
        for key in ["vin", "marca", "modelo", "procedencia", "seccion",
                    "diagnostico_esum", "validacion", "comentario", "colaborador"]:
            val = record.get(key, "")
            record[key] = val if val else None

        # Filtrar filas sin VIN
        if not record.get("vin"):
            logger.debug("Fila de datos %d ignorada (VIN vacío)", row_idx + 1)
            continue

        records.append(record)

    logger.info(
        "Parse de Pintura completado — %d filas de datos, %d registros válidos",
        len(data_rows), len(records),
    )
    return records
