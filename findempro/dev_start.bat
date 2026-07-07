@echo off
setlocal

echo ============================================================
echo  FINDEMPRO AI - Entorno DEVELOPMENT
echo  Puerto: 8000  ^|  DB: PostgreSQL (findempro_dev)
echo ============================================================
echo.

cd /d "%~dp0"

:: Verificar entorno virtual
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Entorno virtual no encontrado. Ejecuta setup.bat primero.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

:: Definir entorno
set DJANGO_ENV=development
set DJANGO_SETTINGS_MODULE=findempro.settings.development

echo [1/3] Cargando .env.development...
if not exist ".env.development" (
    echo [AVISO] .env.development no encontrado. Se usan valores por defecto.
)

echo [2/3] Aplicando migraciones...
python manage.py migrate --settings=findempro.settings.development
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Fallo en migraciones. Revisa la configuracion.
    pause
    exit /b 1
)

echo [3/3] Iniciando servidor de desarrollo en http://127.0.0.1:8000
echo.
echo  Presiona Ctrl+C para detener el servidor
echo.
python manage.py runserver 0.0.0.0:8000 --settings=findempro.settings.development

endlocal
