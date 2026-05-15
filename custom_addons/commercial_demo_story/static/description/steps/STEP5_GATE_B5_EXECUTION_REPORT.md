# Step 5 Gate B5 Execution Report

> **Execution date:** 2026-05-14  
> **Scope:** Gate **B5 only** — POS **operational structure** baseline (configs, warehouse/locations, payment methods, HR/cashier rules, empty session lifecycle)  
> **Explicitly NOT done:** Gate B6+ (no product expansion, no real selling, no eCommerce, no custom modules)

---

## 1. Executed actions

| # | Action | Command / path |
|---|--------|----------------|
| 1 | Create POS configs, picking types, cashiers, duplicate AUH cash journal/method, open+close empty sessions (**`env.cr.commit()`**) | `odoo-bin shell -c config/projects/odoo_demo_pos_accounting.conf -d demo_pos_accounting < projects/demo_pos_accounting/evidence_gateB5/gateb5_shell_input.py` → `evidence_gateB5/gateB5_shell.txt` |
| 2 | SQL verification | `psql …` + `evidence_gateB5/SQL_VERIFICATION.txt` |
| 3 | UI smoke + screenshots | `./venv19/bin/python3 projects/demo_pos_accounting/evidence_gateB5/gateB5_browser_capture.py` (Playwright + **Chrome** channel) → `evidence_gateB5/screenshots/*.png`, `browser_gateB5.json` |
| 4 | Backups | `pg_dump -Fc` + filestore `tar.gz` → `backups/gateB5_*_20260514.*` |
| 5 | Git | Commit + annotated tag **`step5_gateB5_baseline`** |

---

## 2. POS configs created

| Name | `id` | Warehouse | Picking type | `module_pos_hr` | Price control | Cash diff governance | Order edit audit |
|------|------|-----------|--------------|-----------------|----------------|----------------------|------------------|
| **POS-DXB-01** | 5 | WH-HRG-MAIN (1) | Branch PoS **12** (`PDXB0`, source **WH-HRG-MAIN/POS/DXB-01**) | Yes | Restricted to managers (`restrict_price_control`) | `set_maximum_difference`, `amount_authorized_diff` **0.01** | `order_edit_tracking` |
| **POS-AUH-01** | 6 | WH-HRG-MAIN (1) | Branch PoS **13** (`PAUH0`, source **WH-HRG-MAIN/POS/AUH-01**) | Yes | Same | Same | Same |

Receipt text: **VALIDATION ONLY — Gate B5** (header) / **No live operations. Training / structure baseline.** (footer).

**Sequences:** created with configs (`order_seq_id`, session sequence on open, etc.) — standard Odoo POS sequencing.

---

## 3. Payment linkage verification

| Shop | Cash method | Bank/card methods (shared) |
|------|-------------|----------------------------|
| POS-DXB-01 | **POS Cash AED** → journal **POS-CASH-AED** (`PCASH`) | Visa, Mastercard, Stripe (same records as Gate B4) |
| POS-AUH-01 | **POS Cash AED AUH** → journal **POS-CASH-AUH** (`PCAHU`) | Same three bank methods |

**Why a second cash journal/method:** Odoo **forbids** attaching the same **cash** `pos.payment.method` to more than one `pos.config` (`_check_payment_method_ids_journal`). AUH therefore uses a **duplicate cash journal** and **POS Cash AED AUH**; card methods remain shared (constraint applies to cash journals only).

---

## 4. Cashier / security / governance

| Item | Implementation |
|------|------------------|
| **Separate cashiers (no shared logins)** | `hr.employee` **POS Cashier DXB-01** (PIN **9182**) and **POS Cashier AUH-01** (PIN **8273**); each linked only to its shop’s `basic`/`minimal` lists |
| **PIN** | Set on employees (`hr.employee.pin`) for **pos_hr** login flow |
| **Refund / elevated UI** | **`minimal_employee_ids`** = shop cashier only → **minimal** role hides refund/advanced ticket subpads unless manager-class employee is used (`pos_hr` behaviour) |
| **Manager path** | Administrator’s employee stays in **`basic_employee_ids`**; `pos_hr` auto-adds **PoS Manager** users to **advanced** on `pos.config` write |
| **Overnight sessions** | No open sessions left after validation; Odoo also schedules **stale-session** reminders after **7 days** (`_alert_old_session`) — **midnight hard-close is an operational policy**, not a separate toggle in core PoS |
| **Opening/closing control** | Cash methods ⇒ **`cash_control`** computed **True**; sessions exercised through **opening** (`set_opening_control(0,…)`) and **closing** (`action_pos_session_closing_control` → `action_pos_session_close`) with **zero orders** |

---

## 5. Frontend validation

| Check | Result |
|-------|--------|
| POS backend config UI | Loaded `/odoo/pos.config/5` |
| POS shop list | `/odoo/action-660` |
| POS UI | `/pos/ui/5/login?config_id=5` (employee login / session entry — **no sale**) |
| Sessions | `/odoo/pos-sessions` (list after navigation) |
| `page_errors` / Owl / console errors | **None** in `browser_gateB5.json` |
| Session open + close (structural) | Shell: two sessions **closed**, **0** `pos.order`, **0** `account.move`, **0** `stock.move` |

---

## 6. Screenshot paths

Directory: `projects/demo_pos_accounting/evidence_gateB5/screenshots/`

| File | Description |
|------|-------------|
| `01_pos_configurations_list.png` | POS configurations (`action-660`) |
| `02_pos_config_dxb_form.png` | **POS-DXB-01** form (warehouse, payment methods, HR) |
| `03_pos_payment_methods.png` | Payment methods list (`action-657`) |
| `04_pos_frontend.png` | POS frontend entry (**login** screen for `config_id=5`) |
| `05_pos_sessions_list.png` | Sessions list |
| `06_pos_settings_action.png` | POS configuration entry (`action-640`) |

---

## 7. SQL verification

File: `evidence_gateB5/SQL_VERIFICATION.txt`

| Check | Result |
|-------|--------|
| `pos_config` (company 1) | **2** rows (**POS-DXB-01**, **POS-AUH-01**) |
| `pos_order` | **0** |
| `account_move` | **0** |
| `stock_move` | **0** |
| `sale_order` | **0** |

---

## 8. Logs summary

| File | Notes |
|------|--------|
| `evidence_gateB5/gateB5_shell.txt` | `PICKING_TYPES`, `POS_CONFIG`, `SESSION_*`, `TOTAL_COUNTS`, `COMMIT_OK`; **no** `Traceback` / `ERROR` grep hits |
| `evidence_gateB5/gateB5_browser_run.log` | Playwright run (stdout minimal) |
| `evidence_gateB5/browser_gateB5.json` | No page/console/Owl/network failures |

---

## 9. Backup paths

| Artifact | Path |
|----------|------|
| PostgreSQL (custom format) | `projects/demo_pos_accounting/backups/gateB5_demo_pos_accounting_20260514.dump` |
| Filestore | `projects/demo_pos_accounting/backups/gateB5_filestore_20260514.tar.gz` |

---

## 10. Git tag

- **Tag:** `step5_gateB5_baseline` (annotated). **Commit:** `git rev-parse step5_gateB5_baseline^{commit}` on this repository (points at the amended commit that contains this report and all `evidence_gateB5/` files).

---

## 11. Failures / fixes

| Issue | Fix |
|-------|-----|
| `ValidationError`: cash payment method already used on another PoS | Added journal **POS-CASH-AUH** (`PCAHU`) + method **POS Cash AED AUH** for **POS-AUH-01**; **POS-DXB-01** keeps **POS Cash AED** on **PCASH** |
| Picking type `sequence_code` length | Generated **≤5** char codes (`PDXB0`, `PAUH0`) |

---

## 12. Final status

### **PASSED**

Two POS configurations, branch stock sources, payment wiring (with valid cash-method split), HR/PIN/minimal-access pattern, structural session open/close, UI loads without Owl/JS errors, **no** orders/moves/account moves.

---

## 13. STOP

**Do not proceed to Gate B6** unless separately authorized.
