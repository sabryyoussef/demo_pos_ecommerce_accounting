# Step 5 Gate C2 Execution Report

> **Execution date:** 2026-05-14  
> **Scope:** Gate **C2 only** — **controlled demo retail catalog** (15 new `product.template`, 18 new variants), **POS / website flags**, **taxes and UoM**, **minimal variants** (size + colour), **no stock loading**, **no commercial documents**.  
> **Explicitly NOT done:** Gate D1+ (no inventory quantities programme, no POS/sale orders, no purchases, no invoices).

---

## 1. Executed actions

| # | Action | Command / path |
|---|--------|----------------|
| 1 | Load catalog (`env.cr.commit()`), POS categories, attribute values, uniqueness checks | `odoo-bin shell … < projects/demo_pos_accounting/evidence_gateC2/gatec2_shell_input.py` → `evidence_gateC2/gateC2_shell.txt` |
| 2 | Playwright: products list, forms, variants, POS shop (cashier **pos.cashier.dxb**) | `evidence_gateC2/gateC2_browser_capture.py` → `browser_gateC2.json`, `screenshots/*.png` |
| 3 | SQL verification | `evidence_gateC2/SQL_VERIFICATION.txt` + `SQL_VERIFICATION_results.txt` |
| 4 | Backups (gitignored) | `pg_dump -Fc` + filestore `tar.gz` → `backups/gateC2_*_20260514.*` |
| 5 | Git | Commit + annotated tag **`step5_gateC2_baseline`** |

---

## 2. Products created (15 templates, 18 variants)

**SKU prefix:** `RET-G2-` (internal reference on each variant).  
**Barcode block:** synthetic **13-digit** codes `6290010001011`–`6290010001028` (demo-only block; globally unique within this database).

| Template | Variants | Category (Gate C1 tree) | POS | eCom (`is_published`) | Type |
|------------|----------|-------------------------|-----|----------------------|------|
| Still Spring Water 500 ml | 1 | BEVERAGES | Yes | Yes | Goods |
| Sparkling Mineral Water 330 ml | 1 | BEVERAGES | Yes | No | Goods |
| Orange Juice Not From Concentrate 1 L | 1 | BEVERAGES | Yes | Yes | Goods |
| Lemon Flavour Iced Tea 500 ml | 1 | BEVERAGES | Yes | No | Goods |
| Salted Potato Crisps 40 g | 1 | FOOD | Yes | No | Goods |
| Dry Roasted Almonds 100 g | 1 | FOOD | Yes | Yes | Goods |
| Dark Chocolate Tablet 45 g | 1 | FOOD | Yes | No | Goods |
| Soft Oat Granola Bar 35 g | 1 | FOOD | Yes | Yes | Goods |
| Cotton Carry Bag | 1 | RETAIL | Yes | No | Goods |
| Alkaline AA Batteries 4-Pack | 1 | RETAIL | Yes | No | Goods |
| USB-C Sync Cable 1 m | 1 | ECOM ITEMS | Yes | Yes | Goods |
| Gift Wrapping | 1 | SERVICES | Yes | No | Service |
| Local Same-Day Delivery | 1 | SERVICES | No | Yes | Service |
| Cotton Crew Neck T-Shirt | 3 (S/M/L) | RETAIL | Yes | Yes | Goods |
| Insulated Travel Mug 350 ml | 2 (Black / Silver) | RETAIL | Yes | Yes | Goods |

**Purchase:** enabled on all **goods** (company default purchase tax applied); **disabled** on **services** (no vendor catalogue in this gate).

**Taxes:** company **sale** tax on sellable lines; **purchase** tax on purchasable goods only.

**UoM:** **Units** on all lines (Odoo 19 has no `uom_po_id` on `product.template`; purchase UoM follows standard product configuration).

---

## 3. Variants created

| Template | Attribute | Values |
|----------|-----------|--------|
| **Cotton Crew Neck T-Shirt** | Size (`product.attribute` **size**) | **S**, **M**, **L** — SKUs `RET-G2-PAR-TSH-S`, `-M`, `-L` |
| **Insulated Travel Mug 350 ml** | Colour (`product.attribute` **color**) | **Black**, **Silver** — SKUs `RET-G2-PAR-MUG350-BLA`, `RET-G2-PAR-MUG350-SIL` (*“BLA” is the live abbreviation from the first run; the shell script now maps **Black → BLK** for future installs.*) |

---

## 4. Barcode strategy

- **One barcode per `product.product`** (variant row), **never reused**.  
- **13-digit numeric** strings in the **6290010001xxx** demo range (aligned with common retail barcode length; **not** registered GS1 data).  
- **Internal references** follow `RET-G2-<family>-<token>` for stable sorting and future scale-out (family: `BEV`, `SNK`, `RTL`, `SRV`, `PAR`).

---

## 5. POS visibility validation

- **ORM / domain check:** `product.template._load_pos_data_domain({}, pos.config(5))` → **14** templates (the full database set matching **sale_ok** + **available_in_pos** for company **1**; all **14** are Gate C2 lines — **Local Same-Day Delivery** is intentionally **excluded** from POS).  
- **Gate C2 SQL check:** **14** templates with `available_in_pos`, `sale_ok`, and at least one `RET-G2%` variant.  
- **UI:** Playwright cashier session → `05_pos_shop_products.png` (no captured Owl/console/RPC errors in `browser_gateC2.json`).

---

## 6. Screenshot paths

Directory: `projects/demo_pos_accounting/evidence_gateC2/screenshots/`

| File | Description |
|------|-------------|
| `01_products_list.png` | Products (`action-207`), **admin** |
| `02_product_form_water.png` | Template **25** — Still Spring Water |
| `03_product_variants_tshirt.png` | Template **38** — T-shirt, **Variants** tab |
| `04_product_barcode_general.png` | Template **25** — **General** tab (barcode / reference area) |
| `05_pos_shop_products.png` | POS shop (**pos.cashier.dxb**, config **5**) |

---

## 7. SQL verification

Files:

- `projects/demo_pos_accounting/evidence_gateC2/SQL_VERIFICATION.txt`  
- `projects/demo_pos_accounting/evidence_gateC2/SQL_VERIFICATION_results.txt`  

**Snapshot summary:**

| Check | Result |
|--------|--------|
| `product_template` total | **22** (7 baseline + **15** Gate C2) |
| Gate C2 templates | **15** |
| Gate C2 variants (`product.product`) | **18** |
| Duplicate `barcode` | **0** rows |
| Duplicate `default_code` | **0** rows |
| By category | BEVERAGES **4**, FOOD **4**, RETAIL **4**, SERVICES **2**, ECOM ITEMS **1** |
| POS-visible Gate C2 templates | **14** |
| Website-published Gate C2 templates | **8** |
| `stock_move` total | **0** |
| `stock_quant` total | **0** |
| `product_value` total | **0** (cost revaluation suppressed via `disable_auto_revaluation` on create/write) |

---

## 8. Logs summary

| File | Summary |
|------|---------|
| `evidence_gateC2/gateC2_shell.txt` | Baseline counts; POS categories; per-product create lines; `POS_LOAD_DOMAIN_COUNT`; `UNIQUENESS_OK`; `COMMIT_OK` |
| `evidence_gateC2/gateC2_shell_run.log` | Odoo shell stdout — **no** Python traceback after fixes |
| `evidence_gateC2/gateC2_browser_run.log` | Playwright wrapper |
| `evidence_gateC2/browser_gateC2.json` | **No** `page_errors`, **no** `console_errors` / `console_owl`, **no** RPC failures |

---

## 9. Backup paths (local; not in git)

| Artifact | Path |
|----------|------|
| PostgreSQL custom-format dump | `projects/demo_pos_accounting/backups/gateC2_demo_pos_accounting_20260514.dump` |
| Filestore archive | `projects/demo_pos_accounting/backups/gateC2_filestore_20260514.tar.gz` |

---

## 10. Git tag

- **Tag:** `step5_gateC2_baseline` (annotated)  
- **Commit:** resolve with `git rev-parse step5_gateC2_baseline^{commit}` in the repository that contains this report.

---

## 11. Failures / fixes

| Issue | Fix |
|-------|-----|
| `ValueError: Invalid field 'uom_po_id' in 'product.template'` (Odoo 19) | Removed `uom_po_id` from create vals; rely on default purchase UoM behaviour. |
| `AssertionError` on `product.value` count after catalog create | Root cause: AVCO **standard price** hooks creating `product.value` rows. Wrapped `product.template` / `product.product` operations in **`disable_auto_revaluation`** context so **no** valuation history rows are created in this gate. |

---

## 12. Governance

- **English-safe** generic retail naming (no trademarked brand names).  
- **Unique barcodes** enforced by script scan + SQL `HAVING` check.  
- **No duplicate SKUs** (`default_code` unique per variant).  
- **Archive-not-delete** remains the operational policy (no deletes performed in this gate).  
- **Catalog size:** **15** templates (within **10–20** mandate).

---

## 13. Final status

**PASSED** — Gate C2 objectives met: realistic minimal catalog, controlled variants, POS and eCommerce flags where intended, taxes and units set, **no** stock moves or quants, **no** commercial documents, UI and SQL evidence captured.

**STOP** — Gate **D1** is **out of scope** for this report.
