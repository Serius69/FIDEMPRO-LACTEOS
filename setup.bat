@echo off
setlocal EnableDelayedExpansion

echo ============================================================
echo   FINDEMPRO AI - Configuracion Inicial del Entorno
echo ============================================================
echo.

:: Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no encontrado. Instala Python 3.10+ desde python.org
    pause
    exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYTHON_VERSION=%%v
echo [OK] Python %PYTHON_VERSION% detectado

:: Verificar pip
pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip no encontrado.
    pause
    exit /b 1
)
echo [OK] pip disponible

:: Verificar Node.js (opcional)
node --version >nul 2>&1
if errorlevel 1 (
    echo [WARN] Node.js no encontrado. Los assets frontend no se compilaran automaticamente.
) else (
    for /f %%v in ('node --version') do echo [OK] Node.js %%v detectado
)

echo.
echo [1/7] Creando entorno virtual...
if exist venv (
    echo [INFO] Entorno virtual ya existe. Omitiendo creacion.
) else (
    python -m venv venv
    echo [OK] Entorno virtual creado en /venv
)

echo.
echo [2/7] Activando entorno virtual...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] No se pudo activar el entorno virtual.
    pause
    exit /b 1
)
echo [OK] Entorno virtual activo

echo.
echo [3/7] Instalando dependencias Python...
pip install --upgrade pip >nul 2>&1
pip install -r findempro\requirements\base.txt
if errorlevel 1 (
    echo [ERROR] Fallo la instalacion de dependencias.
    pause
    exit /b 1
)
echo [OK] Dependencias instaladas

echo.
echo [4/7] Configurando variables de entorno...
if not exist findempro\.env.development (
    if exist findempro\.env.example (
        copy findempro\.env.example findempro\.env.development >nul
        echo [OK] Archivo .env.development creado desde .env.example
        echo [ACCION REQUERIDA] Edita findempro\.env.development con tus valores
    ) else (
        echo [WARN] .env.example no encontrado. Crea manualmente findempro\.env.development
    )
) else (
    echo [INFO] .env.development ya existe. Omitiendo.
)

echo.
echo [5/7] Aplicando migraciones de base de datos...
cd findempro
python manage.py migrate --settings=findempro.settings.development
if errorlevel 1 (
    echo [WARN] Fallo la migracion. Verifica la configuracion de la base de datos en .env.development
) else (
    echo [OK] Migraciones aplicadas
)

echo.
echo [6/7] Recolectando archivos estaticos...
python manage.py collectstatic --noinput --settings=findempro.settings.development >nul 2>&1
echo [OK] Archivos estaticos recolectados

echo.
echo [7/7] Verificando configuracion...
python manage.py check --settings=findempro.settings.development
if errorlevel 1 (
    echo [WARN] Se encontraron advertencias en la configuracion. Revisa la salida anterior.
) else (
    echo [OK] Configuracion valida
)

cd ..

echo.
echo [EXTRA] Instalando Git hooks (pre-commit, commit-msg)...
if exist .git\hooks (
    echo [OK] Hooks ya instalados en .git/hooks/
    echo [INFO] pre-commit y commit-msg activos para este repositorio
) else (
    echo [WARN] Directorio .git/hooks no encontrado. Asegurate de estar en la raiz del repo.
)

echo.
echo ============================================================
echo   CONFIGURACION COMPLETADA
echo ============================================================
echo.
echo Pasos siguientes:
echo   1. Edita findempro\.env.development con tus credenciales
echo   2. Asegurate que PostgreSQL este corriendo
echo   3. Asegurate que Redis este corriendo
echo   4. Ejecuta: dev_start.bat para iniciar el servidor
echo.
echo Comandos utiles:
echo   python findempro\manage.py createsuperuser  (crear admin)
echo   python findempro\manage.py shell            (consola Django)
echo   python findempro\manage.py test             (ejecutar tests)
echo.
pause
