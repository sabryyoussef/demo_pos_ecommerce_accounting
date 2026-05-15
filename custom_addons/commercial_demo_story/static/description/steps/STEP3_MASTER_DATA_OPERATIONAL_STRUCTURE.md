# Step 3 Result — Enterprise Master Data & Operational Structure

> **Document type:** Pre-implementation architecture & master-data design  
> **Status:** PLANNING ONLY — **No** records created, **no** configuration executed, **no** code, **no** new module installs  
> **Revision:** Step 3 **approved** — architecture **hardening** policies (inventory, reservation, returns, analytics, governance, naming, scalability) incorporated below.  
> **Platform:** Odoo 19 Enterprise (native-first)  
> **Project:** Horizon Retail Group LLC — multi-channel retail (Corporate Sales, eCommerce, 30 POS)  
> **Prior steps:** Step 1 validated; Step 2 plan approved (execution may be parallel — this document does not assume DB state)  
> **Next step:** Step 4 — **not** authorized until human approval after review of this document

---

## Architecture hardening & governance (cross-cutting)

The following policies apply **across** inventory, POS, sales, eCommerce, analytics, and accounting. They are **mandatory for production** unless explicitly labeled “demo exception.”

| ID | Policy | Production rule |
|---|---|---|
| **H-01** | **Negative stock** | **BLOCKED** for production. Odoo must not allow selling below on-hand in locations that feed POS / eCommerce / committed B2B fulfillment. |
| **H-02** | **Reservation** | **Corporate Sales** and **eCommerce** reserve stock per standard Odoo rules. **POS** does **not** reserve stock *before* payment (checkout deducts / commits at payment — see §3.11). |
| **H-03** | **Returns locations** | Three logical return quarantine paths: **RET-CUSTOMER** (B2B), **RET-ECOM**, **RET-POS** — see §3.2. |
| **H-04** | **Damage / loss** | **LOSS-DAMAGE** location **separate** from all return paths — see §3.2. |
| **H-05** | **Barcodes** | **Globally unique** across all products and variants; **no** manual duplicate barcode entry (system + process). |
| **H-06** | **Product lifecycle** | **Active** / **Archived** only; **never delete** products after any inventory or accounting transaction exists. |
| **H-07** | **Analytics** | Every **revenue-impacting** posting line **must** carry required analytic distribution; missing analytics = **reporting failure** (see §2.8). |
| **H-08** | **Manual revenue JEs** | Manual journal entries touching **revenue** (income) accounts: **Finance Manager** (or delegated controller) **only** — see §7.9. |
| **H-09** | **POS sessions** | Sessions **must not** remain open past business day end **without** documented escalation — see §4.12. |
| **H-10** | **Inventory adjustments** | Adjustments above a defined **value threshold** require **approval + mandatory reason code** — see §3.12. |
| **H-11** | **Naming** | Operational **codes** and technical identifiers remain **English-safe** and **system-safe**; display names may be localized — see §9.8. |
| **H-12** | **Future scalability** | Architecture must absorb **loyalty**, **gift cards**, **franchise-style branches**, **BI tools**, and **mobile apps** without redesign — see §11.2. |

---

## 1. Enterprise Structure Design

### 1.1 Company structure

| Element | Design |
|---|---|
| **Legal / fiscal company** | **One** Odoo company: **Horizon Retail Group LLC** |
| **Country** | United Arab Emirates |
| **Currency** | AED (company currency) |
| **Fiscal year** | 1 January — 31 December |
| **TRN (demo)** | 100345678900003 — replace before production |

### 1.2 Single-company confirmation

- **Confirmed:** Phase 1 is **single legal entity** only. No `res.company` proliferation, no inter-company rules, no consolidated multi-legal reporting inside Odoo.
- **Why native Odoo:** One company = one chart of accounts, one tax engine, one AR/AP ledger, one bank reconciliation universe. Channel and branch economics are expressed through **analytic dimensions** and **stock locations**, not through artificial legal splits.

### 1.3 Operational departments (for governance & HR alignment)

Departments are **organizational**, not separate accounting entities. In Odoo they support:

- Approval routing (future, if Approvals app is used)
- HR / expense attribution (if HR scope expands)
- Optional **analytic “Department” plan** for internal management P&L slices

**Recommended department set (demo / enterprise):**

| Code | Department name | Primary role |
|---|---|---|
| DEPT-SALES | Sales & Corporate Accounts | B2B revenue, quotations, credit |
| DEPT-ECOM | eCommerce & Digital | Online channel, content, conversion |
| DEPT-OPS | Retail Operations | POS network, branches, cash |
| DEPT-SC | Supply Chain & Inventory | Warehousing, replenishment, transfers |
| DEPT-FIN | Finance & Control | GL, AR/AP, tax, reconciliation |
| DEPT-IT | IT & Systems | Access, integrations, incidents |

**Why in native Odoo:** Uses standard **Departments** (`hr.department` when HR is installed) and/or analytic tags. No custom org chart module required.

### 1.4 Sales teams

Sales teams segment **pipeline and revenue attribution** for Corporate vs. eCommerce vs. (if needed) key accounts — not legal entities.

| Team code | Team name | Channel | Default use |
|---|---|---|---|
| ST-CORP-UAE-N | Corporate — UAE North | Corporate Sales | Dubai + Northern UAE account managers |
| ST-CORP-UAE-S | Corporate — UAE South | Corporate Sales | Abu Dhabi + Al Ain + Western region |
| ST-CORP-GIFT | Corporate — Gifting & Hospitality | Corporate Sales | Bulk gifting, events |
| ST-ECOM | eCommerce | eCommerce | All website orders (B2C default) |
| ST-ECOM-B2B | eCommerce — B2B Portal *(optional)* | eCommerce | Only if B2B portal users are segmented in reporting |

**Why native Odoo:** `crm.team` / sales team is first-class on quotations and orders; **Sales Analysis** pivots natively by team. No custom fields required for “channel” if team + analytic are used consistently.

### 1.5 Regional structure

Regions group **POS branches** for operations reporting and optional analytic defaults — they are not warehouses.

| Region code | Region name | Typical emirates / clusters |
|---|---|---|
| REG-DXB-N | Dubai North | Deira, Al Garhoud, Mirdif corridor |
| REG-DXB-S | Dubai South | Marina, Jebel Ali corridor, DWC retail |
| REG-DXB-C | Dubai Central | Downtown, Business Bay |
| REG-AD | Abu Dhabi | Abu Dhabi emirate |
| REG-SHJ | Sharjah | Sharjah emirate |
| REG-N-UAE | Northern UAE | Ajman, RAK, UAQ, Fujairah |
| REG-AAN | Al Ain | Al Ain cluster |

**Why native Odoo:** Implemented as **tags on POS configs**, **analytic defaults**, or **custom “Region” on POS shop** only if a standard field exists in Odoo 19 — prefer **analytic account naming** (`POS-REG-DXB-N-...`) over custom development. Keeps reporting in pivot/favorite views.

### 1.6 Branch hierarchy

```
Horizon Retail Group LLC (Company)
└── Retail Network (conceptual)
    ├── Region: Dubai North
    │   └── Branches: POS shops (leaf = one POS configuration)
    ├── Region: Dubai South
    │   └── Branches: ...
    ├── Region: Abu Dhabi
    │   └── Branches: ...
    └── ... (other regions)
```

**Leaf node = one POS shop** = one **POS configuration** + one **analytic account** + one **stock location** (virtual shop stock).

**Why this hierarchy:** Matches how retail COOs think (region → branch), while Odoo’s posting engine stays **single company**. Reporting rolls up using **analytic** and **location** filters, not company consolidation.

---

## 2. Analytic Architecture Design

### 2.1 Strategy overview

Use **Odoo 19 Analytic Plans** (with `analytic_enterprise`) to slice P&L and operational reports by:

1. **Channel** (Sales / eCommerce / POS)  
2. **POS location** (30 branches)  
3. **Department** (optional internal management)

**Corporate Sales and eCommerce** lines default to channel-level analytics; **POS** lines default to **channel + location** (location inherits channel = POS).

### 2.2 Analytic plans (recommended)

| Plan | Technical purpose | Cardinality |
|---|---|---|
| **Plan: Channel** | Revenue/cost attribution to commercial channel | Low (3–5 accounts) |
| **Plan: POS Location** | Branch P&L for retail | 30 accounts (+ buffer for new shops) |
| **Plan: Department** *(optional)* | Internal management view | ~6 accounts |

**Why three plans:** Odoo 19 supports **multi-plan distribution** on journal items and SO/invoice lines — finance can answer “POS Dubai Mall — what was revenue?” and “All eCommerce — what was margin?” without SQL or custom BI.

### 2.3 Analytic accounts — naming convention

**Channel plan**

| Code | Name |
|---|---|
| AN-CH-SALES | Channel — Corporate Sales |
| AN-CH-ECOM | Channel — eCommerce |
| AN-CH-POS | Channel — Point of Sale (rollup; optional if every POS line already has location) |

**POS location plan (30)** — pattern:

`AN-POS-{REGION}-{SEQ}-{SHORTNAME}`

Examples:

- `AN-POS-DXB-N-001-DUBAI-MALL`
- `AN-POS-AD-011-YAS-MALL`

**Department plan (optional)**

- `AN-DPT-SALES`, `AN-DPT-ECOM`, `AN-DPT-OPS`, …

### 2.4 Channel segmentation rules

| Source document | Default analytic |
|---|---|
| Corporate SO / invoice lines | **Channel = Sales**; optional **Department = Sales** |
| Website / eCommerce orders / invoices | **Channel = eCommerce**; **Department = eCommerce** |
| POS orders / session postings | **Channel = POS** (if used) + **Location = specific branch** |

**POS nuance:** Practically, **location analytic alone** may suffice for POS revenue if channel is implied; still recommend **explicit channel plan** for unified “channel dashboard” pivots that include non-POS lines.

### 2.5 Hierarchy examples (reporting)

**Example A — CFO channel P&L (month)**

- Filter: Analytic **Channel** ∈ {Sales, eCommerce, POS}  
- Report: P&L (native) with analytic columns or exported pivot

**Example B — Regional retail performance**

- Filter: Analytic **POS Location** where code prefix `AN-POS-DXB-`  
- Measure: Revenue, margin (if COGS lines carry same analytic)

**Example C — Single branch deep dive**

- Filter: `AN-POS-DXB-N-001-DUBAI-MALL`  
- Cross-check: POS session list + inventory moves from that shop’s stock location

### 2.6 Risks if analytics are inconsistent

| Risk | Impact |
|---|---|
| Mixed tagging (some POS sales without location analytic) | Branch P&L false; “top locations” wrong |
| eCommerce orders without eCommerce analytic | Channel revenue misallocated to “unallocated” |
| Duplicative analytic accounts per branch | User selects wrong account; double-counting in manual Excel |
| Changing analytic mid-year without cutover rules | Broken comparables YoY |

**Mitigation (implementation phase, not now):** Default analytic on **POS config**, **sales team**, and **product category** where Odoo allows; periodic audit favorite “Lines missing analytic.”

### 2.7 Analytic governance (mandatory)

**Rule:** Every **revenue-impacting** transaction (and, by extension, **matched COGS / stock valuation lines** where Odoo allows analytic propagation) **must** carry the **required analytic distribution** per channel design (Channel plan + POS Location plan where applicable + optional Department plan).

| Principle | Definition |
|---|---|
| **“Revenue-impacting”** | Customer invoices/credit notes, POS session accounting lines posted to revenue, eCommerce auto-invoices, and any manual adjustment that reclasses into revenue accounts |
| **Reporting failure** | If month-end analytics show **unallocated** or **missing** dimensions on revenue (or material COGS mismatch by channel), the period is **not** acceptable for management or CFO sign-off until corrected or journal entries are reposted per policy |
| **Operational meaning** | Missing analytics is treated as **defect severity = high** — same class as unreconciled bank or wrong VAT box |

**Why:** Native Odoo channel and branch P&L depend on disciplined distribution. Multi-company is not used; therefore **analytics are the control plane** for segmentation.

**Implementation levers (Step 4, not now):** defaults on POS shop, sales team, product category, invoicing policies; saved **Accounting / Sales** pivot favorites for “lines missing analytic”; lock or warn on posting where native options exist.

**Cross-reference:** See **Architecture hardening H-07** at document top.

### 2.8 Why analytics are preferred over multi-company

| Topic | Multi-company | Single company + analytics |
|---|---|---|
| Legal reality | Needed for **separate legal entities** | Matches **one** LLC |
| Inter-company | Complex eliminations, billing between entities | None |
| Tax | Per-entity registration | One TRN, one filing (simpler for this scope) |
| Bank | Many bank journals per entity | Centralized treasury with analytic tagging |
| Maintenance | High | **Low** — native Odoo sweet spot |

---

## 3. Inventory & Warehouse Architecture

### 3.1 Warehouse structure

| Element | Design |
|---|---|
| **Warehouses count** | **1** main warehouse: `WH-HRG-MAIN` (Horizon Retail Group — Main) |
| **Why not 30 warehouses** | Each extra warehouse multiplies routes, rules, valuation complexity, and operational noise. Thirty warehouses **do not** equal thirty P&L branches in Odoo — branches are **POS configs + locations + analytics**. |

### 3.2 Stock locations (under the main warehouse)

Use **physical and virtual locations** under one warehouse.

| Location code | Type | Purpose |
|---|---|---|
| `WH-HRG-MAIN/Stock` | Internal | Central sellable bulk / back-store |
| `WH-HRG-MAIN/ECOM-OUT` | Internal | eCommerce picking / packing staging |
| `WH-HRG-MAIN/SALES-OUT` | Internal | Corporate B2B pick/stage (if differentiated) |
| `WH-HRG-MAIN/POS/{BRANCH}` | Internal *(virtual shop)* | **One per POS shop** — sellable qty at branch |
| `WH-HRG-MAIN/RET-CUSTOMER` | Internal | **B2B / corporate** returns quarantine (customer-originated, non-POS, non-eComm channel) |
| `WH-HRG-MAIN/RET-ECOM` | Internal | **eCommerce** returns quarantine — distinct reporting and triage vs retail |
| `WH-HRG-MAIN/RET-POS` | Internal | **POS / retail** returns quarantine — shop-level damaged/exchange intake before QC |
| `WH-HRG-MAIN/LOSS-DAMAGE` | Internal | **Damaged, obsolete, or write-off** stock **only** — **not** a substitute for returns; separated for valuation, insurance, and shrink analytics |
| `WH-HRG-MAIN/ADJUSTMENT` | Inventory Loss / Adj | **Approved** cycle-count adjustments (policy-controlled); not a dumping ground for returns |
| `WH-HRG-MAIN/SCRAP` | Virtual | Scrap workflow destination (optional; align with `LOSS-DAMAGE` policy so operators have one clear path) |

**Returns policy (hardened):** Use **three** logical return locations (**RET-CUSTOMER**, **RET-ECOM**, **RET-POS**) instead of a single mixed “returns” bucket.

**Reason:** Improves **reporting** (return rates by channel), **damaged-stock triage** (QC workflows differ: eComm shipped vs POS worn vs B2B bulk), and **finance** (different write-off approval paths can be tied to location + reason code in SOP).

**Damaged goods policy (hardened):** **`LOSS-DAMAGE`** is **only** for damaged, unsellable, or approved write-off inventory — **never** for customer return intake. Returned sellable goods flow **RET-*** → QC → `Stock` or `LOSS-DAMAGE` after decision.

**Naming convention:** `WH-HRG-MAIN/POS/AN-POS-...` mirroring analytic codes reduces operational errors.

### 3.3 POS virtual locations

- Each of **30** POS shops = **one dedicated internal location** under `POS/`.  
- Stock in that location = **available to sell at that shop** in POS (subject to product routes and POS config).

### 3.4 eCommerce staging

- **`ECOM-OUT`**: pick/pack/ship for online orders; clear ownership for ops (“eComm wall” in warehouse).

### 3.5 Outgoing locations

- Use standard **Customers** / **Partners** virtual stock locations from Odoo for deliveries (do not invent parallel “customer” locations unless process requires).

### 3.6 Returns locations (three-path model)

- See **§3.2** table: **RET-CUSTOMER**, **RET-ECOM**, **RET-POS** + separate **LOSS-DAMAGE**.  
- **Returns quarantine** prevents returned goods from being immediately resold until QC.  
- **Demo note:** For the smallest possible demo DB, operations may temporarily use fewer locations — **production architecture retains all four paths** (three returns + loss/damage).

### 3.7 Adjustment locations

- Central **`ADJUSTMENT`** (or Odoo default adjustment location) for **approved** cycle-count corrections.  
- **`LOSS-DAMAGE`** for damaged/write-off stock (see §3.2).  
- **POS cash variance** is **not** inventory — do not mix cash shortage with stock adjustment without policy.

### 3.8 Replenishment philosophy

- **Pull from central `Stock` to each `POS/{branch}`** based on min/max or reordering rules (implementation phase).  
- **eCommerce** consumes from `ECOM-OUT` or directly from `Stock` depending on picking discipline — pick **one** standard and document it in SOP.

### 3.9 Transfer flows (design)

```
Supplier → WH-HRG-MAIN/Stock  (receipt)
WH-HRG-MAIN/Stock → WH-HRG-MAIN/POS/{branch}  (internal transfer / replenishment)
WH-HRG-MAIN/POS/{branch} → Customers  (POS sale / delivery)
WH-HRG-MAIN/Stock → WH-HRG-MAIN/ECOM-OUT  (optional pre-pick)
WH-HRG-MAIN/ECOM-OUT → Customers  (eCommerce delivery)
Customers → WH-HRG-MAIN/RET-CUSTOMER  (B2B return receipt)
Customers → WH-HRG-MAIN/RET-ECOM     (eCommerce return receipt)
Customers → WH-HRG-MAIN/RET-POS      (POS return receipt)
WH-HRG-MAIN/RET-* → WH-HRG-MAIN/Stock (QC pass — return to sellable)
WH-HRG-MAIN/RET-* → WH-HRG-MAIN/LOSS-DAMAGE  (QC fail — damage / write-off)
```

### 3.10 Inventory policy — negative stock (**production: BLOCKED**)

**Policy:** For **production** architecture, **negative stock must be BLOCKED** (no backorders that drive quantity negative in sellable locations; no silent oversell).

**Reason:** **Retail + AVCO + multi-channel** operations become **financially dangerous** with negative inventory: average cost and COGS alignment degrade, channel reports lie, eCommerce can oversell, and audit/compliance risk rises.

**Odoo lever (implementation):** Configure product / warehouse / location rules consistent with “**do not allow negative stock**” for fulfillment and POS shop locations (exact toggles depend on Odoo 19 settings for out-of-stock behavior on SO vs POS — Step 4 maps native options per channel).

**Demo exception:** Only if a **controlled** UAT scenario explicitly requires simulating a backlog — never for production go-live.

### 3.11 Reservation policy (explicit)

| Channel | Reservation expectation | Rationale |
|---|---|---|
| **Corporate Sales** | **Reserve** stock on confirmed sales / delivery policy per SOP | B2B commitments must not oversell confirmed obligations; pick planning needs reliability |
| **eCommerce** | **Reserve** stock on order confirmation (or at payment — pick **one** SOP) per native `website_sale_stock` behavior | Prevents overselling the web catalog |
| **POS** | **Do NOT** reserve stock **before payment** | Checkout speed and retail reality: stock must remain available to other registers/customers until the tender is complete; POS fulfillment follows **payment-confirmed** consumption (native POS flow) |

**Operational impact:** Warehouse and eComm see **reserved** quantities; POS shops rely on **physical available** in `POS/{branch}` minus concurrent baskets (accepted retail trade-off). Replenishment must keep **POS shop mins** above peak concurrent demand where possible.

### 3.12 Inventory governance — adjustments (threshold + reason codes)

**Policy:** Inventory adjustments (physical inventory / scrap moves / write-offs) above a **finance-defined value threshold** require:

1. **Approval** (e.g. Inventory Manager + Finance Manager per governance matrix), and  
2. **Mandatory reason code** (standardized list: `COUNT-VAR`, `SHRINK-THEFT`, `DAMAGE`, `EXPIRY`, `SYSTEM-CORR`, etc.) — captured in **reference / chatter / inventory adjustment reason** per Odoo native fields available in Step 4.

**Why:** Prevents “silent shrink” and creates an **audit trail** aligned with enterprise controls.

### 3.13 Why NOT 30 warehouses (summary)

| Anti-pattern | Problem |
|---|---|
| 30 warehouses | 30× procurement rules, duplicated reorder logic, heavier month-end inventory reconciliation |
| 1 warehouse + 30 POS locations | **Clear stock ownership per branch**, **single valuation** roll-up, simpler inter-branch transfers |

---

## 4. POS Operational Structure

### 4.1 Thirty POS architecture

| Layer | Count | Odoo object |
|---|---|---|
| Shops | **30** | **Point of Sale → Configuration → Point of Sale** (one record per branch) |
| Registers / sessions | Many per shop | **POS sessions** — concurrent sessions per shop only if operationally required |

**One POS config per branch** named per **Section 9** convention (e.g. `POS-DXB-N-001 | Dubai Mall`).

### 4.2 POS grouping strategy

- **By region:** Use naming prefix + optional analytic parent report (pivot group by substring — favorite saved view).  
- **By format:** Flagship / Standard / Kiosk — implement as **tags** or naming suffix (`-FLAG`, `-STD`, `-KSK`) for filtering, not as separate companies.

### 4.3 Payment methods strategy

**Design:** Few **payment methods** reused across all 30 POS; **not** 30×4 duplicate method records.

| Method | Type | Journal mapping (conceptual) |
|---|---|---|
| Cash AED | Cash | `POS-CASH-AED` |
| Visa | Bank | `POS-VISA` |
| Mastercard | Bank | `POS-MC` |
| Apple Pay / Wallet | Bank | Map to same card clearing journal **or** separate if bank settles separately |
| Gift card | Cash or Bank | `POS-GIFT` (if activated later) |

**Why:** Cashiers need simple tender types; finance needs **minimal journals** for reconciliation.

### 4.4 Session ownership

- **Cashier** opens session, sells, proposes close.  
- **POS Manager** validates closing counts, resolves variance, enters manager PIN for sensitive actions.

### 4.5 Cashier hierarchy (native)

- **Employees** linked to users for `pos_hr`.  
- **Role separation:** cashier user ≠ POS manager user (different Odoo groups).

### 4.6 Manager PIN governance

- Enforce **PIN** for: above-threshold discount, above-threshold refund, price override, cash drawer operations (per Odoo POS settings).  
- Thresholds to be set in implementation from governance matrix — not in this planning doc’s numbers.

### 4.7 Refund governance

- Refunds tied to **original order** where possible.  
- Tiered approval by amount (PIN / manager) — aligns with blueprint; exact AED limits are business sign-off during config.

### 4.8 Opening / closing flow (conceptual)

1. Open session → opening cash count  
2. Trade  
3. Close session → system expected vs physical → variance handling  
4. Accounting: session posts to **shared POS journals** with **branch analytic**

### 4.9 Shared journals strategy

- **Shared** cash and card **journals** across all POS (e.g. one `POS-CASH-AED`, one `POS-VISA`).  
- **Differentiation:** **Analytic account per POS config** on POS orders / session lines so P&L by branch remains accurate.

### 4.10 Analytic tagging strategy (POS)

- Mandatory: **POS Location analytic** on every POS sale line (via POS shop default).  
- Optional: **Channel = POS** on same lines for unified channel dashboards.

### 4.11 Risks of journal explosion

| Risk | Consequence |
|---|---|
| Journal per branch × payment type | Dozens of bank/cash journals; reconciliation **unmanageable**; statement matching fragile |
| Journal minimization + analytic | **Preferred** — bank rec stays at “real” bank accounts; branch economics stay in analytic + POS reports |

### 4.12 POS governance — sessions must not remain open overnight (escalation)

**Policy:** A **POS session must not** remain in **open** state across the **business-day boundary** (e.g. past store closing / overnight) **without** a documented **escalation**.

| Requirement | Rationale |
|---|---|
| **Close same day** | Cash control, fraud prevention, and **daily cash-to-bank** alignment require a closed session per SOP |
| **Escalation if impossible** | If technical failure prevents close: **POS Manager → Branch Manager → IT → Finance** notified same evening; session status and cash variance documented in chatter / ops log |

**Why:** Open sessions **block** clean day-level POS accounting, distort “sessions open” KPIs, and increase **cash shrink** and **reconciliation mismatch** risk.

**Cross-reference:** **Architecture hardening H-09** at document top.

---

## 5. Product Master Data Strategy

### 5.1 Product categories

Use a **shallow, stable category tree** aligned to merchandising and COGS reporting — not SKU-level categories.

**Example top-level:**

- `CAT-WOMEN` — Women’s fashion  
- `CAT-MEN` — Men’s fashion  
- `CAT-ACC` — Accessories & beauty  
- `CAT-GIFT` — Corporate gifting (B2B-heavy)  
- `CAT-NONINV` — Non-inventory services *(if ever needed)*

**Subcategories** only where reporting requires (e.g. `CAT-WOMEN-DRESSES`).

### 5.2 Variant strategy (mandatory for fashion)

- **Step 2 / Step 3 principle:** Variants enabled **before** SKU creation.  
- **Attributes:** e.g. `Size` (XS–XL), `Color` (controlled palette).  
- **Variants = sellable SKU** with own barcode where applicable.

### 5.3 Attribute structure

- **Few global attributes** reused across products (Size, Color).  
- Avoid **product-specific attribute explosion** (e.g. “Embroidery thread color” as top-level attribute) unless category team owns it.

### 5.4 Barcode strategy and governance (mandatory)

**Operational rule**

- **One primary barcode per variant** (EAN/UPC or GS1-assigned where available).  
- POS scanners use the **primary** barcode; packaging alternates use Odoo’s **additional barcode** fields where applicable (implementation).

**Governance — global uniqueness (mandatory)**

- Barcodes must be **globally unique across all product templates and variants** in the company catalog.  
- **No manual duplicate barcode entry** is permitted: if Odoo warns of a duplicate, **resolve** (wrong SKU, retired SKU, or packaging barcode) before saving.  
- **Reason:** Duplicate barcodes cause **wrong product picks** at POS, **incorrect inventory moves**, **COGS/revenue misclassification**, and **failed** WMS / eCommerce scans.

**Process (Step 4):** periodic **duplicate barcode audit** (export / pivot); integration imports must enforce uniqueness at source.

**Cross-reference:** **Architecture hardening H-05** at document top.

### 5.5 Internal reference strategy

Pattern:

`{CAT}-{TYPE}-{SEQ}`

Examples: `WF-DRS-001`, `MF-SHIRT-010`, `AC-SUN-004`

- **Never** reuse internal reference across variants; append `-{COLOR}-{SIZE}` if policy prefers flat codes (choose **one** convention during implementation).

### 5.6 Costing policy

- **Demo / approved:** **AVCO** at **product category** level (or product template level per Odoo 19 model).  
- **Production:** re-confirm AVCO **before first stock move** (irreversible choice cost).

### 5.7 Tax assignment strategy

- **Default customer taxes** on products: UAE **5% standard VAT** where applicable.  
- **Zero-rated / exempt:** limited SKUs + fiscal positions for qualifying B2B/export scenarios — **do not** overload POS cashier with manual tax selection; use **fiscal positions** on partners where possible.

### 5.8 Fashion retail considerations

- Seasonality: use **product tags** or **seasonal pricelists** (implementation), not duplicate SKUs.  
- Size curves: enforce **attribute value lists** to prevent “Size=Free text”.  
- Markdowns: prefer **pricelists / promotions** over editing sale price on template (auditability).

### 5.9 Future scalability (architecture must not require redesign)

The following capabilities must be absorbable **without structural redesign** (only **configuration + optional native apps + standard integrations**):

| Future capability | How current architecture already fits |
|---|---|
| **Loyalty** | Single company + `pos_loyalty` / `sale_loyalty` style native apps; anonymous POS customer still valid; identified customers optional |
| **Gift cards** | Shared POS journals + optional `POS-GIFT`; no per-branch journal explosion |
| **Franchise-style branches** | New POS config + `POS/{branch}` location + analytic account per site; if future **legal** franchise is a separate LLC, that is a **new company** decision — out of Phase 1 scope but does not break current naming |
| **BI tools** | Analytic-disciplined facts export cleanly to spreadsheet / warehouse / ODBC; no reliance on hand-maintained Excel mappings |
| **Mobile apps / POS mobility** | Native Odoo POS in browser + enterprise mobile assets; no custom asset pipeline assumed |

**Baseline:** New branch = **POS + location + analytic**; new channel = **sales team + analytic**; products remain centralized.

**Cross-reference:** **Architecture hardening H-12** at document top.

### 5.10 Inventory valuation impact

- AVCO rolls purchase costs into average unit cost; **branch transfers** do not change company-wide inventory value — only **location** of stock.  
- **Incorrect category costing method** misstates margin — finance owns category template.

### 5.11 Product lifecycle policy — Active / Archived; never delete

**Policy:**

- Products use lifecycle states **Active** (sellable / visible per rules) and **Archived** (not offered, hidden from default searches).  
- **Never delete** product records once **any** inventory move, POS order line, invoice line, or BOM reference exists — **archive** instead.

**Reason:** Deletion breaks **audit trail**, **historical reporting**, **warranty/returns lookup**, and **tax** reconstruction.

**Cross-reference:** **Architecture hardening H-06** at document top.

---

## 6. Customer & Vendor Master Strategy

### 6.1 B2B customers (Corporate Sales)

- **Full company records** with TRN, invoice address, payment terms, credit limit, pricelist, salesperson, fiscal position.  
- **One commercial entity per legal customer**; use **contacts/addresses** for branches.

### 6.2 POS anonymous customer

- **Design:** Single generic partner (e.g. `POS Walk-in Customer`) for anonymous retail sales.  
- **Why operationally necessary:** Majority of POS transactions have **no** identifiable customer; forcing customer lookup **slows checkout**, increases errors, and creates **dirty master data** (duplicate “John” contacts).  
- **Trade-off:** Limited per-walk-in CRM; loyalty handled later via **Loyalty** app if required (out of Step 3 execution scope).

### 6.3 eCommerce customers

- **B2C:** portal/guest customers auto-created or consolidated per policy; avoid duplicate emails via **merge** tools when duplicates appear.  
- **B2B portal:** dedicated company contacts with credit terms and portal users.

### 6.4 Credit customers

- Credit only on **explicit B2B** partners with approved limits — **not** on walk-in POS customer.

### 6.5 Vendor grouping

- Use **supplier categories / tags** (e.g. `VEND-APPAREL`, `VEND-LOGISTICS`, `VEND-MARKETING`) for spend analytics.  
- **Payment terms** per vendor; bank accounts for batch payments where used.

### 6.6 Duplication prevention

- Enforce **TRN / VAT ID** uniqueness discipline (manual process + periodic duplicate search).  
- **Merge partners** tool for eCommerce duplicates.  
- Naming standard for `Child Company c/o Parent` addresses when needed.

---

## 7. Financial Structure Design

### 7.1 Journal strategy (minimize)

| Journal | Type | Scope |
|---|---|---|
| `INV-CUST` | Sales | Customer invoices (can be one or split by team — **prefer one** unless statutory need) |
| `INV-CUST-ECOM` *(optional)* | Sales | Only if finance insists separate invoice sequence for eCommerce — **not required** if analytic is reliable |
| `POS-CASH-AED` | Cash | All branches — cash tender |
| `POS-VISA` | Bank | Card tender — Visa clearing |
| `POS-MC` | Bank | Card tender — Mastercard clearing |
| `POS-GIFT` | Cash/Bank | If gift cards activated |
| `BNK-MAIN` | Bank | Primary operating bank (e.g. Emirates NBD) |
| `BNK-STRIPE-SETTLE` | Bank | **Acquirer settlement** mirror (recommended for clean matching) |
| `MISC` / `EXCH` | Miscellaneous | Rare manual entries — tightly permissioned |

### 7.2 Payment journal strategy

- **Customer payments** recorded against **bank** or **undeposited funds** model per policy.  
- **POS:** session closes into **POS journals**; later **bank statement** lines represent deposits and card batches.

### 7.3 Bank journal philosophy

- **One bank journal per real bank account** — mirrors bank statements 1:1.  
- Do **not** create bank journals per branch for the same physical account.

### 7.4 POS journal structure

- **Minimize:** cash + one card journal per scheme **or** consolidate if bank reports combined card deposits.  
- **Never** multiply journals per branch.

### 7.5 Acquirer journal structure

- Use a **clearing** approach: online charges hit a **Stripe/suspense** journal, then **settlement** moves to `BNK-MAIN`.  
- Prevents eCommerce order noise from polluting the main bank rec.

### 7.6 Receivable / payable

- **Single AR control account** per company (standard) unless localization mandates split — UAE typically **one**.  
- **AP** similarly centralized.

### 7.7 Reconciliation philosophy

- **Bank journals:** reconcile **often** (weekly in ops-heavy retail).  
- **Acquirer:** reconcile **settlement batches** to order-level entries.  
- **POS cash:** reconcile **session closing** to **physical deposit** lines.

### 7.8 Why journal minimization matters

| Problem with too many journals | Effect |
|---|---|
| Statement lines split unpredictably | Low auto-match % |
| User selects wrong journal | Misclassified revenue, VAT noise |
| Month-end review takes longer | CFO distrust |

### 7.9 Accounting governance — manual entries to revenue accounts

**Policy:** Manual **journal entries** that post to **revenue / income accounts** (including reclassification into revenue) are restricted to **Finance Manager** (or a formally delegated **Financial Controller** user), **not** to Finance Officer or operations roles.

**Reason:** Prevents **silent revenue manipulation**, VAT mis-declaration, and broken channel analytics.

**Native lever (Step 4):** Odoo **account groups / security** on journals and sensitive accounts; prefer **reversing documented corrections** over ad-hoc revenue postings.

**Cross-reference:** **Architecture hardening H-08** at document top.

---

## 8. Tax Structure Design

### 8.1 UAE VAT handling (native)

- Install and retain **`l10n_ae`** + **`l10n_ae_reports`**.  
- Use localization tax templates for **standard 5%**, **zero-rated**, **exempt** as per UAE rules.

### 8.2 Standard VAT

- **5%** on taxable supplies — default on B2C/B2B domestic retail and corporate sales where applicable.

### 8.3 Zero-rated

- For qualifying supplies per UAE law — assign via **fiscal position** or specific product fiscal classification — **not** cashier discretion at POS.

### 8.4 Exempt

- Narrow categories only; same rule — **automation via fiscal positions**.

### 8.5 POS tax behavior

- POS uses **product default taxes** + **fiscal positions** when B2B invoicing from POS.  
- Train cashiers **not** to manually change tax unless explicit SOP exception.

### 8.6 Tax-inclusive vs tax-exclusive policy

| Context | Recommendation |
|---|---|
| **B2B quotes / corporate** | Typically **tax-exclusive** display + clear VAT lines (business norm UAE) |
| **B2C POS / shelf** | Often **tax-inclusive** display for consumer clarity — configure POS/website display accordingly |
| **Risk** | Mixing modes without clear product/website configuration causes **1 fils** rounding disputes — align pricelist and display settings in implementation |

---

## 9. Naming Conventions Standard

**Objective:** Prevent operational chaos across 30 branches, finance, and analytics.

### 9.1 POS

`POS-{REGION}-{NNN} | {Public Shop Name}`

Example: `POS-DXB-N-001 | Dubai Mall`

### 9.2 Warehouses

`WH-{COMPANY}-{ROLE}`

Example: `WH-HRG-MAIN`

### 9.3 Locations

`WH-HRG-MAIN/{FUNCTION}/{DETAIL}`

Examples: `.../POS/DXB-N-001-DUBAI-MALL`, `.../ECOM-OUT`, `.../RET-ECOM`, `.../LOSS-DAMAGE`

### 9.4 Journals

`{DOMAIN}-{TYPE}-{DETAIL}`

Examples: `POS-CASH-AED`, `BNK-MAIN`, `BNK-STRIPE-SETTLE`

### 9.5 Analytics

- Channel: `AN-CH-{SALES|ECOM|POS}`  
- POS branch: `AN-POS-{REGION}-{NNN}-{SHORT}`  
- Department: `AN-DPT-{CODE}`

### 9.6 Products

- Category codes: `CAT-*`  
- Internal reference: `WF-*`, `MF-*`, `AC-*`, `CG-*` (per blueprint style)

### 9.7 Sales teams

`ST-{SEGMENT}-{AREA}`

Examples: `ST-CORP-UAE-N`, `ST-ECOM`

### 9.8 Naming governance — English-safe, system-safe codes

**Policy:**

- **Operational codes** (POS codes, warehouse/location path segments, journal short codes, analytic codes, internal references, reason codes) must remain **English ASCII-safe** (letters, digits, hyphen) and **stable** across releases.  
- **Display names** on records (shop name, product name, category name) may be **localized** (e.g. Arabic) for staff and customers, but **must not** be the only carrier of identity — reports, APIs, and integrations key off **codes + IDs**.

**Reason:** Prevents **encoding issues**, **broken exports**, **unstable URLs**, and **integration failures** when BI or mobile tools assume Latin identifiers.

**Cross-reference:** **Architecture hardening H-11** at document top.

---

## 10. Risks & Anti-Patterns

### 10.1 Dangerous implementation mistakes

| Mistake | Why dangerous |
|---|---|
| Loading Odoo sample industry demo data | Pollutes controlled demo dataset; breaks UAT scenarios |
| Creating **30 warehouses** | Operational and reporting debt |
| **Per-branch POS journals** for each payment type | Reconciliation gridlock |
| Letting cashiers pick tax manually | VAT compliance + audit risk |
| Enabling production **LIVE** payment keys in demo | Financial and compliance exposure |
| **Negative stock allowed** in sellable locations | AVCO + multi-channel **financial distortion**; audit risk |
| **Duplicate barcodes** | Wrong picks, wrong COGS, POS blocking |
| **Deleting** products post-transaction | Broken history and audit |
| **Open POS sessions overnight** without escalation | Cash control and reconciliation failure |
| **Manual revenue JEs** by non-authorized roles | Fraud and misstated channel P&L |

### 10.2 Scalability traps

| Trap | Outcome |
|---|---|
| SKU sprawl without attributes | Unmaintainable variant matrix in Excel |
| Ad-hoc analytic accounts per user | Non-comparable management reports |
| Duplicate vendors/customers | Broken AR/AP and wrong statements |

### 10.3 Reporting traps

| Trap | Outcome |
|---|---|
| Revenue recognized without aligned COGS analytic | “Fake margin” by channel |
| **Missing analytic on revenue-impacting lines** | **Reporting failure** per §2.7 / H-07; channel P&L not trustworthy |
| Using **company** field to mimic branches | Wrong architecture; breaks single-LLC assumption |
| Saved filters referencing obsolete account codes | Silent wrong numbers after CoA tweak |

### 10.4 Reconciliation traps

| Trap | Outcome |
|---|---|
| Card deposits matched to wrong journal | Unreconciled residuals forever |
| Stripe gross vs net mismatch | Mystery differences each month |
| POS cash not deposited daily | Bank rec drift and fraud risk |

### 10.5 Inventory architecture mistakes

| Mistake | Outcome |
|---|---|
| Selling from **Stock** location at POS | Branch availability wrong |
| Returns straight to sellable without QC | Shrink and customer complaints |
| Ignoring internal transfer lead time | Stockouts despite “system shows stock” |
| **Mixing returns into LOSS-DAMAGE** | Broken return-rate vs shrink reporting |
| **Adjustments without reason codes** | No audit defense |

### 10.6 What NOT to do (summary)

- Do **not** use multi-company for internal channels.  
- Do **not** explode journals per branch.  
- Do **not** create products before variant policy is frozen.  
- Do **not** mix demo TRN into production.  
- Do **not** customize Python for reporting that analytic + native pivots solve.  
- Do **not** allow **negative stock** in production sellable paths (see §3.10).  
- Do **not** leave **POS sessions open overnight** without escalation (see §4.12).  
- Do **not** bypass **RET-*** vs **LOSS-DAMAGE** separation (see §3.2).

---

## 11. Final Recommendation

| Criterion | Assessment |
|---|---|
| **Scalable** | **Yes** — adding branches, SKUs, or channels maps to **new POS configs + locations + analytics**, not structural rewrites. |
| **Maintainable** | **Yes** — minimal journals, single warehouse, standard UAE localization, native apps only. |
| **Native-compatible** | **Yes** — design uses Odoo 19 Enterprise primitives: analytic plans, stock locations, POS configs, sales teams, fiscal positions, standard tax reports. |
| **Enterprise-safe** | **Yes** — segregation intent via roles (implementation phase), audit trails via posted documents, controlled demo data discipline, **hardening policies H-01–H-12** for production-grade controls. |

### 11.2 Future scalability confirmation

The architecture explicitly supports **loyalty**, **gift cards**, **additional branches (including franchise-style operations at data level)**, **external BI**, and **mobile POS clients** through **native apps + stable codes + analytic segmentation** (see **§5.9**). No redesign of warehouse, journal minimization, or single-company model is required for those extensions.

**Verdict:** Proceed to **Step 4 (implementation)** only after human approval of this document (including hardening) and confirmation that **Step 2 execution evidence** is complete.

---

> **STOP — Step 4 is not authorized from this chat. Awaiting human approval.**

---

*Step 3 — Enterprise Master Data & Operational Structure (Planning Only) | Horizon Retail Group LLC | Odoo 19 Enterprise | May 2026*
