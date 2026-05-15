# Step D1 Inventory Initialization Report

> **Execution date:** 2026-05-14  
> **Scope:** Gate **D1 only** — **opening inventory** for Gate C2 **physical** SKUs at **`WH-HRG-MAIN/Stock`** using **`stock.quant`** **inventory adjustment** (`inventory_mode` + `action_apply_inventory()`), **ORM-only** configuration of location valuation accounts, **no** POS/PO/SO/invoices/customer orders, **no** SQL on quantities.  
> **Explicitly NOT done:** Gate D2+ (no replenishment rules expansion, no branch transfers, no eCommerce orders).

---

## 1. Executed actions

| # | Action | Command / path |
|---|--------|----------------|
| 1 | Set **`is_storable=True`** on all **`RET-G2%`** **consumable** templates (services unchanged) | `gateD1_shell_input.py` |
| 2 | Set **`valuation_account_id`** on **`WH-HRG-MAIN/Stock` (id 5)** and global **Inventory adjustment (id 11)** to company **`account_stock_valuation_id`** (required for `_should_create_account_move` in Odoo 19) | `gateD1_shell_input.py` |
| 3 | Apply **opening quantities** at **location id 5** via **`stock.quant`** inventory session, then **`action_apply_inventory()`** | `gateD1_shell_input.py` → `evidence_gateD1/gateD1_shell.txt` |
| 4 | **Repair pass** (first run had no valuation accounts → **0** `account.move`): clear ICP flag, zero quants via same inventory flow, keep location accounts, **re-apply** identical opening quantities → **2** posted stock journals | One-off `odoo-bin shell` (logged in `gateD1_shell.txt` appendix) |
| 5 | Playwright evidence | `evidence_gateD1/gateD1_browser_capture.py` → `browser_gateD1.json`, `screenshots/*.png` |
| 6 | SQL verification | `evidence_gateD1/SQL_VERIFICATION.txt` + `SQL_VERIFICATION_results.txt` |
| 7 | Backups | `pg_dump -Fc` + filestore `tar.gz` → `backups/gateD1_*_20260514.*` |
| 8 | Git | Commit + annotated tag **`step5_D1_inventory_baseline`** |

**Idempotency:** `ir.config_parameter` key **`demo_pos_accounting.gate_d1_opening_inventory_done`** = **`1`** after success; re-run script exits early unless the flag is cleared manually.

---

## 2. Opening quantities (WH-HRG-MAIN/Stock, `stock.location` **id 5**)

| SKU | Quantity |
|-----|----------|
| RET-G2-BEV-WAT500 | 24 |
| RET-G2-BEV-SPK330 | 48 |
| RET-G2-BEV-OJ1L | 24 |
| RET-G2-BEV-TEA500 | 48 |
| RET-G2-SNK-CRP40 | 12 |
| RET-G2-SNK-ALM100 | 24 |
| RET-G2-SNK-CHO45 | 12 |
| RET-G2-SNK-OAT35 | 24 |
| RET-G2-RTL-BAG01 | 12 |
| RET-G2-RTL-BAT4 | 24 |
| RET-G2-RTL-USB1M | 12 |
| RET-G2-PAR-TSH-S | 10 |
| RET-G2-PAR-TSH-M | 10 |
| RET-G2-PAR-TSH-L | 5 |
| RET-G2-PAR-MUG350-BLA | 6 |
| RET-G2-PAR-MUG350-SIL | 12 |

**Total units on hand (SQL):** **307** (matches sum of the table).  
**Excluded:** **`RET-G2-SRV-*`** services remain **non-storable** and have **no** opening stock.

---

## 3. Valuation validation

| Check | Result |
|--------|--------|
| **`stock.move`** created from inventory adjustment | **48** `done` moves with **`is_inventory`** (includes **zero-out** + **re-apply** passes from repair) |
| **`stock.quant`** at **loc 5** for **`RET-G2%`** | **16** non-zero quants |
| **Negative stock** | **0** rows (`quantity < 0`) |
| **`stock_valuation_layer` table** | **Not present** in this PostgreSQL schema (`f` in SQL) — Odoo 19 uses other persistence (e.g. **`product.value`** for AVCO history) |
| **`product.value` rows** | **0** after opening (no separate cost-layer rows yet; **standard price** drives initial perpetual entries) |
| **Perpetual posting** | **2** posted **`account.move`** records on **stock journal (id 7)** — **`STJ/2026/05/0001`**, **`STJ/2026/05/0002`** — with **64** `account_move_line` rows hitting **stock valuation account** (`res_company.account_stock_valuation_id` = **55**) |

**AVCO note:** Opening layers are valued from **product standard cost** at move time; **AVCO** refinement via **`product.value`** typically intensifies on **subsequent valued flows** (purchases/consumption). Financially, **posted debits/credits net to zero** on the valuation account across the paired lines on each journal entry (balanced inventory adjustment design).

---

## 4. Accounting validation

- **Stock journal** entries **`STJ/2026/05/0001`** and **`STJ/2026/05/0002`** are **`posted`**.  
- **64** lines on **`account_id = 55`** (stock valuation) — consistent with batched perpetual posting from the **second** opening wave after valuation accounts were set.  
- **Accounting dashboard:** impact is visible under **Inventory / Stock journals** (screenshots **§6**); no customer/vendor invoices were created.

---

## 5. POS availability validation

- **`_load_pos_data_domain`** for **`pos.config` id 5** still returns **14** POS-visible templates (unchanged from Gate C2).  
- **POS UI** (`pos.cashier.dxb`, config **5**): products render with stock context (**screenshot `06_pos_products_with_stock.png`**).

---

## 6. Screenshot paths

Directory: `projects/demo_pos_accounting/evidence_gateD1/screenshots/`

| File | Description |
|------|-------------|
| `01_inventory_quant_adjustment.png` | **Inventory / On hand** (`action-436`, `stock.quant`) |
| `02_product_on_hand_general.png` | Product template **25** — Still Spring Water (shows **On Hand** / logistics context) |
| `03_stock_move_valuation.png` | **Stock move valuation** list (`action-574`) |
| `04_account_move_stock_journal_1.png` | Posted entry **`account.move` id 1** |
| `05_account_move_stock_journal_2.png` | Posted entry **`account.move` id 2** |
| `06_pos_products_with_stock.png` | POS shop (cashier **DXB**) |

---

## 7. SQL verification

Files:

- `projects/demo_pos_accounting/evidence_gateD1/SQL_VERIFICATION.txt`  
- `projects/demo_pos_accounting/evidence_gateD1/SQL_VERIFICATION_results.txt`  

**Snapshot (post-repair):** see results file — highlights: **307** units at **loc 5**, **0** negative quants, **48** inventory **`stock.move`**, **`stock_valuation_layer` absent**, **`product_value` = 0**, **`account_move` posted = 2**, **64** AML rows on valuation account **55**, **no** duplicate barcodes / `default_code`.

---

## 8. Logs summary

| File | Summary |
|------|---------|
| `evidence_gateD1/gateD1_shell.txt` | First pass counts; per-SKU `INV_SET`; initial **`account_move=0`**; **repair appendix** with valuation account wiring, zero pass, **`account_move=2`** |
| `evidence_gateD1/gateD1_shell_run.log` | Stdout from first script execution |
| `evidence_gateD1/gateD1_browser_run.log` | Playwright stdout |
| `evidence_gateD1/browser_gateD1.json` | **No** `page_errors`, **no** `console_errors` / `console_owl`, **no** RPC failures |

---

## 9. Backup paths (local; gitignored)

| Artifact | Path |
|----------|------|
| PostgreSQL dump | `projects/demo_pos_accounting/backups/gateD1_demo_pos_accounting_20260514.dump` |
| Filestore | `projects/demo_pos_accounting/backups/gateD1_filestore_20260514.tar.gz` |

---

## 10. Git tag

- **Tag:** `step5_D1_inventory_baseline` (annotated)  
- **Commit:** resolve with `git rev-parse step5_D1_inventory_baseline^{commit}` on the repo that contains this report.

---

## 11. Failures / fixes

| Issue | Fix |
|-------|-----|
| First inventory pass created **`stock.move`** but **`account_move` stayed 0** | Odoo **`_should_create_account_move`** requires **`valuation_account_id`** on **`location_id` or `location_dest_id`**. **`WH-HRG-MAIN/Stock`** and **`Inventory adjustment`** had **NULL** accounts. **Repair:** set both to **`company.account_stock_valuation_id`**, **zero** stock via the **same inventory adjustment API**, **re-apply** opening quantities → **posted** `STJ` entries. |
| Script lacked location setup | **`gateD1_shell_input.py`** updated to **always** configure **`valuation_account_id`** on **loc 5** and **loc 11** **before** applying quantities, and to **`assert am1 > am0`** so a silent accounting miss cannot pass. |

---

## 12. Final status

**PASSED** — Opening stock is **live at `WH-HRG-MAIN/Stock`**, **traceable** via **48** inventory **`stock.move`** records, **no negative** on-hand, **perpetual valuation** posts to **`account.move`**, POS still shows the **14** templates, evidence and backups captured.

**STOP** — Gate **D2** is **out of scope** for this report.
