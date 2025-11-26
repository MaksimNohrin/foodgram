FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir

COPY . .
RUN chmod +x entrypoint.sh
ENTRYPOINT [ "./entrypoint.sh" ]

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "backend.wsgi:application"]
