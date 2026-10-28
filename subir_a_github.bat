@echo off
chcp 65001 >nul
cd /d "%~dp0"
set REPO=https://github.com/SimonSalamanca/Sistemas_Expertos_Rutinas.git

where git >nul 2>nul
if errorlevel 1 (
    echo Git no esta instalado. Descarguelo de https://git-scm.com/download/win y vuelva a ejecutar este archivo.
    pause
    exit /b 1
)

if not exist .git (
    git init -b main
)

rem Identidad para el commit (solo si no esta configurada)
git config user.email >nul 2>nul
if errorlevel 1 (
    set /p NOMBRE=Su nombre para los commits:
    set /p CORREO=Su correo de GitHub:
    git config user.name "%NOMBRE%"
    git config user.email "%CORREO%"
)

echo.
echo === Archivos que se van a subir (config_local.py y venv quedan fuera) ===
git add .
git status --short
echo.
git commit -m "Sistema experto de rutinas: motor bayesiano e interfaz web"

git remote remove origin >nul 2>nul
git remote add origin %REPO%
git branch -M main

echo.
echo === Subiendo a GitHub (puede abrirse el navegador para iniciar sesion) ===
git push -u origin main
if errorlevel 1 (
    echo.
    echo El repositorio ya tenia archivos. Combinando y reintentando...
    git pull origin main --allow-unrelated-histories --no-edit
    git push -u origin main
)
echo.
pause
