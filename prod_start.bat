@echo off
setlocal EnableDelayedExpansion

echo ============================================================
echo   FINDEMPRO AI - Servidor de Produccion
echo ============================================================
echo.

:: ADVERTENCIA DE SEGURIDAD
echo [ADVERTENCIA] Este script inicia el servidor en modo PRODUCCION.
echo [ADVERTENCIA] Asegurate de que las variables de entorno esten correctamente configuradas.
echo.
set /p CONFIRM="Continuar? (s/N): "
if /i not "%CONFIRM%"=="s" (
    echo Operacion cancelada.
    pause
    exit /b 0
)

:: Verificar entorno virtual
if not exist venv\Scripts\activate.bat (
    echo [ERROR] Entorno virtual no encontrado. Ejecuta setup.bat primero.
    pause
    exit /b 1
)

:: Activar entorno virtual
call venv\Scripts\activate.bat
echo [OK] Entorno virtual activo

:: Configurar variables de entorno de produccion
set DJANGO_ENV=production
set DJANGO_SETTINGS_MODULE=findempro.settings.production

:: Verificar archivo .env de produccion
if not exist findempro\.env.production (
    echo [ERROR] findempro\.env.production no encontrado.
    echo [INFO] Crea este archivo con las variables de produccion antes de continuar.
    cd ..
    pause
    exit /b 1
)

:: Cargar variables de entorno desde .env.production
for /f "usebackq tokens=1,* delims==" %%A in ("findempro\.env.production") do (
    if not "%%A"=="" if not "%%A:~0,1%"=="#" (
        set "%%A=%%B"
    )
)

cd findempro

echo.
echo [1/5] Verificando configuracion de produccion...
python manage.py check --deploy --settings=findempro.settings.production
if errorlevel 1 (
    echo [WARN] Se encontraron advertencias de despliegue. Revisa antes de continuar.
)

echo.
echo [2/5] Aplicando migraciones...
python manage.py migrate --settings=findempro.settings.production --no-input
if errorlevel 1 (
    echo [ERROR] Fallo la migracion en produccion.
    cd ..
    pause
    exit /b 1
)
echo [OK] Migraciones aplicadas

echo.
echo [3/5] Recolectando archivos estaticos...
python manage.py collectstatic --noinput --settings=findempro.settings.production
echo [OK] Estaticos recolectados

echo.
echo [4/5] Verificando gunicorn...
gunicorn --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Gunicorn no encontrado. Instala con: pip install gunicorn
    cd ..
    pause
    exit /b 1
)
echo [OK] Gunicorn disponible

echo.
echo [5/5] Iniciando servidor Gunicorn...
echo.
echo ============================================================
echo   Servidor de produccion iniciando...
echo   Workers: 4, Threads: 2
echo   Bind: 0.0.0.0:8000
echo   Presiona Ctrl+C para detener
echo ============================================================
echo.

:: Iniciar Gunicorn con configuracion de produccion
if exist gunicorn.conf.py (
    gunicorn findempro.wsgi:application --config gunicorn.conf.py
) else (
    gunicorn findempro.wsgi:application ^
        --bind 0.0.0.0:8000 ^
        --workers 4 ^
        --threads 2 ^
        --worker-class sync ^
        --timeout 120 ^
        --keepalive 5 ^
        --max-requests 1000 ^
        --max-requests-jitter 100 ^
        --access-logfile logs/access.log ^
        --error-logfile logs/error.log ^
        --log-level warning
)

cd ..
pause
