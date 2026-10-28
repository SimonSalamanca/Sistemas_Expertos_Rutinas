"""Vistas reutilizables: rutina, historial y base de conocimiento."""
from __future__ import annotations

from rich import box
from rich.panel import Panel
from rich.text import Text

from negocio.entidades import (Consulta, Hecho, Hipotesis, ReglaInferencia,
                               ResultadoInferencia)
from presentacion.consola import ACENTO, console, tabla


def _rutina_en_vinetas(descripcion: str) -> Text:
    texto = Text()
    frases = [f.strip().rstrip(".") for f in descripcion.split(". ") if f.strip()]
    for frase in frases:
        texto.append("  • ", style=f"bold {ACENTO}")
        texto.append(frase + ".\n")
    texto.rstrip()
    return texto


def _pct(p: float) -> str:
    return f"{p:.1%}".replace(".", ",")


def _barra(p: float, ancho: int = 20) -> str:
    llenos = round(p * ancho)
    return "█" * llenos + "░" * (ancho - llenos)


def mostrar_rutina(hipotesis: Hipotesis, regla: str | ReglaInferencia | None = None,
                   respuestas: list[Hecho] | list[str] | None = None,
                   probabilidad: float | None = None) -> None:
    cuerpo = Text()
    if probabilidad is not None:
        cuerpo.append("Probabilidad: ", style="bold")
        cuerpo.append(f"{_pct(probabilidad)}  ", style="bold green")
        cuerpo.append(_barra(probabilidad) + "\n", style="green")
    cuerpo.append("Perfil: ", style="bold")
    cuerpo.append(hipotesis.perfil() + "\n\n")
    cuerpo.append_text(_rutina_en_vinetas(hipotesis.descripcion_rutina))
    console.print(Panel(cuerpo, title=f"[bold]Rutina recomendada {hipotesis.codigo}[/]",
                        border_style="green", box=box.ROUNDED, padding=(1, 2)))

    if regla is None:
        return
    # Módulo de explicación: por qué el sistema llegó a esta rutina
    explicacion = Text()
    if respuestas:
        explicacion.append("Sus respuestas: ", style="bold")
        explicacion.append(" · ".join(str(getattr(r, "valor", r)) for r in respuestas) + "\n")
    if isinstance(regla, ReglaInferencia):
        explicacion.append(f"Camino del árbol que la respalda {regla.codigo}: ", style="bold")
        explicacion.append(regla.texto())
    else:
        explicacion.append("Camino del árbol que la respalda ", style="bold")
        explicacion.append(regla)
    console.print(Panel(explicacion, title="¿Por qué esta rutina?", border_style="dim",
                        box=box.ROUNDED))


def mostrar_resultado(resultado: ResultadoInferencia, respuestas: list[Hecho]) -> None:
    """Rutina más probable, alternativas y cómo cambió la probabilidad."""
    mostrar_rutina(resultado.hipotesis, resultado.regla, respuestas, resultado.probabilidad)

    filas = [[f"Respuesta: {paso}" if i else paso, _pct(p), _barra(p)]
             for i, (paso, p) in enumerate(resultado.evolucion)]
    console.print(tabla(["Evidencia", f"P({resultado.hipotesis.codigo})", ""], filas,
                        titulo=f"Actualización bayesiana de {resultado.hipotesis.codigo}"))

    if resultado.alternativas:
        filas = [[h.codigo, h.perfil(), _pct(p)] for h, p in resultado.alternativas]
        console.print(tabla(["Rutina", "Perfil", "Probabilidad"], filas,
                            titulo="Otras rutinas posibles"))


def mostrar_consultas(consultas: list[Consulta], con_usuario: bool = False) -> None:
    if not consultas:
        console.print("[dim]No hay diagnósticos registrados.[/]")
        return
    columnas = ["#", "Fecha"] + (["Usuario"] if con_usuario else []) + \
               ["Respuestas", "Rutina", "Probabilidad", "Perfil"]
    filas = []
    for i, c in enumerate(consultas, 1):
        fila = [str(i), c.fecha.strftime("%Y-%m-%d %H:%M")]
        if con_usuario:
            fila.append(c.usuario)
        fila += [" · ".join(c.respuestas), c.hipotesis.codigo,
                 _pct(c.probabilidad) if c.probabilidad is not None else "-",
                 c.hipotesis.perfil()]
        filas.append(fila)
    console.print(tabla(columnas, filas))


def mostrar_hipotesis(hipotesis: list[Hipotesis]) -> None:
    console.print(tabla(["Código", "Nivel", "Equipo", "Objetivo", "Fase", "P. a priori"],
                        [[h.codigo, h.nivel, h.equipo, h.objetivo, h.fase,
                          _pct(h.probabilidad_previa)] for h in hipotesis],
                        titulo=f"Hipótesis ({len(hipotesis)})"))


def mostrar_reglas(reglas: list[ReglaInferencia]) -> None:
    filas = [[r.codigo, " Y ".join(str(h) for h in r.hechos), r.hipotesis.codigo]
             for r in reglas]
    console.print(tabla(["Regla", "SI (hechos unidos con Y)", "ENTONCES"], filas,
                        titulo=f"Reglas de inferencia ({len(reglas)})"))


def mostrar_hechos_de_hipotesis(hipotesis: Hipotesis, reglas: list[ReglaInferencia]) -> None:
    propias = [r for r in reglas if r.hipotesis.codigo == hipotesis.codigo]
    filas = [[r.codigo, h.codigo, h.variable, h.valor] for r in propias for h in r.hechos]
    console.print(Panel(f"{hipotesis.perfil()}\n\n{hipotesis.descripcion_rutina}",
                        title=f"[bold]{hipotesis.codigo}[/]", border_style=ACENTO))
    console.print(tabla(["Regla", "Hecho", "Variable", "Valor"], filas,
                        titulo=f"{len(propias)} regla(s) y {len(filas)} hecho(s) en hecho_hipotesis"))
