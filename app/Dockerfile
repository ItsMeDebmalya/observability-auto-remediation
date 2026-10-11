# syntax=docker/dockerfile:1
FROM python:3.12-slim
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
RUN useradd --create-home appuser
USER appuser
EXPOSE 8080
# Single worker so the in-process health/metric state is consistent across scrapes.
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "app:app"]
