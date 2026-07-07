@echo off
chcp 65001 >nul
setlocal

title FINDEMPRO AI - DEV

cd /d "%~dp0findempro"

echo ============================================================
echo FINDEMPRO AI - MODO DESARROLLO
echo Django : http://localhost:8003
echo Dir    : %cd%
echo ============================================================
echo.

if not exist "venv\Scripts\python.exe" (
    echo [ERROR] venv no encontrado en: %cd%\venv\
    echo         Ejecuta: python -m venv venv
    echo         Luego  : venv\Scripts\pip install -r requirements\development.txt
    pause
    exit /b 1
)

if not exist "manage.py" (
    echo [ERROR] manage.py no encontrado en: %cd%
    pause
    exit /b 1
)

set DJANGO_ENV=development
set DJANGO_SETTINGS_MODULE=findempro.settings.development

echo [1/2] Aplicando migraciones...
venv\Scripts\python.exe manage.py migrate --settings=findempro.settings.development
if %ERRORLEVEL% NEQ 0 (
    echo [WARN] Migraciones fallaron - verifica que la base de datos este corriendo.
    echo        Continuando con runserver de todas formas...
)

echo.
echo [2/2] Iniciando Django en http://localhost:8003 ...
echo Presiona Ctrl+C para detener.
echo.
venv\Scripts\python.exe manage.py runserver 0.0.0.0:8003 --settings=findempro.settings.development
