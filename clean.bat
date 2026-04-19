@echo off
setlocal EnableDelayedExpansion

echo ============================================================
echo   FINDEMPRO AI - Limpieza del Proyecto
echo ============================================================
echo.
echo Este script elimina archivos temporales y de cache.
echo Los archivos de codigo fuente NO se veran afectados.
echo.
set /p CONFIRM="Continuar con la limpieza? (s/N): "
if /i not "%CONFIRM%"=="s" (
    echo Operacion cancelada.
    pause
    exit /b 0
)

echo.
echo [1/6] Eliminando __pycache__ y archivos .pyc...
for /d /r . %%d in (__pycache__) do (
    if exist "%%d" (
        rmdir /s /q "%%d"
    )
)
del /s /q *.pyc 2>nul
del /s /q *.pyo 2>nul
echo [OK] Cache de Python eliminado

echo.
echo [2/6] Limpiando archivos de cobertura y tests...
if exist .coverage del .coverage
if exist coverage.xml del coverage.xml
if exist htmlcov rmdir /s /q htmlcov
if exist .pytest_cache rmdir /s /q .pytest_cache
echo [OK] Archivos de test eliminados

echo.
echo [3/6] Limpiando archivos temporales...
del /s /q *.tmp 2>nul
del /s /q *.temp 2>nul
del /s /q *.bak 2>nul
del /s /q *.orig 2>nul
echo [OK] Archivos temporales eliminados

echo.
echo [4/6] Limpiando logs de desarrollo...
if exist findempro\logs (
    del /q findempro\logs\*.log 2>nul
    echo [OK] Logs eliminados
) else (
    echo [INFO] Carpeta de logs no encontrada
)

echo.
echo [5/6] Limpiando staticfiles generados...
if exist findempro\staticfiles (
    rmdir /s /q findempro\staticfiles
    mkdir findempro\staticfiles
    echo [OK] staticfiles limpiado (se regenera con collectstatic)
) else (
    echo [INFO] staticfiles no encontrado
)

echo.
echo [6/6] Verificando estado de Git...
git status --short
echo.
echo ============================================================
echo   LIMPIEZA COMPLETADA
echo ============================================================
echo.
echo Para regenerar los archivos estaticos ejecuta:
echo   dev_start.bat  (los regenera automaticamente)
echo.
pause
