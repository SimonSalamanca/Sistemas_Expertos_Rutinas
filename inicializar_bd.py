"""Crea la base de datos, carga el conocimiento y registra usuarios de prueba.

Uso:  python inicializar_bd.py
Advertencia: borra y vuelve a crear todas las tablas.
"""
from pathlib import Path

import psycopg
from psycopg import sql

import config
from datos.conexion import Conexion
from datos.repositorio_conocimiento import RepositorioConocimiento
from datos.repositorio_consultas import RepositorioConsultas
from datos.repositorio_usuarios import RepositorioUsuarios
from negocio.servicio_diagnostico import ServicioDiagnostico
from negocio.servicio_usuarios import ServicioUsuarios
from presentacion.consola import console, tabla

CARPETA_SQL = Path(__file__).parent / "sql"
CONTRASENA_DEMO = "demo123"

CUENTAS_POR_ROL = [
    ("Administrador del sistema", "admin@rutinas.com", "administrador"),
    ("Cristian Moreno (experto)", "experto@rutinas.com", "experto"),
    ("Ingeniero del conocimiento", "ingeniero@rutinas.com", "ingeniero"),
]

# Usuarios de prueba del documento (Tabla 19) y sus respuestas
USUARIOS_PRUEBA = [
    ("Laura Gómez", "laura.gomez@example.com", ["No", "Básico o en casa"]),
    ("Andrés Rojas", "andres.rojas@example.com", ["No estoy seguro", "Gimnasio completo"]),
    ("Camila Torres", "camila.torres@example.com", ["Sí", "Menos de 6 meses", "Básico o en casa"]),
    ("Valentina Ruiz", "valentina.ruiz@example.com",
     ["Sí", "6 meses a 2 años", "Básico o en casa", "Pérdida de grasa"]),
    ("Julián Pérez", "julian.perez@example.com",
     ["Sí", "6 meses a 2 años", "Gimnasio completo", "Hipertrofia"]),
    ("Daniela Castro", "daniela.castro@example.com",
     ["Sí", "Más de 2 años", "Básico o en casa", "Rendimiento deportivo"]),
    ("Santiago Díaz", "santiago.diaz@example.com",
     ["Sí", "Más de 2 años", "Gimnasio completo", "Fuerza", "Intensidad"]),
    ("Mateo Herrera", "mateo.herrera@example.com",
     ["Sí", "Más de 2 años", "Gimnasio completo", "Resistencia"]),
]


def crear_base_si_no_existe() -> None:
    with psycopg.connect(host=config.DB_HOST, port=config.DB_PORT, dbname="postgres",
                         user=config.DB_USER, password=config.DB_PASSWORD,
                         autocommit=True) as conn:
        existe = conn.execute("SELECT 1 FROM pg_database WHERE datname = %s",
                              (config.DB_NAME,)).fetchone()
        if not existe:
            conn.execute(sql.SQL("CREATE DATABASE {} ENCODING 'UTF8' TEMPLATE template0")
                         .format(sql.Identifier(config.DB_NAME)))
            console.print(f"Base de datos [bold]{config.DB_NAME}[/] creada.")


def ejecutar_scripts(conexion: Conexion) -> None:
    for archivo in ("01_esquema.sql", "02_carga_conocimiento.sql"):
        script = (CARPETA_SQL / archivo).read_text(encoding="utf-8")
        script = script.replace("BEGIN;", "").replace("COMMIT;", "")
        with conexion.transaccion() as cur:
            cur.execute(script)
        console.print(f"[green]✔[/] {archivo}")


def main() -> None:
    crear_base_si_no_existe()
    conexion = Conexion()
    ejecutar_scripts(conexion)

    usuarios = ServicioUsuarios(RepositorioUsuarios(conexion))
    diagnostico = ServicioDiagnostico(RepositorioConocimiento(conexion),
                                      RepositorioConsultas(conexion))

    for nombre, correo, rol in CUENTAS_POR_ROL:
        usuarios.registrar(nombre, correo, CONTRASENA_DEMO, rol)

    # Cada usuario de prueba responde el cuestionario a través del motor
    filas = []
    for nombre, correo, respuestas in USUARIOS_PRUEBA:
        usuario = usuarios.registrar(nombre, correo, CONTRASENA_DEMO)
        sesion = diagnostico.nueva_sesion()
        for valor in respuestas:
            pregunta = sesion.siguiente_pregunta()
            hecho = next(op for op in sesion.opciones(pregunta) if op.valor == valor)
            sesion.responder(pregunta, hecho)
        resultado = sesion.concluir()
        diagnostico.registrar(usuario.id, sesion, resultado)
        alternativa = (f"{resultado.alternativas[0][0].codigo} "
                       f"({resultado.alternativas[0][1]:.1%})" if resultado.alternativas else "-")
        filas.append([nombre, " · ".join(respuestas), resultado.hipotesis.codigo,
                       f"{resultado.probabilidad:.1%}", alternativa, resultado.regla.codigo])

    console.print(tabla(["Usuario", "Respuestas", "Hipótesis", "Probabilidad",
                         "2.ª opción", "Regla"], filas,
                        titulo="Diagnósticos de prueba (motor bayesiano)"))
    console.print(tabla(["Rol", "Correo"],
                        [[r, c] for _, c, r in CUENTAS_POR_ROL] +
                        [["usuario", USUARIOS_PRUEBA[0][1]]],
                        titulo=f"Cuentas de prueba (contraseña: {CONTRASENA_DEMO})"))
    conexion.cerrar()


if __name__ == "__main__":
    try:
        main()
    except psycopg.OperationalError as e:
        console.print(f"[bold red]No se pudo conectar a PostgreSQL.[/]\n{e}\n"
                      "Revise los datos de conexión en config_local.py.")
