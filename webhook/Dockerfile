# syntax=docker/dockerfile:1
# NOTE: build with the repository root as context:
#   docker build -f webhook/Dockerfile -t remediation-webhook .
FROM python:3.12-slim

# Docker CLI lets the restart_service playbook restart the target container.
RUN apt-get update \
    && apt-get install -y --no-install-recommends docker.io \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /srv
COPY webhook/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && ansible-galaxy collection install community.docker

COPY webhook/receiver.py .
COPY remediation/playbooks /remediation/playbooks

EXPOSE 5001
# Single worker so the remediation run counter is consistent across requests.
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--workers", "1", "receiver:app"]
