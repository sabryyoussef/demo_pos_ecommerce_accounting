# Step 2 Result — Environment Setup Plan

> **Status:** Step 2 **plan approved** — assumptions locked. Plan updated with post-approval corrections (demo data, `addons_path`, POS/accounting validations, crons, email/payment scope, git baseline tag). Execution still follows this document until Step 3 is authorized.
> **Date:** May 2026
> **Project:** Horizon Retail Group LLC — Odoo 19 Enterprise Demo
> **Prior Step:** `STEP1_ENVIRONMENT_SCOPE_VALIDATION.md` (APPROVED WITH CONDITIONS)
> **Next Step:** Step 3 — **do not start** until this plan is executed and human approval is given.

---

## Locked Assumptions (from Step 1 approval)

| Item | Confirmed value |
|---|---|
| Company legal name | Horizon Retail Group LLC |
| Country / localization | United Arab Emirates |
| VAT / TRN (demo) | 100345678900003 |
| Fiscal year | January 1 — December 31 |
| Costing method (demo) | AVCO — **re-confirm in writing before production** (difficult to change after stock moves) |
| Legal entity | Single company only; no multi-company in Phase 1 |
| Product variants | Enable **before** any product creation (fashion sizes/colors later) |
| Enterprise license | Assume valid; **if activation fails, stop and report** |
| Database name | `demo_pos_accounting` |
| HTTP port | `8025` |
| Customization | None: native Odoo, configuration only, no Studio, no custom modules, no code |

---

## Critical recommendations (post–Step 2 approval)

### R-A — Do **not** install Odoo sample-industry demo data

**Recommendation:** **Do NOT install demo data from Odoo sample industries** (e.g. industry configuration wizards, “load demo data” options, or sample-industry apps that seed generic contacts/products).

**Reason:** This project follows a **controlled enterprise demo dataset strategy** (`COMMERCIAL_OPERATIONS_PLAN.md` Section 7). Odoo’s canned industry demos introduce unrelated records, skew channel reporting, and conflict with deliberate UAT scenarios. The database must stay clean until Step 3 loads the approved dataset only.

**Execution:** When using the database creation wizard or any “Try sample” flows, **decline** demo data. Prefer CLI/database creation paths that install only required modules without industry sample packs.

### R-B — Git baseline before Step 3

**Recommendation:** After Step 2 execution passes all validations (Section 7) and before any Step 3 work, create a **clean git baseline tag**:

`step2_environment_baseline`

Tag the repository commit that reflects the approved plan + any committed config templates (not secrets). This gives a reproducible rollback point for documentation and optional automation, separate from the PostgreSQL dump backup.

---

## 1. Database creation plan

### 1.1 Objective

Create a **dedicated** PostgreSQL database and Odoo instance for this demo, isolated from other projects (e.g. existing `dbfilter` patterns on port 8021), with a clean slate for later master data (Step 3+).

### 1.2 Configuration file (to be created when execution starts)

| Setting | Planned value | Rationale |
|---|---|---|
| Config path | `config/projects/odoo_demo_pos_accounting.conf` | Aligns with repo convention (`config/projects/*.conf`) |
| `db_name` | *(omit — use `-d` on first run)* or leave unset | First install: create DB via `createdb` + `-i base` or Odoo `-d demo_pos_accounting` |
| `dbfilter` | `^demo_pos_accounting$` | Strict match so this instance only serves this database |
| `http_port` | `8025` | Per approval; avoids conflict with other instances |
| `http_interface` | `127.0.0.1` (or per org policy) | Demo safety; widen only if remote access required |
| `addons_path` | Community `addons` + `enterprise` + **one empty future-ready custom directory only** (e.g. `projects/demo_pos_accounting/custom_addons` — directory exists, **no** modules inside) | **No other custom addons paths** may be active. Prevents accidental auto-loading of unrelated modules from other development trees on the same machine. Only the empty placeholder path is allowed until a verified native gap justifies a first-party module (not expected in demo). |
| `data_dir` | e.g. `projects/demo_pos_accounting/.filestore` | Keeps filestore next to project; create empty dir before first run |
| `admin_passwd` | Strong secret (documented in secure store, not in git) | Required for database manager / master password |

### 1.3 PostgreSQL database

| Step | Action | Owner |
|---|---|---|
| D-1 | Ensure PostgreSQL user (e.g. `odoo19`) exists and can create DBs | IT / DBA |
| D-2 | Create database: `demo_pos_accounting` with correct encoding (`UTF8`) and locale | IT |
| D-3 | **Do not** load production dumps into this DB | IT |
| D-4 | First Odoo start: install `base` (or use Apps / `-i` only as per section 2) with **English** or **English + Arabic** as agreed UI languages | Implementer |

### 1.4 First-run URL and module install

- After DB exists, open `http://127.0.0.1:8025` (or host as configured).
- Complete the **database creation wizard** only if creating DB through the web UI; otherwise prefer CLI `-d demo_pos_accounting -i ...` for reproducibility.
- **Country:** United Arab Emirates (this drives fiscal localization offer in the wizard when applicable).
- **Demo data:** Do **not** enable Odoo sample-industry or generic demo datasets (see **Critical recommendation R-A**).

### 1.5 What Step 2 explicitly does **not** include

- No CSV imports, no products, no contacts, no POS, no analytic structure, no custom journals beyond what UAE CoA install creates (that remains “localization outcome,” not “master data design”).
- **No outgoing mail server configuration in Step 2** — do not configure SMTP, Odoo mail relay, or third-party mail APIs. Chatter and internal notifications may queue locally; avoid mass mail and follow-up sends until mail is explicitly scoped in a later step.
- **No payment gateway LIVE credentials in Step 2** — do not enter production Stripe/PayPal keys. Payment provider modules may be **installed** without keys; any credential work belongs to a later step using **sandbox / test mode only** (see Section 2.5 and Step 3 boundaries).

---

## 2. Required apps installation order

Principle: install **foundational** apps first, then **commerce**, then **localization-specific** bridges, then **reporting/analytics** enhancements. Order reduces dependency errors and repeated upgrades.

### 2.1 Tier 0 — Core (usually with DB / wizard)

| Order | App / technical name | Notes |
|---|---|---|
| 0 | `base`, `web`, `web_enterprise` | Enterprise UI; ensure enterprise is on `addons_path` |
| 0b | `mail`, `contacts` | Standard for users and chatter |

### 2.2 Tier 1 — Accounting & inventory base

| Order | App / technical name | Why before sales |
|---|---|---|
| 1 | `account` → **Accounting** (`account_accountant` recommended for full enterprise accounting) | CoA, journals, taxes foundation |
| 2 | `stock` → **Inventory** | Locations, operations; required before `sale_stock` / POS stock |
| 3 | `purchase` (optional but recommended before operational demo of replenishment) | Only install if purchase flow is in scope soon; otherwise defer to Step 3 decision |

*Approved demo path: install `purchase` in Step 2 only if Step 3 will use PO receipts; otherwise leave off until Step 3 to keep the environment minimal. Default recommendation: **install `purchase` in Step 2** so inventory valuation and receipts are testable without custom data.*

### 2.3 Tier 2 — UAE fiscal localization

| Order | App / technical name | Notes |
|---|---|---|
| 4 | `l10n_ae` | UAE chart, taxes, tax report data — depends on `account` + `l10n_gcc_invoice` (auto chain) |
| 5 | `l10n_ae_reports` (Enterprise) | UAE reporting pack — install after accounting + `l10n_ae` |

### 2.4 Tier 3 — Sales & CRM

| Order | App / technical name | Notes |
|---|---|---|
| 6 | `crm` | Pipeline |
| 7 | `sale_management` | Quotations / SO |
| 8 | `sale_stock` | Links sales to stock (almost always required for retail + corporate deliveries) |
| 9 | `sale_enterprise` (Enterprise) | Enhanced sales reporting |

### 2.5 Tier 4 — eCommerce & payments

| Order | App / technical name | Notes |
|---|---|---|
| 10 | `website` | Required for storefront |
| 11 | `website_sale` | eCommerce |
| 12 | `website_sale_stock` | Stock on web |
| 13 | `payment` + `payment_stripe` (and `account_payment` if not auto-installed) | Install only; **leave providers disabled or without credentials**. **No LIVE keys in Step 2.** When credentials are introduced (later), use **sandbox / test mode** only until an explicit go-live approval. |

### 2.6 Tier 5 — POS stack

| Order | App / technical name | Notes |
|---|---|---|
| 14 | `point_of_sale` | Core POS |
| 15 | `pos_enterprise` | Auto-installs with enterprise stack; verify present |
| 16 | `pos_hr` | Cashier login / employee on POS |
| 17 | `pos_discount` | Discount limits for governance |
| 18 | `pos_sale` | B2B invoice / SO link from POS when needed |
| 19 | `l10n_ae_pos` | Usually **auto_install** when `l10n_ae` + `point_of_sale` — verify installed |

### 2.7 Tier 6 — HR minimal & analytics

| Order | App / technical name | Notes |
|---|---|---|
| 20 | `hr` | Employees for `pos_hr` |
| 21 | `analytic_enterprise` (Enterprise) | Multi-plan analytic UI — install before relying on analytic plans in Step 3 |

### 2.8 Tier 7 — Optional enterprise enhancements (install if license OK)

| Order | App / technical name | When |
|---|---|---|
| 22 | `account_reports` | With `account_accountant` — financial statements |
| 23 | `account_followup` | AR reminders — useful for corporate demo |
| 24 | `account_bank_statement_import_csv` | Bank CSV import |
| 25 | `stock_enterprise` | Inventory dashboards |
| 26 | `pos_account_reports` | POS accounting reports |

### 2.9 Product variants (configuration order, not an “app”)

- Enable **Variants** in **Sales → Configuration → Settings** (product variants) **before creating any product**.
- This is a **settings** action in Step 2 execution, not master data entry.

### 2.10 Apps explicitly **not** installed in Step 2

- **Studio** (`web_studio`) — per instruction.
- **Approvals** (`approvals`) — optional; add in Step 3 if governance demos need it; keeps Step 2 lean.
- **IoT** (`pos_iot`) — only if hardware requires; not part of “environment only” unless confirmed.

---

## 3. UAE localization activation

### 3.1 Steps (execution order)

| Step | Action | Validation |
|---|---|---|
| L-1 | Set **company country** to United Arab Emirates | Company record shows AE |
| L-2 | Install **`l10n_ae`** | UAE fiscal position and taxes available |
| L-3 | Install **`l10n_ae_reports`** (Enterprise) | UAE-specific reports visible in Accounting |
| L-4 | Confirm **`l10n_ae_pos`** is installed (auto or manual) | POS receipt/tax behavior aligned with UAE/GCC |
| L-5 | Open **Accounting → Configuration → Settings** and confirm fiscal country / tax units as per UAE | No configuration of custom tax rates in Step 2 unless wizard left gaps — prefer defaults from localization |

### 3.2 TRN (demo)

- Enter **TRN** `100345678900003` on the **company** contact / accounting settings (exact field label depends on Odoo 19 UAE layout — typically company form or VAT field).
- Label clearly in UI or internal note: **“DEMO TRN — replace before production.”**

### 3.3 If localization fails

- **Stop.** Do not invent manual CoA in Step 2.
- Capture error log, module version, and missing dependency.
- Report to stakeholder; fix `addons_path` / enterprise subscription / version skew first.

---

## 4. Company profile setup

All fields below are **company-level** only (no customer/vendor records).

| Area | Field / action | Value / note |
|---|---|---|
| Identity | Legal name | Horizon Retail Group LLC |
| Identity | Country | United Arab Emirates |
| Tax | TRN (demo) | 100345678900003 — demo only |
| Address | Street, city, emirate | Use a single consistent **demo** address block (realistic format); avoid P.O. Box only if invoice rules require street |
| Contact | Email, phone, website | Demo placeholders only — **no** reliance on outbound email in Step 2 (no mail server configuration; see Section 1.5) |
| Logo | Company logo | Optional image file for PDFs — not required for Step 2 pass |
| Currency | Main currency | **AED** — set as company currency |
| Document layout | Invoice layout | Default UAE / GCC layout from localization |

**Do not** in Step 2: create branches as separate companies, inter-company rules, or additional companies.

---

## 5. Currency and fiscal year setup

### 5.1 Currency

| Item | Action |
|---|---|
| Company currency | **AED** |
| Multi-currency | Leave **disabled** for Phase 1 demo unless explicitly approved later (reduces reconciliation scope) |

### 5.2 Fiscal year

| Item | Action |
|---|---|
| Fiscal year end | **December 31** |
| Fiscal year start | **January 1** |
| Lock dates | **Do not** set accounting lock date in Step 2 beyond what wizard suggests; lock dates belong after first controlled postings in Step 3 |

### 5.3 Costing method (demo acknowledgment)

| Item | Action |
|---|---|
| Product categories | When categories are created in Step 3, set **costing method = AVCO** on categories used for demo stock |
| **Production reminder** | Document in runbook: **re-confirm costing method and variant strategy with Finance before first real stock move in production** |

Step 2 does **not** create categories/products; it only documents that AVCO is the approved demo default and must be revalidated for production.

---

## 6. Initial admin / user preparation

### 6.1 Bootstrap users

| User | Purpose | Step 2 scope |
|---|---|---|
| `admin` (or first admin from wizard) | Full technical access | Set strong password; enable 2FA if policy requires |
| Dedicated **Implementation Admin** (optional) | Day-to-day installs without sharing `admin` password | Create user in **Settings → Users** with Admin / Settings group — still “technical,” not operational roles |

### 6.2 Operational roles — **prepare names only** (optional in Step 2)

Per blueprint, roles will include Cashier, POS Manager, Salesperson, Finance Officer, etc.

**Step 2 recommendation:**

- Create **at most** one test user per role **without** assigning POS configs, teams, or limits yet **OR** defer **all** operational users to Step 3 to strictly separate “environment” from “master data and access rules.”

**Preferred lazy approach:** **Defer operational users to Step 3** except a single `demo_tester` user for smoke tests.

### 6.3 Groups / apps linkage

- Installing apps automatically adds implied groups; **do not** hand-craft XML rights in Step 2.
- After app install, verify the **Apps** menu shows expected modules as **Installed**.

---

## 7. Validation checklist after setup

Execute these checks **before** declaring Step 2 complete. All are pass/fail.

### 7.1 Infrastructure

| ID | Check | Pass criteria |
|---|---|---|
| V-01 | Odoo starts on port **8025** | Browser loads; no port bind error |
| V-02 | `dbfilter` isolates DB | Only `demo_pos_accounting` is selectable / used |
| V-03 | Enterprise UI loads | Enterprise menus visible; if not, **stop** (license / path) |
| V-04 | Filestore writable | Attachments / company logo upload works |

### 7.2 License / enterprise

| ID | Check | Pass criteria |
|---|---|---|
| V-05 | No “expired” / “invalid enterprise” blocking banner | If failure: **stop and report** per approval |
| V-06 | Enterprise accounting apps install without error | `account_accountant`, `account_reports` (if chosen) installed |

### 7.3 Localization

| ID | Check | Pass criteria |
|---|---|---|
| V-07 | Company country = AE | Confirmed on company |
| V-08 | `l10n_ae` installed | Apps list / technical name |
| V-09 | UAE taxes visible | Standard 5% VAT tax present (names may vary by version) |
| V-10 | Demo TRN saved on company | Field populated |
| V-11 | `l10n_ae_pos` present | Installed |

### 7.4 Apps matrix (smoke)

| ID | Check | Pass criteria |
|---|---|---|
| V-12 | Sales app opens | Menu accessible |
| V-13 | CRM app opens | Menu accessible |
| V-14 | Accounting app opens — **Accounting dashboard** | App opens **and** Accounting dashboard loads **without** enterprise subscription warning banners and **without** traceback / 500 error in server log |
| V-15 | Inventory app opens | Operations menu loads |
| V-16 | Website / Shop menus present | eCommerce installed |
| V-17 | POS app — backend menu | POS app menu / dashboard loads in backend (no custom POS config required yet) |
| V-18 | Payment providers menu exists | `payment` stack present |

### 7.5 Variants setting

| ID | Check | Pass criteria |
|---|---|---|
| V-19 | Product variants enabled in Sales settings | Toggle ON before any product |

### 7.6 POS frontend (browser) — mandatory smoke

After POS-related apps are installed, open the **POS frontend** at least once (use any default or minimal shop session Odoo allows for an empty POS config, or the standard POS open flow without creating master data beyond what the UI requires).

| ID | Check | Pass criteria |
|---|---|---|
| V-20 | POS frontend loads in browser | POS UI opens successfully (session/product config may be minimal) |
| V-20a | Browser developer console | **No OWL errors** (uncaught exceptions in OWL components) |
| V-20b | Network / assets tab | **No asset loading failures** (missing JS/CSS bundles, 404 on critical assets) |
| V-20c | Enterprise POS assets | **No missing enterprise assets** (no repeated 404 on `pos_enterprise` or enterprise bundle paths) |
| V-20d | Server log during POS open | **No traceback** attributable to POS asset registration or enterprise merge |

If any of V-20–V-20d fail: **stop**, capture console + server log, fix `addons_path` / enterprise subscription / asset build before Step 3.

### 7.7 Scheduled actions (crons) and background jobs

After installation stabilizes (wait a few minutes or trigger a safe manual cron cycle if policy allows):

| ID | Check | Pass criteria |
|---|---|---|
| V-21 | Scheduled actions | **Settings → Technical → Automation → Scheduled Actions** (or equivalent in Odoo 19): review recently run jobs — **no failed cron** state that indicates repeated tracebacks (investigate any job in “Failed” / error state) |
| V-22 | Mail queue / mail failures | With **no** mail server configured, confirm there are **no unhandled mail subsystem errors** flooding the log (e.g. repeated SMTP connection exceptions from misconfigured outbound mail). If outbound mail was accidentally configured, remove it for Step 2 |
| V-23 | Localization / accounting crons | No **localization-related traceback** in log from periodic accounting or sync jobs tied to freshly installed `l10n_ae` / reporting modules |

*Interpretation:* Step 2 does not require a perfectly empty cron history; it requires **no critical recurring failures** and **no localization traceback** attributable to the new install before sign-off.

### 7.8 Negative checks (must NOT exist yet)

| ID | Check | Pass criteria |
|---|---|---|
| N-01 | No Odoo sample-industry / generic demo data | **No** industry demo packs, **no** canned sample products/contacts from Odoo sample industries (see R-A). Product list must reflect only a clean DB (remove any accidental wizard-seeded records before sign-off) |
| N-02 | No customers except possibly portal/public | No corporate customer list |
| N-03 | No POS configurations beyond Odoo defaults | Zero custom POS configs **or** only untouched templates — prefer **zero** new POS configs |
| N-04 | Custom addons path policy | `addons_path` includes **only** the empty future-ready custom directory (see §1.2); **no** third paths pointing at other projects; **no** `.py` modules loaded from that directory until explicitly approved |

---

## 8. Risks and rollback plan

### 8.1 Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Enterprise license invalid | Low–Med | **High** — blocks enterprise apps | Check V-05 immediately; stop |
| Wrong `addons_path` (enterprise missing) | Med | High — wrong accounting stack | Verify paths in `.conf` before first run |
| Port 8025 in use | Med | Medium — instance won’t start | `ss -tlnp \| grep 8025` before bind; pick alternate only if approved |
| DB created with wrong country | Med | High — wrong localization | Drop DB and recreate **before** any master data |
| Variants enabled late | Med | **High** — retrofit pain | V-19 before Step 3 |
| Accidental early stock move | Low | **High** — locks costing choices | No receipts/deliveries in Step 2 |
| Admin password weak / committed to git | Med | High | Use secrets manager; `.conf` in `.gitignore` |
| Sample-industry demo data loaded | Med | Med–High | Pollutes DB; conflicts with controlled demo dataset — follow R-A |
| Extra addons paths active | Med | High | Loads wrong modules — enforce §1.2 empty custom dir only |
| Mail server misconfigured in Step 2 | Low | Med | Log noise / failed jobs — keep mail **unconfigured** per §1.5 |
| LIVE payment keys entered early | Low | **High** | Financial and compliance risk — **sandbox only** when keys are added later |

### 8.2 Rollback plan

| Scenario | Rollback action |
|---|---|
| Fresh DB, no valuable work | **Drop database** `demo_pos_accounting`; delete filestore folder; recreate DB; restart Odoo with clean `-i` sequence |
| Wrong modules installed only | Uninstall modules **in reverse dependency order** (risky); prefer **recreate DB** for demo cleanliness |
| License failure mid-install | Stop; fix subscription; **recreate DB** after subscription valid to avoid half-enterprise state |
| Filestore corruption | Restore from empty snapshot or delete `data_dir` contents with DB recreation |

### 8.3 Backup and git baseline before Step 3

After Step 2 passes all validations:

1. **Database + filestore:** Take a **dump** of `demo_pos_accounting` + tarball of filestore → label `step2_baseline_YYYYMMDD`.
2. **Git tag (mandatory):** On the repository commit that represents the approved frozen plan and any safe committed artifacts (never commit secrets), create tag:
   - **`step2_environment_baseline`**
   - Document the tag in the implementation log (date, operator, commit hash).

This tag is the **clean configuration baseline** before Step 3; it complements the DB dump, not replaces it.

---

## Step 2 completion criteria

Step 2 is complete when:

1. Database `demo_pos_accounting` exists and is served on port **8025** with correct `dbfilter`.
2. UAE localization and enterprise accounting stack are installed and **license is valid** (V-05).
3. Company profile reflects **Horizon Retail Group LLC**, **UAE**, **demo TRN**, **AED**, fiscal year **Jan 1 – Dec 31**.
4. Required apps per section 2 are **Installed** (tiers may be adjusted per the optional `purchase` note, but document the choice in the execution log).
5. **Product variants** setting is ON **before** any product work in Step 3.
6. Validation checklist (Section 7) is **100% pass** on infrastructure + license + localization + variants; **negative checks** pass (no master data).
7. **POS frontend** validation (Section 7.6, V-20) passes: no OWL errors, no asset errors, no missing enterprise assets, POS loads.
8. **Accounting dashboard** (V-14) loads with **no** enterprise subscription warnings and **no** traceback.
9. **Scheduled actions / crons** (Section 7.7): no failed critical crons, no mail-queue errors from accidental SMTP config, no localization tracebacks from recurring jobs.
10. **No** outgoing mail server configuration and **no** LIVE payment credentials in Step 2 (Sections 1.5, 2.5).
11. **No** Odoo sample-industry demo data loaded (R-A).
12. Baseline **DB dump + filestore** exists for rollback into Step 3.
13. Git tag **`step2_environment_baseline`** created on the agreed commit (Section 8.3).

---

## Explicit boundaries — Step 3 preview (not authorized yet)

The following belong to **Step 3** and must **not** be done during Step 2:

- Products, categories, attributes, attribute values
- Customers / suppliers
- POS configurations for 30 locations
- Warehouse structure beyond defaults / localization
- Analytic plans and analytic accounts
- Bank journals beyond localization defaults
- Payment provider **LIVE** keys (when configuring payments, use **sandbox / test** only until explicit approval)
- Outgoing **email server** configuration (SMTP, etc.) — defer until a dedicated mail step
- Operational user matrix and record rules per branch

---

> **STOP — Step 3 requires separate human approval after Step 2 execution and evidence (screenshots/logs) that Section 7 passed.**

---

*Step 2 Environment Setup Plan — Horizon Retail Group LLC (Demo) | Odoo 19 Enterprise | May 2026*
