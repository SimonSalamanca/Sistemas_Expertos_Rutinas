"""Motor de inferencia bayesiano del sistema experto.

Cada rutina (hipótesis H) tiene una probabilidad a priori P(H) y, para
cada hecho E (opción de respuesta), una verosimilitud P(E | H). Ambas se
leen de la base de conocimiento y se derivan de las reglas del árbol de
decisión.

Con cada respuesta el motor actualiza la probabilidad de todas las rutinas
con el teorema de Bayes:

    P(H | E1..En) = P(H) · Π P(Ei | H) / Σ_k [ P(Hk) · Π P(Ei | Hk) ]

Al terminar el cuestionario recomienda la rutina con mayor probabilidad a
posteriori y presenta las siguientes como alternativas.

Las reglas siguen decidiendo qué preguntas aplican a cada usuario (columna
"Aplica cuando" del cuestionario): solo se muestra una pregunta si alguna
regla que todavía es posible necesita un hecho de esa pregunta. También
sirven para explicar el resultado (camino del árbol que lo respalda).
"""
from __future__ import annotations

from negocio.entidades import (BaseHechos, Hecho, Hipotesis, Pregunta,
                               ReglaInferencia, ResultadoInferencia)
from negocio.excepciones import ErrorNegocio, SinConclusionError

ALTERNATIVAS = 2   # rutinas adicionales que se muestran junto a la recomendada


class MotorInferencia:

    def __init__(self, preguntas: list[Pregunta], reglas: list[ReglaInferencia],
                 hipotesis: list[Hipotesis],
                 verosimilitudes: dict[tuple[int, int], float]) -> None:
        if not reglas:
            raise ErrorNegocio("La base de conocimiento no tiene reglas cargadas.")
        if not verosimilitudes:
            raise ErrorNegocio("La base de conocimiento no tiene probabilidades cargadas.")
        self._preguntas = sorted(preguntas, key=lambda p: p.orden)
        self._reglas = reglas
        self._hipotesis = sorted(hipotesis, key=lambda h: h.codigo)
        # (id_hipotesis, id_hecho) -> P(hecho | hipótesis)
        self._verosimilitud = verosimilitudes

    # --- Aplicabilidad de las preguntas ---------------------------------

    @staticmethod
    def _es_compatible(regla: ReglaInferencia, base: BaseHechos) -> bool:
        """Una regla sigue siendo posible si ningún hecho suyo contradice
        una respuesta ya dada (las preguntas sin responder no la descartan)."""
        for hecho in regla.hechos:
            respuesta = base.respuesta_a(hecho.id_pregunta)
            if respuesta is not None and respuesta.id != hecho.id:
                return False
        return True

    def reglas_candidatas(self, base: BaseHechos) -> list[ReglaInferencia]:
        return [r for r in self._reglas if self._es_compatible(r, base)]

    def siguiente_pregunta(self, base: BaseHechos) -> Pregunta | None:
        """Primera pregunta, por orden, que aplica según las reglas que aún
        son posibles. Devuelve None cuando el cuestionario terminó."""
        candidatas = self.reglas_candidatas(base)
        necesarias = {h.id_pregunta for r in candidatas for h in r.hechos}
        for pregunta in self._preguntas:
            if pregunta.id in necesarias and not base.respondida(pregunta.id):
                return pregunta
        return None

    def opciones_validas(self, pregunta: Pregunta, base: BaseHechos) -> list[Hecho]:
        """Opciones de la pregunta que mantienen viva al menos una regla."""
        usados = {h.id for r in self.reglas_candidatas(base) for h in r.hechos}
        return [op for op in pregunta.opciones if op.id in usados]

    # --- Inferencia probabilística ----------------------------------------

    def _bayes(self, hechos: list[Hecho]) -> list[tuple[Hipotesis, float]]:
        """Probabilidad a posteriori de cada hipótesis dados los hechos,
        ordenadas de mayor a menor."""
        conjuntas = []
        for h in self._hipotesis:
            p = h.probabilidad_previa
            for e in hechos:
                p *= self._verosimilitud.get((h.id, e.id), 0.0)
            conjuntas.append((h, p))
        evidencia = sum(p for _, p in conjuntas)       # P(E1..En)
        if evidencia <= 0:
            raise SinConclusionError(
                "Ninguna rutina de la base de conocimiento es compatible con estas respuestas.")
        posteriores = [(h, p / evidencia) for h, p in conjuntas]
        return sorted(posteriores, key=lambda x: (-x[1], x[0].codigo))

    def probabilidades(self, base: BaseHechos) -> list[tuple[Hipotesis, float]]:
        """Distribución actual de probabilidad sobre todas las rutinas."""
        return self._bayes(base.hechos())

    def _regla_que_explica(self, hipotesis: Hipotesis, base: BaseHechos) -> ReglaInferencia:
        """Camino del árbol de la hipótesis que mejor coincide con las
        respuestas (el que tiene más hechos cumplidos)."""
        propias = [r for r in self._reglas if r.hipotesis.codigo == hipotesis.codigo]
        if not propias:
            raise SinConclusionError(f"La hipótesis {hipotesis.codigo} no tiene reglas.")
        ids = base.ids()
        return max(propias, key=lambda r: (len(r.ids_hechos() & ids),
                                           -len(r.ids_hechos() - ids)))

    def inferir(self, base: BaseHechos) -> ResultadoInferencia:
        hechos = base.hechos()
        ranking = self._bayes(hechos)
        mejor, probabilidad = ranking[0]

        # Evolución: probabilidad de la rutina final después de cada respuesta
        evolucion = [("Antes de responder", mejor.probabilidad_previa)]
        for i in range(1, len(hechos) + 1):
            p = dict((h.codigo, v) for h, v in self._bayes(hechos[:i]))[mejor.codigo]
            evolucion.append((str(hechos[i - 1]), p))

        return ResultadoInferencia(
            hipotesis=mejor, probabilidad=probabilidad,
            alternativas=[x for x in ranking[1:1 + ALTERNATIVAS] if x[1] > 0],
            regla=self._regla_que_explica(mejor, base),
            evolucion=evolucion)
