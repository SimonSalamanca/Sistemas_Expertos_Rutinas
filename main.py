"""Sistema experto para la generación de rutinas de entrenamiento.

Arquitectura POO a tres capas:
  presentacion/  ->  negocio/  ->  datos/  ->  PostgreSQL
Aquí se crean los objetos de cada capa y se conectan entre sí.
"""
import sys

import psycopg

from datos.conexion import Conexion
from datos.repositorio_conocimiento import RepositorioConocimiento
from datos.repositorio_consultas import RepositorioConsultas
from datos.repositorio_usuarios import RepositorioUsuarios
from negocio.servicio_base_conocimiento import ServicioBaseConocimiento
from negocio.servicio_diagnostico import ServicioDiagnostico
from negocio.servicio_usuarios import ServicioUsuarios
from presentacion.app import AplicacionConsola
from presentacion.consola import console


def main() -> None:
    conexion = Conexion()

    # Capa de datos
    repo_conocimiento = RepositorioConocimiento(conexion)
    repo_consultas = RepositorioConsultas(conexion)
    repo_usuarios = RepositorioUsuarios(conexion)

    # Capa de negocio (recibe las interfaces, no PostgreSQL)
    servicio_usuarios = ServicioUsuarios(repo_usuarios)
    servicio_diagnostico = ServicioDiagnostico(repo_conocimiento, repo_consultas)
    servicio_conocimiento = ServicioBaseConocimiento(repo_conocimiento)

    # Capa de presentación
    app = AplicacionConsola(servicio_usuarios, servicio_diagnostico, servicio_conocimiento)
    try:
        conexion.probar()
        app.ejecutar()
    except psycopg.OperationalError as e:
        console.print(f"[bold red]No se pudo conectar a PostgreSQL.[/]\n{e}\n"
                      "Revise los datos de conexión en config_local.py.")
        sys.exit(1)
    except (KeyboardInterrupt, EOFError):
        console.print("\n[dim]Programa cerrado.[/]")
    finally:
        conexion.cerrar()


if __name__ == "__main__":
    main()
