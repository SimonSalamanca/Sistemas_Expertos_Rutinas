"""Registro, inicio de sesión y gestión de roles (RF-01, RNF-01)."""
from __future__ import annotations

import hashlib
import hmac
import re
import secrets

from negocio.entidades import Usuario
from negocio.excepciones import CredencialesInvalidasError, ErrorNegocio
from negocio.repositorios import IRepositorioUsuarios

ROLES = ("usuario", "experto", "ingeniero", "administrador")
_ITERACIONES = 200_000


def cifrar_contrasena(contrasena: str) -> str:
    sal = secrets.token_hex(16)
    clave = hashlib.pbkdf2_hmac("sha256", contrasena.encode(), bytes.fromhex(sal), _ITERACIONES)
    return f"pbkdf2_sha256${_ITERACIONES}${sal}${clave.hex()}"


def verificar_contrasena(contrasena: str, almacenada: str) -> bool:
    try:
        _, iteraciones, sal, esperado = almacenada.split("$")
        clave = hashlib.pbkdf2_hmac("sha256", contrasena.encode(),
                                    bytes.fromhex(sal), int(iteraciones))
    except ValueError:
        return False
    return hmac.compare_digest(clave.hex(), esperado)


class ServicioUsuarios:

    def __init__(self, repositorio: IRepositorioUsuarios) -> None:
        self._repo = repositorio

    def registrar(self, nombre: str, correo: str, contrasena: str,
                  rol: str = "usuario") -> Usuario:
        nombre, correo = nombre.strip(), correo.strip().lower()
        if len(nombre) < 3:
            raise ErrorNegocio("El nombre debe tener al menos 3 caracteres.")
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", correo):
            raise ErrorNegocio("El correo no tiene un formato válido.")
        if len(contrasena) < 6:
            raise ErrorNegocio("La contraseña debe tener al menos 6 caracteres.")
        if rol not in ROLES:
            raise ErrorNegocio("Rol no válido.")
        if self._repo.buscar_por_correo(correo):
            raise ErrorNegocio("Ya existe una cuenta con ese correo.")
        return self._repo.crear(nombre, correo, cifrar_contrasena(contrasena), rol)

    def iniciar_sesion(self, correo: str, contrasena: str) -> Usuario:
        encontrado = self._repo.buscar_por_correo(correo.strip().lower())
        if not encontrado or not verificar_contrasena(contrasena, encontrado[1]):
            raise CredencialesInvalidasError("Correo o contraseña incorrectos.")
        return encontrado[0]

    def listar(self) -> list[Usuario]:
        return self._repo.listar()

    def cambiar_rol(self, id_usuario: int, rol: str) -> None:
        if rol not in ROLES:
            raise ErrorNegocio("Rol no válido.")
        if not self._repo.actualizar_rol(id_usuario, rol):
            raise ErrorNegocio("El usuario no existe.")
