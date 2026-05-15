# Step D2 POS Sales Flow Report

**Gate:** D2 only (controlled POS sales). **Date:** 2026-05-13. **Database:** `demo_pos_accounting`. **Final status:** **PASSED**.

This gate executes **three** POS orders across **POS-DXB-01** and **POS-AUH-01**, validates inventory and accounting synchronization, captures evidence (screenshots, SQL, logs), creates backups on disk, and tags the repository. **No further gates (D3+)** are executed here.

---

## 1. Executed transactions

| # | POS config   | Flow | Lines | Payments |
|---|--------------|------|-------|----------|
| 1 | POS-DXB-01 | Beverage + snack combo | `RET-G2-BEV-WAT500` × 2, `RET-G2-SNK-CRP40` × 1 | Mixed: **POS Cash AED** 3.00 + **POS Visa AED** remainder (4.35); total **7.35** (tax **0.35**) |
| 2 | POS-AUH-01 | Apparel variant | `RET-G2-PAR-TSH-M` × 1 | **POS Cash AED AUH** 51.45 (tax **2.45**) |
| 3 | POS-DXB-01 | Mug variant | `RET-G2-PAR-MUG350-BLA` × 1 | **POS Mastercard AED** 68.25 (tax **3.25**) |

**`pos.order` ids:** 18, 19, 20 (all **done** after session close). **Sessions:** DXB `POS-DXB-01/00016` (id 18), AUH `POS-AUH-01/00017` (id 19), both **closed** and posted.

---

## 2. POS validation

- **Sessions:** Opened via `pos.config.open_ui()` and `set_opening_control` under **admin** user (avoids superuser `open_ui` restriction).
- **Selling path:** Backend `pos.order` + `pos.make.payment` (same pattern as Odoo’s `create_backend_pos_order` in `point_of_sale/tests/common.py`), then **session close** via `action_pos_session_closing_control` → posted session `account.move`.
- **Session balance:** Session moves **19** (DXB) and **24** (AUH) are **posted**; SQL check for posted moves with non-zero line-balance sum returned **no rows**.
- **Payment methods:** Existing AED Cash / Visa / Mastercard / AUH Cash; no new methods.
- **Cashier / frontend smoke:** Playwright logged in as `pos.cashier.dxb`, opened POS UI (`/pos/ui/5/login?config_id=5`). **No `OwlError`**, no page errors, no console errors (see `browser_gateD2.json`).

---

## 3. Inventory validation

- **Pickings** for the three orders: ids **17**, **18**, **19** — all **done** (see SQL / `gateD2_shell.txt`).
- **`stock_move`:** Count increased by **+4** from baseline (48 → 52) per shell log.
- **`stock.quant`:** Net quantity summed over **all internal locations** per sold SKU is non-negative; SQL “negative net internal” query returned **0 rows**.
- **On-hand (internal net) after sales:** Water **22.0**, Crisps **11.0**, T-shirt M **9.0**, Mug BLA **5.0** (matches sold quantities vs D1 opening).
- **Note:** D1 opening was on **WH-HRG-MAIN/Stock**; POS pickings source **WH-HRG-MAIN/POS/…** shop locations. Validation uses **internal net** and **done pickings**, not only location id 5.

---

## 4. Accounting validation

- **`account_move`:** Total count **10** after gate (+8 vs baseline 2). Session refs **POS-DXB-01/00016**, **POS-AUH-01/00017** on journals **22** (POSS).
- **Inter payment journals:** **PPVISA/2026/00001** (id 21), **PMCARD/2026/00001** (id 20) — “Combine POS … payments from POS-DXB-01/00016”.
- **Balanced:** No posted move with non-zero sum of line balances (SQL section 5).
- **`pos.payment.account_move_id`:** Empty on individual payments in this flow; **card totals** are reflected in the **combine** moves above and in the **session** move — expected for aggregated POS closing.

---

## 5. Tax validation

- Order taxes: **0.35**, **2.45**, **3.25** on the three orders (see `pos_order` SQL).
- Session moves **19** and **24** each have **≥1** line with `tax_line_id` set (SQL section 6).

---

## 6. AVCO

- Product categories for RET-G2 goods use **`property_cost_method = average`** (AVCO). Script assertion: **PASSED** (`COST_METHOD_AVCO_OK` in `gateD2_shell.txt`).

---

## 7. POS operations

- **Open → sell → close:** Both configs: sessions opened, three orders paid, sessions moved to **closed**, session moves **posted**.
- **Mixed payment:** Order 1 validated two payment lines (cash + Visa).

---

## 8. Screenshot paths

All under `projects/demo_pos_accounting/evidence_gateD2/screenshots/`:

| File | Content |
|------|---------|
| `01_pos_order_combo_lines_payments.png` | POS order (combo): lines + payments (**receipt / cart data** via backend order form) |
| `02_pos_order_mug_payments.png` | POS order (mug) + payments |
| `03_pos_session_dxb_closed.png` | Closed POS session (DXB) |
| `04_account_move_pos_session_dxb.png` | Session accounting entry (DXB) |
| `05_stock_picking_pos_sale.png` | Stock picking (first picking id from manifest) |
| `06_product_water_on_hand.png` | Product template (water) — inventory / on-hand |
| `07_pos_shop_floor_dxb.png` | POS frontend floor (cashier DXB) |
| `08_pos_session_auh_closed.png` | Closed POS session (AUH) |
| `09_account_move_pos_session_auh.png` | Session accounting entry (AUH) |

---

## 9. SQL verification

- **Script:** `projects/demo_pos_accounting/evidence_gateD2/SQL_VERIFICATION.txt`
- **Output:** `projects/demo_pos_accounting/evidence_gateD2/SQL_VERIFICATION_results.txt`
- **Highlights:** `pos_order_count = 3`; no imbalanced posted moves; no net-negative internal quants for any product; `stock_valuation_layer` table **not present** (`to_regclass` null); `product_value` count **0** in this DB (valuation still driven through stock/accounting moves as observed).

---

## 10. Logs summary

- **Shell execution log (stdout):** `evidence_gateD2/gateD2_shell_run.log`
- **Structured gate log:** `evidence_gateD2/gateD2_shell.txt`
- **Browser listeners:** `evidence_gateD2/browser_gateD2.json` (empty error arrays)

---

## 11. Backup paths

Created on disk (paths relative to repo root `base_odoo_19`):

- `projects/demo_pos_accounting/backups/gateD2_demo_pos_accounting_20260513.dump` — `pg_dump` custom format
- `projects/demo_pos_accounting/backups/gateD2_filestore_demo_pos_accounting_20260513.tar.gz` — archive of `projects/demo_pos_accounting/.filestore`

These filenames match **authoritative project date 2026-05-13**. They are listed in `.gitignore` and are **not** committed to git.

---

## 12. Git tag

- **Tag name:** `step5_D2_pos_sales_baseline`
- **Scope:** Evidence + report + shell script committed; backups excluded by ignore rules.

---

## 13. Failures / fixes (during implementation)

1. **Product union bug:** Initial code used Python lists instead of recordsets for `|` union — **fixed** (`product.product` browse set).
2. **Strict `pos.payment.account_move_id` on bank lines:** False negative for aggregated POS — **removed** assertion; documented combine moves **20** / **21**.
3. **Negative `stock.quant` on `usage=inventory`:** D1 adjustment mirror — **excluded** from “bad negative” by checking **net internal** sum per SKU instead of raw negative rows on non-internal locations.
4. **SQL typo:** `pmt.amount` — **fixed** alias to `ppay`.

---

## 14. Governance checklist

| Rule | Result |
|------|--------|
| Auditable transactions | Three named POS orders, posted moves, done pickings |
| No negative operational stock | Net internal per SKU ≥ 0; SQL HAVING check empty |
| POS session balances | Session moves posted; line balance sum check empty |
| Payment / journal reconciliation | Session + combine payment moves present |
| Inventory / accounting sync | Pickings done; stock move increase; session COGS/tax lines |

---

## 15. Final status

**PASSED**

**STOP — Gate D2 complete. Do not proceed to D3.**
