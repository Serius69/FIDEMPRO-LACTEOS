@echo off
setlocal

echo ============================================================
echo  FINDEMPRO AI - Entorno PRODUCTION
echo  Puerto: 8002  ^|  DB: PostgreSQL (findempro_prod)
echo ============================================================
echo.

cd /d "%~dp0"

:: Verificar entorno virtual
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Entorno virtual no encontrado. Ejecuta setup.bat primero.
    pause
    exit /b 1
)

:: Verificar que existe .env.production (obligatorio)
if not exist ".env.production" (
    echo [ERROR] Falta .env.production
    echo.
    echo  No se puede iniciar produccion sin variables de entorno configuradas.
    echo  Copia .env.production.example y rellena los valores reales:
    echo    SECRET_KEY, DJANGO_ALLOWED_HOSTS, DB_PASSWORD, etc.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

:: Definir entorno
set DJANGO_ENV=production
set DJANGO_SETTINGS_MODULE=findempro.settings.production

echo [1/4] Cargando .env.production...

echo [2/4] Recolectando archivos estaticos...
python manage.py collectstatic --noinput --settings=findempro.settings.production
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Fallo en collectstatic. Revisa STATIC_ROOT.
    pause
    exit /b 1
)

echo [3/4] Aplicando migraciones...
python manage.py migrate --settings=findempro.settings.production
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Fallo en migraciones de produccion. Revisa la conexion a PostgreSQL.
    pause
    exit /b 1
)

echo [4/4] Iniciando servidor en http://0.0.0.0:8002
echo.
echo  NOTA: Para produccion real usa Gunicorn + Nginx en lugar de runserver.
echo  Comando Gunicorn: gunicorn findempro.wsgi:application -c gunicorn.conf.py
echo.
echo  Presiona Ctrl+C para detener el servidor
echo.
python manage.py runserver 0.0.0.0:8002 --settings=findempro.settings.production

endlocal
