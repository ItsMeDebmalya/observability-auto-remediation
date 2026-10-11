# observability-auto-remediation

[![CI](https://github.com/ItsMeDebmalya/observability-auto-remediation/actions/workflows/ci.yml/badge.svg)](https://github.com/ItsMeDebmalya/observability-auto-remediation/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> A full observability stack — **Prometheus, Grafana, Alertmanager, and ELK** —
> wired to **Ansible playbooks that auto-remediate** common incidents, so the
> system restarts failed services, scales under load, and reclaims disk
> **without manual intervention**.

An instrumented service exposes metrics; Prometheus evaluates recording and
alerting rules; Alertmanager routes firing alerts (by a `remediation` label) to
a webhook receiver; the receiver maps each alert to an allow-listed Ansible
playbook and runs it. Application and remediation logs flow through an ELK
pipeline for search in Kibana.

---

## The auto-remediation loop

```
  ┌──────────┐   scrape    ┌────────────┐  rule fires  ┌──────────────┐
  │ sample   │────────────▶│ Prometheus │─────────────▶│ Alertmanager │
  │  app     │  /metrics   │  rules     │   alert      │   routing    │
  └──────────┘             └────────────┘              └──────┬───────┘
       ▲                                                       │ webhook
       │ restart / scale / reclaim                             ▼
  ┌────┴───────────────┐   runs playbook   ┌─────────────────────────────┐
  │  Ansible playbooks │◀──────────────────│  remediation webhook         │
  │ restart/scale/disk │                   │ (maps remediation label ->   │
  └────────────────────┘                   │  allow-listed playbook)      │
                                            └─────────────────────────────┘
```

| Alert | Condition | Remediation playbook |
|-------|-----------|----------------------|
| `AppUnhealthy` | `app_healthy == 0` for 30s | `restart_service.yml` |
| `AppDown` | scrape target down 30s | `restart_service.yml` |
| `AppHighLatency` | p95 > 500ms for 2m | `scale_service.yml` |
| `NodeDiskFilling` | root fs > 85% for 5m | `reclaim_disk.yml` |

The webhook only runs **allow-listed** playbooks, and each playbook honours a
`demo_mode` flag (log-only) so the whole chain can run safely in CI.

## Stack

| Component | Role |
|-----------|------|
| Prometheus | scraping, recording rules, alert evaluation |
| Alertmanager | routes alerts to the remediation webhook |
| Grafana | provisioned Prometheus datasource + Service Overview dashboard |
| node-exporter | host metrics (disk, cpu, mem) |
| ELK (Elasticsearch, Logstash, Kibana) | log pipeline (opt-in profile) |
| remediation-webhook | Alertmanager webhook → Ansible |

## Run it

```bash
# Core stack (metrics + remediation)
docker compose up -d --build

# Add the ELK log pipeline
docker compose --profile elk up -d
```

Then open:
- Grafana → http://localhost:3000 (admin / admin)
- Prometheus → http://localhost:9090 · Alertmanager → http://localhost:9093
- Kibana (elk profile) → http://localhost:5601

### See auto-remediation happen

```bash
# Mark the app unhealthy for 5 minutes
curl http://localhost:8080/fail/300

# Within ~1 minute the AppUnhealthy alert fires, Alertmanager calls the
# webhook, and the restart_service playbook runs. Watch it:
curl http://localhost:5001/stats
docker compose logs -f remediation-webhook
```

Set `DEMO_MODE=true` (default in CI) to make playbooks log-only; unset for real
actions (container restart, disk prune).

## Testing

CI runs on every push/PR and:
- lints (ruff) and unit-tests the **webhook → Ansible** chain,
- `ansible-lint`s the remediation playbooks,
- validates Prometheus rules (`promtool`), Alertmanager config (`amtool`), and
  the compose file,
- stands up the live stack and **drives the full alert → auto-remediation loop**,
  asserting the `restart_service` playbook actually fires.

## License

MIT — see [LICENSE](LICENSE).
