#!/bin/bash

# Script para iniciar el entorno de desarrollo de Habilitat

set -e

echo "🚀 Iniciando Habilitat..."

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar que estamos en el directorio correcto
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}Error: Ejecuta este script desde el directorio raíz del proyecto${NC}"
    exit 1
fi

# Opción 1: Con Docker
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    echo -e "${GREEN}Docker detectado. Usando docker-compose...${NC}"
    docker-compose up -d
    echo ""
    echo -e "${GREEN}✅ Servicios iniciados:${NC}"
    echo "   - Frontend: http://localhost:3000"
    echo "   - Backend:  http://localhost:8000"
    echo "   - API Docs: http://localhost:8000/docs"
    echo ""
    echo "Para ver logs: docker-compose logs -f"
    echo "Para detener:  docker-compose down"
    exit 0
fi

echo -e "${YELLOW}Docker no disponible. Iniciando manualmente...${NC}"
echo ""

# Verificar PostgreSQL
if ! command -v psql &> /dev/null; then
    echo -e "${RED}PostgreSQL no está instalado. Instálalo primero.${NC}"
    exit 1
fi

# Iniciar Backend
echo -e "${GREEN}Iniciando Backend...${NC}"
cd backend

# Crear virtual environment si no existe
if [ ! -d "venv" ]; then
    echo "Creando virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt -q

# Variables de entorno
export DATABASE_URL="postgresql://habilitat:habilitat123@localhost:5432/habilitat"
export JWT_SECRET_KEY="dev-secret-key-at-least-32-characters"

# Ejecutar migraciones
alembic upgrade head 2>/dev/null || echo "Migraciones ya aplicadas o error"

# Iniciar servidor backend en background
uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!
cd ..

# Iniciar Frontend
echo -e "${GREEN}Iniciando Frontend...${NC}"
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo -e "${GREEN}✅ Servicios iniciados:${NC}"
echo "   - Frontend: http://localhost:3000"
echo "   - Backend:  http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo ""
echo "Presiona Ctrl+C para detener todos los servicios"

# Esperar y capturar Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
wait
