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

HOST="127.0.0.1"
PORT="8000"
URL="http://${HOST}:${PORT}"

# Función para abrir el navegador según el sistema operativo
abrir_navegador() {
    echo "[3/4] Esperando a que el servidor esté disponible..."
    # Espera activa hasta que el servidor responda (máx. ~15s)
    for i in $(seq 1 30); do
        if curl -s -o /dev/null "${URL}"; then
            break
        fi
        sleep 0.5
    done

    echo "[4/4] Abriendo el navegador en ${URL} ..."
    if command -v xdg-open &> /dev/null; then
        xdg-open "${URL}" &> /dev/null &        # Linux
    elif command -v open &> /dev/null; then
        open "${URL}" &> /dev/null &            # macOS
    elif command -v start &> /dev/null; then
        start "${URL}" &> /dev/null &           # Windows (Git Bash / cmd)
    else
        echo "No se pudo detectar un comando para abrir el navegador."
        echo "Abre manualmente: ${URL}"
    fi
}

echo "[2/4] Iniciando servidor en ${URL} ..."

# Lanza el navegador en segundo plano mientras arranca el servidor
abrir_navegador &

# Arranca el servidor (queda en primer plano, con auto-reload)
uv run uvicorn main:app --host "${HOST}" --port "${PORT}" --reload
