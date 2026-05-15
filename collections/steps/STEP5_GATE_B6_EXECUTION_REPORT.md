# Step 5 Gate B6 Execution Report

> **Execution date:** 2026-05-14  
> **Scope:** Gate **B6 only** — **users, groups, and access control** baseline (no products, no sales, no inventory operations, no accounting moves)  
> **Explicitly NOT done:** Gate C1+ (no operational go-live cutover, no master data expansion beyond security)

---

## 1. Executed actions

| # | Action | Command / path |
|---|--------|----------------|
| 1 | Create five operational users + HR links + POS employee sets (**`env.cr.commit()`**) | `odoo-bin shell … < projects/demo_pos_accounting/evidence_gateB6/gateb6_shell_input.py` → `evidence_gateB6/gateB6_shell.txt` |
| 2 | Generate **per-user** login passwords (gitignored) | `projects/demo_pos_accounting/.gateB6_demo_passwords.txt` (see **§11**) |
| 3 | Playwright: login / menu / denial checks (fresh browser context per user) | `projects/demo_pos_accounting/evidence_gateB6/gateB6_browser_capture.py` → `browser_gateB6.json`, `screenshots/*.png` |
| 4 | SQL verification | `evidence_gateB6/SQL_VERIFICATION.txt` + `psql` |
| 5 | Backups | `pg_dump -Fc` + filestore `tar.gz` → `backups/gateB6_*_20260514.*` |
| 6 | Git | Commit + annotated tag **`step5_gateB6_baseline`** |

---

## 2. Users created

| Login | Display name | Primary privilege (direct `group_ids`) | Notes |
|-------|----------------|------------------------------------------|--------|
| **pos.cashier.dxb** | POS Cashier DXB | `point_of_sale.group_pos_user` + `base.group_user` | Linked `hr.employee` **POS Cashier DXB-01**, PIN **9182** |
| **pos.cashier.auh** | POS Cashier AUH | `point_of_sale.group_pos_user` + `base.group_user` | Linked **POS Cashier AUH-01**, PIN **8273** |
| **pos.manager** | POS Manager | `point_of_sale.group_pos_manager` + `base.group_user` | Implies **PoS User** + **Inventory / User** per standard Odoo; employee **POS Manager Demo**, PIN **7364** |
| **inventory.manager** | Inventory Manager | `stock.group_stock_manager` + `base.group_user` | Implies **stock.group_stock_user** |
| **finance.manager** | Finance Manager | `account.group_account_user` + `account.group_account_manager` + `base.group_user` | Full accounting features + accounting admin (per Gate B6 scope) |

**`admin`** remains the **break-glass** system account (not used for the scripted operational tests). Operational work is intended to use the five dedicated logins only.

---

## 3. Groups / access verification

### 3.1 Direct group membership (SQL)

From live `psql` (`res_groups_users_rel`):

| Login | `group_pos_user` | `group_pos_manager` | `group_stock_manager` | `group_account_manager` | `group_account_user` |
|-------|------------------|---------------------|------------------------|-------------------------|----------------------|
| pos.cashier.dxb | Yes | — | — | — | — |
| pos.cashier.auh | Yes | — | — | — | — |
| pos.manager | — | Yes | — | — | — |
| inventory.manager | — | — | Yes | — | — |
| finance.manager | — | — | — | Yes | Yes |

*(PoS Manager also receives **implied** PoS User rights through `group_pos_manager`; not always visible as a separate row in `res_groups_users_rel`.)*

### 3.2 POS configuration (employee allow-lists)

`pos.config` **basic** / **minimal** lists were tightened so **Administrator** is **not** on the cashier path: each shop keeps **POS Manager Demo** + its cashier on **basic**, cashier only on **minimal** (Gate B5 `pos_hr` pattern for restricted refund UI on minimal role).

---

## 4. Frontend validation

File: `evidence_gateB6/browser_gateB6.json`

| Test | Result |
|------|--------|
| **pos.cashier.dxb** → Chart of Accounts (`action-299`) | **Access denied** messaging detected (`access_denied_text`: **true**) |
| **pos.cashier.dxb** → POS configurations (`action-660`) | **OK** |
| **pos.cashier.dxb** → `/odoo/settings` | **Access denied** text detected (**true**) |
| **pos.cashier.dxb** → POS UI login (`/pos/ui/5/login`) | Page loads (screenshot) |
| **pos.cashier.auh** → POS configs + POS-AUH UI (`/pos/ui/6/login`) | **OK** |
| **finance.manager** → Journals (`action-301`) | **OK** |
| **inventory.manager** → Stock operations (`action-444`) | **OK** |
| **pos.manager** → POS configurations (`action-660`) | **OK** |

**Errors:** no `page_errors`, no `console_errors` / `console_owl`, no failing RPC `call_kw` / `action_load` captures in this run.

---

## 5. Screenshot paths

Directory: `projects/demo_pos_accounting/evidence_gateB6/screenshots/`

| File | Description |
|------|-------------|
| `01_users_list.png` | Users list (`action-70`, **admin**) |
| `02_user_pos_cashier_dxb_form.png` | User form **pos.cashier.dxb** (`/odoo/res.users/5`) |
| `03_access_privileges_groups.png` | Access-rights privileges (`action-67`) |
| `04_cashier_chart_accounts.png` | Cashier on Chart of Accounts (**restricted**) |
| `05_cashier_pos_configs.png` | Cashier on POS configurations |
| `06_pos_frontend_login_cashier.png` | POS frontend login (**DXB** config) |
| `06b_cashier_auh_pos_configs.png` | **AUH** cashier — POS configurations |
| `06c_pos_frontend_login_cashier_auh.png` | POS frontend login (**AUH** config) |
| `07_cashier_settings_attempt.png` | Cashier **Settings** attempt (**restricted**) |
| `08_finance_journals.png` | **finance.manager** — Journals |
| `09_inventory_operations.png` | **inventory.manager** — stock operations |
| `10_pos_manager_configs.png` | **pos.manager** — POS configurations |

---

## 6. SQL verification

File: `evidence_gateB6/SQL_VERIFICATION.txt`

| Check | Result |
|-------|--------|
| Operational users | **5** active rows |
| Duplicate `login` | **0** |
| `base.group_system` on operational logins | **0** rows |
| `pos_order` / `account_move` | **0** / **0** |

---

## 7. Logs summary

| File | Notes |
|------|--------|
| `evidence_gateB6/gateB6_shell.txt` | `PASSWORDS_WRITTEN`, `EMPLOYEES`, `EMP_POS_MANAGER`, `POS_CONFIGS_UPDATED`, `COMMIT_OK`; grep `Traceback` / ` ERROR ` → **none** |
| `evidence_gateB6/gateB6_browser_run.log` | Playwright stdout (minimal) |
| `evidence_gateB6/browser_gateB6.json` | Structured test results (see §4) |

---

## 8. Backup paths

| Artifact | Path |
|----------|------|
| PostgreSQL (custom) | `projects/demo_pos_accounting/backups/gateB6_demo_pos_accounting_20260514.dump` |
| Filestore | `projects/demo_pos_accounting/backups/gateB6_filestore_20260514.tar.gz` |

---

## 9. Git tag

- **Tag:** `step5_gateB6_baseline` (annotated)  
- **Commit:** `git rev-parse step5_gateB6_baseline^{commit}` on the repository that contains this report and `evidence_gateB6/`.

---

## 10. Failures / fixes

| Issue | Fix |
|-------|-----|
| `ValueError: Invalid field 'groups_id'` on **Odoo 19** | Use **`group_ids`** on `res.users` |
| Playwright **login field not visible** after cookie-only logout | Use a **fresh browser context per user** so each login starts clean |

---

## 11. Secrets / governance

- **Passwords** for the five operational users are stored only in **`projects/demo_pos_accounting/.gateB6_demo_passwords.txt`**, which is **gitignored** (see `.gitignore`). **Rotate** before any shared environment.  
- **PINs** (employee-level, PoS HR): **9182** / **8273** / **7364** — acceptable for this **demo** database only; treat as **placeholder** secrets.  
- **Least privilege:** cashiers = **PoS User** only; no Accounting / Settings access in automated checks.  
- **Auditability:** unchanged from Gate B5 (`order_edit_tracking` on POS configs); user accounts are **individual** (no shared operational logins).

---

## 12. Final status

### **PASSED**

---

## 13. STOP

**Do not proceed to Gate C1** unless separately authorized.
