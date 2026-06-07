# Imagen opcional para desplegar la Porra en plataformas con contenedores
# (Fly.io, Railway, etc.). Para Render + Turso NO hace falta: Render usa el
# runtime de Python con render.yaml. Se incluye por si mas adelante quieres
# saltar a Fly.io con un volumen persistente (SQLite sin cambios de codigo).
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# El servidor lee HOST/PORT del entorno (porra/config.py).
ENV HOST=0.0.0.0 \
    PORT=8000
EXPOSE 8000

CMD ["python", "run.py"]
