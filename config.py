"""Parámetros de conexión a PostgreSQL.

Orden de prioridad:
  1. Variables de entorno (DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD).
  2. El archivo config_local.py (no se sube a GitHub; copie
     config_local.ejemplo.py como config_local.py y ponga sus datos).
  3. Los valores por defecto de abajo.
"""
import os

try:
    import config_local as _local
except ImportError:
    _local = None


def _valor(nombre: str, defecto: str) -> str:
    return os.getenv(nombre) or str(getattr(_local, nombre, defecto))


DB_HOST = _valor("DB_HOST", "localhost")
DB_PORT = int(_valor("DB_PORT", "5432"))
DB_NAME = _valor("DB_NAME", "sistema_experto_rutina")
DB_USER = _valor("DB_USER", "postgres")
DB_PASSWORD = _valor("DB_PASSWORD", "postgres")
