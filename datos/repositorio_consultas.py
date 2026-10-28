"""Acceso a las tablas consulta y respuesta_pregunta."""
from __future__ import annotations

from datos.conexion import Conexion
from negocio.entidades import BaseHechos, Consulta, Hipotesis, ResultadoInferencia
from negocio.repositorios import IRepositorioConsultas


class RepositorioConsultas(IRepositorioConsultas):

    def __init__(self, conexion: Conexion) -> None:
        self._db = conexion

    def guardar(self, id_usuario: int, resultado: ResultadoInferencia,
                base: BaseHechos) -> int:
        """Guarda la consulta y sus respuestas en una sola transacción."""
        with self._db.transaccion() as cur:
            cur.execute("""
                INSERT INTO consulta (id_usuario, id_regla, id_hipotesis, probabilidad)
                VALUES (%s, %s, %s, %s) RETURNING id_consulta""",
                (id_usuario, resultado.regla.id, resultado.hipotesis.id,
                 round(resultado.probabilidad, 5)))
            id_consulta = cur.fetchone()["id_consulta"]
            cur.executemany("""
                INSERT INTO respuesta_pregunta (id_consulta, id_pregunta, id_hecho)
                VALUES (%s, %s, %s)""",
                [(id_consulta, h.id_pregunta, h.id) for h in base.hechos()])
        return id_consulta

    def listar(self, id_usuario: int | None = None) -> list[Consulta]:
        with self._db.transaccion() as cur:
            cur.execute("""
                SELECT c.id_consulta, c.fecha, u.nombre,
                       r.codigo || ': SI ' ||
                       (SELECT string_agg(p.variable || ' = ' || he.valor, ' Y ' ORDER BY p.orden)
                          FROM hecho_hipotesis hh
                          JOIN hecho he   ON he.id_hecho = hh.id_hecho
                          JOIN pregunta p ON p.id_pregunta = he.id_pregunta
                         WHERE hh.id_regla = r.id_regla)
                       || ' ENTONCES ' || hi.codigo AS regla,
                       hi.id_hipotesis, hi.codigo, hi.nivel, hi.equipo, hi.objetivo,
                       hi.fase, hi.descripcion_rutina, c.probabilidad,
                       ARRAY(SELECT he.valor
                               FROM respuesta_pregunta rp
                               JOIN hecho he    ON he.id_hecho = rp.id_hecho
                               JOIN pregunta p  ON p.id_pregunta = rp.id_pregunta
                              WHERE rp.id_consulta = c.id_consulta
                              ORDER BY p.orden) AS respuestas
                  FROM consulta c
                  JOIN usuario u           ON u.id_usuario = c.id_usuario
                  JOIN regla_inferencia r  ON r.id_regla = c.id_regla
                  JOIN hipotesis hi        ON hi.id_hipotesis = c.id_hipotesis
                 WHERE %(id)s::int IS NULL OR c.id_usuario = %(id)s::int
                 ORDER BY c.fecha DESC, c.id_consulta DESC""", {"id": id_usuario})
            filas = cur.fetchall()
        return [Consulta(
                    id=f["id_consulta"], fecha=f["fecha"], usuario=f["nombre"], regla=f["regla"],
                    hipotesis=Hipotesis(f["id_hipotesis"], f["codigo"], f["nivel"], f["equipo"],
                                        f["objetivo"], f["fase"], f["descripcion_rutina"]),
                    respuestas=list(f["respuestas"]),
                    probabilidad=float(f["probabilidad"]))
                for f in filas]
