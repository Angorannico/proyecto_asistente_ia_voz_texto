"""
Modelos de base de datos SQLite.
Define las tablas y sus columnas para almacenar metadatos de sesiones.
"""

# Definición SQL de las tablas.
# Se usa SQL directo con aiosqlite (sin ORM) para mantener
# el MVP simple y sin dependencias adicionales.

CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS sesiones (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha           TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    modo            TEXT    NOT NULL CHECK(modo IN ('virtual', 'presencial')),
    estado          TEXT    NOT NULL DEFAULT 'grabando'
                            CHECK(estado IN ('grabando', 'analizando', 'completada', 'error')),
    transcripcion   TEXT,
    datos_extraidos TEXT,
    ruta_documento  TEXT,
    error_mensaje   TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);
"""
