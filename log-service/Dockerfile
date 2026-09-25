# syntax=docker/dockerfile:1
FROM python:3.13-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

# Sem DB, sem alembic: log-service não tem estado próprio em SQL, só o
# Redis (que é outro container). Sem EXPOSE pro host: só alcançável pela
# rede interna do Docker, pelo nome do serviço (log-service:8002) — mesmo
# princípio do auth-service na atividade 3.
EXPOSE 8002
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
