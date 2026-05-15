# Step 4 Result — Execution & Configuration Sequence Blueprint

> **Document type:** Enterprise deployment playbook / implementation runbook / rollback-aware execution plan  
> **Status:** PLANNING ONLY — **No** live configuration, **no** record creation in production systems, **no** code, **no** custom modules, **no** implementation execution in this step  
> **Revision:** **Final operational hardening** incorporated — rules **R-13–R-24** and **§12** (timezone, filestore, browser, hardware, audit, users, staging, pilot SLA, monitoring, API readiness, month-end freeze).
> **Platform:** Odoo 19 Enterprise (native-first)  
> **Project:** Horizon Retail Group LLC — multi-channel retail  
> **Authoritative architecture:** `STEP3_MASTER_DATA_OPERATIONAL_STRUCTURE.md` (fully approved, including hardening H-01–H-12)  
> **Environment baseline:** `STEP2_ENVIRONMENT_SETUP_PLAN.md` + git tag `step2_environment_baseline` (when executed)  
> **Next step:** Step 5 — **not** authorized until human approval after review of this blueprint (includes **final operational hardening**: §2 R-13–R-24, **§12**)

---

## 1. Implementation Philosophy

### 1.1 Why sequence matters

Odoo is a **dependency graph**: accounting, stock valuation, taxes, products, locations, and POS all reference each other. **Wrong order** causes:

- blocked installs (“you must configure X first”),
- silent misconfiguration (defaults applied where you did not intend),
- **irreversible** states (costing method, stock moves, posted invoices with wrong tax).

Execution therefore follows **strict layers**: environment → fiscal core → structure (analytics, journals, locations) → master data → channel configs → validation.

### 1.2 Why ERP implementations fail

| Failure mode | Typical cause |
|---|---|
| “Big bang” configuration | Too many variables change at once; defects are untraceable |
| Weak validation | Users discover errors at month-end or audit |
| Heroic customization | Scope creep, upgrade debt, no native upgrade path |
| Weak ownership | Finance vs Ops blame game; no single approver per gate |
| Skipping rollback discipline | One bad week destroys trust and timeline |

This blueprint prevents those by **gates**, **smoke tests**, and **rollback points**.

### 1.3 Why validation gates are mandatory

A **gate** is a **hard stop**: no next layer until defined tests pass and a named role approves. Gates convert “hope we configured it right” into **evidence-based progression**. Missing analytics (per Step 3 H-07), broken POS assets, or invalid enterprise license are **stop-the-line** events.

### 1.4 Why rollback points are critical

Even careful teams hit **unknowns** (bad import, wrong CoA country, half-installed localization). **Rollback points** (DB dump + filestore + git tag) bound blast radius: you always return to a **known-good state** instead of repairing forward from a corrupted foundation.

### 1.5 Defined principles

| Principle | Meaning |
|---|---|
| **Never configure blindly** | Every setting change has a **documented intent** (SOP or this blueprint). If the UI field is not understood, **stop** and consult Odoo documentation or architecture doc — do not toggle experimentally on a shared demo DB that will become golden master. |
| **Test before proceeding** | After each **stage** (Section 3) and each **layer** (Section 4), run the **minimal smoke** (Section 6) relevant to that layer. |
| **One dependency layer at a time** | No parallel streams (see Section 2). Complete **environment** before **master data** before **channel** (POS/eComm) tuning. |

---

## 2. Global Execution Rules

These rules are **mandatory** for anyone executing Step 4+ implementation.

| ID | Rule |
|---|---|
| **R-01** | **No parallel configuration streams** — one implementer (or one tightly pair-reviewed stream) owns the database until Gate C is passed. |
| **R-02** | **No production-like data imports** before the agreed gate (typically after Gate B and smoke pass). No bulk customer/vendor/product CSV until structure is frozen. |
| **R-03** | **No skipping smoke tests** defined for the completed layer. |
| **R-04** | **No LIVE credentials** — payment providers: sandbox/test only until explicit cutover approval; no production SMTP (per Step 2 plan). |
| **R-05** | **No custom modules** and **no Studio** unless a documented native gap is opened as a formal change request (out of scope for this project). |
| **R-06** | **No direct SQL updates** to business tables — all changes through Odoo UI or supported import APIs. |
| **R-07** | **No deleting transactional data** — invoices, moves, POS orders: **never delete**; use reversals, credit notes, archiving (per Step 3 product lifecycle policy). |
| **R-08** | **No Odoo sample-industry demo data** — controlled dataset only (Step 2 / Step 3). |
| **R-09** | **Negative stock blocked** in production paths (Step 3 §3.10) — configure and verify before high-volume testing. |
| **R-10** | **Variants before products** — attributes and variant settings before any SKU with size/color. |
| **R-11** | **Barcodes globally unique** — resolve duplicates before go-live (Step 3 §5.4). |
| **R-12** | **POS sessions** — no overnight open sessions without escalation (Step 3 §4.12). |
| **R-13** | **Timezone governance** — single agreed timezone across servers, PostgreSQL, Odoo logs, and cron scheduling; see **§12.1**. |
| **R-14** | **Attachment / filestore governance** — no uncontrolled storage of large binaries, exports, or backups inside Odoo filestore; see **§12.2**. |
| **R-15** | **Browser governance** — production POS runs only on **supported browsers**; see **§12.3**. |
| **R-16** | **POS hardware validation** — receipt printer, barcode scanner, and cash drawer tests **mandatory** before any pilot rollout; see **§12.4**. |
| **R-17** | **Audit logging** — critical actions must remain traceable (refunds, adjustments, manual JEs, credit overrides, POS closures); see **§12.5**. |
| **R-18** | **No shared operational user accounts** — one human, one login for operational roles; see **§12.6**. |
| **R-19** | **Staging policy** — production changes flow **DEV → UAT → PILOT → PRODUCTION** only; see **§12.7**. |
| **R-20** | **Pilot rollout order** — **1 POS branch** → **3-branch regional pilot** → **full rollout**; see **§12.8**. |
| **R-21** | **Reconciliation SLA** — POS **cash and card** reconciliation **completed daily**; see **§12.9**. |
| **R-22** | **Monitoring** — daily monitoring dashboard must cover defined health signals; see **§12.10**. |
| **R-23** | **API / integration future-readiness** — no naming or structure decisions that block mobile, BI, REST, WhatsApp commerce, or marketplaces; see **§12.11**. |
| **R-24** | **Operational freeze** — no structural accounting/tax/inventory changes during **month-end close** windows; see **§12.12**. |

---

## 3. Environment Initialization Sequence

**Objective:** Reach a **clean, licensed, localized, module-complete** database with **no** master data beyond company shell — matching Step 2 completion criteria extended by Step 3 readiness.

### Stage 3.0 — Preconditions

| Step | Action | Checkpoint |
|---|---|---|
| P-1 | Confirm PostgreSQL access, port **8025** free, `demo_pos_accounting` name available | IT sign-off |
| P-2 | Confirm `addons_path` = community + enterprise + **empty** `custom_addons` only | Config file reviewed |
| P-3 | Confirm enterprise subscription key available (not in git) | **Rollback trigger:** key missing → do not start |
| P-4 | **Timezone governance (§12.1):** OS + PostgreSQL + Odoo server use **UTC**; Odoo **user preferences** use local timezone for UI timestamps where required; document NTP/time sync | Logs and crons align across hosts; no “off by 4h” reconciliation |

**Rollback trigger:** Any precondition fails → **do not create DB**; fix infra first.

---

### Stage 3.1 — Database creation

| Step | Action | Checkpoint |
|---|---|---|
| D-1 | Create empty DB `demo_pos_accounting` (UTF-8) | DB exists |
| D-2 | Deploy `odoo_demo_pos_accounting.conf` with `dbfilter=^demo_pos_accounting$`, `data_dir` under project | Filestore path writable |
| D-3 | First Odoo start; **decline** sample industry demo data (Step 2 R-A) | No junk demo records |

**Validation:** Connect to URL; database selector shows only target DB.

**Rollback:** Drop DB + delete filestore directory (no business loss).

---

### Stage 3.2 — Enterprise validation

| Step | Action | Checkpoint |
|---|---|---|
| E-1 | Verify Enterprise UI and no subscription fatal banner | V-05 equivalent |
| E-2 | Install `web_enterprise` path verified | Menus load |

**Failure / rollback trigger:** Enterprise invalid → **stop**; fix license; **recreate DB** after fix (avoid half-enterprise).

---

### Stage 3.3 — Localization activation (UAE)

| Step | Action | Checkpoint |
|---|---|---|
| L-1 | Set company country **United Arab Emirates** | Company form |
| L-2 | Install `account` → `account_accountant` (as per Step 2 tier) | Accounting app |
| L-3 | Install `l10n_ae`, `l10n_ae_reports` | Taxes and UAE reports present |
| L-4 | Set company legal name, **demo TRN**, AED, addresses | Step 1 assumptions |

**Rollback trigger:** Wrong country selected → **recreate DB** before continuing.

---

### Stage 3.4 — Core module installation (ordered)

Follow **`STEP2_ENVIRONMENT_SETUP_PLAN.md` §2** tier order (Tier 0 → 7): `stock`, `purchase` (if chosen), `crm`, `sale_management`, `sale_stock`, `sale_enterprise`, `website`, `website_sale`, `website_sale_stock`, `payment`, `payment_stripe` (no keys), `point_of_sale`, `pos_hr`, `pos_discount`, `pos_sale`, confirm `l10n_ae_pos`, `hr`, `analytic_enterprise`, `account_reports`, `account_followup`, `account_bank_statement_import_csv`, `stock_enterprise`, `pos_account_reports`.

| Step | Action | Checkpoint |
|---|---|---|
| M-1 | Install tier by tier; fix dependency errors immediately | Apps list = Installed |
| M-2 | Enable **product variants** in Sales settings **before** any product | V-19 |

**Rollback trigger:** Unresolvable module dependency → snapshot current state; prefer **DB recreate** if state is toxic.

---

### Stage 3.5 — Service restart validation

| Step | Action | Checkpoint |
|---|---|---|
| S-1 | Restart Odoo service / process | Clean start, no traceback in log |
| S-2 | Re-login; open Apps, Settings, Accounting | No 500 errors |

**Rollback trigger:** Startup failure → fix config/port/path; restore previous dump if needed.

---

### Stage 3.6 — Cron validation

| Step | Action | Checkpoint |
|---|---|---|
| C-1 | Review Scheduled Actions / recent server log | No critical recurring failures (Step 2 §7.7) |
| C-2 | Confirm **no** outbound mail server configured | No SMTP flood errors |

**Fix-forward:** Misconfigured mail → remove config. **Rollback:** only if cron corruption is systemic (rare).

---

### Stage 3.7 — POS frontend validation

| Step | Action | Checkpoint |
|---|---|---|
| PF-1 | Open POS UI in browser | POS loads |
| PF-2 | Browser console | No OWL errors; no missing enterprise assets (Step 2) |
| PF-3 | **Browser governance (§12.3):** validate POS on **Chrome or Edge stable only** for **production** POS lanes | POS UI functional; no unsupported-browser variance |

**Rollback trigger:** Asset/OWL failures → fix `addons_path` / subscription; **do not** proceed to POS master config. Unsupported browser for production POS → **fix-forward** by standardizing device image only (not a DB rollback).

---

### Stage 3.8 — Accounting dashboard validation

| Step | Action | Checkpoint |
|---|---|---|
| A-1 | Open Accounting dashboard | No enterprise warning / traceback (Step 2 V-14) |

**End of Section 3 checkpoint:** Tag/snapshot recommended: `step3_env_ready` or extend `step2_environment_baseline` policy per org — **minimum:** fresh **pg_dump + filestore** labeled `post_stage3_YYYYMMDD`.

---

## 4. Master Data Configuration Sequence

**Rule:** Configure **reference data** before **transactional masters** before **volumes**. Below is the **exact** recommended order and **why**.

| Seq | Area | Order within area | Why this order is required |
|---|---|---|---|
| **1** | **Company setup** | Legal name, TRN, address, logo, document footer | All downstream documents inherit company identity |
| **2** | **Currencies** | AED company currency; multi-currency off unless approved | FX and rounding affect every monetary field |
| **3** | **Fiscal year** | Start Jan 1; periods / tax reporting alignment | Locks period logic for reporting |
| **4** | **Taxes** | Confirm `l10n_ae` taxes; fiscal positions skeleton | Products and POS **require** valid tax defaults; changing tax after posted moves is painful |
| **5** | **Product categories** | Tree + **costing method = AVCO** on categories (production re-confirm) | Products inherit category defaults; **AVCO is irreversible** once stock moves exist for valued products |
| **6** | **Units of measure** | Base units, optional retail pack UoMs | Products cannot be saved without UoM |
| **7** | **Product attributes** | Size, Color value lists | **Must exist before variant SKUs** (Step 3 / R-10) |
| **8** | **Analytic plans & accounts** | Channel, POS location (30), optional Department | Journals and POS can default analytics **before** first invoice/POS session |
| **9** | **Journals** | Bank, POS shared journals, optional acquirer settlement journal | Payments and POS sessions **post to journals** — must exist before operational testing |
| **10** | **Warehouse & locations** | `WH-HRG-MAIN`, `Stock`, `ECOM-OUT`, `POS/{branch}`, `RET-*`, `LOSS-DAMAGE`, `ADJUSTMENT` | Stock moves **require** valid locations; POS config picks stock location |
| **11** | **Payment methods** (POS + optional payment providers without LIVE keys) | Map to shared journals | POS cannot sell with undefined tenders |
| **12** | **Users & roles** | Admin, Finance Manager/Officer, POS Manager, Cashier, Sales, Inventory | **Segregation** before sensitive journals go live (Step 3 H-08) |
| **13** | **POS configs** (30) | One per branch; default analytic; default location; manager PIN limits | POS needs **locations + journals + users** |
| **14** | **Products** | Templates → variants → barcodes (unique) → POS/website flags | **After** categories, attributes, taxes, locations exist |
| **15** | **Customers & vendors** | B2B, walk-in POS customer, eComm policy | AR/credit and pricelists reference partners; fewer mistakes after products exist for price lists testing |

**Explicit exclusions from “early” sequence:** bulk opening balances and historical migration — separate cutover runbook after structure sign-off.

---

## 5. Validation Gates

### Gate A — **Environment Golden** (end of Section 3)

| Criterion | Content |
|---|---|
| **Required tests** | Port/dbfilter; enterprise license valid; UAE taxes visible; core apps installed per Step 2 tier; **product variants** setting ON; **timezone P-4** verified; POS frontend (no OWL/asset errors); **PF-3** Chrome/Edge stable for POS lane; Accounting dashboard (no subscription warning/traceback); crons/mail checks per Step 2 |
| **Expected results** | All Section 3 stage checkpoints green; clean logs on restart |
| **Failure conditions** | Enterprise invalid; POS assets broken; wrong company country; blocking tracebacks on core apps |
| **Rollback conditions** | Any failure condition → drop DB + delete filestore + recreate after root-cause fix (no fix-forward on wrong country/license) |
| **Approval authority** | **IT Lead + Implementer** |

---

### Gate B — **Structure Golden** (after Section 4 items 1–11)

| Criterion | Content |
|---|---|
| **Required tests** | Journals exist and types correct; analytic plans and accounts complete; warehouse + full location tree (`RET-*`, `LOSS-DAMAGE`, `POS/*`); payment methods map to shared POS journals; tax/fiscal skeleton matches UAE |
| **Expected results** | Naming matches `STEP3` §9; no duplicate journal short codes; locations navigable in UI |
| **Failure conditions** | Missing mandatory location; journals pointing to wrong suspense; tax accounts not aligned to localization |
| **Rollback conditions** | Restore snapshot taken **immediately before** bulk structural work (typically before seq. 8–11 mass create) |
| **Approval authority** | **Finance Manager** (journals, taxes) + **Operations Manager** (locations) |

---

### Gate C — **Master Data Golden** (after Section 4 items 12–15)

| Criterion | Content |
|---|---|
| **Required tests** | Users/roles smoke (cashier ≠ admin); 30 POS configs (or approved pilot subset) with default **location + analytic**; sample products with **unique** barcodes; **negative stock blocked** on sellable paths; pilot POS session open/close |
| **Expected results** | Section 6 smokes pass on pilot scope; revenue lines carry required analytics (H-07) |
| **Failure conditions** | Duplicate barcodes; POS selling from central Stock; missing analytic on posted revenue; segregation broken |
| **Rollback conditions** | Restore snapshot taken **before** bulk product/partner import or before mass POS config paste |
| **Approval authority** | **Finance Manager + COO delegate (Retail Ops)** |

---

### Gate D — **Channel Pilot** (optional sub-gate before full 30-branch rollout)

| Criterion | Content |
|---|---|
| **Required tests** | One corporate SO → pick/ship (as applicable) → invoice; one eCommerce order with **sandbox** payment; one full POS session with close |
| **Expected results** | GL, stock, and tax consistent; branch/channel analytics populated |
| **Failure conditions** | Wrong COGS account; missing VAT; missing branch analytic on POS revenue |
| **Rollback conditions** | Reverse posted test transactions where supported; else restore pre-pilot snapshot |
| **Required tests** | As Gate D **plus** **§12.4**: receipt printer (test ticket), barcode scanner (known SKU), cash drawer (open on payment / kickout); all on **Chrome or Edge stable** (§12.3) |
| **Expected results** | Hardware path proven end-to-end; no duplicate scan / double-print in smoke |
| **Failure conditions** | Printer driver mismatch; scanner HID failure; drawer not firing; only unsupported browser works |
| **Rollback conditions** | N/A for DB — **stop pilot** until hardware/browser remediated |
| **Approval authority** | **Retail Ops Manager + IT** |

---

### Gate F — **Staging promotion** (optional, per §12.7)

| Criterion | Content |
|---|---|
| **Required tests** | Change promoted only after same change validated on **DEV**, then **UAT**, then **PILOT** per policy |
| **Expected results** | Evidence pack (screenshots, test IDs) per environment |
| **Failure conditions** | Direct edit on PRODUCTION skipping UAT |
| **Rollback conditions** | Restore PRODUCTION snapshot; incident review |
| **Approval authority** | **PMO + Finance Manager** (cross-functional) |

---

## 6. Smoke Test Strategy

**Minimal** tests after each **major layer** (not exhaustive UAT — that is a separate pack).

### After environment (Gate A)

- Login; open Apps; Accounting dashboard; POS UI; Settings save (e.g. company phone).

### After structure (Gate B)

- Create **draft** internal transfer between two internal locations (cancel or delete draft if policy allows **only** before stock moves — prefer **validate** tiny qty test SKU later at Gate C).
- Open journal list; confirm POS journals exist.

### Sales smoke (after products + customers partial)

- Create quotation → confirm SO (within approval rules) → **do not** ship until inventory ready.

### Inventory smoke

- Receipt **small** test qty into `Stock` → internal transfer to **one** `POS/{branch}` → on-hand matches.

### POS smoke

- Open session → one cash sale → one card or split if configured → close session → verify GL session lines and **branch analytic**.  
- **Before pilot (§12.4):** execute **hardware smoke** — print receipt, scan barcode, verify drawer; browser = **Chrome or Edge stable** (§12.3).

### Accounting smoke

- Post one test customer invoice (or use SO flow) → tax lines correct; Aged Receivable shows row.

### eCommerce smoke (sandbox)

- Place order with **test** payment; auto-invoice if enabled; **no** LIVE keys.

---

## 7. Rollback & Recovery Strategy

### 7.1 Database snapshots

| When | Action |
|---|---|
| Before Gate B structural bulk | `pg_dump demo_pos_accounting` → `pre_gateB_YYYYMMDD_HHMM.dump` |
| Before Gate C product/partner import | `pre_gateC_YYYYMMDD_HHMM.dump` |
| After each **irreversible** milestone | Same pattern |

### 7.2 Filestore backups

| When | Action |
|---|---|
| Paired with every `pg_dump` | Tar `data_dir`/filestore → matching label |

**Attachment / filestore governance (R-14 / §12.2):**

- **Do not** use Odoo attachments or the live filestore as an informal document repository for **large exports**, **database backups**, or **binary dumps**.  
- Store backups and large artifacts in **controlled object storage** or **secured backup paths** outside the web-served tree, with retention and access policy.  
- Prefer **scheduled `pg_dump`** + **filestore tar** to backup servers, not “upload to chatter.”

**Reason:** Uncontrolled filestore growth harms **performance**, **backups**, and **security**; restores become unreliable.

| Tag | Meaning |
|---|---|
| `step2_environment_baseline` | Post–Step 2 execution (per Step 2 plan) |
| `step4_pre_masterdata` | Optional: commit of config templates / docs only |
| `step4_post_gateB` | Optional: tag on repo after Gate B evidence archived |

### 7.4 Rollback naming convention

`rollback_{gate}_{YYYYMMDD}_{reason_slug}`

Example: `rollback_GateC_20260514_bad_import`.

### 7.5 Rollback triggers (mandatory rollback)

- Wrong fiscal localization or company country after transactions  
- Enterprise license invalidated mid-project  
- Corrupted module state / repeated ORM integrity errors  
- Bulk import with **material** duplicate partners/products discovered late

### 7.6 Fix-forward (allowed)

- Single wrong **draft** record  
- Mis-typed display name (no postings)  
- Missing **favorite** report (no data change)  
- One POS config typo **before** first session with sales

**Rule:** If in doubt whether fix-forward is safe → **rollback** to last gate snapshot.

---

## 8. Dependency Risk Map

| Chain / mistake | Risk | Mitigation |
|---|---|---|
| **Products before attributes/variants** | Cannot retrofit clean variant matrix | Attributes → then products (Section 4) |
| **Stock moves before AVCO confirmation** | Costing locked wrong | Set category costing **before** first receipt |
| **Invoices before taxes/fiscal positions** | Wrong VAT; painful corrections | Taxes complete (seq 4) before first invoice |
| **POS sessions before journals/locations** | Posting errors or wrong inventory | Gate B before POS pilot |
| **Analytics after high-volume transactions** | H-07 reporting failure | Analytic defaults before Gate D volume |
| **Changing CoA / tax after go-live postings** | Audit and FTA issues | Freeze after Gate B sign-off |
| **Deleting products / moves** | Broken audit trail | Archive only (Step 3 §5.11) |
| **Direct SQL** | Unsupported state | Forbidden (R-06) |
| **Parallel config** | Conflicting truth | Forbidden (R-01) |

**Hidden Odoo dependencies (examples):**

- `sale_stock` requires `stock` before meaningful SO delivery.  
- `website_sale_stock` requires `stock` + `website_sale`.  
- `l10n_ae_pos` requires `l10n_ae` + `point_of_sale`.  
- `pos_hr` requires `hr` for employee login.

---

## 9. Operational Readiness Checklist

Use before declaring **“ready for pilot operations”** (not full retail rollout until all branches pass).

### Finance

- [ ] Chart and tax reports run without error  
- [ ] Journals minimized per Step 3 §7  
- [ ] Bank / POS / acquirer journals identified  
- [ ] Manual revenue JE restriction designed (Step 3 §7.9) and **tested** on non-prod user  
- [ ] Lock date policy agreed (implementation date TBD)

### POS

- [ ] 30 configs (or pilot subset) with manager PIN, discount limits  
- [ ] POS frontend validated (OWL/assets)  
- [ ] Overnight session policy communicated (§4.12)  
- [ ] Shared journals + branch analytic verified on test close

### Inventory

- [ ] Single warehouse + full location tree including **RET-*** and **LOSS-DAMAGE**  
- [ ] Negative stock blocked on sellable paths (production)  
- [ ] Reservation behavior understood: SO/eComm reserve; POS at payment (Step 3 §3.11)  
- [ ] Adjustment reason codes + threshold approval ready

### Taxes

- [ ] Standard / zero / exempt paths assigned without cashier guesswork  
- [ ] TRN on invoices validated on sample PDF

### Reconciliation

- [ ] Bank CSV import tested on sample file  
- [ ] Acquirer settlement journal design agreed

### Reporting

- [ ] Channel P&L favorite (analytic)  
- [ ] “Missing analytic on revenue” audit favorite (Gate D criterion)

### Users

- [ ] Role matrix applied; no cashier with accounting admin  
- [ ] Password policy / 2FA per org IT

### Backups

- [ ] Automated backup schedule for demo DB (IT)  
- [ ] Latest `pg_dump` + filestore after Gate C

### Auditability

- [ ] No transactional deletes policy enforced  
- [ ] Chatter / posted document discipline for corrections  
- [ ] **Audit logging policy** active per **§12.5** (refunds, inventory adjustments, manual JEs, credit overrides, POS closures traceable to user + time)

### Timezone & infrastructure

- [ ] **UTC** on servers/PostgreSQL/Odoo process; NTP verified (**§12.1**)  
- [ ] User-facing timezone preference documented for stores vs HQ

### Staging & rollout

- [ ] **DEV → UAT → PILOT → PRODUCTION** path enforced for structural changes (**§12.7**)  
- [ ] **Pilot order** planned: **1 branch** → **3-branch regional** → **full 30** (**§12.8**)

### Reconciliation & monitoring

- [ ] **POS cash + card** reconciliation **SLA = daily** (**§12.9**)  
- [ ] **Daily monitoring** covers at minimum: failed crons, open POS sessions, negative stock attempts, missing analytics, unreconciled payments, mail queue failures (**§12.10**)

### Security & access

- [ ] **No shared operational accounts** — audit trail per human (**§12.6**)  
- [ ] Break-glass admin accounts documented and rare

### Change freeze

- [ ] **Month-end operational freeze** calendar agreed with Finance (**§12.12**) — no CoA/tax/location structure changes during close

### Integration readiness

- [ ] **English-safe codes** (Step 3 §9.8) + no blocking naming for future **REST / mobile / BI / WhatsApp commerce / marketplace** integrations (**§12.11**)

---

## 10. Anti-Patterns During Execution

| Never do | Why it destroys projects |
|---|---|
| Configure production bank **live** feed on demo first | Money movement / compliance risk |
| “Just” import 10k rows to see what happens | Breaks gates; dirty master for weeks |
| Give **everyone** Administrator for speed | Irreversible security rot |
| “Quick fix” revenue with manual JE | Breaks channel reporting + tax (H-08) |
| Delete posted invoice / stock move | Breaks audit chain |
| Turn on **negative stock** to unblock a demo sale | Violates architecture; teaches wrong behavior |
| Skip POS session close “we’ll fix tomorrow” | Cash control failure (§4.12) |
| Local-language-only **codes** on integrations | Breaks BI/API (Step 3 §9.8) |
| Parallel consultants on same DB | Conflicting edits, no accountability |
| **Shared cashier “store” login** | Breaks R-18 / §12.6 — audit and fraud defense void |
| **Safari / Firefox for production POS** | Unsupported variance — use **Chrome/Edge stable** only per §12.3 |
| **Skipping hardware smoke before pilot** | Go-live hardware failure — violates §12.4 |
| **Structural tax/CoA edits during month-end close** | Violates §12.12 — causes filing and recon chaos |

---

## 11. Final Recommendation

| Question | Answer |
|---|---|
| Is the architecture **executable safely** with this sequence? | **Yes** — provided gates, snapshots, and smoke tests are enforced. |
| Is **rollout risk** acceptable? | **Acceptable** for **pilot-first** (subset POS + subset SKU) then scale to 30 branches per phased rollout already in `COMMERCIAL_OPERATIONS_PLAN.md`. |
| Does **native Odoo** remain sufficient? | **Yes** — no custom modules required for the approved design; Studio not required. |
| Is the project **ready for actual implementation**? | **Yes, pending** human approval of **this Step 4 blueprint** (including **§12 operational hardening**) and confirmation that **Step 2 execution** and **Gate A** evidence exists (or will be produced as first implementation sprint). |

---

## 12. Operational hardening (Step 4 final approval)

This section materializes rules **R-13–R-24** for execution teams.

### 12.1 Timezone governance

**Policy:** All **servers**, **PostgreSQL**, **Odoo worker processes**, and **log aggregation** use one agreed infrastructure timezone.

**Recommendation:**

- **UTC** at infrastructure level (OS `TZ`, PostgreSQL `TimeZone`, Odoo server where applicable).  
- **User-local timezone** at Odoo **user preference** / browser level for display to staff (e.g. UAE local time in UI).

**Why:** Mixed timezones cause **bank statement line mismatch**, **cron drift**, **POS session close** vs bank deposit date confusion, and **support hell** when reading logs.

**Validation:** Compare PostgreSQL `now()` at UTC, Odoo server log timestamps, and a known posted entry’s `create_date` after Gate A.

---

### 12.2 Attachment and filestore governance

**Policy:** Large **binary files**, **data exports**, and **database backups** must **not** be stored in an **uncontrolled** way inside the Odoo **filestore** or as ad-hoc **attachments** on random records.

**Required behavior:**

- Backups: `pg_dump` + filestore archive to **designated backup storage** (encrypted, retention policy).  
- Exports: download to **secure corporate storage**, not permanent chatter attachments.  
- Train users: **no** 500 MB ZIPs on **Sales order** chatter.

**Why:** Filestore bloat degrades backup/restore time and risks **PII** leakage via over-shared documents.

---

### 12.3 Browser governance (POS)

**Policy:** **Supported browsers for production POS** must be **defined and enforced** on POS devices.

**Recommendation:**

- **Google Chrome Stable** or **Microsoft Edge Stable** **only** for **production** POS frontends.  
- Other browsers (Safari, Firefox, mobile WebKit wrappers) — **not supported** for production POS unless explicitly re-qualified by IT and signed by Retail Ops.

**Why:** POS uses heavy **OWL** + cached assets; unsupported browsers cause **silent failures**, **printing bugs**, and **payment timing** issues.

**Validation:** PF-3 in Section 3.7; repeat on each new device image before store deployment.

---

### 12.4 POS hardware validation (mandatory before pilot)

**Policy:** Before **any** pilot rollout to a live shop lane, the following **physical tests** must pass on the **exact** device stack:

| Device | Test |
|---|---|
| **Receipt printer** | Print test ticket; Arabic/Latin rendering per template; no truncation |
| **Barcode scanner** | Scan sample SKU → correct line; no double-enter; USB HID stability |
| **Cash drawer** | Open on payment / kick command; key lock documented |

**Failure:** **Stop pilot** for that branch — software go-live does not proceed without hardware sign-off.

---

### 12.5 Audit logging policy (critical actions)

The following must remain **traceable** to **user + timestamp + object** (native Odoo chatter / mail logs / POS order history / accounting audit where available):

| Action | Traceability expectation |
|---|---|
| **POS refunds** | Linked order, cashier/manager PIN user, amount |
| **Inventory adjustments** | Reason code (Step 3 §3.12), approver, location |
| **Manual journal entries** | Creator, approver (Finance Manager per Step 3 §7.9), narrative |
| **Credit limit overrides** | Approver, customer, prior vs new limit |
| **POS session closures** | Closing user, variance, time |

**Why:** Retail fraud defense and **external audit** readiness.

---

### 12.6 User governance — no shared accounts

**Policy:** **Shared accounts are forbidden** for **operational** users (cashiers, sales, warehouse, finance operators).

**Required:** One **named human** ↔ one **Odoo user**; shared **break-glass** admin only under **controlled** break-glass procedure.

**Why:** Shared logins **destroy non-repudiation** and invalidate **§12.5** audit policy.

---

### 12.7 Staging policy

**Policy:** Production-impacting changes must first pass:

**DEV → UAT → PILOT → PRODUCTION**

| Stage | Purpose |
|---|---|
| **DEV** | Rapid config iteration, module install experiments |
| **UAT** | Full gate + smoke + regression pack |
| **PILOT** | Limited real stores / SKUs / users |
| **PRODUCTION** | Full network |

**Forbidden:** Direct structural change on PRODUCTION (CoA, tax, warehouse tree) without prior promotion path — except **emergency** with CFO-written rollback plan.

---

### 12.8 Pilot rollout strategy (POS)

**Mandatory order:**

1. **Single POS branch pilot** — one shop, limited SKUs, full day session discipline.  
2. **Three-branch regional pilot** — same region preferred (shared ops manager).  
3. **Full rollout** — remaining branches in waves with Gate checkpoints.

Aligns with Gate D / E progression; expands phased plan in `COMMERCIAL_OPERATIONS_PLAN.md`.

---

### 12.9 Reconciliation SLA — POS cash and card

**Policy:** **POS cash and POS card** clearing must be **reconciled daily** (business day end or next business morning per SOP, but **not** less than **daily**).

**Why:** Daily discipline prevents **cash shrink** blind spots, **card batch** drift, and **month-end** surprise.

**Owner:** Finance Officer + Branch Manager escalation on variance.

---

### 12.10 Monitoring recommendation (daily dashboard)

A **daily monitoring** view (native Odoo + spreadsheet export + log tail, or IT SIEM) should include at minimum:

| Signal | Intent |
|---|---|
| **Failed cron jobs** | Background breakage (mail, currency, payment capture) |
| **POS sessions still open** | Overnight / fraud / forget-to-close |
| **Negative stock attempts** | Policy violation or config regression |
| **Missing analytics** on revenue lines | H-07 reporting failure early warning |
| **Unreconciled payments** | AR / acquirer / POS clearing hygiene |
| **Mail queue failures** | SMTP / digest / follow-up breakage |

**Action:** Assign owner (IT or Finance Ops) to clear red items same day.

---

### 12.11 API and integration future-readiness

**Policy:** Architecture and **naming** must not block future:

- **Mobile apps** (POS mobile / companion)  
- **BI tools** (warehouse, ODBC, spreadsheet)  
- **REST / JSON-RPC** integrations  
- **WhatsApp commerce** / messaging-led sales  
- **Marketplace** feeds (Amazon, noon, etc.)

**Means:** Strict **English-safe codes** (Step 3 §9.8); stable **internal references** and **barcodes**; **analytic** discipline; **no** hard-coded partner-specific hacks in data that should remain generic; prefer **native** payment and delivery modules when integrating.

---

### 12.12 Operational freeze policy (month-end close)

**Policy:** During agreed **month-end close windows** (e.g. T-3 calendar days through lock date), **no structural** changes to:

- Chart of accounts mapping  
- **Tax** configuration or fiscal positions  
- **Warehouse / location** topology  
- **Analytic plan** structure (account merges/splits)

**Allowed:** Operational postings, reconciliations, corrections **within** approved authority — not master-structure edits.

**Why:** Prevents **FTA / management reporting** variance during freeze.

---

> **STOP — Step 5 is not authorized from this chat. Awaiting human approval of Step 4 (including §12).**

---

*Step 4 — Execution & Configuration Sequence Blueprint (Planning Only) | Horizon Retail Group LLC | Odoo 19 Enterprise | May 2026*
