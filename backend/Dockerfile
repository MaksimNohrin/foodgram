FROM python:3.12

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir

COPY . .

CMD ["gunicorn", \
    "--access-logfile", "-", \
    "--error-logfile", "-", \
    "--capture-output", \
    "--log-level", "debug", \
    "--bind", "0.0.0.0:8000", \
    "backend.wsgi"]
