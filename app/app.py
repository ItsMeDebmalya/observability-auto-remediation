"""Instrumented sample service.

Exposes Prometheus metrics at /metrics and a couple of endpoints that let us
drive the alerting + auto-remediation demo:

- /healthz        liveness probe
- /work           increments a request counter and records latency
- /fail/<seconds>  marks the service unhealthy for N seconds (fires an alert)
"""
from __future__ import annotations

import time

from flask import Flask, jsonify
from prometheus_client import Counter, Gauge, Histogram, make_wsgi_app
from werkzeug.middleware.dispatcher import DispatcherMiddleware

app = Flask(__name__)

REQUESTS = Counter("app_requests_total", "Total requests", ["endpoint"])
LATENCY = Histogram("app_request_latency_seconds", "Request latency", ["endpoint"])
UP = Gauge("app_healthy", "1 if the service considers itself healthy, else 0")
UP.set(1)

_unhealthy_until = 0.0


@app.get("/healthz")
def healthz():
    healthy = time.time() >= _unhealthy_until
    UP.set(1 if healthy else 0)
    return (jsonify(status="ok"), 200) if healthy else (jsonify(status="unhealthy"), 503)


@app.get("/work")
def work():
    with LATENCY.labels("/work").time():
        REQUESTS.labels("/work").inc()
        time.sleep(0.01)
    return jsonify(done=True), 200


@app.get("/fail/<int:seconds>")
def fail(seconds: int):
    """Simulate an outage for the given number of seconds."""
    global _unhealthy_until
    _unhealthy_until = time.time() + seconds
    UP.set(0)
    return jsonify(unhealthy_for=seconds), 200


# Expose /metrics for Prometheus.
app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {"/metrics": make_wsgi_app()})


def create_app() -> Flask:
    return app


if __name__ == "__main__":  # pragma: no cover
    app.run(host="0.0.0.0", port=8080)
