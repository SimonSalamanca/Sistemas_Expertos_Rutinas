"""Módulo de adquisición del conocimiento (RF-04).

Lo usa el ingeniero del conocimiento para cargar hipótesis y reglas, y el
experto para consultarlas. Valida que lo cargado sea coherente antes de
guardarlo.
"""
from __future__ import annotations

import re

from negocio.entidades import Hipotesis, Pregunta, ReglaInferencia
from negocio.excepciones import ErrorNegocio
from negocio.repositorios import IRepositorioConocimiento

NIVELES = ("Principiante", "Intermedio", "Avanzado")


class ServicioBaseConocimiento:

    def __init__(self, repositorio: IRepositorioConocimiento) -> None:
        self._repo = repositorio

    # --- Consulta --------------------------------------------------------

    def preguntas(self) -> list[Pregunta]:
        return self._repo.obtener_preguntas()

    def hipotesis(self) -> list[Hipotesis]:
        return self._repo.obtener_hipotesis()

    def reglas(self) -> list[ReglaInferencia]:
        return self._repo.obtener_reglas()

    def valores_de(self, variable: str) -> list[str]:
        for p in self.preguntas():
            if p.variable == variable:
                return [op.valor for op in p.opciones]
        return []

    # --- Hipótesis ---------------------------------------------------------

    def registrar_hipotesis(self, hipotesis: Hipotesis) -> None:
        h = hipotesis
        if not re.fullmatch(r"H\d{2}", h.codigo):
            raise ErrorNegocio("El código de la hipótesis debe tener la forma H00.")
        if h.nivel not in NIVELES:
            raise ErrorNegocio(f"El nivel debe ser uno de: {', '.join(NIVELES)}.")
        if h.equipo not in self.valores_de("equipo_disponible"):
            raise ErrorNegocio("El equipo no corresponde a ninguna opción del cuestionario.")
        if h.nivel == "Principiante" and (h.objetivo or h.fase):
            raise ErrorNegocio("Principiante no se diferencia por objetivo ni fase.")
        if h.nivel != "Principiante" and not h.objetivo:
            raise ErrorNegocio("Intermedio y Avanzado requieren un objetivo.")
        if h.objetivo and h.objetivo not in self.valores_de("objetivo_principal"):
            raise ErrorNegocio("El objetivo no corresponde a ninguna opción del cuestionario.")
        requiere_fase = h.nivel == "Avanzado" and h.objetivo in ("Fuerza", "Hipertrofia")
        if bool(h.fase) != requiere_fase:
            raise ErrorNegocio("La fase solo aplica a Avanzado con Fuerza o Hipertrofia.")
        if h.fase and h.fase not in self.valores_de("fase_priorizada"):
            raise ErrorNegocio("La fase no corresponde a ninguna opción del cuestionario.")
        if not h.descripcion_rutina.strip():
            raise ErrorNegocio("La descripción de la rutina es obligatoria.")
        self._repo.guardar_hipotesis(h)

    def eliminar_hipotesis(self, codigo: str) -> None:
        if not self._repo.eliminar_hipotesis(codigo):
            raise ErrorNegocio(f"La hipótesis {codigo} no existe.")

    # --- Reglas ---------------------------------------------------------------

    def registrar_regla(self, codigo: str, codigo_hipotesis: str,
                        ids_hechos: list[int]) -> None:
        if not re.fullmatch(r"R\d{2}", codigo):
            raise ErrorNegocio("El código de la regla debe tener la forma R00.")

        hipotesis = next((h for h in self.hipotesis() if h.codigo == codigo_hipotesis), None)
        if hipotesis is None:
            raise ErrorNegocio(f"La hipótesis {codigo_hipotesis} no existe.")

        todos = {op.id: op for p in self.preguntas() for op in p.opciones}
        if not ids_hechos or any(i not in todos for i in ids_hechos):
            raise ErrorNegocio("La regla debe tener hechos válidos.")
        hechos = [todos[i] for i in ids_hechos]

        por_variable = {}
        for h in hechos:
            if h.variable in por_variable:
                raise ErrorNegocio(f"La regla tiene dos valores para {h.variable}.")
            por_variable[h.variable] = h.valor

        # Coherencia con el perfil de la hipótesis
        esperado = {"equipo_disponible": hipotesis.equipo,
                    "objetivo_principal": hipotesis.objetivo,
                    "fase_priorizada": hipotesis.fase}
        for variable, valor in esperado.items():
            if por_variable.get(variable) != valor:
                raise ErrorNegocio(
                    f"Los hechos no corresponden a la hipótesis {codigo_hipotesis} "
                    f"({variable} debería ser {valor or 'no evaluado'}).")

        # No puede repetir las premisas de otra regla
        nuevos = frozenset(ids_hechos)
        for regla in self.reglas():
            if regla.codigo != codigo and regla.ids_hechos() == nuevos:
                raise ErrorNegocio(f"Tiene los mismos hechos que la regla {regla.codigo}.")

        self._repo.guardar_regla(codigo, hipotesis.id, ids_hechos)

    def eliminar_regla(self, codigo: str) -> None:
        if not self._repo.eliminar_regla(codigo):
            raise ErrorNegocio(f"La regla {codigo} no existe.")
