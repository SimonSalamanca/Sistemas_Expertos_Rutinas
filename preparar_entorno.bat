@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo === Creando entorno virtual (venv) ===
if not exist venv\Scripts\python.exe (
    py -3 -m venv venv 2>nul || python -m venv venv
)
echo === Instalando dependencias ===
venv\Scripts\python.exe -m pip install --upgrade pip
venv\Scripts\python.exe -m pip install -r requirements.txt
echo.
echo === Probando conexion a PostgreSQL ===
venv\Scripts\python.exe probar_conexion.py
if %errorlevel%==2 (
    echo.
    echo === Inicializando la base de datos ===
    venv\Scripts\python.exe inicializar_bd.py
    venv\Scripts\python.exe probar_conexion.py
)
echo.
pause
