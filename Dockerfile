FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    MPLBACKEND=Agg

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# El código se monta como volumen en docker-compose; esta copia permite
# usar la imagen también sin volumen.
COPY . .

CMD ["python", "-c", "print('Usa: docker compose run --rm <sim|dbt|evo|baselines|test|jupyter>')"]
