"""Alertmanager webhook receiver that triggers Ansible remediation playbooks.

Alertmanager POSTs firing alerts to /alert. Each alert carries a `remediation`
label naming the action to take; this service maps that label to an allow-listed
Ansible playbook and runs it. A DEMO_MODE flag makes the playbooks log-only so
the full chain can be exercised safely in CI.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

from flask import Flask, jsonify, request

app = Flask(__name__)

# Allow-list: only these remediation labels may trigger a playbook.
REMEDIATION_PLAYBOOKS = {
    "restart_service": "restart_service.yml",
    "scale_service": "scale_service.yml",
    "reclaim_disk": "reclaim_disk.yml",
}

_runs: dict[str, int] = {k: 0 for k in REMEDIATION_PLAYBOOKS}


def _playbook_dir() -> Path:
    return Path(os.environ.get("PLAYBOOK_DIR", "/remediation/playbooks"))


def _demo_mode() -> bool:
    return os.environ.get("DEMO_MODE", "false").lower() == "true"


def run_playbook(name: str, target: str) -> dict:
    playbook = REMEDIATION_PLAYBOOKS.get(name)
    if playbook is None:
        return {"remediation": name, "status": "rejected", "reason": "not allow-listed"}

    cmd = [
        "ansible-playbook",
        str(_playbook_dir() / playbook),
        "-i", "localhost,",
        "-c", "local",
        "-e", f"target_service={target}",
        "-e", f"demo_mode={str(_demo_mode()).lower()}",
    ]
    result = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=120)
    _runs[name] += 1
    return {
        "remediation": name,
        "target": target,
        "playbook": playbook,
        "status": "ok" if result.returncode == 0 else "failed",
        "rc": result.returncode,
    }


@app.get("/healthz")
def healthz():
    return jsonify(status="ok", demo_mode=_demo_mode()), 200


@app.get("/stats")
def stats():
    return jsonify(runs=_runs), 200


@app.post("/alert")
def alert():
    payload = request.get_json(force=True, silent=True) or {}
    actions = []
    for a in payload.get("alerts", []):
        if a.get("status") != "firing":
            continue
        labels = a.get("labels", {})
        remediation = labels.get("remediation")
        target = labels.get("target_service", "unknown")
        if remediation:
            actions.append(run_playbook(remediation, target))
    return jsonify(received=len(payload.get("alerts", [])), actions=actions), 200


def create_app() -> Flask:
    return app


if __name__ == "__main__":  # pragma: no cover
    app.run(host="0.0.0.0", port=5001)
