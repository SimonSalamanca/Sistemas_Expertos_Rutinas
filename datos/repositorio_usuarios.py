"""Acceso a la tabla usuario."""
from __future__ import annotations

from datos.conexion import Conexion
from negocio.entidades import Usuario
from negocio.repositorios import IRepositorioUsuarios


def _a_usuario(f: dict) -> Usuario:
    return Usuario(id=f["id_usuario"], nombre=f["nombre"], correo=f["correo"],
                   rol=f["rol"], fecha_registro=f["fecha_registro"])


class RepositorioUsuarios(IRepositorioUsuarios):

    def __init__(self, conexion: Conexion) -> None:
        self._db = conexion

    def crear(self, nombre: str, correo: str, contrasena_hash: str, rol: str) -> Usuario:
        with self._db.transaccion() as cur:
            cur.execute("""
                INSERT INTO usuario (nombre, correo, contrasena_hash, rol)
                VALUES (%s, %s, %s, %s)
                RETURNING id_usuario, nombre, correo, rol, fecha_registro""",
                (nombre, correo, contrasena_hash, rol))
            return _a_usuario(cur.fetchone())

    def buscar_por_correo(self, correo: str) -> tuple[Usuario, str] | None:
        with self._db.transaccion() as cur:
            cur.execute("""SELECT id_usuario, nombre, correo, rol, fecha_registro,
                                  contrasena_hash
                             FROM usuario WHERE correo = %s""", (correo,))
            f = cur.fetchone()
        return (_a_usuario(f), f["contrasena_hash"]) if f else None

    def listar(self) -> list[Usuario]:
        with self._db.transaccion() as cur:
            cur.execute("""SELECT id_usuario, nombre, correo, rol, fecha_registro
                             FROM usuario ORDER BY id_usuario""")
            return [_a_usuario(f) for f in cur.fetchall()]

    def actualizar_rol(self, id_usuario: int, rol: str) -> bool:
        with self._db.transaccion() as cur:
            cur.execute("UPDATE usuario SET rol = %s WHERE id_usuario = %s", (rol, id_usuario))
            return cur.rowcount > 0
