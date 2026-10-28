"""Caso de uso principal: responder el cuestionario y obtener la rutina."""
from __future__ import annotations

from negocio.entidades import (BaseHechos, Consulta, Hecho, Hipotesis, Pregunta,
                               ResultadoInferencia)
from negocio.excepciones import ErrorNegocio
from negocio.motor_inferencia import MotorInferencia
from negocio.repositorios import IRepositorioConocimiento, IRepositorioConsultas


class SesionDiagnostico:
    """Una consulta en curso: guarda la base de hechos y habla con el motor."""

    def __init__(self, motor: MotorInferencia) -> None:
        self._motor = motor
        self.base_hechos = BaseHechos()

    def siguiente_pregunta(self) -> Pregunta | None:
        return self._motor.siguiente_pregunta(self.base_hechos)

    def opciones(self, pregunta: Pregunta) -> list[Hecho]:
        return self._motor.opciones_validas(pregunta, self.base_hechos)

    def responder(self, pregunta: Pregunta, hecho: Hecho) -> None:
        if hecho not in self.opciones(pregunta):
            raise ErrorNegocio("La opción elegida no es válida para esta pregunta.")
        self.base_hechos.afirmar(hecho)

    def probabilidades(self) -> list[tuple[Hipotesis, float]]:
        """Probabilidad actual de cada rutina, de mayor a menor."""
        return self._motor.probabilidades(self.base_hechos)

    def concluir(self) -> ResultadoInferencia:
        if self.siguiente_pregunta() is not None:
            raise ErrorNegocio("Faltan preguntas por responder.")
        return self._motor.inferir(self.base_hechos)


class ServicioDiagnostico:

    def __init__(self, conocimiento: IRepositorioConocimiento,
                 consultas: IRepositorioConsultas) -> None:
        self._conocimiento = conocimiento
        self._consultas = consultas

    def nueva_sesion(self) -> SesionDiagnostico:
        # El conocimiento se lee en cada consulta: lo que cargue el ingeniero
        # se usa de inmediato, sin reiniciar el programa.
        motor = MotorInferencia(self._conocimiento.obtener_preguntas(),
                                self._conocimiento.obtener_reglas(),
                                self._conocimiento.obtener_hipotesis(),
                                self._conocimiento.obtener_verosimilitudes())
        return SesionDiagnostico(motor)

    def registrar(self, id_usuario: int, sesion: SesionDiagnostico,
                  resultado: ResultadoInferencia) -> int:
        return self._consultas.guardar(id_usuario, resultado, sesion.base_hechos)

    def historial(self, id_usuario: int) -> list[Consulta]:
        return self._consultas.listar(id_usuario)

    def todas_las_consultas(self) -> list[Consulta]:
        return self._consultas.listar()
