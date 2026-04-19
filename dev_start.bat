@echo off
setlocal EnableDelayedExpansion

echo ============================================================
echo   FINDEMPRO AI - Servidor de Desarrollo
echo ============================================================
echo.

:: Verificar entorno virtual
if not exist venv\Scripts\activate.bat (
    echo [ERROR] Entorno virtual no encontrado. Ejecuta setup.bat primero.
    pause
    exit /b 1
)

:: Activar entorno virtual
call venv\Scripts\activate.bat
echo [OK] Entorno virtual activo

:: Configurar variable de entorno Django
set DJANGO_ENV=development
set DJANGO_SETTINGS_MODULE=findempro.settings.development

:: Verificar archivo .env
if not exist findempro\.env.development (
    echo [WARN] findempro\.env.development no encontrado.
    echo [INFO] Usando configuracion por defecto de development.py
)

:: Ir a la carpeta del proyecto
cd findempro

echo.
echo [INFO] Verificando configuracion Django...
python manage.py check --settings=findempro.settings.development
if errorlevel 1 (
    echo [ERROR] La verificacion fallo. Revisa la configuracion.
    cd ..
    pause
    exit /b 1
)

echo.
echo [INFO] Aplicando migraciones pendientes...
python manage.py migrate --settings=findempro.settings.development

echo.
echo ============================================================
echo   Servidor Django iniciando en http://127.0.0.1:8000
echo   Admin panel: http://127.0.0.1:8000/admin/
echo   Swagger API: http://127.0.0.1:8000/swagger/
echo   Presiona Ctrl+C para detener
echo ============================================================
echo.

:: Iniciar servidor Django
python manage.py runserver 0.0.0.0:8000 --settings=findempro.settings.development

cd ..
pause
