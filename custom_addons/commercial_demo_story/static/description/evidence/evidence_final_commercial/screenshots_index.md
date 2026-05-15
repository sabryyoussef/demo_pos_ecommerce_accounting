# Screenshots index (capture manually before presentation)

Capture from the **Horizon Retail** demo company (`demo_pos_accounting` DB) with the same user flows as `STEP5_FINAL_COMMERCIAL_OPERATIONS_REPORT.md`. Store files under `evidence_final_commercial/screenshots/` using the suggested filenames.

| # | Suggested filename | Menu / action | What to show |
|---|-------------------|---------------|----------------|
| 1 | `01_accounting_dashboard.png` | Accounting → Dashboard (or Spreadsheet Dashboard) | Executive overview widgets |
| 2 | `02_pos_session_dxb.png` | Point of Sale → POS-DXB-01 → open session | Active session, receipt header |
| 3 | `03_pos_order_history.png` | POS → Orders / Reporting | Sample orders (mixed payment) |
| 4 | `04_website_shop.png` | Website → Shop | Categories and products |
| 5 | `05_website_cart_checkout.png` | Website checkout | Tax line, total (optional new cart) |
| 6 | `06_sale_quotation_list.png` | Sales → Quotations | Pipeline mix (draft + confirmed) |
| 7 | `07_sale_order_fin_a.png` | Sales → Orders → S00011 | `client_order_ref` FIN-A-NORTH-001, salesperson |
| 8 | `08_customer_invoice_paid.png` | Accounting → Customers → Invoices → INV/2026/00001 | `payment_state`: Paid |
| 9 | `09_bank_reconciliation_widget.png` | Accounting → Bank → BNK-MAIN-AED | Statement lines `FIN-DEMO-RECON-*` matched |
| 10 | `10_crm_team_target.png` | CRM / Sales → Teams → Corporate Direct | `invoiced_target` vs invoiced (if widget visible) |
| 11 | `11_pos_report_by_location.png` | Point of Sale → Reporting | Filter by POS config / session |
| 12 | `12_inventory_valuation.png` | Inventory → Reporting → Valuation | AVCO layers, no alerts |
| 13 | `13_analytic_reporting.png` | Accounting → Reporting → Analytic (if installed) | Tags on SO lines if used |
| 14 | `14_pos_configs_30.png` | Point of Sale → Configuration → Point of Sale | List showing 30 configs |
| 15 | `15_users_pos_cashiers.png` | Settings → Users | Sample cashier logins (mask passwords) |

**Note:** Headless CI cannot produce these images; they are intentionally left for a presenter workstation with `--http-interface` reachable locally.
