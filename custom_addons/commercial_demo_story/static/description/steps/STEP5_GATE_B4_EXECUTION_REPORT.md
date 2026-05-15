# Step 5 Gate B4 Execution Report

> **Execution date:** 2026-05-13  
> **Scope:** Gate **B4 only** — financial **journals** + **POS payment methods** baseline (structure only)  
> **Explicitly NOT done:** Gate B5+ (no POS branch rollout, no sales/invoicing flows, no new products/partners by this gate’s script)

---

## 1. Executed actions

| # | Action | Command / path |
|---|--------|----------------|
| 1 | Create/align journals + POS payment methods (**`env.cr.commit()`** at end) | `odoo-bin shell -c config/projects/odoo_demo_pos_accounting.conf -d demo_pos_accounting < projects/demo_pos_accounting/evidence_gateB4/gateb4_shell_input.py` → `evidence_gateB4/gateB4_shell.txt` *(this workspace used the same `odoo-bin` path as prior gates; see transcript header)* |
| 2 | SQL verification | `psql …` checks recorded in `evidence_gateB4/SQL_VERIFICATION.txt` |
| 3 | UI smoke + screenshots | `./venv19/bin/pip install -q playwright` (package only) + `projects/demo_pos_accounting/evidence_gateB4/gateB4_browser_capture.py` (uses **system Chrome** via `channel="chrome"`) → `evidence_gateB4/screenshots/*.png`, `evidence_gateB4/browser_gateB4.json` |
| 4 | Backups | `pg_dump -Fc` + filestore `tar.gz` → `backups/gateB4_*_20260513.*` |
| 5 | Git | Commit evidence + report; annotated tag **`step5_gateB4_baseline`** |

---

## 2. Default journals verified

Existing **company_id = 1** journals (unchanged except new rows appended): Sales (`INV`), Purchases (`BILL`), Miscellaneous (`MISC`), Exchange Difference (`EXCH`), Cash Basis Taxes (`CABA`), default Bank (`BNK1`), Inventory Valuation (`STJ`), Tax Adjustments (`TA`), IFRS 16 (`IFRS`), Tax Returns (`TAX`). Full list in `SQL_VERIFICATION.txt` queries.

---

## 3. Journals created / verified (Gate B4)

Odoo **`account.journal.code` is limited to 5 characters**. Display names follow your blueprint; short codes are unique per company.

| Display name (`name`) | `code` (≤5) | `type` | Notes |
|------------------------|------------|--------|--------|
| **BNK-MAIN-AED** | `BMAIN` | `bank` | Main AED bank journal |
| **POS-CASH-AED** | `PCASH` | `cash` | POS cash |
| **POS-VISA-AED** | `PVISA` | `bank` | `pos.payment.method` only allows **`cash` or `bank`** journals (not `credit`); mapped as dedicated **bank** clearance |
| **POS-MC-AED** | `MCARD` | `bank` | Same constraint as Visa |
| **ACQ-STRIPE-AED** | `AQSTR` | `bank` | Acquirer-style journal; **no** Stripe API keys stored (see §8) |

All five use **`currency_id`** = AED (`base.AED`, id **128** in this DB).

---

## 4. POS payment methods created / verified

| Method name | `journal_id` → journal |
|-------------|-------------------------|
| POS Cash AED | `POS-CASH-AED` (`PCASH`) |
| POS Visa AED | `POS-VISA-AED` (`PVISA`) |
| POS Mastercard AED | `POS-MC-AED` (`MCARD`) |
| POS Stripe AED | `ACQ-STRIPE-AED` (`AQSTR`) |

**`pos.config`:** **0** rows (no POS shop configuration in this gate; payment methods exist globally for later attachment).

---

## 5. SQL / accounting verification

File: `projects/demo_pos_accounting/evidence_gateB4/SQL_VERIFICATION.txt`

| Check | Result |
|-------|--------|
| Journals for company 1 | **15** rows (10 default + **5** Gate B4) |
| `pos.payment.method` | **4** rows |
| Duplicate `(code, company_id)` on `account_journal` | **0** |
| `account_move` | **0** |
| `account_move_line` | **0** |
| `account_bank_statement` | **0** |
| `account_bank_statement_line` | **0** |
| `account_payment` | **0** |
| `payment_stripe.*` in `ir_config_parameter` | **No rows** (keys unset) |

---

## 6. Screenshot paths

Directory: `projects/demo_pos_accounting/evidence_gateB4/screenshots/`

| File | Description |
|------|-------------|
| `01_journals_list.png` | Journals list (`/odoo/action-301`) |
| `02_journal_pos_visa_detail.png` | Journal form — **POS-VISA-AED** (`account.journal` id **17**) |
| `03_pos_payment_methods.png` | POS Payment Methods (`/odoo/action-657`) |

---

## 7. Logs summary

| File | Notes |
|------|--------|
| `evidence_gateB4/gateB4_shell.txt` | Transcript: `JOURNALS …`, `POS_PAYMENT_METHODS …`, `COUNTS_BEFORE_AFTER` (moves/statements/payments unchanged), `COMMIT_OK`; `grep -iE 'traceback|error'` → **no matches** |
| `evidence_gateB4/gateB4_browser_run.log` | Playwright run stdout (empty on success); no traceback |
| `evidence_gateB4/browser_gateB4.json` | **No** `page_errors`, **no** `console_errors` / `console_owl`, **no** `network_failures` |

---

## 8. Backups paths

| Artifact | Path |
|----------|------|
| PostgreSQL (custom format) | `projects/demo_pos_accounting/backups/gateB4_demo_pos_accounting_20260513.dump` |
| Filestore archive (`filestore/demo_pos_accounting`) | `projects/demo_pos_accounting/backups/gateB4_filestore_20260513.tar.gz` |

*(Project `.gitignore` excludes `backups/*.dump` / `backups/*.tar.gz`.)*

---

## 9. Git tag

- **Tag:** `step5_gateB4_baseline` (annotated). **Commit:** `git rev-parse step5_gateB4_baseline^{commit}` on this repository (the tag points at the single amended commit that contains this report and all `evidence_gateB4/` artifacts).

---

## 10. Failures / fixes

| Issue | Fix |
|-------|-----|
| `pos.payment.method` **journal** domain allows only **`cash`** or **`bank`** | Visa / MC / Stripe journals created as **`bank`** (not `credit`) so methods validate and remain POS-eligible |
| `account.journal` **`code` max 5** | Used short codes (`BMAIN`, `PCASH`, …) while keeping full **`name`** as requested |
| First `tar` path for filestore used wrong directory | Archived **`.filestore/filestore/demo_pos_accounting`** instead of non-existent `.filestore/demo_pos_accounting` |
| `playwright` not in venv; bundled Chromium download hung | **`pip install playwright`** only; launch with **`channel="chrome"`** (system **Google Chrome**) |

---

## 11. Final status

### **PASSED**

Journals and POS payment methods are **visible** in UI captures, **no duplicate** journal codes, **no** moves / statements / payments created, **no** Stripe parameters populated, shell and browser runs show **no traceback / OwlError**.

---

## 12. STOP

**Do not proceed to Gate B5** unless separately authorized.
