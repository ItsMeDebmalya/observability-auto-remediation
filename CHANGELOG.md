# Changelog

All notable changes to this project are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added
- Instrumented Flask sample app exposing Prometheus metrics.
- Prometheus config with recording rules and alerting rules (app health,
  target down, high latency, disk filling) carrying remediation labels.
- Alertmanager routing firing alerts to a remediation webhook.
- Remediation webhook mapping alert labels to allow-listed Ansible playbooks
  (restart service, scale out, reclaim disk) with a demo-mode safety flag.
- Grafana provisioning (Prometheus datasource + Service Overview dashboard).
- ELK log pipeline (Elasticsearch, Logstash, Kibana) behind a compose profile.
- docker-compose stack for the whole system.
- CI: ruff, webhook→Ansible unit tests, ansible-lint, promtool/amtool/compose
  validation, and a live alert → auto-remediation integration test.
- README and architecture documentation.
