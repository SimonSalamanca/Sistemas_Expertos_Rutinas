"""Interfaz web del sistema experto.

Es otra capa de presentación: crea los mismos objetos que main.py y llama a
los mismos servicios. La lógica del motor bayesiano y de la base de
conocimiento no cambia.
"""
from __future__ import annotations

import os
import secrets
from functools import wraps

from flask import (Flask, flash, redirect, render_template, request, session,
                   url_for)

from datos.conexion import Conexion
from datos.repositorio_conocimiento import RepositorioConocimiento
from datos.repositorio_consultas import RepositorioConsultas
from datos.repositorio_usuarios import RepositorioUsuarios
from negocio.entidades import Usuario
from negocio.excepciones import ErrorNegocio
from negocio.servicio_base_conocimiento import ServicioBaseConocimiento
from negocio.servicio_diagnostico import ServicioDiagnostico, SesionDiagnostico
from negocio.servicio_usuarios import ROLES, ServicioUsuarios

# --- Objetos de cada capa (igual que en main.py) ---------------------------
conexion = Conexion()
repo_conocimiento = RepositorioConocimiento(conexion)
servicio_usuarios = ServicioUsuarios(RepositorioUsuarios(conexion))
servicio_diagnostico = ServicioDiagnostico(repo_conocimiento, RepositorioConsultas(conexion))
servicio_conocimiento = ServicioBaseConocimiento(repo_conocimiento)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY") or secrets.token_hex(32)

ROLES_CONOCIMIENTO = ("experto", "ingeniero", "administrador")
NOMBRE_ROL = {"usuario": "Usuario", "experto": "Experto humano",
              "ingeniero": "Ingeniero del conocimiento", "administrador": "Administrador"}


# --- Filtros y utilidades de plantilla --------------------------------------

@app.template_filter("pct")
def _pct(valor: float | None) -> str:
    return "-" if valor is None else f"{valor:.1%}".replace(".", ",")


@app.template_filter("vinetas")
def _vinetas(descripcion: str) -> list[str]:
    return [f.strip().rstrip(".") + "." for f in descripcion.split(". ") if f.strip()]


@app.context_processor
def _contexto():
    return {"usuario": usuario_actual(), "NOMBRE_ROL": NOMBRE_ROL,
            "ROLES_CONOCIMIENTO": ROLES_CONOCIMIENTO}


# --- Sesión del usuario -----------------------------------------------------

def usuario_actual() -> Usuario | None:
    datos = session.get("usuario")
    return Usuario(**datos) if datos else None


def _iniciar(usuario: Usuario) -> None:
    session.clear()
    session["usuario"] = {"id": usuario.id, "nombre": usuario.nombre,
                          "correo": usuario.correo, "rol": usuario.rol}


def requiere_sesion(*roles: str):
    def decorador(vista):
        @wraps(vista)
        def envoltura(*args, **kwargs):
            u = usuario_actual()
            if u is None:
                return redirect(url_for("login"))
            if roles and u.rol not in roles:
                flash("No tiene permiso para ver esa sección.", "error")
                return redirect(url_for("inicio"))
            return vista(*args, **kwargs)
        return envoltura
    return decorador


@app.errorhandler(ErrorNegocio)
def _error_negocio(e: ErrorNegocio):
    flash(str(e), "error")
    return redirect(request.referrer or url_for("inicio"))


# --- Autenticación (RF-01) ----------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        try:
            _iniciar(servicio_usuarios.iniciar_sesion(request.form["correo"],
                                                      request.form["contrasena"]))
            return redirect(url_for("inicio"))
        except ErrorNegocio as e:
            flash(str(e), "error")
    return render_template("login.html", correo=request.form.get("correo", ""))


@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        f = request.form
        try:
            if f["contrasena"] != f["confirmacion"]:
                raise ErrorNegocio("Las contraseñas no coinciden.")
            _iniciar(servicio_usuarios.registrar(f["nombre"], f["correo"], f["contrasena"]))
            flash("Cuenta creada. ¡Bienvenido!", "ok")
            return redirect(url_for("inicio"))
        except ErrorNegocio as e:
            flash(str(e), "error")
    return render_template("registro.html", datos=request.form)


@app.route("/salir")
def salir():
    session.clear()
    return redirect(url_for("login"))


# --- Secciones del usuario -----------------------------------------------------

@app.route("/")
@requiere_sesion()
def inicio():
    historial = servicio_diagnostico.historial(usuario_actual().id)
    return render_template("inicio.html", ultima=historial[0] if historial else None,
                           total=len(historial),
                           total_rutinas=len(servicio_conocimiento.hipotesis()))


@app.route("/catalogo")
@requiere_sesion()
def catalogo():
    nivel = request.args.get("nivel", "")
    equipo = request.args.get("equipo", "")
    todas = servicio_conocimiento.hipotesis()
    rutinas = [h for h in todas if (not nivel or h.nivel == nivel)
               and (not equipo or h.equipo == equipo)]
    return render_template("catalogo.html", rutinas=rutinas, nivel=nivel, equipo=equipo,
                           niveles=("Principiante", "Intermedio", "Avanzado"),
                           equipos=sorted({h.equipo for h in todas}))


@app.route("/catalogo/<codigo>")
@requiere_sesion()
def rutina(codigo: str):
    h = next((x for x in servicio_conocimiento.hipotesis() if x.codigo == codigo), None)
    if h is None:
        flash(f"La rutina {codigo} no existe.", "error")
        return redirect(url_for("catalogo"))
    reglas = [r for r in servicio_conocimiento.reglas() if r.hipotesis.codigo == codigo]
    # Los pesos hecho–hipótesis solo los ven experto, ingeniero y administrador
    pesos = (servicio_conocimiento.pesos_de(h)
             if usuario_actual().rol in ROLES_CONOCIMIENTO else [])
    return render_template("rutina.html", h=h, reglas=reglas, pesos=pesos)


@app.route("/mis-rutinas")
@requiere_sesion()
def historial():
    return render_template("historial.html",
                           consultas=servicio_diagnostico.historial(usuario_actual().id))


@app.route("/mis-rutinas/<int:id_consulta>")
@requiere_sesion()
def consulta(id_consulta: int):
    u = usuario_actual()
    fuente = (servicio_diagnostico.todas_las_consultas() if u.rol in ROLES_CONOCIMIENTO
              else servicio_diagnostico.historial(u.id))
    c = next((x for x in fuente if x.id == id_consulta), None)
    if c is None:
        flash("Ese diagnóstico no existe.", "error")
        return redirect(url_for("historial"))
    return render_template("consulta.html", c=c)


@app.route("/como-funciona")
@requiere_sesion()
def como_funciona():
    return render_template("como_funciona.html", preguntas=servicio_conocimiento.preguntas())


# --- Diagnóstico estilo chat (RF-02 y RF-03) ---------------------------------
# Las respuestas se guardan en la sesión del navegador como ids de hechos y,
# en cada petición, se vuelven a pasar por SesionDiagnostico: el motor decide
# qué preguntar y qué opciones son válidas, exactamente como en la consola.

def _reconstruir(respuestas: list[int]) -> tuple[SesionDiagnostico, list[tuple]]:
    sesion = servicio_diagnostico.nueva_sesion()
    conversacion = []
    for id_hecho in respuestas:
        pregunta = sesion.siguiente_pregunta()
        hecho = next((op for op in sesion.opciones(pregunta) if op.id == id_hecho), None) \
            if pregunta else None
        if hecho is None:
            raise ErrorNegocio("La conversación no es válida; se reinició el diagnóstico.")
        sesion.responder(pregunta, hecho)
        conversacion.append((pregunta, hecho))
    return sesion, conversacion


@app.route("/diagnostico")
@requiere_sesion()
def diagnostico():
    respuestas = session.get("respuestas", [])
    try:
        sesion, conversacion = _reconstruir(respuestas)
    except ErrorNegocio as e:
        session.pop("respuestas", None)
        session.pop("id_consulta", None)
        flash(str(e), "error")
        return redirect(url_for("diagnostico"))

    pregunta = sesion.siguiente_pregunta()
    resultado = None
    if pregunta is None and respuestas:
        resultado = sesion.concluir()
        if "id_consulta" not in session:   # se registra una sola vez
            session["id_consulta"] = servicio_diagnostico.registrar(
                usuario_actual().id, sesion, resultado)
    return render_template("diagnostico.html", conversacion=conversacion,
                           pregunta=pregunta,
                           opciones=sesion.opciones(pregunta) if pregunta else [],
                           resultado=resultado, paso=len(conversacion) + 1)


@app.post("/diagnostico/responder")
@requiere_sesion()
def responder():
    if "id_consulta" not in session:
        session["respuestas"] = session.get("respuestas", []) + [int(request.form["hecho"])]
    return redirect(url_for("diagnostico"))


@app.post("/diagnostico/deshacer")
@requiere_sesion()
def deshacer():
    if "id_consulta" not in session and session.get("respuestas"):
        session["respuestas"] = session["respuestas"][:-1]
    return redirect(url_for("diagnostico"))


@app.post("/diagnostico/nuevo")
@requiere_sesion()
def nuevo_diagnostico():
    session.pop("respuestas", None)
    session.pop("id_consulta", None)
    return redirect(url_for("diagnostico"))


# --- Secciones de experto, ingeniero y administrador -------------------------

@app.route("/conocimiento")
@requiere_sesion(*ROLES_CONOCIMIENTO)
def conocimiento():
    return render_template("conocimiento.html",
                           hipotesis=servicio_conocimiento.hipotesis(),
                           reglas=servicio_conocimiento.reglas())


@app.route("/diagnosticos")
@requiere_sesion(*ROLES_CONOCIMIENTO)
def diagnosticos():
    return render_template("diagnosticos.html",
                           consultas=servicio_diagnostico.todas_las_consultas())


@app.route("/usuarios", methods=["GET", "POST"])
@requiere_sesion("administrador")
def usuarios():
    if request.method == "POST":
        servicio_usuarios.cambiar_rol(int(request.form["id_usuario"]), request.form["rol"])
        flash("Rol actualizado.", "ok")
        return redirect(url_for("usuarios"))
    return render_template("usuarios.html", usuarios=servicio_usuarios.listar(), roles=ROLES)
