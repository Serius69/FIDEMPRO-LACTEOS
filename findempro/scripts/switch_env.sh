#!/bin/bash
# Script para cambiar entre entornos

YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}Selecciona el entorno:${NC}"
echo "1) Desarrollo"
echo "2) Staging"
echo "3) Producción"
read -p "Opción: " choice

case $choice in
    1)
        ENV="development"
        ENV_FILE=".env.development"
        COMPOSE_FILE="docker-compose.dev.yml"
        ;;
    2)
        ENV="staging"
        ENV_FILE=".env.staging"
        COMPOSE_FILE="docker-compose.staging.yml"
        ;;
    3)
        ENV="production"
        ENV_FILE=".env.production"
        COMPOSE_FILE="docker-compose.prod.yml"
        ;;
    *)
        echo -e "${RED}Opción inválida${NC}"
        exit 1
        ;;
esac

# Detener servicios actuales
echo -e "${YELLOW}Deteniendo servicios actuales...${NC}"
docker-compose down

# Cambiar archivo de entorno
echo -e "${YELLOW}Cambiando a entorno $ENV...${NC}"
cp $ENV_FILE .env

# Actualizar variable de entorno
export DJANGO_ENV=$ENV

# Iniciar nuevos servicios
echo -e "${YELLOW}Iniciando servicios de $ENV...${NC}"
docker-compose -f $COMPOSE_FILE up -d

echo -e "${GREEN}✅ Cambiado a entorno $ENV${NC}"
echo -e "${GREEN}Archivo de configuración: $ENV_FILE${NC}"
echo -e "${GREEN}Docker Compose: $COMPOSE_FILE${NC}"