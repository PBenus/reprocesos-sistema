"""
database.py
Gestión del cliente Supabase para el backend.
Usa la service_key (privilegios de admin) para operaciones del servidor.
"""

from __future__ import annotations

from functools import lru_cache

from supabase import Client, create_client

from config import settings


@lru_cache()
def get_supabase() -> Client:
    """
    Retorna un cliente Supabase singleton autenticado con la service_key.
    El service_key omite las políticas RLS de Supabase, por lo que el backend
    tiene acceso completo a todas las tablas.

    Uso:
        from database import get_supabase
        db = get_supabase()
        result = db.table("vehiculos").select("*").execute()
    """
    return create_client(
        supabase_url=settings.SUPABASE_URL,
        supabase_key=settings.SUPABASE_SERVICE_KEY,
    )
