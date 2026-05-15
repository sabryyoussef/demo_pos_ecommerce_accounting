# Browser validation — Gate A final

**Tool:** Playwright (Chromium headless), script `browser_validation/gateA_browser_capture.py`  
**Base URL:** `http://127.0.0.1:8025`  
**Login:** `/web/login?db=demo_pos_accounting` (db-scoped backend login)  
**Web password:** supplied as env `GATEA_WEB_PASSWORD` (default `admin` for this evidence DB).

## Artifacts

| Item | Path |
|------|------|
| Machine-readable report | `browser_validation/browser_report.json` |
| Screenshots | `screenshots/01_after_login_web.png` … `05_pos_ui.png` |

## Results (from `browser_report.json`)

| Check | Result |
|-------|--------|
| Authenticated | `true` |
| `page_errors` (JS exceptions) | `[]` |
| `network_failures` (HTTP ≥400 on `/web/`, assets, POS-related URLs) | `[]` |
| OWL-related console errors | none (`owl_console_lines` empty) |
| Enterprise expiration panel | 1× panel, **`alert-info`**, dismissible — **not** blocking |
| `blocking_subscription` (danger/warning class on panel) | `false` |

## Routes exercised

1. Post-login web client (`/odoo`)  
2. Accounting (`/odoo/accounting`)  
3. POS entry (`/pos/ui?config_id=1`) — final `page.url` may show the web client POS action URL after redirect; no asset 404s recorded in the harness.

## Console noise

Odoo debug-style `console.log` lines (e.g. CRM menu click traces) may appear; they are **not** classified as OWL errors and did not coincide with `pageerror` events.
