# Step 5 Gate C1 Execution Report

> **Execution date:** 2026-05-14  
> **Scope:** Gate **C1 only** — **product category hierarchy**, **category-level accounting (AVCO + valuation)**, **company inventory defaults**, and **governance documentation** (no new products, no stock operations, no accounting moves).  
> **Explicitly NOT done:** Gate C2+ (no product master data load, no quantities, no POS sales, no purchases, no invoices, no custom modules).

---

## 1. Executed actions

| # | Action | Command / path |
|---|--------|----------------|
| 1 | Create/update seven product categories + company `cost_method` / `inventory_valuation` + enforce **SERVICES** periodic valuation after company perpetual default (`env.cr.commit()`) | `odoo-bin shell … < projects/demo_pos_accounting/evidence_gateC1/gatec1_shell_input.py` → `evidence_gateC1/gateC1_shell.txt` |
| 2 | Playwright: admin UI — categories list, category form (accounting), settings (inventory / product) | `projects/demo_pos_accounting/evidence_gateC1/gateC1_browser_capture.py` → `browser_gateC1.json`, `screenshots/*.png` |
| 3 | SQL verification | `evidence_gateC1/SQL_VERIFICATION.txt` + live `psql` (see **§7**) |
| 4 | Backups (not committed; gitignored) | `pg_dump -Fc` + filestore `tar.gz` → `backups/gateC1_*_20260513.*` |
| 5 | Git | Commit under this repo + tag **`step5_gateC1_baseline`** |

---

## 2. Categories created (hierarchy)

| Name | Parent | `property_cost_method` | `property_valuation` | Notes |
|------|--------|------------------------|----------------------|--------|
| **ALL PRODUCTS** | — | **average (AVCO)** | **real_time** | Root governance tree |
| **RETAIL** | ALL PRODUCTS | average | real_time | |
| **FOOD** | RETAIL | average | real_time | |
| **BEVERAGES** | RETAIL | average | real_time | |
| **SERVICES** | ALL PRODUCTS | average | **periodic** | Non-stocked / service-style branch; periodic closing model |
| **POS ITEMS** | ALL PRODUCTS | average | real_time | Future POS catalogue |
| **ECOM ITEMS** | ALL PRODUCTS | average | real_time | Future e-commerce catalogue |

Existing Odoo categories (**Services**, **Deliveries**, etc.) were **not** repurposed; the new tree is **parallel** so default POS/sale helper products stay on their original categories.

---

## 3. Accounting configuration verification

### 3.1 Company defaults (`res.company` id **1**)

| Field | Value |
|-------|--------|
| `cost_method` | **average** (AVCO) |
| `inventory_valuation` | **real_time** (automated perpetual valuation at invoicing where applicable) |

### 3.2 Category properties (ORM check on `product.category` **id 7** — **ALL PRODUCTS**)

| Property | Resolved record |
|----------|-----------------|
| `property_account_income_categ_id` | `account.account` **155** (company default income) |
| `property_account_expense_categ_id` | `account.account` **81** (company default expense) |
| `property_stock_valuation_account_id` | `account.account` **55** (company stock valuation) |
| `property_stock_journal` | `account.journal` **7** (company stock journal) |

The same account and journal IDs were written on all seven Gate C1 categories for **company 1** (verified in UI screenshot **§6** and ORM read above). **No** `account.move` rows were created by this gate.

### 3.3 Failures / fixes

| Issue | Resolution |
|-------|------------|
| After setting company to **real_time**, the **SERVICES** category needed an explicit second `write({'property_valuation': 'periodic'})` so it stayed **periodic** under a company-wide perpetual default | Script now runs **`SERVICES_ENFORCED_PERIODIC`** immediately after the company write (see `gatec1_shell_input.py` and `gateC1_shell.txt`) |

---

## 4. Product governance baseline (structure + Odoo behaviour)

| Topic | Baseline |
|-------|----------|
| **Internal reference** | Use **unique** `default_code` / internal reference per variant; Odoo surfaces a duplicate warning on change (`product.template` `_onchange_default_code`). |
| **Barcode uniqueness** | Enforced by **SQL uniqueness** on variant barcode and coordination with packaging barcodes (`product.product` / `product.uom` constraints). |
| **Archiving** | Prefer **archiving** (`active=False`) over deletion for catalogue drift; no archiving was applied to live POS/sale helpers in this gate (**§5**). |
| **Variant-ready structure** | **`product.group_product_variant`** is already implied on **`base.group_user`** in this database (`VARIANT_GROUP_ALREADY_IMPLIED_ON_INTERNAL_USER` in shell log). |
| **No deletion after transactions** | Standard Odoo unlink guards apply once a product is referenced; operational policy: **archive**, do not delete, after go-live. |

---

## 5. Existing product audit (`product_template`)

**Count before Gate C1:** **7**  
**Count after Gate C1:** **7** (unchanged)

| id | Name | Type | Category | Classification | Archived? |
|----|------|------|----------|------------------|-----------|
| 1 | Tips | consu | Services | Odoo **POS / gratuity** helper | **No** — required for POS tipping flows |
| 2 | Standard delivery | service | Deliveries | **Sale / delivery** service line | **No** |
| 3 | Discount | consu | Services | **Sale discount** line product | **No** |
| 4 | Down Payment (POS) | service | Services | **POS / sale** down payment | **No** |
| 5 | Settle Due | service | Services | **POS / receivable** settlement helper | **No** |
| 6 | Deposit | service | Services | **POS / deposit** helper | **No** |
| 7 | Settle Invoice | service | Services | **POS / invoice** settlement helper | **No** |

**Conclusion:** All seven rows are **harmless Odoo/POS/sale infrastructure** products, not demo merchandising stock. **None** were archived: doing so would risk **POS and payment settlement** flows.

---

## 6. Screenshot paths

Directory: `projects/demo_pos_accounting/evidence_gateC1/screenshots/`

| File | Description |
|------|-------------|
| `01_product_categories_list.png` | Product categories list (`action-214`, **admin**) |
| `02_category_all_products_accounting.png` | Form **`product.category` id 7** — costing, valuation, accounts, stock journal |
| `03_settings_inventory_valuation.png` | **Settings** — Inventory section (valuation / costing context) |
| `04_settings_barcode_product.png` | **Settings** — Inventory / product controls (barcode-related options visibility) |

---

## 7. SQL verification

Primary reference: `projects/demo_pos_accounting/evidence_gateC1/SQL_VERIFICATION.txt`

**Live snapshot (2026-05-14):**

- Gate C1 named categories: **7** rows  
- `product_template` total: **7**  
- `stock_move` total: **0**  
- `product_value` total: **0** (Odoo 19 valuation table in this deployment; **`stock_valuation_layer` does not exist** in `information_schema`)  
- `account_move` total: **0**  
- `res_company`: `cost_method = average`, `inventory_valuation = real_time`  
- Categories **7–13**: `property_cost_method` → `{"1": "average"}` for all; `property_valuation` → `real_time` except **SERVICES (11)** → `periodic`

---

## 8. Logs summary

| File | Summary |
|------|---------|
| `evidence_gateC1/gateC1_shell.txt` | Baseline counts; category create/update lines; `COMPANY_DEFAULTS`; `SERVICES_ENFORCED_PERIODIC`; variant group note; post counts match baseline; **`COMMIT_OK`** |
| `evidence_gateC1/gateC1_shell_run.log` | Full Odoo shell stdout (no Python traceback) |
| `evidence_gateC1/gateC1_browser_run.log` | Playwright wrapper (minimal) |
| `evidence_gateC1/browser_gateC1.json` | **No** `page_errors`, **no** `console_errors` / `console_owl`, **no** RPC failures captured |

---

## 9. Backup paths (local disk; not in git)

Per `projects/demo_pos_accounting/.gitignore` (`*.dump`, `*.tar.gz`):

| Artifact | Path |
|----------|------|
| PostgreSQL custom-format dump | `projects/demo_pos_accounting/backups/gateC1_demo_pos_accounting_20260513.dump` |
| Filestore archive | `projects/demo_pos_accounting/backups/gateC1_filestore_20260513.tar.gz` |

---

## 10. Git tag

- **Tag:** `step5_gateC1_baseline` (annotated)  
- **Commit:** resolve with `git rev-parse step5_gateC1_baseline^{commit}` in the repository that contains this report (the tag points at the commit that adds this report and `evidence_gateC1/`).

---

## 11. Final status

**PASSED** — Gate C1 objectives met: category tree and accounting properties in place, **AVCO** on categories and company, **automated perpetual valuation** on stock-bearing branches with **SERVICES** on **periodic**, **no** new products, **no** stock moves, **no** `product_value` rows, **no** `account_move` rows, UI capture without captured Owl/console errors.

**STOP** — Gate **C2** is **out of scope** for this report.
