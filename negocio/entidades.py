"""Entidades del dominio del sistema experto."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class Hecho:
    """Una afirmación del tipo variable = valor (una opción de respuesta)."""
    id: int
    codigo: str
    id_pregunta: int
    variable: str
    valor: str

    def __str__(self) -> str:
        return f"{self.variable} = {self.valor}"


@dataclass
class Pregunta:
    id: int
    codigo: str
    texto: str
    variable: str
    orden: int
    opciones: list[Hecho] = field(default_factory=list)


@dataclass
class Hipotesis:
    """Una conclusión del sistema: la rutina recomendada."""
    id: int | None
    codigo: str
    nivel: str
    equipo: str
    objetivo: str | None
    fase: str | None
    descripcion_rutina: str
    probabilidad_previa: float = 0.0     # P(H)

    def perfil(self) -> str:
        partes = [self.nivel, self.equipo, self.objetivo, self.fase]
        return " · ".join(p for p in partes if p)


@dataclass
class ReglaInferencia:
    """Camino del árbol: SI hecho1 Y hecho2 ... ENTONCES hipótesis."""
    id: int | None
    codigo: str
    hipotesis: Hipotesis
    hechos: list[Hecho] = field(default_factory=list)

    def ids_hechos(self) -> frozenset[int]:
        return frozenset(h.id for h in self.hechos)

    def texto(self) -> str:
        premisas = " Y ".join(str(h) for h in self.hechos)
        return f"SI {premisas} ENTONCES {self.hipotesis.codigo}"


@dataclass
class ResultadoInferencia:
    """Conclusión del motor bayesiano."""
    hipotesis: Hipotesis                          # rutina más probable
    probabilidad: float                           # P(H | respuestas)
    alternativas: list[tuple[Hipotesis, float]]   # siguientes más probables
    regla: ReglaInferencia                        # camino del árbol que la respalda
    evolucion: list[tuple[str, float]]            # P de la rutina tras cada respuesta


class BaseHechos:
    """Memoria de trabajo de una consulta: lo que el usuario ha respondido."""

    def __init__(self) -> None:
        self._hechos: dict[int, Hecho] = {}   # id_pregunta -> hecho

    def afirmar(self, hecho: Hecho) -> None:
        self._hechos[hecho.id_pregunta] = hecho

    def respuesta_a(self, id_pregunta: int) -> Hecho | None:
        return self._hechos.get(id_pregunta)

    def respondida(self, id_pregunta: int) -> bool:
        return id_pregunta in self._hechos

    def ids(self) -> frozenset[int]:
        return frozenset(h.id for h in self._hechos.values())

    def hechos(self) -> list[Hecho]:
        return list(self._hechos.values())


@dataclass
class Usuario:
    id: int
    nombre: str
    correo: str
    rol: str
    fecha_registro: datetime | None = None


@dataclass
class Consulta:
    """Diagnóstico ya registrado (para historial y revisión del experto)."""
    id: int
    fecha: datetime
    usuario: str
    regla: str          # código y texto de la regla: "R25: SI ... ENTONCES H21"
    hipotesis: Hipotesis
    respuestas: list[str] = field(default_factory=list)
    probabilidad: float | None = None   # P(H | respuestas) al momento del diagnóstico
