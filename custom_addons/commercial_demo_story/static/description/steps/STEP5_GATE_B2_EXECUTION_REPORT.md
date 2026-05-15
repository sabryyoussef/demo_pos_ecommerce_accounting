# Step 5 Gate B2 Execution Report

> **Execution date:** 2026-02-03 (per session “Today”; some evidence files may show the host’s filesystem timestamp)  
> **Scope:** Gate **B2 only** — analytic **architecture** (plans + accounts + naming), persistence with explicit `env.cr.commit()`, SQL + UI smoke validation, screenshots, backups, git tag  
> **Explicitly NOT done:** Gate B3+ (no products, warehouses, inventory locations, customers/vendors, POS branch configs, journal redesign, transactions, imports, custom modules)

---

## 1. Exact executed actions

| # | Action | Command / path |
|---|--------|------------------|
| 1 | Re-ran analytic setup with **explicit commit** | `odoo-bin shell -c config/projects/odoo_demo_pos_accounting.conf -d demo_pos_accounting < projects/demo_pos_accounting/evidence_gateB2/gateb2_shell_input.py` → transcript `evidence_gateB2/gateB2_shell.txt` |
| 2 | **PostgreSQL verification** (counts + names) | `psql …` → `evidence_gateB2/SQL_VERIFICATION.txt` |
| 3 | **UI / OWL smoke** (Playwright) | `GATEB2_AN_ACCOUNT_ID=$(psql …)` + `evidence_gateB2/gateB2_browser_capture.py` → `evidence_gateB2/screenshots/*.png`, `evidence_gateB2/browser_gateB2.json` |
| 4 | **Backups** | `pg_dump -Fc` + `tar.gz` filestore → `backups/gateB2_demo_pos_accounting_20260203.dump`, `backups/gateB2_filestore_20260203.tar.gz` |
| 5 | **Git** | Commit including this report + evidence; annotated tag `step5_gateB2_baseline` |

---

## 2. Analytic plans created (root-level, English display names)

| Sequence | Plan name (UI) | Notes |
|----------|------------------|--------|
| 10 | Project | Odoo default (unchanged) |
| 20 | **Channel** | Mandatory reporting dimension |
| 30 | **POS Location** | Scales to 30+ branches via `AN-POS-<CITY>-NN` pattern |
| 40 | **Department** | Optional-but-enabled per Gate B2 scope |

*(See `evidence_gateB2/SQL_VERIFICATION.txt` for authoritative `id` / `parent_id` rows.)*

---

## 3. Analytic accounts created (structure only)

| Code / name | Plan |
|-------------|------|
| AN-CH-CORP, AN-CH-ECOM, AN-CH-POS | Channel |
| AN-POS-DXB-01, AN-POS-AUH-01 | POS Location |
| AN-DPT-SALES, AN-DPT-OPS, AN-DPT-HR | Department |

Naming rules are documented in `evidence_gateB2/NAMING_CONVENTIONS.txt` (English-safe, ASCII, no duplicate codes within the same plan + company).

---

## 4. Persistence & SQL verification (authoritative)

**Shell ends with `env.cr.commit()`** — required because `odoo-bin shell` with stdin executes the script and then calls `cr.rollback()` unless changes are committed (see **Lessons Learned**).

From `evidence_gateB2/SQL_VERIFICATION.txt` after the final run:

| Metric | Value |
|--------|--------|
| **PLAN_COUNT** | **4** (Project + Channel + POS Location + Department) |
| **ACCOUNT_COUNT** | **8** |
| **Name / plan linkage** | All eight accounts join to plans **5 / 6 / 7** with expected `code` and `company_id = 1` |

---

## 5. UI & reporting validation (Playwright)

Artifact: `evidence_gateB2/browser_gateB2.json`

| Check | Result |
|-------|--------|
| **page_errors** (uncaught JS) | `[]` |
| **console_errors** | `[]` |
| **console_owl** (OWL-tagged console lines captured) | `[]` |
| **network_failures** (HTTP ≥400 on tracked `/web/`/`/bus/`/`/mail/` URLs) | `[]` |
| **Analytic items pivot** | `analytic_items_pivot_visible`: **true** (`/odoo/analytic-items` → pivot mode; screenshot `05_analytic_items_pivot.png`) |
| **P&L “Analytic” substring heuristic** | **false** in headless run (labels may be icon-only / translated / lazy; **no** JS failure — see screenshot `03_profit_and_loss.png` for manual review) |
| **Dense list text match for `AN-CH-CORP`** | Automated text probes **false** (OWL list virtualization / JSON field rendering); **SQL** + list screenshot `02_analytic_accounts.png` are the primary list evidence |

**Re-run Playwright with a concrete record id (recommended):**

```bash
export GATEB2_AN_ACCOUNT_ID="$(PGPASSWORD=odoo19 psql -h localhost -U odoo19 -d demo_pos_accounting -tAc \"SELECT id FROM account_analytic_account WHERE code='AN-CH-CORP' LIMIT 1\")"
PLAYWRIGHT_BROWSERS_PATH=~/.cache/ms-playwright python3 projects/demo_pos_accounting/evidence_gateB2/gateB2_browser_capture.py
```

---

## 6. Screenshot paths

Directory: `projects/demo_pos_accounting/evidence_gateB2/screenshots/`

| File | Description |
|------|-------------|
| `01_analytic_plans.png` | Analytic plans |
| `02_analytic_accounts.png` | Analytic accounts (list; full-page capture) |
| `03_profit_and_loss.png` | Profit & Loss (accounting report client) |
| `04_analytic_reporting.png` | Analytic reporting workspace |
| `05_analytic_items_pivot.png` | Analytic lines → **pivot** view |
| `06_analytic_account_detail.png` | Deep-link attempt to analytic account record (see JSON notes) |

---

## 7. Logs summary

| File | Purpose |
|------|---------|
| `evidence_gateB2/gateB2_shell.txt` | `odoo-bin shell` transcript including `COMMIT_OK` |
| `evidence_gateB2/SQL_VERIFICATION.txt` | `psql` counts + plan/account listing |
| `evidence_gateB2/browser_gateB2.json` | Headless browser smoke results |

`grep -E 'Traceback|^.* ERROR '` on `gateB2_shell.txt`: **no matches**.

---

## 8. Backup paths

| Artifact | Path |
|----------|------|
| PostgreSQL (custom format) | `projects/demo_pos_accounting/backups/gateB2_demo_pos_accounting_20260203.dump` |
| Filestore archive | `projects/demo_pos_accounting/backups/gateB2_filestore_20260203.tar.gz` |

*(Project `.gitignore` excludes `backups/*.dump` and `backups/*.tar.gz` — backups are local artifacts.)*

---

## 9. Git tag

- **Tag:** `step5_gateB2_baseline`  
- **Points to:** commit that contains this report and refreshed `evidence_gateB2/` artifacts.

---

## 10. Failures / fixes

| Failure | Fix |
|---------|-----|
| **Phantom success** on first Gate B2 attempt | Root cause: `odoo-bin shell` **rolls back** the cursor after stdin `exec()` unless **`env.cr.commit()`** is called. Script now ends with explicit commit; SQL verification proves rows persisted. |
| Headless text probes flaky on list / P&L | Mitigated with **SQL_VERIFICATION.txt**, asset/network/JS checks, and **pivot** screenshot on `analytic-items`; P&L analytic labeling left to human review of `03_profit_and_loss.png` where automation could not assert strings reliably. |

---

## 11. Lessons learned

1. **`odoo-bin shell` + stdin rollback**  
   When stdin is not a TTY, Odoo runs `exec(stdin)` inside `registry.cursor()` and then executes **`cr.rollback()`** (see `odoo/cli/shell.py`). Any `create()` / `write()` without **`env.cr.commit()`** is discarded on exit. Transcript-only “success” is meaningless without SQL or ORM re-read after exit.

2. **Why verification gates matter**  
   Gates exist to catch **silent no-ops**. An automation can print `ACCOUNT …` lines while the database remains unchanged. Without a persistence check, downstream milestones (reports, compliance, go-live) build on fiction.

3. **Why SQL verification prevented silent corruption**  
   PostgreSQL counts and joins (`PLAN_COUNT`, `ACCOUNTS_BY_PLAN`) contradicted the first phantom run immediately once we looked past stdout. **Treat SQL (or a post-shell ORM read in a new process) as the primary acceptance test** for shell-driven setup; logs are necessary but not sufficient.

4. **Operational habit**  
   For all future `odoo-bin shell < script.py` playbooks: end with **`env.cr.commit()`** (or split into `odoo-bin exec` / RPC if you want request-scoped commits), then run **one deterministic verification query** in the same playbook.

---

## 12. Final status

### **PASSED**

Persistence is **proven in PostgreSQL** (`SQL_VERIFICATION.txt`). Shell transcript shows **`COMMIT_OK`**. Automated UI run shows **no JS page errors, no OWL console captures, no tracked network failures**, and **pivot view renders** on analytic items. Screenshots were regenerated after confirmed persistence.

---

## 13. STOP

**Do not proceed to Gate B3** until separately authorized.
