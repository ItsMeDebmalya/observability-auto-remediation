# Architecture

## Goal

Close the loop between **detection** and **response**: instead of paging a human
for every routine incident, well-understood failures (a dead service, saturation,
a filling disk) are remediated automatically, and only the exceptions need
attention.

## Data flow

1. **Instrumentation** — the sample app exposes Prometheus metrics at `/metrics`
   (`app_healthy`, request counters, latency histogram). node-exporter exposes
   host metrics.
2. **Recording rules** precompute common expressions (request rate, p95 latency,
   filesystem usage ratio) so alerts and dashboards stay cheap and readable.
3. **Alerting rules** evaluate those series. Every alert carries two labels that
   drive remediation: `remediation` (which action) and `target_service` (on what).
4. **Alertmanager** groups and routes firing alerts. A route matcher
   (`remediation=~".+"`) forwards only remediable alerts to the webhook.
5. **Remediation webhook** receives the Alertmanager payload, looks the
   `remediation` label up in an **allow-list**, and runs the mapped Ansible
   playbook with `target_service` as a variable.
6. **Ansible playbooks** perform the fix (restart the container, scale out,
   reclaim disk). A `demo_mode` variable makes them log-only for safe testing.
7. **ELK** receives JSON logs over Logstash TCP and indexes them in
   Elasticsearch for search/visualisation in Kibana.

## Why a label-driven allow-list

Encoding the remediation in the alert rule (`remediation: restart_service`)
keeps the mapping declarative and co-located with the alert definition, while
the webhook's allow-list ensures an alert can only ever trigger a known-safe
playbook — an injected or unexpected label is rejected, never executed.

## Safety

- **Allow-list** — only `restart_service`, `scale_service`, `reclaim_disk` can run.
- **demo_mode** — playbooks log their intent and skip destructive steps unless
  explicitly enabled, so CI exercises the real chain without side effects.
- **Single worker** services — the app and webhook run one gunicorn worker so
  in-process health/metric state is consistent across scrapes and requests.

## Testing strategy

| Layer | Tool | Proves |
|-------|------|--------|
| Lint | ruff, ansible-lint | code & playbook hygiene |
| Unit | pytest | Alertmanager payload → correct playbook selection/run |
| Config | promtool, amtool | rules and routing are valid before deploy |
| Integration | docker compose in CI | **the real alert → remediation loop fires** |

## Extending

- Add an alert + a `remediation` label, add the matching playbook, and register
  it in the webhook allow-list.
- Point `scale_service` at a real orchestrator (`docker compose up --scale`, or a
  Kubernetes `kubectl scale` / Deployment patch) — the companion
  `gitops-eks-argocd` project provides the cluster.
