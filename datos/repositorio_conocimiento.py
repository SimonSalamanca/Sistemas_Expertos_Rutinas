"""Acceso a la base de conocimiento: preguntas, hechos, hipótesis y reglas."""
from __future__ import annotations

import psycopg

from datos.conexion import Conexion
from negocio.entidades import Hecho, Hipotesis, Pregunta, ReglaInferencia
from negocio.excepciones import ErrorNegocio
from negocio.repositorios import IRepositorioConocimiento


def _a_hecho(fila: dict) -> Hecho:
    return Hecho(id=fila["id_hecho"], codigo=fila["codigo_hecho"],
                 id_pregunta=fila["id_pregunta"], variable=fila["variable"],
                 valor=fila["valor"])


def _a_hipotesis(fila: dict) -> Hipotesis:
    return Hipotesis(id=fila["id_hipotesis"], codigo=fila["codigo_hipotesis"],
                     nivel=fila["nivel"], equipo=fila["equipo"],
                     objetivo=fila["objetivo"], fase=fila["fase"],
                     descripcion_rutina=fila["descripcion_rutina"],
                     probabilidad_previa=float(fila["probabilidad_previa"]))


class RepositorioConocimiento(IRepositorioConocimiento):

    def __init__(self, conexion: Conexion) -> None:
        self._db = conexion

    def obtener_preguntas(self) -> list[Pregunta]:
        with self._db.transaccion() as cur:
            cur.execute("""
                SELECT p.id_pregunta, p.codigo, p.texto, p.variable, p.orden,
                       h.id_hecho, h.codigo AS codigo_hecho, h.valor
                  FROM pregunta p
                  JOIN hecho h ON h.id_pregunta = p.id_pregunta
                 ORDER BY p.orden, h.codigo""")
            filas = cur.fetchall()
        preguntas: dict[int, Pregunta] = {}
        for f in filas:
            p = preguntas.setdefault(f["id_pregunta"], Pregunta(
                id=f["id_pregunta"], codigo=f["codigo"], texto=f["texto"],
                variable=f["variable"], orden=f["orden"]))
            p.opciones.append(_a_hecho(f))
        return list(preguntas.values())

    def obtener_hipotesis(self) -> list[Hipotesis]:
        with self._db.transaccion() as cur:
            cur.execute("""
                SELECT id_hipotesis, codigo AS codigo_hipotesis, nivel, equipo,
                       objetivo, fase, descripcion_rutina, probabilidad_previa
                  FROM hipotesis ORDER BY codigo""")
            return [_a_hipotesis(f) for f in cur.fetchall()]

    def obtener_reglas(self) -> list[ReglaInferencia]:
        with self._db.transaccion() as cur:
            cur.execute("""
                SELECT r.id_regla, r.codigo AS codigo_regla,
                       hi.id_hipotesis, hi.codigo AS codigo_hipotesis, hi.nivel,
                       hi.equipo, hi.objetivo, hi.fase, hi.descripcion_rutina,
                       hi.probabilidad_previa,
                       he.id_hecho, he.codigo AS codigo_hecho, he.valor,
                       p.id_pregunta, p.variable
                  FROM regla_inferencia r
                  JOIN hipotesis hi       ON hi.id_hipotesis = r.id_hipotesis
                  JOIN hecho_hipotesis hh ON hh.id_regla = r.id_regla
                  JOIN hecho he           ON he.id_hecho = hh.id_hecho
                  JOIN pregunta p         ON p.id_pregunta = he.id_pregunta
                 ORDER BY r.codigo, p.orden""")
            filas = cur.fetchall()
        reglas: dict[int, ReglaInferencia] = {}
        for f in filas:
            r = reglas.setdefault(f["id_regla"], ReglaInferencia(
                id=f["id_regla"], codigo=f["codigo_regla"], hipotesis=_a_hipotesis(f)))
            r.hechos.append(_a_hecho(f))
        return list(reglas.values())

    def obtener_verosimilitudes(self) -> dict[tuple[int, int], float]:
        with self._db.transaccion() as cur:
            cur.execute("""SELECT id_hipotesis, id_hecho, probabilidad
                             FROM probabilidad_condicional""")
            return {(f["id_hipotesis"], f["id_hecho"]): float(f["probabilidad"])
                    for f in cur.fetchall()}

    @staticmethod
    def _recalcular(cur: psycopg.Cursor) -> None:
        """Vuelve a derivar P(H) y P(E | H) después de cambiar el conocimiento."""
        cur.execute("SELECT recalcular_probabilidades()")

    def guardar_hipotesis(self, h: Hipotesis) -> None:
        with self._db.transaccion() as cur:
            cur.execute("""
                INSERT INTO hipotesis (codigo, nivel, equipo, objetivo, fase, descripcion_rutina)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (codigo) DO UPDATE
                   SET nivel = EXCLUDED.nivel, equipo = EXCLUDED.equipo,
                       objetivo = EXCLUDED.objetivo, fase = EXCLUDED.fase,
                       descripcion_rutina = EXCLUDED.descripcion_rutina""",
                (h.codigo, h.nivel, h.equipo, h.objetivo, h.fase, h.descripcion_rutina))
            self._recalcular(cur)

    def guardar_regla(self, codigo: str, id_hipotesis: int, ids_hechos: list[int]) -> None:
        """Crea la regla o la reemplaza si ya existe. Todo en una transacción."""
        try:
            with self._db.transaccion() as cur:
                cur.execute("SELECT id_regla FROM regla_inferencia WHERE codigo = %s", (codigo,))
                existente = cur.fetchone()
                if existente:
                    id_regla = existente["id_regla"]
                    cur.execute("DELETE FROM hecho_hipotesis WHERE id_regla = %s", (id_regla,))
                    cur.execute("UPDATE regla_inferencia SET id_hipotesis = %s WHERE id_regla = %s",
                                (id_hipotesis, id_regla))
                else:
                    cur.execute("""INSERT INTO regla_inferencia (codigo, id_hipotesis)
                                   VALUES (%s, %s) RETURNING id_regla""", (codigo, id_hipotesis))
                    id_regla = cur.fetchone()["id_regla"]
                cur.executemany(
                    """INSERT INTO hecho_hipotesis (id_hecho, id_hipotesis, id_regla)
                       VALUES (%s, %s, %s)""",
                    [(i, id_hipotesis, id_regla) for i in ids_hechos])
                self._recalcular(cur)
        except psycopg.errors.ForeignKeyViolation:
            raise ErrorNegocio(f"La regla {codigo} ya tiene diagnósticos asociados "
                               "a otra hipótesis; cree una regla nueva.") from None

    def _eliminar(self, tabla: str, codigo: str, que: str) -> bool:
        try:
            with self._db.transaccion() as cur:
                cur.execute(f"DELETE FROM {tabla} WHERE codigo = %s", (codigo,))
                eliminado = cur.rowcount > 0
                self._recalcular(cur)
                return eliminado
        except psycopg.errors.ForeignKeyViolation:
            raise ErrorNegocio(f"No se puede eliminar {que} {codigo}: tiene "
                               "diagnósticos de usuarios asociados.") from None

    def eliminar_regla(self, codigo: str) -> bool:
        return self._eliminar("regla_inferencia", codigo, "la regla")

    def eliminar_hipotesis(self, codigo: str) -> bool:
        return self._eliminar("hipotesis", codigo, "la hipótesis")
