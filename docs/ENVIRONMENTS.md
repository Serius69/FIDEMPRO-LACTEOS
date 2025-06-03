# Gestión de Entornos - Findempro

## Resumen

El proyecto Findempro utiliza una configuración modular para separar los entornos de desarrollo, staging y producción.

## Entornos Disponibles

### 1. Development (Desarrollo)
- **Propósito**: Desarrollo local y pruebas
- **Características**:
  - DEBUG = True
  - Base de datos local
  - Email en consola
  - Sin HTTPS
  - Logs detallados
  - Django Debug Toolbar activo

### 2. Staging (Pre-producción)
- **Propósito**: Pruebas finales antes de producción
- **Características**:
  - DEBUG = False
  - Base de datos separada
  - Email en archivos
  - HTTPS opcional
  - Logs moderados
  - Misma infraestructura que producción

### 3. Production (Producción)
- **Propósito**: Entorno en vivo para usuarios finales
- **Características**:
  - DEBUG = False
  - Base de datos de producción
  - Email SMTP real
  - HTTPS obligatorio
  - Logs mínimos
  - Monitoreo con Sentry

## Cambiar Entre Entornos

### Método 1: Variables de Entorno
```bash
export DJANGO_ENV=development  # o staging, production