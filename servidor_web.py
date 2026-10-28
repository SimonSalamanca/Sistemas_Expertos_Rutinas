"""Inicia la interfaz web del sistema experto.

Uso:  python servidor_web.py   y abrir  http://127.0.0.1:5000
"""
import sys

import psycopg

from datos.conexion import Conexion
from web.app import app

if __name__ == "__main__":
    try:
        Conexion().probar()
    except psycopg.OperationalError as e:
        print(f"No se pudo conectar a PostgreSQL.\n{e}\nRevise los datos de conexión en config_local.py.")
        sys.exit(1)
    print("Sistema experto disponible en  http://127.0.0.1:5000  (Ctrl + C para detener)")
    # Un solo hilo: la capa de datos comparte una conexión (patrón Singleton).
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=False)
