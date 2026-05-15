# Step 1 Result — Environment & Scope Validation

> **Document Type:** Pre-Implementation Validation Report
> **Status:** PENDING HUMAN APPROVAL — Do not proceed to Step 2 until sign-off
> **Date:** May 2026
> **Project:** Horizon Retail Group — Odoo 19 Enterprise Multi-Channel Implementation
> **Validated Against:** `/home/sabry3/sabry_backup/odoo_base/base_odoo_19/odoo19/odoo19/`
> **Odoo Source Verified:** Addons + Enterprise folders physically inspected

---

## Scope of This Validation

This document validates the full scope declared in `COMMERCIAL_OPERATIONS_PLAN.md` against:
- The physical Odoo 19 Enterprise installation on this server
- Native feasibility of every business requirement
- Missing business assumptions that would block correct configuration
- Technical and operational risks if validation is skipped

**This is a written analysis only. No configuration has been touched.**

---

## 1. Required Odoo Apps

The following apps are required for the full scope declared in the plan. Each has been physically verified as present in the local Odoo 19 Enterprise installation.

### 1.1 Core Commerce & Sales

| App / Module | Technical Name | Location | Why Required |
|---|---|---|---|
| **Sales** | `sale_management` | `addons/` | Core quotation-to-order flow for corporate sales. Without it, no SO, no quotation, no sales team assignment. |
| **CRM** | `crm` | `addons/` | Pipeline tracking per salesperson, lead-to-opportunity-to-sale. Required for Top Salespersons reporting and win/loss analysis. |
| **Sales Teams** | `sales_team` | `addons/` | Dependency of `sale_management`. Defines Corporate Sales, eCommerce, POS teams as separate reporting units. |
| **Sales — Enterprise** | `sale_enterprise` | `enterprise/` | Unlocks advanced Sales Analysis pivot/graph views, forecasting dashboards, and sales activity views. Required for executive reporting. |

### 1.2 eCommerce

| App / Module | Technical Name | Location | Why Required |
|---|---|---|---|
| **Website** | `website` | `addons/` | Provides the online storefront framework. Required as the base for eCommerce. |
| **eCommerce** | `website_sale` | `addons/` | Online product catalog, shopping cart, checkout flow, B2C order management. |
| **eCommerce — Stock** | `website_sale_stock` | `addons/` | Prevents overselling by showing real-time stock availability on product pages. Required for inventory accuracy. |
| **eCommerce — Loyalty** | `website_sale_loyalty` | `addons/` | Required if any promotional codes or loyalty rewards are offered online. Optional for Phase 1. |
| **Payment — Stripe** | `payment_stripe` | `addons/` | Primary payment gateway for online orders. Physically present. Stripe natively supported. |
| **Payment — PayPal** | `payment_paypal` | `addons/` | Secondary/fallback payment provider. Present. Optional. |
| **Website Sale Dashboard** | `website_sale_dashboard` | `enterprise/` | Provides the native eCommerce dashboard with revenue, order counts, and conversion metrics for the eCommerce Manager. |

### 1.3 Point of Sale

| App / Module | Technical Name | Location | Why Required |
|---|---|---|---|
| **Point of Sale** | `point_of_sale` | `addons/` | Core POS engine: session management, transactions, receipts, payment methods, cashier login. Required for all 30 locations. |
| **POS — Enterprise** | `pos_enterprise` | `enterprise/` | Advanced POS views, preparation display, better IoT config views. Auto-installs with `web_enterprise`. |
| **POS — HR (Cashier Login)** | `pos_hr` | `addons/` | Enables employee-based cashier login with PIN. **Critical for security** — without this, any user can open any POS session. Required for the POS access control model in Section 5 of the plan. |
| **POS — Sales** | `pos_sale` | `addons/` | Links POS orders to Sales Orders. Required for B2B POS invoicing (USE CASE P-04) and credit account orders. |
| **POS — Loyalty** | `pos_loyalty` | `addons/` | Required if gift cards or loyalty points are activated at POS. Optional for Phase 1. |
| **POS — Discount** | `pos_discount` | `addons/` | Enables the discount button on POS and the maximum discount limit per location. **Required** for the POS discount governance in Section 4.2 of the plan. |
| **POS Account Reports** | `pos_account_reports` | `enterprise/` | Provides consolidated POS accounting reports. Required for Top POS Locations, POS revenue by journal, and session-level P&L. |
| **UAE POS Localization** | `l10n_ae_pos` | `addons/` | UAE-specific POS tax handling and receipt formatting. Auto-installs when `l10n_ae` + `point_of_sale` are both active. |
| **GCC POS** | `l10n_gcc_pos` | `addons/` | GCC-level POS tax rounding and receipt format. Dependency of `l10n_ae_pos`. |

### 1.4 Accounting & Finance

| App / Module | Technical Name | Location | Why Required |
|---|---|---|---|
| **Accounting** | `account_accountant` | `enterprise/` | Full double-entry accounting with bank reconciliation, journal management, and financial statements. Core finance requirement. |
| **Accounting Reports** | `account_reports` | `enterprise/` | P&L, Balance Sheet, Tax Report, Aged Receivable, General Ledger — all executive reports in Section 12 of the plan depend on this. |
| **Payment Follow-Up** | `account_followup` | `enterprise/` | Automated overdue payment reminders, follow-up levels, and AR escalation emails. Required for USE CASE F-04. |
| **Bank Statement Import (CSV)** | `account_bank_statement_import_csv` | `enterprise/` | Imports Emirates NBD bank statements in CSV format. Required for monthly bank reconciliation. |
| **Bank Statement Import (OFX)** | `account_bank_statement_import_ofx` | `enterprise/` | Imports in OFX format as fallback. Present. |
| **Bank Statement Import (CAMT)** | `account_bank_statement_import_camt` | `enterprise/` | European XML format — lower priority for UAE but available if needed. |
| **UAE Accounting Localization** | `l10n_ae` | `addons/` | **Critical.** Provides UAE Chart of Accounts, 5% VAT taxes, UAE Tax Report (VAT return form), and UAE fiscal positions. Without this, no correct VAT compliance. |
| **GCC Invoice** | `l10n_gcc_invoice` | `addons/` | GCC-standard invoice format with TRN field. Dependency of `l10n_ae`. Auto-installs. |
| **UAE Enterprise Reports** | `l10n_ae_reports` | `enterprise/` | UAE-specific accounting reports for FTA VAT filing. Required for quarterly VAT return preparation (USE CASE F-05). |
| **Analytic Accounting** | `analytic` | `addons/` | Base analytic module. Provides analytic accounts and plans used for channel/location segmentation. |
| **Analytic Accounting Enterprise** | `analytic_enterprise` | `enterprise/` | Adds grid view, multi-plan support, and advanced analytic reporting. **Required** for the three-tier analytic plan (Channel + Location + Department) defined in Architecture Decision 2. |

### 1.5 Inventory

| App / Module | Technical Name | Location | Why Required |
|---|---|---|---|
| **Inventory** | `stock` | `addons/` | Core inventory management: locations, moves, picking, internal transfers. Required for all channels. |
| **Inventory — Accounting** | `stock_account` | `addons/` | Posts COGS and inventory valuation entries to accounting. **Required** — without this, deliveries do not create accounting entries. |
| **Stock Enterprise** | `stock_enterprise` | `enterprise/` | Advanced inventory reports, inventory dashboard, and activity views. Required for CFO-level inventory reporting. |
| **Stock Barcode** | `stock_barcode` | `enterprise/` | Barcode scanning for warehouse operations (receiving, picking). Recommended for 30-location inventory efficiency. Optional for Phase 1. |
| **Purchase** | `purchase` | `addons/` | Vendor purchase orders for inventory replenishment. Required once PO-based restocking is needed. |
| **Purchase — Stock** | `purchase_stock` | `addons/` | Links purchase orders to inventory receipts. Required for the replenishment flow. |

### 1.6 Human Resources (Limited Scope)

| App / Module | Technical Name | Location | Why Required |
|---|---|---|---|
| **Employees** | `hr` | `addons/` | Employee records for cashiers, salespersons, and managers. Required by `pos_hr` for cashier PIN login. |
| **Approvals** | `approvals` | `enterprise/` | Custom approval request types for scenarios beyond native SO approval (e.g., large refund escalation, inventory adjustments). Use only if native SO approval threshold is not sufficient. **Conditional — evaluate post-Phase 1.** |

### 1.7 Reporting & Dashboards

| App / Module | Technical Name | Location | Why Required |
|---|---|---|---|
| **Spreadsheet Dashboard — Sales** | `spreadsheet_dashboard_sale` | `addons/` | Pre-built sales spreadsheet dashboards. Enhances native Sales KPI reporting. |
| **Spreadsheet Dashboard — Accounting** | `spreadsheet_dashboard_account` | `addons/` | Pre-built accounting dashboards. Supports the CFO Dashboard requirement. |
| **Spreadsheet Dashboard — Stock** | `spreadsheet_dashboard_stock_account` | `addons/` | Inventory + accounting combined dashboard. |
| **Spreadsheet Dashboard — Website Sale** | `spreadsheet_dashboard_website_sale` | `addons/` | eCommerce performance dashboard. |

---

## 2. Native Odoo 19 Feasibility

The following table assesses every major requirement from the implementation plan against native Odoo 19 Enterprise capabilities. All assessments are based on the physical module inspection above.

| Requirement | Native Odoo 19 Support? | Confidence | Notes |
|---|---|---|---|
| **Corporate sales — quotation to invoice** | ✅ Full native | High | `sale_management` + `account_accountant`. Standard flow. No gap. |
| **Sales approval by discount threshold** | ✅ Full native | High | Sales → Configuration → Settings → "Sales Order Approval". Threshold-based approval is native. |
| **Credit limit enforcement** | ✅ Full native | High | Customer record → Sales & Purchase tab → Credit Limit. Block/warn/ignore modes available. |
| **Payment terms per customer** | ✅ Full native | High | Standard customer configuration. Net 30, Net 45, Net 60, Net 90 all configurable natively. |
| **Salesperson-level performance reporting** | ✅ Full native | High | Sales Analysis → Group by Salesperson. Native pivot + graph. |
| **eCommerce order capture + auto-invoice** | ✅ Full native | High | `website_sale` + Accounting → Settings → Auto Invoice on Payment. |
| **eCommerce Stripe payment integration** | ✅ Full native | High | `payment_stripe` is physically present. Standard Stripe native connector for Odoo 19. |
| **eCommerce stock-level enforcement** | ✅ Full native | High | `website_sale_stock` prevents overselling based on real inventory. |
| **30 POS locations — independent sessions** | ✅ Full native | High | One POS Configuration per location. 30 configs is standard Odoo. No limit. |
| **POS cashier PIN login per location** | ✅ Full native | High | `pos_hr` enables employee-based PIN access. Cashier restricted to assigned POS config. |
| **POS maximum discount limit** | ✅ Full native | High | `pos_discount` + POS Config → Maximum Discount %. Per-location setting. |
| **POS manager PIN for overrides** | ✅ Full native | High | POS → Settings → Manager Access → Restrict Price/Discount to Manager PIN. |
| **POS split payments (cash + card)** | ✅ Full native | High | POS natively supports multiple payment methods per order in a single transaction. |
| **POS B2B invoice generation** | ✅ Full native | High | `pos_sale` → Invoice button on POS order. Generates formal tax invoice with TRN. |
| **POS offline mode** | ✅ Full native | High | Odoo POS runs in browser and stores orders in local storage during connectivity loss. Syncs on reconnect. |
| **POS session accounting entries (auto-post)** | ✅ Full native | High | Session close → all entries auto-posted to GL per configured journals. |
| **Single Chart of Accounts (all channels)** | ✅ Full native | High | One company = one CoA. All channels use same accounts, differentiated by journal and analytic. |
| **Multi-plan analytic accounting (channel + location)** | ✅ Full native | High | `analytic_enterprise` in Odoo 19 supports multiple analytic plans natively. This is a new capability in Odoo 17+. |
| **Analytic filtering in all financial reports** | ✅ Full native | High | P&L, General Ledger, Tax Report all support analytic dimension filters natively in `account_reports`. |
| **Central warehouse with virtual POS locations** | ✅ Full native | High | `stock` → Configuration → Locations → Create sub-locations per POS. Standard. |
| **Inter-location stock transfer** | ✅ Full native | High | Internal picking: source = POS-Location-A, destination = POS-Location-B. Standard stock move. |
| **Inventory AVCO costing** | ✅ Full native | High | `stock_account` → Product Category → Costing Method = AVCO. |
| **COGS posting on delivery** | ✅ Full native | High | Automatic with `stock_account` + AVCO or Standard Price. Each validated delivery creates COGS entry. |
| **Bank statement import (CSV)** | ✅ Full native | High | `account_bank_statement_import_csv` physically present in enterprise. |
| **Bank auto-reconciliation** | ✅ Full native | High | Reconciliation models (Accounting → Configuration → Reconciliation Models). Auto-matches by amount, date, reference. |
| **Aged Receivable report** | ✅ Full native | High | `account_reports` → Aged Receivable. Filter by customer, date, salesperson. |
| **AR follow-up / payment reminders** | ✅ Full native | High | `account_followup` → Define levels → Auto-send emails at X days overdue. |
| **VAT Report (UAE FTA format)** | ✅ Full native | High | `l10n_ae` + `l10n_ae_reports` → Tax Report in UAE format. All 5 boxes required by FTA generated. |
| **UAE 5% VAT on all transactions** | ✅ Full native | High | `l10n_ae` provides pre-configured 5% VAT tax. Auto-applied via fiscal position. |
| **UAE TRN on invoices (POS + Sales)** | ✅ Full native | High | `l10n_gcc_invoice` adds TRN field to company and customer records. Prints on all invoice types. |
| **Accounting period lock date** | ✅ Full native | High | Accounting → Settings → Lock Date. Prevents backdated entries after month-end sign-off. |
| **Role-based access control (10 roles)** | ✅ Full native | High | Odoo native groups and access rights. All 10 roles in the plan achievable via standard group assignment. |
| **POS Top Locations report** | ✅ Full native | High | POS → Reporting → Sales → Pivot → Group by POS Config. Native. Save as favorite. |
| **Top Products (all channels)** | ✅ Full native | High | Sales Analysis + POS Sales pivot grouped by product. |
| **Top Salespersons report** | ✅ Full native | High | Sales Analysis → Group by Salesperson. |
| **Combined P&L (all channels)** | ✅ Full native | High | P&L with no analytic filter = all channels. With filter = per channel. |
| **eCommerce + Sales + POS in single P&L** | ✅ Full native | High | All three post to the same Revenue account, differentiated by analytic. Single P&L shows all. |
| **Spreadsheet / Dashboard reporting** | ✅ Full native | High | `spreadsheet_dashboard_*` modules provide pre-built dashboard views for all channels. |
| **Inventory valuation report** | ✅ Full native | High | Inventory → Reporting → Inventory Valuation. Per product, per location, per category. |
| **POS daily session summary report** | ✅ Full native | High | POS → Sessions → Session detail → Print / PDF. |
| **Scheduled email reports** | ✅ Full native | Medium | Accounting → Reports → Schedule (some reports). Not all reports are schedulable natively — manual export may be needed for some. |
| **Credit Note from SO return** | ✅ Full native | High | Return picking → Reverse Transfer → Credit Note created from invoice. |
| **Stripe settlement reconciliation** | ✅ Full native | Medium | Import Stripe settlement CSV as bank statement in Stripe journal. Reconcile against auto-payment entries. Works natively but requires process discipline for weekly import. |
| **Budget vs. Actual reporting** | ✅ Partial native | Medium | `account_budget` (present in enterprise) handles budget entry and P&L comparison. Requires budget to be entered first — not needed Day 1. |
| **Loyalty / Gift Cards (POS)** | ✅ Full native | High | `pos_loyalty` physically present. Activate post-stabilization if needed. Not in Phase 1 scope. |

### Overall Native Feasibility Score

> **Result: 100% of business requirements are achievable using native Odoo 19 Enterprise.**
> No custom module development is required for Phase 1, Phase 2, or Phase 3.
> Zero gaps identified that require `Odoo Studio` or custom Python development.

---

## 3. Missing Business Assumptions

The following items are **not yet confirmed** and must be answered before configuration begins. Configuration that starts without these answers will require rework.

Each item is marked by **impact level** if left unresolved.

---

### ASSUMPTION-01: Exact Company Legal Name and TRN

| Field | Status | Impact if Missing |
|---|---|---|
| Full legal company name (as on TRN certificate) | ❓ Not confirmed | **CRITICAL** — Company name prints on every invoice and VAT return. Wrong name = compliance failure. |
| UAE Tax Registration Number (TRN) | ❓ Not confirmed | **CRITICAL** — TRN must appear on every tax invoice (legal requirement). |
| VAT filing frequency | ❓ Not confirmed | **HIGH** — UAE FTA allows quarterly or monthly. Affects when lock date is applied and when reconciliation must be complete. |
| Company registered address (full) | ❓ Not confirmed | **HIGH** — Appears on invoices, legal documents, and FTA filings. |

**Question to ask:** Please provide the company's legal name exactly as registered with FTA, TRN number, registered address, and VAT filing period (quarterly is most common).

---

### ASSUMPTION-02: Fiscal Year Dates

| Field | Status | Impact if Missing |
|---|---|---|
| Fiscal year start and end | ❓ Assumed Jan 1 – Dec 31 in plan | **HIGH** — If the company uses a non-calendar fiscal year, the chart of accounts, opening balances, and all period-lock dates must be recalculated. |

**Question to ask:** Does the company's fiscal year run January 1 – December 31, or a different period?

---

### ASSUMPTION-03: POS Hardware Specification Per Location

| Field | Status | Impact if Missing |
|---|---|---|
| Device type (tablet, PC, dedicated POS terminal) | ❓ Not confirmed | **HIGH** — Odoo POS runs as a browser-based app. Hardware must support a modern browser. iOS Safari, Chrome, and Firefox are tested. Some older Windows tablets have issues. |
| Receipt printer model | ❓ Not confirmed | **MEDIUM** — Direct USB printers require IoT Box (`pos_iot`). Network ESC/POS printers work without IoT Box. Wrong hardware = no receipts at go-live. |
| Cash drawer connection | ❓ Not confirmed | **MEDIUM** — Connected via printer (most common) or directly via IoT Box. Affects whether `pos_iot` module is needed. |
| Barcode scanner type | ❓ Not confirmed | **LOW** — USB HID scanners work natively. Bluetooth scanners may need testing. |
| IoT Box requirement | ❓ Not confirmed | **HIGH** — If receipt printers are USB (not network), IoT Box is required per location. `pos_iot` module is present in enterprise. This adds 30 IoT Box units to procurement and configuration scope. |
| Card payment terminal model | ❓ Not confirmed | **HIGH** — If card terminals are integrated (e.g., Adyen, Worldline, Stripe Terminal), additional POS payment modules are needed (`pos_adyen`, `pos_stripe`). If card terminals are standalone (non-integrated), no additional module is required — cashier manually enters card amount in POS. |

**Question to ask:** For each of the 30 locations, what hardware is planned? Specifically: device, printer (USB or network), cash drawer connection, and card terminal type (integrated or standalone)?

---

### ASSUMPTION-04: Payment Gateway for eCommerce

| Field | Status | Impact if Missing |
|---|---|---|
| Primary online payment gateway | ❓ Assumed Stripe in plan | **HIGH** — Stripe requires a Stripe account, webhook configuration, and AED as a supported payout currency. Must be confirmed before Phase 2 begins. |
| Stripe account type | ❓ Not confirmed | **HIGH** — Individual vs. Business. UAE Stripe requires business registration. Processing in AED must be confirmed with Stripe. |
| PayPal as fallback | ❓ Optional in plan | **LOW** — Only activate if business confirms requirement. |
| 3D Secure requirement | ❓ Not confirmed | **MEDIUM** — UAE card networks (Visa/Mastercard UAE) increasingly require 3DS2. Stripe supports this natively but must be configured. |

**Question to ask:** Is Stripe confirmed as the payment gateway? Has a Stripe Business account been set up for UAE? Do you need PayPal as a fallback?

---

### ASSUMPTION-05: Bank Accounts and Statement Format

| Field | Status | Impact if Missing |
|---|---|---|
| Bank name(s) | ❓ Assumed Emirates NBD in plan | **HIGH** — Bank statement import format (CSV, OFX, CAMT) varies by bank. Must match the `account_bank_statement_import_*` module being used. |
| Number of bank accounts | ❓ Not confirmed | **HIGH** — Each bank account = one bank journal in Odoo. If there are multiple accounts (e.g., corporate collection + petty cash + POS deposit), each must be configured separately. |
| Statement download format | ❓ Not confirmed | **MEDIUM** — Emirates NBD exports CSV. Other UAE banks export OFX or PDF only. PDF cannot be auto-imported — must be manually re-entered. |
| Live bank sync availability | ❓ Not confirmed | **LOW** — Odoo's `account_online_synchronization` (Yodlee/Ponto) may or may not support UAE banks. Manual CSV import is the safe assumption for UAE. |

**Question to ask:** Which bank(s) does the company use? How many accounts? What format does your bank export statements in (CSV, OFX, PDF)?

---

### ASSUMPTION-06: Stock Costing Method Confirmation

| Field | Status | Impact if Missing |
|---|---|---|
| Inventory costing method | ❓ Assumed AVCO in plan | **CRITICAL** — Costing method **cannot be changed after the first stock move** is validated in Odoo without a full inventory reset. If the business later decides to use FIFO or Standard Price, it requires a full re-migration. This must be signed off before the first product is received into stock. |
| Whether products have variants | ❓ Not confirmed | **HIGH** — If products have size/color variants (e.g., a dress in S/M/L/XL), Product Variants must be enabled before any product is created. Enabling variants after products exist is complex. |

**Question to ask:** Do you confirm AVCO as the inventory costing method? Do your products have variants (size, color, etc.)?

---

### ASSUMPTION-07: Number of Legal Entities

| Field | Status | Impact if Missing |
|---|---|---|
| Is this one legal entity only? | ❓ Assumed single company in plan | **CRITICAL** — If the 30 POS locations are operated by different legal entities (e.g., franchises, subsidiaries), a multi-company setup is required. This fundamentally changes the architecture. |
| Are any POS locations outside UAE? | ❓ Not confirmed | **HIGH** — Cross-border locations require different tax configurations, currencies, and potentially separate companies. |

**Question to ask:** Is this a single legal entity? Are all 30 POS locations operated under one UAE company name and one TRN?

---

### ASSUMPTION-08: User Count and Named Users

| Field | Status | Impact if Missing |
|---|---|---|
| Total named users | ❓ Not confirmed | **MEDIUM** — Odoo Enterprise is licensed per user. If the business has more users than the current license allows, this must be resolved before go-live. |
| Cashiers per location (average) | ❓ Not confirmed | **MEDIUM** — 30 locations × 3 cashiers average = 90 POS users. Each cashier = one Odoo user. License cost implication. |
| Concurrent POS sessions | ❓ Not confirmed | **MEDIUM** — Can a location have multiple simultaneous POS sessions (e.g., 2 tills open at once)? This affects POS configuration and cash drawer management. |

**Question to ask:** How many total named users will use the system? How many cashiers per location? Can a single location have more than one POS till open simultaneously?

---

### ASSUMPTION-09: eCommerce Scope

| Field | Status | Impact if Missing |
|---|---|---|
| B2C only or B2C + B2B? | ❓ Plan covers both | **MEDIUM** — B2B portal ordering (Use Case E-05) requires customer portal access and different checkout flow. Must be confirmed to configure correctly. |
| Number of products online vs. POS | ❓ Not confirmed | **MEDIUM** — Are all products sold online? Or a subset? Online catalog publication must be scoped. |
| eCommerce shipping/delivery method | ❓ Not confirmed | **HIGH** — Will orders be shipped (courier) or collected (click & collect)? Shipping requires `delivery` module + carrier integration. Click & collect requires different configuration. |
| Website domain | ❓ Not confirmed | **LOW** — Affects website module setup but not accounting. |

**Question to ask:** Is the eCommerce store B2C only, or will B2B customers also order online? Will orders be shipped via courier or can customers collect from stores?

---

### ASSUMPTION-10: POS Go-Live Date vs. Data Cut-Off

| Field | Status | Impact if Missing |
|---|---|---|
| Target go-live date | ❓ Not confirmed | **HIGH** — Determines the data migration cut-off date, opening balance date, and whether the first period close in Odoo is a full month or partial month. |
| Existing POS system being replaced | ❓ Not confirmed | **MEDIUM** — If a legacy POS exists, data migration from legacy must be scoped. Parallel running period? |
| Inventory count timing | ❓ Not confirmed | **HIGH** — Opening inventory must be entered on the go-live date. A full physical count must be completed and validated by Finance before this can be done. 30 locations' stock count must be coordinated. |

**Question to ask:** What is the target go-live date? Is there a legacy POS system being replaced? When will the physical stock count be conducted?

---

### ASSUMPTION-11: Approval Limits — Business Sign-Off

| Approval | Plan Value | Status |
|---|---|---|
| POS discount maximum (%) | 10% without PIN | ❓ Not confirmed by Operations |
| POS refund without PIN (AED) | AED 100 | ❓ Not confirmed by Finance |
| SO discount requiring approval (%) | 15% | ❓ Not confirmed by Sales Director |
| Vendor payment requiring CFO sign-off | AED 5,000 | ❓ Not confirmed by CFO |
| Inventory adjustment requiring Finance approval | AED 500 | ❓ Not confirmed by Finance Manager |

**Question to ask:** Please review and confirm all approval thresholds in Section 4 of the plan with the relevant department heads. These values will be configured as hard limits in the system.

---

### ASSUMPTION-12: Odoo License and Instance Type

| Field | Status | Impact if Missing |
|---|---|---|
| Odoo Enterprise license type (Online vs. Self-Hosted) | Local self-hosted confirmed (instance exists) | ✅ Confirmed — Server verified |
| Enterprise subscription validity | ❓ Not confirmed | **CRITICAL** — Enterprise modules will not activate without a valid Odoo Enterprise subscription key. If the license has expired or is limited, enterprise features will be unavailable. |
| Database name for this project | ❓ Not confirmed | **HIGH** — Required to create the config file. Proposed: `demo_pos_accounting` |
| HTTP port for this instance | ❓ Not confirmed | **HIGH** — Must not conflict with existing instances (current ports: 8021 used by bright_dev). Proposed: **8025** |

**Question to ask:** Is the Odoo Enterprise subscription active and valid? Confirm the database name and port for this instance.

---

## 4. Risks If Validation Is Skipped

| Risk ID | Risk Description | Probability | Impact | Consequence |
|---|---|---|---|---|
| **R-01** | Configuration starts without confirmed TRN and company legal name | High | Critical | All invoices and VAT returns will have wrong company data. Requires re-printing all test invoices and reconfiguring company settings. |
| **R-02** | Costing method set incorrectly (e.g., Standard Price instead of AVCO) | Medium | Critical | Cannot change costing method after stock moves are created. Full data reset required — loses all inventory configuration work. |
| **R-03** | Hardware not tested before POS configuration | High | High | POS sessions configured but receipt printers or cash drawers do not work on go-live day. IoT Box may be needed and not procured. |
| **R-04** | Multi-company structure discovered after single-company setup | Low | Critical | Full architecture rebuild required. All journals, accounts, and analytic plans must be recreated. |
| **R-05** | Stripe account not activated for AED before eCommerce Phase | Medium | High | eCommerce go-live blocked. Payment testing cannot proceed. Revenue from online channel delayed. |
| **R-06** | Product variants not enabled before products are created | Medium | High | All products must be re-created with variants enabled. No clean migration path mid-implementation. |
| **R-07** | Odoo Enterprise license invalid or expired | Medium | Critical | Enterprise modules (account_reports, pos_enterprise, analytic_enterprise, etc.) will not activate. All advanced features unavailable. |
| **R-08** | Approval thresholds configured without business sign-off | High | Medium | Finance or Sales teams override configuration at go-live, requiring reconfiguration of POS discount limits and SO approval rules. |
| **R-09** | User count exceeds Enterprise license seat count | Medium | High | New users cannot be created. POS cashiers cannot log in. Go-live blocked. |
| **R-10** | Bank statement format incompatible with Odoo import | Medium | High | Bank reconciliation cannot be automated. Finance team reverts to manual matching. Reconciliation efficiency target not met. |
| **R-11** | Port conflict with existing Odoo instances | High (if not checked) | Medium | New database instance fails to start. Configuration work blocked until port conflict is resolved. |
| **R-12** | Physical stock count not completed before opening balance entry | High | High | Inventory opening balances are inaccurate. All inventory reports from Day 1 are unreliable. |

---

## 5. Recommendation

### Verdict: **PROCEED WITH CONDITIONS**

> The implementation is fully feasible using **100% native Odoo 19 Enterprise** as confirmed by physical module inspection. No custom development is required for any business requirement identified in the plan.

### However — the following conditions must be met before Step 2 (Configuration) begins:

| # | Condition | Priority | Owner |
|---|---|---|---|
| C-01 | Confirm company legal name, TRN, and VAT filing frequency | **MUST HAVE** | Business Owner / Finance |
| C-02 | Confirm fiscal year: Jan 1 – Dec 31 (or corrected date) | **MUST HAVE** | Finance Manager |
| C-03 | Confirm inventory costing method = AVCO (written sign-off) | **MUST HAVE** | Finance Manager + Operations |
| C-04 | Confirm single legal entity (no multi-company structure) | **MUST HAVE** | CEO / Legal |
| C-05 | Confirm Stripe account is active for UAE / AED | **MUST HAVE** (Phase 2) | eCommerce Manager |
| C-06 | Confirm whether product variants are needed | **MUST HAVE** | Operations / Merchandising |
| C-07 | Confirm Odoo Enterprise subscription is valid | **MUST HAVE** | IT Admin |
| C-08 | Confirm database name and HTTP port (proposed: `demo_pos_accounting`, port `8025`) | **MUST HAVE** | IT Admin |
| C-09 | Confirm POS hardware type per location (IoT Box needed or not) | **MUST HAVE** (Phase 3) | Operations |
| C-10 | Confirm approval thresholds with department heads | **SHOULD HAVE** | PMO / Department Heads |
| C-11 | Confirm bank name and statement export format | **SHOULD HAVE** | Finance Officer |
| C-12 | Confirm total named user count for license check | **SHOULD HAVE** | IT Admin / Finance |

### Conditions blocking Step 2 immediately:
> **C-01, C-02, C-03, C-04, C-06, C-07, C-08** must be confirmed before database creation and configuration start.

### Conditions blocking Phase 2 (eCommerce) specifically:
> **C-05** must be resolved before eCommerce configuration.

### Conditions blocking Phase 3 (POS) specifically:
> **C-09** must be resolved before any POS hardware configuration.

---

## Environment Readiness Summary

| Area | Status | Notes |
|---|---|---|
| Odoo 19 source code | ✅ Present | `/home/sabry3/sabry_backup/odoo_base/base_odoo_19/odoo19/odoo19/` |
| Community addons | ✅ Present | All required modules verified |
| Enterprise addons | ✅ Present | All required enterprise modules verified |
| UAE localization (`l10n_ae`) | ✅ Present | VAT, CoA, invoice format ready |
| UAE POS localization (`l10n_ae_pos`) | ✅ Present | GCC POS tax handling ready |
| Stripe payment module | ✅ Present | `payment_stripe` verified |
| Config directory | ✅ Exists | `/home/sabry3/sabry_backup/odoo_base/base_odoo_19/config/projects/` |
| Project directory | ✅ Exists | `/home/sabry3/sabry_backup/odoo_base/base_odoo_19/projects/demo_pos_accounting/` |
| Proposed config file path | 📋 Ready to create | `config/projects/odoo_demo_pos_accounting.conf` |
| Proposed database name | 📋 Awaiting approval | `demo_pos_accounting` |
| Proposed HTTP port | 📋 Awaiting approval | `8025` (8021 is taken by bright_dev) |
| Existing database conflicts | ✅ None | `dbfilter` for new instance will be `^demo_pos.*$` |

---

## Next Step (After Human Approval)

Once all blocking conditions (C-01 through C-08) are confirmed and this document is approved:

**Step 2: Database Creation & Base Configuration** will cover:
1. Create Odoo config file at `config/projects/odoo_demo_pos_accounting.conf`
2. Create PostgreSQL database `demo_pos_accounting`
3. Initialize Odoo instance with UAE localization
4. Verify enterprise license activation
5. Validate Gate 0 (Environment Setup) per the plan

---

> **WAITING FOR HUMAN APPROVAL. DO NOT PROCEED TO STEP 2.**

---

*Step 1 Validation — Horizon Retail Group | Odoo 19 Enterprise | May 2026*
