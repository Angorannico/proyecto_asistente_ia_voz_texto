"""
Conexión y operaciones con SQLite async.

Usa aiosqlite para que las operaciones de BD no bloqueen
el event loop de FastAPI (todo es asíncrono).
"""

import json
from datetime import datetime
from typing import Optional

import aiosqlite

from app.config import settings
from app.models.db_models import CREATE_TABLES_SQL


async def get_db() -> aiosqlite.Connection:
    """Abre una conexión a la base de datos SQLite."""
    db = await aiosqlite.connect(str(settings.DB_PATH))
    # Retornar filas como diccionarios en lugar de tuplas
    db.row_factory = aiosqlite.Row
    return db


async def init_db() -> None:
    """
    Inicializa la base de datos creando las tablas si no existen.
    Se ejecuta automáticamente al iniciar el servidor (lifespan).
    """
    db = await get_db()
    try:
        await db.executescript(CREATE_TABLES_SQL)
        await db.commit()
        print("🗄️  Base de datos inicializada correctamente")
    finally:
        await db.close()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# OPERACIONES CRUD
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def crear_sesion(modo: str) -> int:
    """
    Crea una nueva sesión en la BD y retorna su ID.

    Args:
        modo: 'virtual' o 'presencial'

    Returns:
        El ID de la sesión creada
    """
    db = await get_db()
    try:
        cursor = await db.execute(
            "INSERT INTO sesiones (modo) VALUES (?)",
            (modo,)
        )
        await db.commit()
        return cursor.lastrowid
    finally:
        await db.close()


async def actualizar_sesion(
    sesion_id: int,
    estado: Optional[str] = None,
    transcripcion: Optional[str] = None,
    datos_extraidos: Optional[dict] = None,
    ruta_documento: Optional[str] = None,
    error_mensaje: Optional[str] = None,
) -> None:
    """
    Actualiza los campos de una sesión existente.
    Solo actualiza los campos que se pasen (los None se ignoran).
    """
    campos = []
    valores = []

    if estado is not None:
        campos.append("estado = ?")
        valores.append(estado)
    if transcripcion is not None:
        campos.append("transcripcion = ?")
        valores.append(transcripcion)
    if datos_extraidos is not None:
        campos.append("datos_extraidos = ?")
        valores.append(json.dumps(datos_extraidos, ensure_ascii=False))
    if ruta_documento is not None:
        campos.append("ruta_documento = ?")
        valores.append(ruta_documento)
    if error_mensaje is not None:
        campos.append("error_mensaje = ?")
        valores.append(error_mensaje)

    if not campos:
        return

    # Siempre actualizar updated_at
    campos.append("updated_at = ?")
    valores.append(datetime.now().isoformat())

    valores.append(sesion_id)

    db = await get_db()
    try:
        await db.execute(
            f"UPDATE sesiones SET {', '.join(campos)} WHERE id = ?",
            valores
        )
        await db.commit()
    finally:
        await db.close()


async def obtener_sesion(sesion_id: int) -> Optional[dict]:
    """Obtiene una sesión por su ID."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM sesiones WHERE id = ?",
            (sesion_id,)
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return dict(row)
    finally:
        await db.close()


async def listar_sesiones(limit: int = 50) -> list[dict]:
    """Lista las sesiones más recientes."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM sesiones ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()
