"""Contratos que la capa de datos debe cumplir.

La capa de negocio depende de estas interfaces y no de PostgreSQL.
Así el motor de inferencia queda desacoplado de la base de conocimiento
(RNF-04): cambiar hechos, hipótesis o reglas no exige tocar el motor.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from negocio.entidades import (BaseHechos, Consulta, Hipotesis, Pregunta,
                               ReglaInferencia, ResultadoInferencia, Usuario)


class IRepositorioConocimiento(ABC):
    @abstractmethod
    def obtener_preguntas(self) -> list[Pregunta]: ...

    @abstractmethod
    def obtener_hipotesis(self) -> list[Hipotesis]: ...

    @abstractmethod
    def obtener_reglas(self) -> list[ReglaInferencia]: ...

    @abstractmethod
    def obtener_verosimilitudes(self) -> dict[tuple[int, int], float]:
        """(id_hipotesis, id_hecho) -> P(hecho | hipótesis)."""

    @abstractmethod
    def guardar_hipotesis(self, hipotesis: Hipotesis) -> None: ...

    @abstractmethod
    def guardar_regla(self, codigo: str, id_hipotesis: int, ids_hechos: list[int]) -> None: ...

    @abstractmethod
    def eliminar_regla(self, codigo: str) -> bool: ...

    @abstractmethod
    def eliminar_hipotesis(self, codigo: str) -> bool: ...


class IRepositorioUsuarios(ABC):
    @abstractmethod
    def crear(self, nombre: str, correo: str, contrasena_hash: str, rol: str) -> Usuario: ...

    @abstractmethod
    def buscar_por_correo(self, correo: str) -> tuple[Usuario, str] | None: ...

    @abstractmethod
    def listar(self) -> list[Usuario]: ...

    @abstractmethod
    def actualizar_rol(self, id_usuario: int, rol: str) -> bool: ...


class IRepositorioConsultas(ABC):
    @abstractmethod
    def guardar(self, id_usuario: int, resultado: ResultadoInferencia,
                base: BaseHechos) -> int: ...

    @abstractmethod
    def listar(self, id_usuario: int | None = None) -> list[Consulta]: ...
