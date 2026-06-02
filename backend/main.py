"""
main.py
Punto de entrada principal de la API FastAPI.
Sistema de Control de Reprocesos - Backend
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from auth.router import router as auth_router
from config import settings
from routers.fotos import router as fotos_router, UPLOADS_DIR
from routers.items import router as items_router
from routers.reprocesos import router as reprocesos_router
from routers.trabajos import router as trabajos_router
from routers.usuarios import router as usuarios_router
from routers.vehiculos import router as vehiculos_router

# ─────────────────────────────────────────────────────────────────────────────
# Instancia principal
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Sistema de Control de Reprocesos",
    description=(
        "API REST para la gestión de reprocesos de pintura y repuestos en planta. "
        "Roles disponibles: **control_calidad**, **operario_pintura**, **operario_repuesto**."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ─────────────────────────────────────────────────────────────────────────────
# Middleware CORS
# ─────────────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────────────────────
# Archivos estáticos (uploads locales como fallback de Drive)
# ─────────────────────────────────────────────────────────────────────────────

app.mount(
    "/uploads",
    StaticFiles(directory=str(UPLOADS_DIR)),
    name="uploads",
)

# ─────────────────────────────────────────────────────────────────────────────
# Routers
# ─────────────────────────────────────────────────────────────────────────────

from routers.sync import router as sync_router

app.include_router(auth_router)
app.include_router(vehiculos_router)
app.include_router(reprocesos_router)
app.include_router(items_router)
app.include_router(trabajos_router)
app.include_router(usuarios_router)
app.include_router(fotos_router)
app.include_router(sync_router)

# ─────────────────────────────────────────────────────────────────────────────
# Manejo global de excepciones HTTP
# ─────────────────────────────────────────────────────────────────────────────

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Manejador global de HTTPException.
    Garantiza respuestas JSON consistentes con campo 'detail'.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url.path),
        },
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Manejador de excepciones no controladas.
    Retorna 500 sin exponer detalles internos en producción.
    """
    # En desarrollo podrías logear: print(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Error interno del servidor",
            "status_code": 500,
            "path": str(request.url.path),
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
# Health check
# ─────────────────────────────────────────────────────────────────────────────

@app.get(
    "/health",
    tags=["Sistema"],
    summary="Health check",
    description="Verifica que el servidor esté activo.",
)
def health_check() -> dict:
    return {
        "status": "ok",
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "version": app.version,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Root
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/", tags=["Sistema"], include_in_schema=False)
def root() -> dict:
    return {
        "api": app.title,
        "version": app.version,
        "docs": "/docs",
    }
