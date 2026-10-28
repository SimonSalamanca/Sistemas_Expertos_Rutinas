"""Verifica la conexión a PostgreSQL con los datos de config.py.

Uso:  python probar_conexion.py
"""
import sys

import psycopg

import config


def main() -> int:
    print(f"Conectando a {config.DB_USER}@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME} ...")
    # 1) El servidor responde y las credenciales son válidas
    try:
        with psycopg.connect(host=config.DB_HOST, port=config.DB_PORT, dbname="postgres",
                             user=config.DB_USER, password=config.DB_PASSWORD,
                             connect_timeout=5) as conn:
            version = conn.execute("SHOW server_version").fetchone()[0]
            existe = conn.execute("SELECT 1 FROM pg_database WHERE datname = %s",
                                  (config.DB_NAME,)).fetchone()
    except psycopg.OperationalError as e:
        print(f"[ERROR] No se pudo conectar al servidor PostgreSQL:\n{e}")
        return 1
    print(f"[OK] Servidor PostgreSQL {version}: usuario y contraseña correctos.")

    if not existe:
        print(f"[AVISO] La base '{config.DB_NAME}' aún no existe. "
              "Ejecute: python inicializar_bd.py")
        return 2
    print(f"[OK] La base '{config.DB_NAME}' existe.")

    # 2) La base tiene las tablas y el conocimiento cargado
    esperados = {"pregunta": 5, "hecho": 15, "hipotesis": 26,
                 "regla_inferencia": 30, "hecho_hipotesis": 118,
                 "peso_hecho_hipotesis": 390}
    try:
        with psycopg.connect(host=config.DB_HOST, port=config.DB_PORT, dbname=config.DB_NAME,
                             user=config.DB_USER, password=config.DB_PASSWORD,
                             connect_timeout=5) as conn:
            ok = True
            for tabla, n in esperados.items():
                real = conn.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
                marca = "OK" if real == n else "!!"
                ok &= real == n
                print(f"  [{marca}] {tabla:<25} {real:>4} (esperado {n})")
            usuarios = conn.execute("SELECT COUNT(*) FROM usuario").fetchone()[0]
            print(f"  [..] {'usuario':<25} {usuarios:>4}")
    except psycopg.errors.UndefinedTable:
        print("[AVISO] Faltan tablas. Ejecute: python inicializar_bd.py")
        return 2
    print("[OK] Todo listo: puede ejecutar main.py" if ok
          else "[AVISO] Los datos no coinciden. Ejecute: python inicializar_bd.py")
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
