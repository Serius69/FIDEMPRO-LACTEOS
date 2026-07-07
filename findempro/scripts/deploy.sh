#!/bin/bash
# Script de despliegue para producción

set -e

YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Verificar que estamos en producción
if [ "$DJANGO_ENV" != "production" ]; then
    echo -e "${RED}ERROR: Este script solo debe ejecutarse en producción${NC}"
    exit 1
fi

echo -e "${YELLOW}🚀 Iniciando despliegue a producción...${NC}"

# 1. Backup de base de datos
echo -e "${YELLOW}Creando backup de base de datos...${NC}"
./scripts/backup.sh

# 2. Pull últimos cambios
echo -e "${YELLOW}Actualizando código...${NC}"
git pull origin main

# 3. Construir imágenes
echo -e "${YELLOW}Construyendo imágenes Docker...${NC}"
docker-compose -f docker-compose.prod.yml build

# 4. Aplicar migraciones
echo -e "${YELLOW}Aplicando migraciones...${NC}"
docker-compose -f docker-compose.prod.yml run --rm app python manage.py migrate --noinput

# 5. Recolectar estáticos
echo -e "${YELLOW}Recolectando archivos estáticos...${NC}"
docker-compose -f docker-compose.prod.yml run --rm app python manage.py collectstatic --noinput

# 6. Reiniciar servicios
echo -e "${YELLOW}Reiniciando servicios...${NC}"
docker-compose -f docker-compose.prod.yml up -d

# 7. Verificar salud
echo -e "${YELLOW}Verificando estado de la aplicación...${NC}"
sleep 10
curl -f http://localhost/health/ || exit 1

echo -e "${GREEN}✅ Despliegue completado exitosamente!${NC}"