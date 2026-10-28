"""Utilidades visuales de la consola (rich)."""
from __future__ import annotations

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table
from rich.text import Text

console = Console()
ACENTO = "cyan"


def limpiar() -> None:
    console.clear()


def encabezado(titulo: str, subtitulo: str | None = None) -> None:
    limpiar()
    console.print(Panel(Text(titulo, style="bold white", justify="center"),
                        subtitle=subtitulo, border_style=ACENTO, box=box.DOUBLE,
                        padding=(0, 2)))


def menu(opciones: list[str], titulo: str = "Menú") -> int:
    """Muestra opciones numeradas y devuelve el número elegido (1..n)."""
    tabla = Table(box=box.ROUNDED, show_header=False, border_style="dim", title=titulo,
                  title_style=f"bold {ACENTO}")
    tabla.add_column(style=f"bold {ACENTO}", justify="right")
    tabla.add_column()
    for i, op in enumerate(opciones, 1):
        tabla.add_row(str(i), op)
    console.print(tabla)
    return IntPrompt.ask("Elija una opción",
                         choices=[str(i) for i in range(1, len(opciones) + 1)],
                         show_choices=False)


def elegir(opciones: list[str], mensaje: str = "Su respuesta") -> int:
    """Lista numerada sin marco; devuelve el índice elegido (base 0)."""
    for i, op in enumerate(opciones, 1):
        console.print(f"  [bold {ACENTO}]{i}.[/] {op}")
    n = IntPrompt.ask(mensaje, choices=[str(i) for i in range(1, len(opciones) + 1)],
                      show_choices=False)
    return n - 1


def pedir(mensaje: str, *, oculto: bool = False, defecto: str | None = None) -> str:
    while True:
        valor = Prompt.ask(mensaje, password=oculto, default=defecto)
        if valor and valor.strip():
            return valor.strip()
        error("Este dato es obligatorio.")


def confirmar(mensaje: str) -> bool:
    return Confirm.ask(mensaje, default=True)


def exito(mensaje: str) -> None:
    console.print(f"[bold green]✔[/] {mensaje}")


def error(mensaje: str) -> None:
    console.print(f"[bold red]✖[/] {mensaje}")


def pausa() -> None:
    Prompt.ask("\n[dim]Presione Enter para continuar[/]", default="", show_default=False)


def tabla(columnas: list[str], filas: list[list[str]], titulo: str | None = None) -> Table:
    t = Table(box=box.SIMPLE_HEAVY, header_style=f"bold {ACENTO}", title=titulo,
              title_style="bold", show_lines=False)
    for c in columnas:
        t.add_column(c, overflow="fold")
    for f in filas:
        t.add_row(*[x if x is not None else "—" for x in f])
    return t
