"""Punto de entrada de la capa de presentación: inicio de sesión y registro."""
from __future__ import annotations

from negocio.entidades import Usuario
from negocio.excepciones import ErrorNegocio
from negocio.servicio_base_conocimiento import ServicioBaseConocimiento
from negocio.servicio_diagnostico import ServicioDiagnostico
from negocio.servicio_usuarios import ServicioUsuarios
from presentacion import consola as ui
from presentacion.menus import (MenuAdministrador, MenuBase, MenuExperto,
                                MenuIngeniero, MenuUsuarioFinal)


class AplicacionConsola:

    def __init__(self, usuarios: ServicioUsuarios, diagnostico: ServicioDiagnostico,
                 conocimiento: ServicioBaseConocimiento) -> None:
        self.usuarios = usuarios
        self.diagnostico = diagnostico
        self.conocimiento = conocimiento

    def ejecutar(self) -> None:
        while True:
            ui.encabezado("SISTEMA EXPERTO DE RUTINAS DE ENTRENAMIENTO",
                          "Universidad Manuela Beltrán · Sistemas Expertos")
            opcion = ui.menu(["Iniciar sesión", "Registrarme", "Salir"], "Bienvenido")
            if opcion == 3:
                ui.console.print("[dim]Hasta pronto.[/]")
                return
            try:
                usuario = self._iniciar_sesion() if opcion == 1 else self._registrarse()
            except ErrorNegocio as e:
                ui.error(str(e))
                ui.pausa()
                continue
            self._menu_para(usuario).ejecutar()

    def _iniciar_sesion(self) -> Usuario:
        ui.encabezado("Iniciar sesión")
        correo = ui.pedir("Correo")
        contrasena = ui.pedir("Contraseña", oculto=True)
        return self.usuarios.iniciar_sesion(correo, contrasena)

    def _registrarse(self) -> Usuario:
        ui.encabezado("Registro de usuario")
        nombre = ui.pedir("Nombre completo")
        correo = ui.pedir("Correo")
        contrasena = ui.pedir("Contraseña (mínimo 6 caracteres)", oculto=True)
        if contrasena != ui.pedir("Repita la contraseña", oculto=True):
            raise ErrorNegocio("Las contraseñas no coinciden.")
        usuario = self.usuarios.registrar(nombre, correo, contrasena)
        ui.exito("Cuenta creada.")
        ui.pausa()
        return usuario

    def _menu_para(self, usuario: Usuario) -> MenuBase:
        if usuario.rol == "experto":
            return MenuExperto(usuario, self.conocimiento, self.diagnostico)
        if usuario.rol == "ingeniero":
            return MenuIngeniero(usuario, self.conocimiento, self.diagnostico)
        if usuario.rol == "administrador":
            return MenuAdministrador(usuario, self.usuarios, self.diagnostico)
        return MenuUsuarioFinal(usuario, self.diagnostico)
