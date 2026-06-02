"""
routers/fotos.py
Endpoint para subida de fotos de evidencia.

Flujo:
1. Recibe el archivo como multipart/form-data.
2. Convierte la imagen a WebP con Pillow (calidad 75, máx 1920 px).
3. Sube a Supabase Storage (bucket: evidencias).
4. Si falla → guarda localmente en ./uploads/ como fallback.
"""

from __future__ import annotations

import io
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from PIL import Image

from auth.models import UserInfo
from auth.utils import get_current_user
from config import settings

router = APIRouter(prefix="/fotos", tags=["Fotos"])

# Directorio local de uploads (fallback)
UPLOADS_DIR = Path(__file__).parent.parent / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

BUCKET_NAME   = "evidencias"
MAX_DIMENSION = 1920
WEBP_QUALITY  = 75


def _convert_to_webp(file_bytes: bytes) -> bytes:
    """Convierte bytes de imagen a WebP optimizado."""
    try:
        img = Image.open(io.BytesIO(file_bytes))
        img = img.convert("RGB")
        w, h = img.size
        if w > MAX_DIMENSION or h > MAX_DIMENSION:
            img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.LANCZOS)
        output = io.BytesIO()
        img.save(output, format="WebP", quality=WEBP_QUALITY)
        return output.getvalue()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El archivo no es una imagen válida: {exc}",
        ) from exc


def _subir_a_supabase(webp_bytes: bytes, filename: str) -> str | None:
    """Sube la imagen al bucket 'evidencias' en Supabase Storage."""
    try:
        from supabase import create_client
        client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

        # Asegurarse de que el bucket existe (ignora error si ya existe)
        try:
            client.storage.create_bucket(
                BUCKET_NAME,
                options={"public": True, "file_size_limit": 10485760}  # 10 MB
            )
        except Exception:
            pass  # El bucket ya existe, está bien

        # Subir el archivo
        path = f"reprocesos/{filename}"
        client.storage.from_(BUCKET_NAME).upload(
            path=path,
            file=webp_bytes,
            file_options={"content-type": "image/webp", "upsert": "true"},
        )

        # Obtener URL pública
        public_url = client.storage.from_(BUCKET_NAME).get_public_url(path)
        return public_url

    except Exception as exc:
        print(f"[FOTOS] Error al subir a Supabase Storage: {exc}")
        return None


def _guardar_localmente(webp_bytes: bytes, filename: str) -> str:
    """Guarda el archivo localmente como fallback."""
    dest = UPLOADS_DIR / filename
    dest.write_bytes(webp_bytes)
    return f"/uploads/{filename}"


# ─────────────────────────────────────────────────────────────────────────────
# POST /fotos/upload
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/upload",
    summary="Subir foto de evidencia",
    description=(
        "Recibe una imagen, la convierte a WebP (máx 1920px, calidad 75) "
        "y la sube a Supabase Storage (bucket: evidencias)."
    ),
)
async def upload_foto(
    file: UploadFile = File(..., description="Imagen de evidencia"),
    current_user: UserInfo = Depends(get_current_user),
) -> JSONResponse:
    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo está vacío",
        )

    # Convertir a WebP
    webp_bytes = _convert_to_webp(file_bytes)

    # Nombre único
    timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    filename  = f"reproceso_{timestamp}_{unique_id}.webp"

    # Intentar Supabase Storage primero
    url = _subir_a_supabase(webp_bytes, filename)
    storage = "supabase_storage"

    # Fallback local
    if url is None:
        url = _guardar_localmente(webp_bytes, filename)
        storage = "local"

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "url": url,
            "filename": filename,
            "storage": storage,
            "size_bytes": len(webp_bytes),
            "subido_por": current_user.nombre,
        },
    )
