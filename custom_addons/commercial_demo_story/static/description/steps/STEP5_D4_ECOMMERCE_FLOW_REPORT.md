# Step D4 eCommerce Flow Report

**Gate:** D4 only (first online / `website_sale` channel). **Date:** 2026-05-14. **Database:** `demo_pos_accounting`. **Final status:** **PASSED**.

This gate validates a **small** website catalog (**five** RET-G2 templates published), **two** controlled website orders (**Cash on Delivery**), checkout through address and delivery selection, **taxes**, **stock** (reservation → delivery **done**), and **inventory valuation** journal entries. Evidence: Playwright screenshots, SQL, shell logs, database and filestore backups, git tag **`step5_D4_ecommerce_flow`**. **Gate E is not executed.**

---

## 1. Executed website orders

| # | Sale order | Cart lines | Total | Tax | Carrier | Test identity |
|---|------------|------------|-------|-----|---------|----------------|
| A | **S00009** | Water 500 ml + Oat bar | **5.04** AED | **0.24** | Standard delivery (id 1) | Partner email `gate4_ecommerce_flow@example.invalid` |
| B | **S00010** | Orange juice 1 L | **8.93** AED | **0.43** | Standard delivery (id 1) | Same partner email |

**`payment.transaction`:** ids **1** (S00009) and **2** (S00010), **provider_id 22** (Cash on Delivery / custom provider), state **pending** — expected for COD until collection/post-processing.

---

## 2. Website validation

- **Shop / product / cart / checkout / payment / confirmation:** exercised by `evidence_gateD4/gateD4_browser_ecommerce.py` against `http://127.0.0.1:8025` with `db=demo_pos_accounting`.
- **Address submit:** uses `a[name="website_sale_main_button"]` (not portal `#save_address`), matching Odoo 19 `website_sale` + patched `CustomerAddress` interaction.
- **Checkout:** cart uses `a[href^="/shop/checkout"]`; on `/shop/checkout`, delivery radios become enabled after `/shop/get_delivery_rate`; script waits for an enabled `input[name="o_delivery_radio"]`, selects it, then opens `/shop/payment`.
- **Payment:** COD selected via `input[name="o_payment_radio"][data-payment-method-code="cash_on_delivery"]`.
- **Observability:** `gateD4_browser_result.json` records **no** `pageerror`, **no** console errors, **no** Owl-related console noise.

---

## 3. Catalog governance (published subset)

- **Five** product templates (RET-G2 water, OJ, oat bar, T-shirt M, mug BLA) — paths in `evidence_gateD4/gateD4_manifest.json`.
- Part 1 script: `evidence_gateD4/gateD4_shell_part1_publish.py` (ensures `website_sale`, publishes templates, records baselines, and **sets `allow_cash_on_delivery` on all active delivery carriers** so COD is not filtered by `delivery`’s `_get_compatible_providers` override).

---

## 4. Inventory validation

- **Pickings:** `HRG01/OUT/00001` (sale **S00009**, id **20**) and `HRG01/OUT/00002` (sale **S00010**, id **21**) — both **done** after move lines were set to **picked** with full **quantity** and `button_validate` with context **`skip_sms=True`** (avoids `stock_sms` wizard). Script: `evidence_gateD4/gateD4_shell_part2_deliver.py` (idempotent).
- **`stock_move`:** ids **76–78**, state **done**, tied to the above pickings (see `SQL_VERIFICATION_results.txt`).
- **Reservation / deduction:** moves progressed from website flow assignment to **done** validation; quants updated accordingly.
- **No negative net internal stock** for the three SKUs under test (SQL section 6 returns **0 rows**; section 5 shows positive **net_internal_qty** per product).

---

## 5. Accounting validation

- **Customer invoices:** both website orders remain **`invoice_status = to invoice`** — normal for this COD + website flow until invoicing is run; **no** `account_move` with `invoice_origin` for S00009/S00010 yet.
- **Inventory valuation (AVCO-related stock journals):** `account_move` **STJ/2026/05/0003** (id **29**) and **STJ/2026/05/0004** (id **30**), **posted**, linked from `stock_move.account_move_id` for the D4 pickings (SQL sections 8–9).
- **Global `account_move` count:** **12** at verification time (SQL section 7).

---

## 6. Tax validation

- **S00009:** order tax **0.24** AED; lines show tax on water and oat (see SQL section 2).
- **S00010:** order tax **0.43** AED on OJ line.

---

## 7. Screenshots paths

All under `projects/demo_pos_accounting/evidence_gateD4/screenshots/`:

| File | Content |
|------|---------|
| `01_website_shop.png` | Shop grid |
| `02_product_page_water.png` | Product page (water) |
| `cart_order_a.png` / `cart_order_b.png` | Cart per order |
| `checkout_payment_order_a.png` / `checkout_payment_order_b.png` | Payment step |
| `confirmation_order_a.png` / `confirmation_order_b.png` | Website confirmation |
| `10_sales_orders_list.png` | Sales orders list (backend) |
| `11_sale_order_form.png` | Sale order **S00009** form |
| `12_stock_picking_from_so.png` | Stock picking **HRG01/OUT/00001** |
| `13_journal_entries.png` | Journal entries list (backend) |

---

## 8. SQL verification

- **Script:** `projects/demo_pos_accounting/evidence_gateD4/SQL_VERIFICATION.txt`
- **Output:** `projects/demo_pos_accounting/evidence_gateD4/SQL_VERIFICATION_results.txt`

---

## 9. Logs summary

- **Browser output:** `evidence_gateD4/gateD4_browser_result.json`
- **Part 1 publication log:** `evidence_gateD4/gateD4_part1_shell.txt`
- **Part 2 delivery log:** `evidence_gateD4/gateD4_part2_shell.txt`

---

## 10. Backups paths

Relative to repo root `base_odoo_19` (not committed; typically gitignored like other gate dumps):

- `projects/demo_pos_accounting/backups/gateD4_demo_pos_accounting_20260514.dump` — `pg_dump` custom format  
- `projects/demo_pos_accounting/backups/gateD4_filestore_demo_pos_accounting_20260514.tar.gz` — `.filestore` archive  

---

## 11. Git tag

- **Tag:** `step5_D4_ecommerce_flow`  
- **Scope:** Gate D4 evidence scripts, SQL, report, browser automation, part 1 carrier/COD prerequisite.

---

## 12. Failures / fixes

1. **Checkout address:** `#save_address` does not exist on `website_sale` address — **fixed** by submitting with `a[name="website_sale_main_button"]`.
2. **Payment page empty (“No payment method available”):** delivery carrier had **`allow_cash_on_delivery` unset**; `delivery` excludes COD when that flag is falsy. **Fixed** by SQL `UPDATE delivery_carrier SET allow_cash_on_delivery = true` and by **part 1** script so reruns stay reproducible.
3. **COD still invisible until checkout:** delivery radios start **disabled** until rates load — **fixed** by waiting for enabled `o_delivery_radio`, clicking, then navigating to payment; cart uses explicit **`/shop/checkout`** link.
4. **Delivery validation:** `stock_sms` confirmation wizard blocked `button_validate` — **fixed** in part 2 with `skip_sms=True` and explicit move line **picked** / **quantity**.

---

## 13. Final status

**PASSED** — Two website orders confirmed, taxes and stock moves consistent, inventory journals posted for completed deliveries, no negative net internal stock for the validated SKUs, no browser Owl/page errors recorded.

**STOP (Gate E not executed).**
