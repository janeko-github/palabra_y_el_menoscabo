#!/bin/bash
echo "========================================"
echo "   Palabra y Menoscabo "
echo "   Sistema de Gestión de Palabras"
echo "========================================"
echo ""

# Verificar si Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 no está instalado"
    echo "Por favor instala Python 3.8 o superior"
    exit 1
fi

echo "[1/4] Verificando dependencias..."
if ! python3 -c "import fastapi" &> /dev/null; then
    echo "Instalando dependencias de FastAPI..."
    uv pip3 install -r requirements.txt
fi

uv run uvicorn main:app --reload 





