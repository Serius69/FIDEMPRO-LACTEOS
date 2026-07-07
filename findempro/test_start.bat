@echo off
setlocal

echo ============================================================
echo  FINDEMPRO AI - Entorno TESTING
echo  Puerto: 8001  ^|  DB: SQLite (db_test.sqlite3)
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
set DJANGO_ENV=test
set DJANGO_SETTINGS_MODULE=findempro.settings.testing

echo [1/4] Cargando .env.test...
if not exist ".env.test" (
    echo [AVISO] .env.test no encontrado. Se usan valores por defecto.
)

echo [2/4] Aplicando migraciones en DB de testing...
python manage.py migrate --settings=findempro.settings.testing
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Fallo en migraciones de testing. Revisa la configuracion.
    pause
    exit /b 1
)

echo [3/4] Ejecutando suite de tests...
echo.
python -m pytest simulate/tests/test_core_engine.py -v --tb=short
set TEST_RESULT=%ERRORLEVEL%

echo.
if %TEST_RESULT% EQU 0 (
    echo [OK] Todos los tests pasaron correctamente.
) else (
    echo [AVISO] Algunos tests fallaron. Revisa la salida anterior.
)

echo.
echo [4/4] Iniciando servidor de testing en http://127.0.0.1:8001
echo.
echo  Presiona Ctrl+C para detener el servidor
echo.
python manage.py runserver 0.0.0.0:8001 --settings=findempro.settings.testing

endlocal
