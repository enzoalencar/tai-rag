FROM python:3.12-slim

WORKDIR /home

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY ./app /home/app
COPY ./datasets /home/datasets

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]