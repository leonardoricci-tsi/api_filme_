# syntax=docker/dockerfile:1
FROM python:3.13-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .

# DATABASE_URL e JWT_SECRET vêm de variáveis de ambiente na hora do
# `docker run`/compose (--env-file) — nunca copiadas pra dentro da imagem.
# Sem EXPOSE pro host: esse container só é alcançável pela rede interna
# do Docker, pelo nome do serviço (auth-service:8001).
EXPOSE 8001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
