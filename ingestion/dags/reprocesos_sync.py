"""
dags/reprocesos_sync.py
========================
DAG de Airflow para sincronización del Sistema de Control de Reprocesos.

Descarga los reportes de eSUM (Ubicación, Pintura, Repuestos), los parsea
y los sincroniza con Supabase cada 10 minutos.

Flujo de tareas (secuencial para no sobrecargar eSUM):
    task_ubicacion → task_pintura → task_repuesto → task_resumen

NOTA sobre sesiones eSUM:
    Los objetos requests.Session no son serializables para XCom de Airflow.
    Cada tarea crea su propia sesión eSUM (el login tarda ~1 segundo), lo cual
    es aceptable para el volumen de este sistema.

Variables de entorno requeridas (desde ../.env vía docker-compose):
    ESUM_BASE_URL, ESUM_USER, ESUM_PASSWORD_HASH
    ESUM_TALLER_ID, ESUM_USUARIO_ID
    SUPABASE_URL, SUPABASE_SERVICE_KEY
"""

import sys
import os
import logging
from datetime import datetime, timedelta

# Asegurar que /opt/airflow esté en el path para importar tasks.*
sys.path.insert(0, "/opt/airflow")

from airflow import DAG
from airflow.operators.python import PythonOperator

# ──────────────────────────────────────────────
# Configuración del DAG
# ──────────────────────────────────────────────
DEFAULT_ARGS = {
    "owner": "reprocesos",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=3),
}

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Funciones Python callable para cada tarea
# ──────────────────────────────────────────────

def task_ubicacion(**context):
    """
    Tarea 1 — Reporte de Ubicación:
      1. Crea sesión autenticada en eSUM
      2. Descarga el CSV de Ubicación
      3. Parsea los registros
      4. Sincroniza con tabla 'vehiculos' en Supabase
      5. Registra resultado en sync_log
    """
    from tasks.esum_session import create_authenticated_session
    from tasks.descarga_ubicacion import download_ubicacion
    from tasks.parse_ubicacion import parse_ubicacion
    from tasks.sync_supabase import sync_vehiculos, log_sync

    logger.info("=== TASK UBICACIÓN: Iniciando ===")

    try:
        session = create_authenticated_session()
        raw_bytes = download_ubicacion(session)
        records = parse_ubicacion(raw_bytes)

        logger.info("Ubicación: %d registros parseados, iniciando sync...", len(records))

        result = sync_vehiculos(records)

        log_sync(
            reporte="UBICACION",
            estado="OK" if result["errores"] == 0 else "PARCIAL",
            filas=result["procesados"],
            mensaje=(
                f"Procesados: {result['procesados']}, "
                f"Errores: {result['errores']}"
            ),
        )

        logger.info(
            "=== TASK UBICACIÓN finalizada — procesados: %d, errores: %d ===",
            result["procesados"], result["errores"],
        )

        # Guardar resultado en XCom para el resumen final
        context["ti"].xcom_push(key="ubicacion_result", value=result)
        return result

    except Exception as exc:
        logger.exception("TASK UBICACIÓN: error inesperado: %s", exc)
        log_sync(
            reporte="UBICACION",
            estado="ERROR",
            filas=0,
            mensaje=str(exc),
        )
        raise


def task_pintura(**context):
    """
    Tarea 2 — Reporte de Pintura:
      1. Crea sesión autenticada en eSUM
      2. Descarga el HTML de Pintura (mes actual)
      3. Parsea los registros
      4. Sincroniza con tabla 'danos_pintura' en Supabase
      5. Registra resultado en sync_log
    """
    from tasks.esum_session import create_authenticated_session
    from tasks.descarga_pintura import download_pintura
    from tasks.parse_pintura import parse_pintura
    from tasks.sync_supabase import sync_danos_pintura, log_sync

    logger.info("=== TASK PINTURA: Iniciando ===")

    try:
        session = create_authenticated_session()
        raw_bytes = download_pintura(session)
        records = parse_pintura(raw_bytes)

        logger.info("Pintura: %d registros parseados, iniciando sync...", len(records))

        result = sync_danos_pintura(records)

        log_sync(
            reporte="PINTURA",
            estado="OK" if result["errores"] == 0 else "PARCIAL",
            filas=result["procesados"],
            mensaje=(
                f"Procesados: {result['procesados']}, "
                f"Errores: {result['errores']}"
            ),
        )

        logger.info(
            "=== TASK PINTURA finalizada — procesados: %d, errores: %d ===",
            result["procesados"], result["errores"],
        )

        context["ti"].xcom_push(key="pintura_result", value=result)
        return result

    except Exception as exc:
        logger.exception("TASK PINTURA: error inesperado: %s", exc)
        log_sync(
            reporte="PINTURA",
            estado="ERROR",
            filas=0,
            mensaje=str(exc),
        )
        raise


def task_repuesto(**context):
    """
    Tarea 3 — Reporte de Repuestos:
      1. Crea sesión autenticada en eSUM
      2. Descarga el HTML de Repuestos (mes anterior + mes actual)
      3. Parsea los registros
      4. Sincroniza con tabla 'danos_repuesto' en Supabase
      5. Registra resultado en sync_log
    """
    from tasks.esum_session import create_authenticated_session
    from tasks.descarga_repuestos import download_repuestos
    from tasks.parse_repuestos import parse_repuestos
    from tasks.sync_supabase import sync_danos_repuesto, log_sync

    logger.info("=== TASK REPUESTO: Iniciando ===")

    try:
        session = create_authenticated_session()
        raw_bytes = download_repuestos(session)
        records = parse_repuestos(raw_bytes)

        logger.info("Repuesto: %d registros parseados, iniciando sync...", len(records))

        result = sync_danos_repuesto(records)

        log_sync(
            reporte="REPUESTO",
            estado="OK" if result["errores"] == 0 else "PARCIAL",
            filas=result["procesados"],
            mensaje=(
                f"Procesados: {result['procesados']}, "
                f"Errores: {result['errores']}"
            ),
        )

        logger.info(
            "=== TASK REPUESTO finalizada — procesados: %d, errores: %d ===",
            result["procesados"], result["errores"],
        )

        context["ti"].xcom_push(key="repuesto_result", value=result)
        return result

    except Exception as exc:
        logger.exception("TASK REPUESTO: error inesperado: %s", exc)
        log_sync(
            reporte="REPUESTO",
            estado="ERROR",
            filas=0,
            mensaje=str(exc),
        )
        raise


def task_resumen(**context):
    """
    Tarea 4 — Resumen final:
    Lee los resultados de las tareas anteriores desde XCom y
    genera un resumen consolidado en los logs.
    """
    ti = context["ti"]

    ubicacion_result = ti.xcom_pull(task_ids="sync_ubicacion", key="ubicacion_result") or {}
    pintura_result   = ti.xcom_pull(task_ids="sync_pintura",   key="pintura_result")   or {}
    repuesto_result  = ti.xcom_pull(task_ids="sync_repuesto",  key="repuesto_result")  or {}

    resumen = {
        "ubicacion": ubicacion_result,
        "pintura": pintura_result,
        "repuesto": repuesto_result,
        "timestamp": datetime.utcnow().isoformat(),
    }

    total_procesados = (
        ubicacion_result.get("procesados", 0)
        + pintura_result.get("procesados", 0)
        + repuesto_result.get("procesados", 0)
    )
    total_errores = (
        ubicacion_result.get("errores", 0)
        + pintura_result.get("errores", 0)
        + repuesto_result.get("errores", 0)
    )

    logger.info(
        "╔══════════════════════════════════════════════╗\n"
        "║         RESUMEN DE SINCRONIZACIÓN            ║\n"
        "╠══════════════════════════════════════════════╣\n"
        "║  Ubicación  → procesados: %-5d  errores: %-4d║\n"
        "║  Pintura    → procesados: %-5d  errores: %-4d║\n"
        "║  Repuesto   → procesados: %-5d  errores: %-4d║\n"
        "╠══════════════════════════════════════════════╣\n"
        "║  TOTAL      → procesados: %-5d  errores: %-4d║\n"
        "╚══════════════════════════════════════════════╝",
        ubicacion_result.get("procesados", 0), ubicacion_result.get("errores", 0),
        pintura_result.get("procesados", 0), pintura_result.get("errores", 0),
        repuesto_result.get("procesados", 0), repuesto_result.get("errores", 0),
        total_procesados, total_errores,
    )

    return resumen


# ──────────────────────────────────────────────
# Definición del DAG
# ──────────────────────────────────────────────
with DAG(
    dag_id="reprocesos_sync",
    description="Sincronización periódica de reportes eSUM → Supabase (Reprocesos)",
    schedule_interval="*/10 * * * *",   # Cada 10 minutos
    start_date=datetime(2025, 1, 1),
    catchup=False,
    max_active_runs=1,
    default_args=DEFAULT_ARGS,
    tags=["reprocesos", "esum", "supabase"],
) as dag:

    op_ubicacion = PythonOperator(
        task_id="sync_ubicacion",
        python_callable=task_ubicacion,
    )

    op_pintura = PythonOperator(
        task_id="sync_pintura",
        python_callable=task_pintura,
    )

    op_repuesto = PythonOperator(
        task_id="sync_repuesto",
        python_callable=task_repuesto,
    )

    op_resumen = PythonOperator(
        task_id="resumen_sync",
        python_callable=task_resumen,
        trigger_rule="all_done",  # Ejecutar aunque alguna tarea anterior falle
    )

    # Secuencial: no sobrecargar eSUM con requests paralelos
    op_ubicacion >> op_pintura >> op_repuesto >> op_resumen
