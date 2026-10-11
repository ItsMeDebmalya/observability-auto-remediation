# CI Results

Two jobs run on every push/PR.

## 1. Validate configs, lint & unit tests ✅
- ruff clean on `app` and `webhook`
- webhook → Ansible unit tests pass (payload maps to the correct playbook; an
  unknown remediation label is rejected)
- `ansible-lint` passes at the `production` profile
- `promtool check config`, `amtool check-config`, and `docker compose config`
  all valid

## 2. Live alert → auto-remediation loop ✅

The job stands up the real stack and drives the full loop:

```
all core services ready
alert rules loaded
app marked unhealthy; waiting for remediation...
attempt 1:  restart_service runs=0
...
attempt 11: restart_service runs=1
AUTO-REMEDIATION FIRED
```

~50 seconds after the app was marked unhealthy, the `AppUnhealthy` alert fired,
Alertmanager called the remediation webhook, and the `restart_service` playbook
executed — end to end, with no manual intervention.

See the live run history under the repository's **Actions** tab.
