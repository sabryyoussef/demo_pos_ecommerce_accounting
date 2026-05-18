# Demo scenario — 1 admin, 5 POS employees (no user), 5 locations

**Database:** `demo_pos_accounting`  
**Config file:** `config/projects/odoo_demo_pos_accounting.conf`  
**HTTP port (config):** `8025` → http://127.0.0.1:8025  
**Note:** Port `7025` is not active on this machine; Odoo responds on **8025**.

**Company:** Horizon Retail Group (UAE, AED)  
**Prepared:** 2026-05-18 — audit of existing data + recommended focused demo path.  
**Phase I bootstrap:** 2026-05-18 — `commercial_demo_story/scripts/phaseI_five_cashiers_demo.py` (idempotent).

---

## 1. Story you present (5–7 minutes)

| Role | Who | How they work |
|------|-----|----------------|
| **Admin / supervisor** | `admin` (or `pos.manager`) | Logs into **Odoo backend** — does **not** use the POS till. Reviews sales by shop and by cashier. |
| **Cashier 1–5** | Five **HR employees only** (no login user) | Open **POS front-end** at **five different shops**, select their name, enter **PIN**, sell, close session. |

**Message for the audience:**  
One manager, five shops, five cashiers identified only on the till (PIN). All sales roll up to the same company; the admin sees **who** sold **where**.

---

## 2. Target demo cast (to create or align)

| # | Employee name (HR) | Employee ID | PIN | POS location | Config ID | Region |
|---|-------------------|-------------|-----|--------------|-----------|--------|
| 1 | **Demo Cashier — Dubai Flagship** | 92 | `3001` | POS-DXB-01 | 5 | Dubai |
| 2 | **Demo Cashier — Dubai Hills** | 93 | `3002` | POS-RET-04 (Dubai Hills Mall) | 8 | Dubai |
| 3 | **Demo Cashier — Abu Dhabi Mall** | 94 | `3003` | POS-RET-11 (Abu Dhabi Mall) | 15 | Abu Dhabi |
| 4 | **Demo Cashier — Sharjah City Centre** | 95 | `3004` | POS-RET-16 (Sharjah City Centre) | 20 | Northern UAE |
| 5 | **Demo Cashier — Madinat Jumeirah** | 96 | `3005` | POS-RET-24 (Madinat Jumeirah) | 28 | Abu Dhabi |

**Admin**

| Login | Password | Purpose |
|-------|----------|---------|
| `admin` | *(from `.gateB1_web_admin_password.txt` or your install)* | Full backend — Commercial Demo dashboard, all reports |
| `pos.manager` | `FinalDemo2026!` | POS-focused manager (optional second admin persona) |

**Rule:** The five cashiers must **not** have a linked `res.users` record — only `hr.employee` with `pin` set, assigned on each `pos.config` under **Employees**.

---

## 3. Database audit — what is already there (2026-05-18)

Checked via Odoo shell on `demo_pos_accounting`.

### 3.1 Infrastructure — present

| Item | Status | Detail |
|------|--------|--------|
| Database | OK | `demo_pos_accounting` loads, 306 modules |
| POS configs | OK | **390** shops (`POS-DXB-01`, `POS-AUH-01`, `POS-RET-03` … `POS-RET-390`) |
| POS HR on configs | OK | `module_pos_hr = True` on sampled configs |
| Paid POS orders | OK | **417** orders in `paid` / `done` / `invoiced` |
| Orders with cashier | OK | **414** have `employee_id` set |
| Regional CRM teams | OK | POS — Dubai / Abu Dhabi / Northern UAE |
| Commercial Demo module | OK | Dashboard, bootstrap scripts, Build Story |

### 3.2 Users — present but **not** matching “5 employees only”

There are **70+** POS-related **users** (`pos.cashier.*`, `pos.pool.cashier00–07`, `pos_ret03_a`, etc.).  
Each pool cashier has **both** a user login **and** an employee with PIN — that is a **user + employee** model, not “employee only”.

| Pattern | Count (approx.) | Fits this scenario? |
|---------|-----------------|---------------------|
| `admin` | 1 | Yes — admin |
| `pos.manager` | 1 | Yes — optional POS admin |
| `pos.pool.cashier00–07` | 8 | No — have user accounts |
| `pos.cashier.dxb` / `pos_retXX_a` | Many | No — have user accounts |
| Regional managers (`pos.regional.*`) | 3 | No — management layer |

### 3.3 Employees — partially present

| Pattern | Count | Fits this scenario? |
|---------|-------|---------------------|
| Employees with PIN | **84** | Many exist |
| Employees with PIN **and no user** | **12** | Cluster managers only (`Cluster Manager DXB 1` …) — wrong job title for cashiers |
| Dedicated “Demo Cashier — …” (5 names) | **5** (ids 92–96) | **Created** by Phase I — `user_id` empty, PIN 3001–3005 |

### 3.4 Five proposed locations — configs exist, wrong cashiers assigned

| POS config | Exists | Current cashiers on config (sample) |
|------------|--------|-------------------------------------|
| POS-DXB-01 | Yes | **Minimal:** Demo Cashier — Dubai Flagship only (PIN login). Advanced still includes PoS Managers (Odoo core). |
| POS-RET-04 | Yes | **Minimal:** Demo Cashier — Dubai Hills only |
| POS-RET-11 | Yes | **Minimal:** Demo Cashier — Abu Dhabi Mall only |
| POS-RET-16 | Yes | **Minimal:** Demo Cashier — Sharjah City Centre only |
| POS-RET-24 | Yes | **Minimal:** Demo Cashier — Madinat Jumeirah only |

### 3.5 Gap summary

| Requirement | In DB today? | Action |
|-------------|--------------|--------|
| 1 admin sees consolidated results | Yes | Use `admin` + Commercial Demo dashboard / POS reporting |
| 5 employees **without** user | **Yes** (Phase I) | Employees 92–96, all `user_id` false |
| 5 different POS places | Yes | Use table in §2 |
| One paid ticket per cashier today (clean story) | **Yes** (Phase I) | 5 paid orders `DEMO-PHASEI-*` (ids 439–443) |
| Isolated from 390-shop noise | Partially | PIN screen shows **one** demo cashier per shop; advanced list still has regional PoS managers (core `pos_hr`) |

---

## 4. Demo presentation (client walkthrough)

| Where | What |
|-------|------|
| **Demo Presentation** (recommended) | Commercial Demo → **Demo Presentation** — 5–10 min client page (PIN cashiers near top). Odoo: `/odoo/action-<id>/1` (see `action_commercial_demo_presentation`). Static: `/commercial_demo_story/static/description/presentation.html` |
| **Commercial Demo Dashboard** | **Presentation — PIN cashiers** block + **Open POS** buttons |
| **Build Story Gallery** | Technical evidence only — `/odoo/action-799/1` (unchanged) |

Use **Demo Presentation** for clients; **Build Story** for auditors and implementation proof.

---

## 5. Recommended demo flow (live)

### Step A — Admin opens the day (backend)

1. Login: http://127.0.0.1:8025/web/login?db=demo_pos_accounting as **`admin`**.
2. Open **Commercial Demo → Demo Dashboard** (or **POS and Accounting Prep → Commercial demo hub**).
3. Note KPIs: POS order count, top POS location, top cashier (after data load).
4. Optional: **Point of Sale → Reporting → Sales Details** — group by **Point of Sale** and **Employee**.

### Step B — Five cashiers at five shops (POS UI)

For each row in §2:

1. Open POS: `http://127.0.0.1:8025/pos/ui?config_id=<config_id>`  
   (or **Point of Sale → Open POS** and pick the shop).
2. **No Odoo user login** for the cashier — use **employee selection + PIN** on the POS login screen.
3. Sell 2–3 items (e.g. water, snack, accessory).
4. **Close session** (or leave open for admin to show open sessions — your choice).

| Shop | Config ID (current DB) | POS UI URL |
|------|------------------------|------------|
| POS-DXB-01 | 5 | http://127.0.0.1:8025/pos/ui?config_id=5 |
| POS-RET-04 | 8 | http://127.0.0.1:8025/pos/ui?config_id=8 |
| POS-RET-11 | 15 | http://127.0.0.1:8025/pos/ui?config_id=15 |
| POS-RET-16 | 20 | http://127.0.0.1:8025/pos/ui?config_id=20 |
| POS-RET-24 | 28 | http://127.0.0.1:8025/pos/ui?config_id=28 |

*(Verify IDs after DB restore — run SQL below if configs were recreated.)*

### Step C — Admin reviews results

1. **Point of Sale → Orders** — filter by today; column **Employee**.
2. **Point of Sale → Reporting → Sales Details** — measures: amount; rows: Employee + Point of Sale.
3. **Commercial Demo Dashboard** — refresh KPIs: top cashier, top location.
4. Optional: **POS regional targets** menu — team POS sales vs target (if Phase G2 loaded).

---

## 6. Implementation checklist (Phase I — 2026-05-18)

| Item | Status | Notes |
|------|--------|-------|
| Create 5 `hr.employee` (PIN only, no user) | **Done** | ids 92–96; flags `demo_pos_accounting.phase_i_five_cashiers_done` |
| Assign each cashier to one `pos.config` (minimal employees) | **Done** | configs 5, 8, 15, 20, 28; `module_pos_hr` enabled |
| One paid sample order per cashier | **Done** | `floating_order_name` `DEMO-PHASEI-POS-*`; flag `phase_i_five_cashiers_orders_done` |
| ORM verification (no user_id, config assignment) | **Done** | see `docs/phaseI_five_cashiers_shell.txt` |
| Port 8025 active (not 7025) | **Done** | HTTP 200 on 8025; 7025 unreachable |
| Safe admin group audit (`group_ids` / `_fields`) | **Done** | no `groups_id` crash |
| Confirm `admin` password in secure note | **Skipped** | not stored in repo (use install / `.gateB1_web_admin_password.txt`) |
| Playwright / Build Story screenshots | **Skipped** | explicitly out of scope for this task |

**Re-run bootstrap:**

```bash
cd odoo19/odoo19
python3 odoo-bin shell -c ../../config/projects/odoo_demo_pos_accounting.conf \
  -d demo_pos_accounting --no-http \
  < ../../projects/demo_pos_accounting/custom_addons/commercial_demo_story/scripts/phaseI_five_cashiers_demo.py
```

To force a full re-run, clear `ir.config_parameter` keys `demo_pos_accounting.phase_i_five_cashiers_done` and `demo_pos_accounting.phase_i_five_cashiers_orders_done` (employees/orders are idempotent by name/ref).

---

## 7. SQL quick checks (PostgreSQL)

```sql
-- POS configs for the five shops
SELECT id, name FROM pos_config
WHERE name IN ('POS-DXB-01','POS-RET-04','POS-RET-11','POS-RET-16','POS-RET-24')
ORDER BY name;

-- Demo employees (after creation)
SELECT id, name, pin, user_id FROM hr_employee
WHERE name LIKE 'Demo Cashier%';

-- Today's sales by employee and config
SELECT e.name AS cashier, c.name AS shop, COUNT(*) AS orders, SUM(o.amount_total) AS total
FROM pos_order o
JOIN hr_employee e ON e.id = o.employee_id
JOIN pos_session s ON s.id = o.session_id
JOIN pos_config c ON c.id = s.config_id
WHERE o.state IN ('paid','done','invoiced')
GROUP BY e.name, c.name
ORDER BY c.name;
```

---

## 8. Relation to existing bootstrap (commercial_demo_story)

| Existing phase | Relevance to this scenario |
|----------------|----------------------------|
| Phase F (`phaseF_pos_sales_hierarchy.py`) | Created 390 configs, regional teams, pool cashiers **with users** — overlaps but not the same cast |
| Phase C scale | Bulk orders across all shops — good for volume, noisy for “5 cashier” story |
| Phase G / G2 | Team targets — admin can show after cashier demo |
| Phase H / H2 | Kitchen / table prep — optional add-on at **POS-DXB-01** only |
| **Phase I** (`scripts/phaseI_five_cashiers_demo.py`) | **This scenario** — 5 PIN-only employees, 5 configs, 5 sample paid orders |

**Recommendation:** Treat this document as a **focused presentation layer** on top of the existing database. Phase I does not delete the 390-shop dataset.

### Phase I terminal summary (last run)

```
Employees: 92–96 created/updated, user_id=False, PINs 3001–3005
Configs: minimal_employee_ids = one demo cashier each (5, 8, 15, 20, 28)
Orders: DEMO-PHASEI-POS-DXB-01 (439) … POS-RET-24 (443) — all paid
POS-DXB-01 session left open (3 draft table orders from Phase H2 — not closed to avoid data loss)
Port: 8025 OK, 7025 down
```

---

## 9. Decision log

| Question | Decision |
|----------|----------|
| Port 7025 vs 8025? | Use **8025** per `odoo_demo_pos_accounting.conf`; fix firewall/bookmark if you used 7025. |
| Admin account? | **`admin`** primary; **`pos.manager`** optional POS-only admin. |
| Cashiers as users? | **No** — employee + PIN only for this scenario. |
| How many locations? | **5** distinct malls / flagship (see §2). |
| Rebuild whole DB? | **Not required** — add 5 employees + config assignment only. |

---

*Next step (optional): Playwright captures for Build Story “5 cashiers / 5 locations”; Commercial Demo dashboard deep-links to the five POS UI URLs.*
