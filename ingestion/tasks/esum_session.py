"""
tasks/esum_session.py
=====================
Módulo de autenticación con el sistema eSUM (taller automotriz peruano).

Proporciona la función `create_authenticated_session` que realiza el login
contra el endpoint de eSUM y devuelve una sesión requests autenticada.

Variables de entorno requeridas:
    ESUM_BASE_URL          URL base del sistema eSUM
    ESUM_USER              Usuario (DNI) para autenticación
    ESUM_PASSWORD_HASH     Hash SHA-512 de la contraseña

Uso:
    from tasks.esum_session import create_authenticated_session
    session = create_authenticated_session()
"""

import os
import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Constantes por defecto
# ──────────────────────────────────────────────
DEFAULT_BASE_URL = "http://esum.pe"
DEFAULT_USER = "72413102"
DEFAULT_PASSWORD_HASH = (
    "e8604b52001a36ca4d52f336ef8cdc3c1d047d88331da66e2bedb9b945831b34"
    "db9fbc58ac7a37386995347de43babea7625124024068f9cae530835e9e93750"
)
LOGIN_ENDPOINT = "/includes/process_login.php"
REQUEST_TIMEOUT = 30  # segundos


class ESumSessionError(Exception):
    """Excepción que se lanza cuando la autenticación con eSUM falla."""
    pass


def create_authenticated_session(
    user: Optional[str] = None,
    password_hash: Optional[str] = None,
    base_url: Optional[str] = None,
) -> requests.Session:
    """
    Crea y retorna una sesión requests autenticada contra el sistema eSUM.

    Intenta obtener las credenciales en este orden:
      1. Parámetros pasados directamente a la función.
      2. Variables de entorno ESUM_USER, ESUM_PASSWORD_HASH, ESUM_BASE_URL.
      3. Valores por defecto hardcodeados en el módulo.

    Args:
        user:          Nombre de usuario (DNI) para eSUM.
        password_hash: Hash SHA-512 de la contraseña.
        base_url:      URL base del sistema (ej. "http://esum.pe").

    Returns:
        requests.Session autenticada con cookies válidas.

    Raises:
        ESumSessionError: Si el login falla por credenciales incorrectas,
                          respuesta inesperada o ausencia de cookie de sesión.
        requests.RequestException: Si ocurre un error de red.
    """
    # Resolver credenciales
    _user = user or os.environ.get("ESUM_USER", DEFAULT_USER)
    _hash = password_hash or os.environ.get("ESUM_PASSWORD_HASH", DEFAULT_PASSWORD_HASH)
    _base = (base_url or os.environ.get("ESUM_BASE_URL", DEFAULT_BASE_URL)).rstrip("/")

    login_url = f"{_base}{LOGIN_ENDPOINT}"
    payload = {
        "usuario_l": _user,
        "p_l": _hash,
    }

    logger.info("Iniciando autenticación eSUM para usuario '%s' en %s", _user, _base)

    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Content-Type": "application/x-www-form-urlencoded",
    })

    try:
        response = session.post(login_url, data=payload, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.error("Error de red al intentar login en eSUM: %s", exc)
        raise

    # eSUM responde con '1' si el login es exitoso
    response_text = response.text.strip()
    logger.debug("Respuesta del login eSUM: '%s'", response_text)

    if response_text != "1":
        raise ESumSessionError(
            f"Login eSUM fallido. Respuesta inesperada: '{response_text}'. "
            f"Verifique usuario y password_hash."
        )

    # Validar que se haya establecido la cookie de sesión
    if "sec_session_id" not in session.cookies:
        raise ESumSessionError(
            "Login eSUM: respuesta fue '1' pero no se encontró la cookie "
            "'sec_session_id'. El servidor puede haber cambiado su comportamiento."
        )

    logger.info(
        "Autenticación eSUM exitosa. Cookie sec_session_id obtenida (valor parcial: %s...)",
        str(session.cookies.get("sec_session_id", ""))[:8],
    )
    return session


def get_env_credentials() -> dict:
    """
    Retorna un diccionario con las credenciales eSUM leídas del entorno.
    Útil para logging/debugging sin exponer el hash completo.
    """
    return {
        "user": os.environ.get("ESUM_USER", DEFAULT_USER),
        "base_url": os.environ.get("ESUM_BASE_URL", DEFAULT_BASE_URL),
        "hash_prefix": os.environ.get("ESUM_PASSWORD_HASH", DEFAULT_PASSWORD_HASH)[:10] + "...",
    }
