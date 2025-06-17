FROM python:3.12-slim

WORKDIR /home

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY ./app /home/app
COPY ./datasets /home/datasets
COPY ./alembic /home/alembic
COPY alembic.ini /home/

# Criar script de inicialização
# Dentro do Dockerfile:
RUN echo '#!/bin/bash\n\
set -e\n\
echo "Aguardando PostgreSQL em $PGHOST:$PGPORT..."\n\
while ! pg_isready -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE"; do\n\
  echo "PostgreSQL ainda não pronto em $PGHOST:$PGPORT..."\n\
  sleep 2\n\
done\n\
echo "Executando migrações..."\n\
alembic upgrade head\n\
echo "Iniciando aplicação..."\n\
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}\n' > /home/entrypoint.sh
  
RUN chmod +x /home/entrypoint.sh

# Instalar postgresql-client para pg_isready
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

CMD ["/home/entrypoint.sh"]