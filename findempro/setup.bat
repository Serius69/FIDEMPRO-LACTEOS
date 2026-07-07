@echo off
setlocal

echo ============================================================
echo  FINDEMPRO AI - Setup inicial de entornos
echo ============================================================
echo.

cd /d "%~dp0"

:: Verificar que existe el entorno virtual
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] No se encontro el entorno virtual en venv\
    echo.
    echo Crea el venv con:
    echo   python -m venv venv
    echo   venv\Scripts\activate.bat
    echo   pip install -r requirements\base.txt
    echo   pip install -r requirements\development.txt
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

echo [1/5] Instalando dependencias base...
pip install -r requirements\base.txt --quiet
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Fallo al instalar requirements\base.txt
    pause
    exit /b 1
)

echo [2/5] Instalando dependencias de desarrollo...
pip install -r requirements\development.txt --quiet
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Fallo al instalar requirements\development.txt
    pause
    exit /b 1
)

echo [3/5] Verificando archivos .env...
if not exist ".env.development" (
    echo [AVISO] Falta .env.development - usando valores por defecto
) else (
    echo [OK] .env.development encontrado
)
if not exist ".env.test" (
    echo [AVISO] Falta .env.test - usando valores por defecto
) else (
    echo [OK] .env.test encontrado
)
if not exist ".env.production" (
    echo [AVISO] Falta .env.production - requerido para produccion
) else (
    echo [OK] .env.production encontrado
)

echo [4/5] Aplicando migraciones en entorno development...
set DJANGO_ENV=development
python manage.py migrate --settings=findempro.settings.development
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Fallo al aplicar migraciones en development
    pause
    exit /b 1
)

echo [5/5] Aplicando migraciones en entorno testing...
set DJANGO_ENV=testing
python manage.py migrate --settings=findempro.settings.testing
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Fallo al aplicar migraciones en testing
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  Setup completado correctamente
echo ============================================================
echo.
echo  Comandos disponibles:
echo    dev_start.bat   - Desarrollo  (puerto 8000, SQLite)
echo    test_start.bat  - Testing     (puerto 8001, SQLite)
echo    prod_start.bat  - Produccion  (puerto 8002, PostgreSQL)
echo.

endlocal
pause
