# Security Service — Deployment Wiring

Same pattern as subscription/inspector/scheduler services.

---

## Systemd Unit

**File:** `deployment/botivation-security.service.template`

| Setting | Value |
|---------|-------|
| Entry point | `python -m Botivation.security_service` |
| Port | 8004 |
| After | `network.target postgresql.service` |
| Restart | `always`, 10s delay |
| Env vars | `SECURITY_PORT=8004`, `LOG_SERVICE_NAME=security` |
| Env file | `{{PROJECT_DIR}}/.env` |
| Logging | systemd journal, identifier `botivation-security` |
| Security | `NoNewPrivileges=true`, `PrivateTmp=true` |

---

## Installer Script

**File:** `deployment/install_security_service.sh`

Steps (same as other services):
1. Read template, substitute `{{USER}}`, `{{PROJECT_DIR}}`, `{{VENV_PATH}}`
2. Write to `/etc/systemd/system/botivation-security.service`
3. `systemctl daemon-reload`
4. Supports `--yes` flag for auto-confirm

---

## run.sh

Add `security` case to `scripts/run.sh`:

```bash
security)
    python -m Botivation.security_service
    ;;
```

Add to `all)` case — start security service in background alongside others.

---

## deploy_remote.sh

Add to `scripts/deploy_remote.sh`:

```bash
# Install security service if missing
if [ ! -f /etc/systemd/system/botivation-security.service ]; then
    ./deployment/install_security_service.sh --yes
fi

# Add to restart list
sudo systemctl restart botivation-security
```

---

## Environment Variable

Add to `.env.example`:

```
SECURITY_SERVICE_URL=http://127.0.0.1:8004
```

---

## Log Path

Logs via systemd journal. View with:

```bash
journalctl -u botivation-security -f
```

Admin log tab reads from same journal (same pattern as other service log tabs).

---

## Files to Create/Modify

| Action | File |
|--------|------|
| **Create** | `deployment/botivation-security.service.template` |
| **Create** | `deployment/install_security_service.sh` |
| **Modify** | `scripts/run.sh` — add `security` case |
| **Modify** | `scripts/deploy_remote.sh` — add install + restart |
| **Modify** | `.env.example` — add `SECURITY_SERVICE_URL` |
