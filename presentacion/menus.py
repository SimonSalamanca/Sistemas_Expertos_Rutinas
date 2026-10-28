"""Menús de cada rol del sistema."""
from __future__ import annotations

from negocio.entidades import Hipotesis, Usuario
from negocio.excepciones import ErrorNegocio
from negocio.servicio_base_conocimiento import NIVELES, ServicioBaseConocimiento
from negocio.servicio_diagnostico import ServicioDiagnostico
from negocio.servicio_usuarios import ROLES, ServicioUsuarios
from presentacion import consola as ui
from presentacion import vistas


class MenuBase:
    titulo = ""
    opciones: list[tuple[str, str]] = []   # (texto, nombre del método)

    def __init__(self, usuario: Usuario) -> None:
        self.usuario = usuario

    def ejecutar(self) -> None:
        while True:
            ui.encabezado(self.titulo, f"{self.usuario.nombre} · {self.usuario.rol}")
            textos = [t for t, _ in self.opciones] + ["Cerrar sesión"]
            eleccion = ui.menu(textos)
            if eleccion == len(textos):
                return
            texto, metodo = self.opciones[eleccion - 1]
            ui.encabezado(texto)
            try:
                getattr(self, metodo)()
            except ErrorNegocio as e:
                ui.error(str(e))
            ui.pausa()


class _ConsultaConocimiento:
    """Opciones de consulta compartidas por experto, ingeniero y administrador."""
    conocimiento: ServicioBaseConocimiento
    diagnostico: ServicioDiagnostico

    def ver_hipotesis(self) -> None:
        vistas.mostrar_hipotesis(self.conocimiento.hipotesis())

    def ver_reglas(self) -> None:
        vistas.mostrar_reglas(self.conocimiento.reglas())

    def ver_hechos_de_hipotesis(self) -> None:
        hipotesis = self.conocimiento.hipotesis()
        codigo = ui.pedir("Código de la hipótesis (ej. H01)").upper()
        h = next((x for x in hipotesis if x.codigo == codigo), None)
        if h is None:
            raise ErrorNegocio(f"La hipótesis {codigo} no existe.")
        vistas.mostrar_hechos_de_hipotesis(h, self.conocimiento.reglas())

    def ver_diagnosticos(self) -> None:
        vistas.mostrar_consultas(self.diagnostico.todas_las_consultas(), con_usuario=True)


# ---------------------------------------------------------------------------

class MenuUsuarioFinal(MenuBase):
    titulo = "Sistema experto · Rutinas de entrenamiento"
    opciones = [("Realizar diagnóstico", "diagnosticar"),
                ("Ver mi historial de rutinas", "ver_historial")]

    def __init__(self, usuario: Usuario, diagnostico: ServicioDiagnostico) -> None:
        super().__init__(usuario)
        self.diagnostico = diagnostico

    def diagnosticar(self) -> None:
        sesion = self.diagnostico.nueva_sesion()
        numero = 1
        while (pregunta := sesion.siguiente_pregunta()) is not None:
            ui.console.rule(f"[bold {ui.ACENTO}]Pregunta {numero}[/]", align="left")
            ui.console.print(f"[bold]{pregunta.texto}[/]")
            opciones = sesion.opciones(pregunta)
            i = ui.elegir([op.valor for op in opciones])
            sesion.responder(pregunta, opciones[i])
            numero += 1
            ui.console.print()

        resultado = sesion.concluir()
        self.diagnostico.registrar(self.usuario.id, sesion, resultado)
        ui.encabezado("Resultado del diagnóstico")
        vistas.mostrar_resultado(resultado, sesion.base_hechos.hechos())
        ui.exito("La rutina quedó guardada en su historial.")

    def ver_historial(self) -> None:
        consultas = self.diagnostico.historial(self.usuario.id)
        vistas.mostrar_consultas(consultas)
        if not consultas:
            return
        n = ui.pedir("Número para ver el detalle (Enter para volver)", defecto="0")
        if n.isdigit() and 1 <= int(n) <= len(consultas):
            c = consultas[int(n) - 1]
            vistas.mostrar_rutina(c.hipotesis, c.regla, c.respuestas, c.probabilidad)


class MenuExperto(_ConsultaConocimiento, MenuBase):
    titulo = "Experto humano · Validación del conocimiento"
    opciones = [("Ver hipótesis", "ver_hipotesis"),
                ("Ver reglas de inferencia", "ver_reglas"),
                ("Ver hechos de una hipótesis", "ver_hechos_de_hipotesis"),
                ("Ver diagnósticos de los usuarios", "ver_diagnosticos")]

    def __init__(self, usuario: Usuario, conocimiento: ServicioBaseConocimiento,
                 diagnostico: ServicioDiagnostico) -> None:
        super().__init__(usuario)
        self.conocimiento = conocimiento
        self.diagnostico = diagnostico


class MenuIngeniero(_ConsultaConocimiento, MenuBase):
    titulo = "Ingeniero del conocimiento · Base de conocimiento"
    opciones = [("Ver hipótesis", "ver_hipotesis"),
                ("Ver reglas de inferencia", "ver_reglas"),
                ("Ver hechos de una hipótesis", "ver_hechos_de_hipotesis"),
                ("Registrar o actualizar hipótesis", "registrar_hipotesis"),
                ("Registrar o actualizar regla", "registrar_regla"),
                ("Eliminar regla", "eliminar_regla"),
                ("Eliminar hipótesis", "eliminar_hipotesis")]

    def __init__(self, usuario: Usuario, conocimiento: ServicioBaseConocimiento,
                 diagnostico: ServicioDiagnostico) -> None:
        super().__init__(usuario)
        self.conocimiento = conocimiento
        self.diagnostico = diagnostico

    def _elegir_valor(self, variable: str, etiqueta: str) -> str:
        valores = self.conocimiento.valores_de(variable)
        ui.console.print(f"[bold]{etiqueta}[/]")
        return valores[ui.elegir(valores)]

    def registrar_hipotesis(self) -> None:
        codigo = ui.pedir("Código (ej. H27)").upper()
        if any(h.codigo == codigo for h in self.conocimiento.hipotesis()):
            ui.console.print("[yellow]Esa hipótesis ya existe; se actualizará.[/]")
        ui.console.print("[bold]Nivel[/]")
        nivel = NIVELES[ui.elegir(list(NIVELES))]
        equipo = self._elegir_valor("equipo_disponible", "Equipo")
        objetivo = fase = None
        if nivel != "Principiante":
            objetivo = self._elegir_valor("objetivo_principal", "Objetivo")
        if nivel == "Avanzado" and objetivo in ("Fuerza", "Hipertrofia"):
            fase = self._elegir_valor("fase_priorizada", "Fase")
        descripcion = ui.pedir("Descripción de la rutina")
        self.conocimiento.registrar_hipotesis(
            Hipotesis(None, codigo, nivel, equipo, objetivo, fase, descripcion))
        ui.exito(f"Hipótesis {codigo} guardada.")

    def registrar_regla(self) -> None:
        codigo = ui.pedir("Código de la regla (ej. R31)").upper()
        codigo_hip = ui.pedir("Hipótesis a la que conduce (ej. H01)").upper()
        ids, premisas = [], []
        ui.console.print("\nElija el hecho de cada pregunta que exige la regla:")
        for p in self.conocimiento.preguntas():
            ui.console.rule(f"{p.codigo} · {p.variable}", align="left")
            opciones = ["No se evalúa en esta regla"] + [op.valor for op in p.opciones]
            i = ui.elegir(opciones)
            if i > 0:
                hecho = p.opciones[i - 1]
                ids.append(hecho.id)
                premisas.append(str(hecho))
        ui.console.print(f"\n[bold]SI[/] {' [bold]Y[/] '.join(premisas)} "
                         f"[bold]ENTONCES[/] {codigo_hip}")
        if ui.confirmar("¿Guardar la regla?"):
            self.conocimiento.registrar_regla(codigo, codigo_hip, ids)
            ui.exito(f"Regla {codigo} guardada.")

    def eliminar_regla(self) -> None:
        codigo = ui.pedir("Código de la regla").upper()
        if ui.confirmar(f"¿Eliminar la regla {codigo}?"):
            self.conocimiento.eliminar_regla(codigo)
            ui.exito(f"Regla {codigo} eliminada.")

    def eliminar_hipotesis(self) -> None:
        codigo = ui.pedir("Código de la hipótesis").upper()
        if ui.confirmar(f"¿Eliminar {codigo} y todas sus reglas?"):
            self.conocimiento.eliminar_hipotesis(codigo)
            ui.exito(f"Hipótesis {codigo} eliminada.")


class MenuAdministrador(_ConsultaConocimiento, MenuBase):
    titulo = "Administrador · Usuarios y roles"
    opciones = [("Ver usuarios", "ver_usuarios"),
                ("Cambiar rol de un usuario", "cambiar_rol"),
                ("Ver diagnósticos de los usuarios", "ver_diagnosticos")]

    def __init__(self, usuario: Usuario, usuarios: ServicioUsuarios,
                 diagnostico: ServicioDiagnostico) -> None:
        super().__init__(usuario)
        self.usuarios = usuarios
        self.diagnostico = diagnostico

    def ver_usuarios(self) -> None:
        filas = [[str(u.id), u.nombre, u.correo, u.rol,
                  u.fecha_registro.strftime("%Y-%m-%d")] for u in self.usuarios.listar()]
        ui.console.print(ui.tabla(["ID", "Nombre", "Correo", "Rol", "Registro"], filas))

    def cambiar_rol(self) -> None:
        self.ver_usuarios()
        id_usuario = ui.pedir("ID del usuario")
        if not id_usuario.isdigit():
            raise ErrorNegocio("El ID debe ser un número.")
        ui.console.print("[bold]Nuevo rol[/]")
        rol = ROLES[ui.elegir(list(ROLES))]
        self.usuarios.cambiar_rol(int(id_usuario), rol)
        ui.exito("Rol actualizado.")
