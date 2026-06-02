"""
tasks/parse_repuestos.py
=========================
Parsea el reporte de Repuestos de eSUM (HTML disfrazado de .xls con 2 headers).

Características especiales:
  - El archivo tiene extensión .xls pero es HTML real
  - Tiene 2 filas de encabezado:
      Fila 0: encabezados visuales agrupados (decorativos)
      Fila 1: encabezados reales con los nombres de columna
  - Los datos comienzan en la fila 2 (índice 2)
  - Encoding: latin-1

Encabezados reales (fila índice 1):
    TALLER, MARCA, VIN, MODELO, AÑO, COLOR, PROCEDENCIA, SECCIÓN,
    DIAGNÓSTICO, NUM. PEDIDO, FECH. REG., VALIDADO POR,
    VALIDACIÓN CLIENTE, FECH. VAL. CLIENTE, COMENT. VAL. CLIENTE,
    FECHA DE TÉRMINO, LINK EVIDENCIA 1..7

Mapeo de salida:
    taller, marca, vin, modelo, anio, color, procedencia, seccion,
    diagnostico, num_pedido, fecha_registro, validado_por,
    validacion_cliente, fecha_val_cliente, comentario_val_cliente,
    fecha_termino, link_evidencia_1..7

Uso:
    from tasks.parse_repuestos import parse_repuestos
    records = parse_repuestos(html_bytes)
"""

import logging
from datetime import datetime
from typing import Optional

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Encabezados reales de la fila 1 (índice 1) y su mapeo a campos
HEADER_MAP = {
    "TALLER": "taller",
    "MARCA": "marca",
    "VIN": "vin",
    "MODELO": "modelo",
    "AÑO": "anio",
    "COLOR": "color",
    "PROCEDENCIA": "procedencia",
    "SECCIÓN": "seccion",
    "DIAGNÓSTICO": "diagnostico",
    "NUM. PEDIDO": "num_pedido",
    "FECH. REG.": "fecha_registro",
    "VALIDADO POR": "validado_por",
    "VALIDACIÓN CLIENTE": "validacion_cliente",
    "FECH. VAL. CLIENTE": "fecha_val_cliente",
    "COMENT. VAL. CLIENTE": "comentario_val_cliente",
    "FECHA DE TÉRMINO": "fecha_termino",
    "LINK EVIDENCIA 1": "link_evidencia_1",
    "LINK EVIDENCIA 2": "link_evidencia_2",
    "LINK EVIDENCIA 3": "link_evidencia_3",
    "LINK EVIDENCIA 4": "link_evidencia_4",
    "LINK EVIDENCIA 5": "link_evidencia_5",
    "LINK EVIDENCIA 6": "link_evidencia_6",
    "LINK EVIDENCIA 7": "link_evidencia_7",
}

# Columnas que contienen fechas (formato dd-mm-yy de eSUM)
DATE_FIELDS = {"fecha_registro", "fecha_val_cliente", "fecha_termino"}
DATE_FORMATS = ["%d-%m-%y", "%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d"]


def _parse_date(value: str) -> Optional[str]:
    """
    Convierte una fecha en formato dd-mm-yy (u otros) a YYYY-MM-DD.
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
    logger.warning("No se pudo parsear fecha de Repuestos: '%s'", val)
    return None


def _normalize_header(raw: str) -> str:
    """Normaliza un encabezado: strip y uppercase para comparación."""
    return raw.strip().upper()


def _extract_all_rows(soup: BeautifulSoup) -> list[list[str]]:
    """
    Extrae todas las filas de la primera tabla HTML encontrada,
    incluyendo texto de celdas con colspan/rowspan.
    """
    table = soup.find("table")
    if not table:
        raise ValueError("No se encontró ninguna tabla HTML en el reporte de Repuestos.")

    rows = []
    for tr in table.find_all("tr"):
        cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
        if cells:
            rows.append(cells)
    return rows


def parse_repuestos(content: bytes) -> list[dict]:
    """
    Parsea el contenido HTML del reporte de Repuestos de eSUM.

    Args:
        content: Bytes del archivo (HTML con extensión .xls, encoding latin-1,
                 con 2 filas de encabezado).

    Returns:
        Lista de diccionarios con los registros parseados y normalizados.

    Raises:
        ValueError: Si el contenido está vacío, no contiene tabla, o no se
                    pueden identificar los encabezados reales.
    """
    if not content:
        raise ValueError("El contenido del reporte de Repuestos está vacío.")

    # Decodificar con latin-1
    try:
        html_text = content.decode("latin-1", errors="replace")
    except Exception as exc:
        raise ValueError(f"No se pudo decodificar el HTML de Repuestos: {exc}") from exc

    soup = BeautifulSoup(html_text, "html.parser")
    rows = _extract_all_rows(soup)

    logger.debug("Total de filas extraídas del HTML de Repuestos: %d", len(rows))

    if len(rows) < 3:
        logger.warning(
            "El reporte de Repuestos tiene menos de 3 filas "
            "(2 headers + al menos 1 dato). Puede no haber datos."
        )
        return []

    # Fila 1 (índice 1): encabezados reales
    real_headers_row = rows[1]
    logger.debug("Encabezados reales (fila índice 1): %s", real_headers_row)

    # Construir mapeo posición → campo normalizado
    field_map = {}
    for idx, raw_header in enumerate(real_headers_row):
        normalized = _normalize_header(raw_header)

        # Buscar en HEADER_MAP (también normalizado)
        for expected_raw, field_name in HEADER_MAP.items():
            if _normalize_header(expected_raw) == normalized:
                field_map[idx] = field_name
                break

    if not field_map:
        logger.error(
            "Ningún encabezado del reporte de Repuestos coincidió. "
            "Encabezados encontrados: %s",
            real_headers_row,
        )
        raise ValueError(
            "Los encabezados del reporte de Repuestos no coinciden con los esperados."
        )

    logger.debug("Mapeo de campos Repuestos: %s", field_map)

    records = []
    data_rows = rows[2:]  # Los datos empiezan en índice 2

    for row_idx, row_cells in enumerate(data_rows):
        record = {}

        for col_idx, field_name in field_map.items():
            cell_value = row_cells[col_idx].strip() if col_idx < len(row_cells) else ""
            record[field_name] = cell_value

        # Conversiones de fecha
        for date_field in DATE_FIELDS:
            if date_field in record:
                record[date_field] = _parse_date(record[date_field])

        # Limpiar strings vacíos a None para campos no-fecha
        for key, val in record.items():
            if key not in DATE_FIELDS:
                record[key] = val.strip() if val and val.strip() else None

        # Filtrar filas sin VIN
        if not record.get("vin"):
            logger.debug("Fila de datos %d ignorada (VIN vacío)", row_idx + 1)
            continue

        records.append(record)

    logger.info(
        "Parse de Repuestos completado — %d filas de datos, %d registros válidos",
        len(data_rows), len(records),
    )
    return records
