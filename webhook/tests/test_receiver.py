"""Test the webhook -> Ansible remediation chain in demo mode.

Runs the real receiver and real ansible-playbook (demo_mode=true), so it
verifies the full mapping from an Alertmanager payload to a playbook run.
"""
import os
from pathlib import Path

os.environ["DEMO_MODE"] = "true"
os.environ["PLAYBOOK_DIR"] = str(Path(__file__).resolve().parents[2] / "remediation" / "playbooks")

from webhook.receiver import create_app


def client():
    app = create_app()
    app.testing = True
    return app.test_client()


FIRING = {
    "alerts": [
        {
            "status": "firing",
            "labels": {"alertname": "AppUnhealthy", "remediation": "restart_service", "target_service": "app"},
        }
    ]
}


def test_healthz():
    resp = client().get("/healthz")
    assert resp.status_code == 200
    assert resp.get_json()["demo_mode"] is True


def test_firing_alert_runs_mapped_playbook():
    resp = client().post("/alert", json=FIRING)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["received"] == 1
    assert len(body["actions"]) == 1
    action = body["actions"][0]
    assert action["remediation"] == "restart_service"
    assert action["playbook"] == "restart_service.yml"
    assert action["status"] == "ok"


def test_unknown_remediation_is_rejected():
    payload = {"alerts": [{"status": "firing", "labels": {"remediation": "rm_rf_slash", "target_service": "app"}}]}
    resp = client().post("/alert", json=payload)
    assert resp.status_code == 200
    assert resp.get_json()["actions"][0]["status"] == "rejected"
