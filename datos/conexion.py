"""Conexión a PostgreSQL (patrón Singleton)."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import psycopg
from psycopg.rows import dict_row

import config


class Conexion:
    _instancia: "Conexion | None" = None

    def __new__(cls) -> "Conexion":
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia._conn = None
        return cls._instancia

    def _abrir(self) -> psycopg.Connection:
        if self._conn is None or self._conn.closed:
            self._conn = psycopg.connect(
                host=config.DB_HOST, port=config.DB_PORT, dbname=config.DB_NAME,
                user=config.DB_USER, password=config.DB_PASSWORD,
                row_factory=dict_row, client_encoding="UTF8", autocommit=True)
        return self._conn

    @contextmanager
    def transaccion(self) -> Iterator[psycopg.Cursor]:
        """Cursor dentro de una transacción: confirma al final o deshace todo
        si ocurre un error."""
        conn = self._abrir()
        with conn.transaction():
            with conn.cursor() as cur:
                yield cur

    def probar(self) -> None:
        """Abre la conexión de una vez para detectar errores al iniciar."""
        self._abrir().execute("SELECT 1")

    def cerrar(self) -> None:
        if self._conn is not None and not self._conn.closed:
            self._conn.close()
