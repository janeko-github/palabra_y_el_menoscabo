necesito una aplicación web con python de backend, con fastapi y uvicorn, con base de datos sqlite
La aplicación debe soportar dar de alta, editar y mantener palabras.
Cada palabra puede tener una descripción donde introducir varios significados, un registro de sinónimos y otro de antónimos. 
La aplicación se llamará "La Palabra y el Menoscabo".
Se podrá exportar tanto a pdf, como excel xlsx, csv y a el formato anki

# 1. Inicializa el proyecto (crea pyproject.toml)
uv init

# 2. Añade todas las dependencias de golpe
uv add fastapi uvicorn sqlalchemy aiosqlite pydantic reportlab openpyxl pandas genanki python-multipart

# 3. Ejecuta directamente (uv se encarga del entorno automáticamente)
uv run uvicorn main:app --reload


