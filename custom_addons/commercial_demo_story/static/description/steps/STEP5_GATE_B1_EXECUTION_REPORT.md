# Step 5 Gate B1 Execution Report

> **Execution date:** 2026-05-13  
> **Scope:** Gate **B1 only** — company & accounting baseline, UAE localization checks, admin password rotation, validation-only POS labeling, screenshots, backups, git tag  
> **Explicitly NOT done:** Gate B2+ (no products, customers/vendors, analytics, warehouses, POS branches, journal redesign, payment gateways, email, imports, custom modules)

---

## 1. Exact executed actions

| # | Action | Command / path |
|---|--------|----------------|
| 1 | Extended `.gitignore` | `projects/demo_pos_accounting/.gitignore` — ignore `.gateB1_web_admin_password.txt` |
| 2 | Generated new internal **admin** password | `python3 -c "secrets.token_urlsafe(24)"` → `projects/demo_pos_accounting/.gateB1_web_admin_password.txt` (mode `600`, not committed) |
| 3 | Company & baseline updates + validations + password | `odoo-bin shell … < gateb1_shell_input.py` → transcript `evidence_gateB1/gateB1_shell.txt` |
| 4 | Recreated **single** POS config labeled validation-only | `odoo-bin shell …` → `evidence_gateB1/gateB1_pos_validation_only.txt` |
| 5 | Browser screenshots (Playwright) | `evidence_gateB1/gateB1_browser_capture.py` → `evidence_gateB1/screenshots/*.png` |
| 6 | Database backup | `pg_dump -Fc …` → `backups/gateB1_demo_pos_accounting_20260513.dump` |
| 7 | Filestore backup | `tar -czf …` → `backups/gateB1_filestore_20260513.tar.gz` |
| 8 | Git tag (after commit of evidence + report) | `step5_gateB1_baseline` |

---

## 2. Company verification / update

| Field | Target | Result |
|-------|--------|--------|
| Legal / company name | Horizon Retail Group LLC | `res.company.name` + `res.partner` (company partner) updated |
| Country | UAE | Partner `country_id` = AE (`base.ae`); company already had fiscal country AE |
| Currency | AED | `currency_id` = `base.AED` |
| TRN | 100345678900003 | Stored on company **partner** `vat` |
| Emirate (for domestic fiscal mapping) | Dubai | Partner `state_id` = Dubai (`DU`) |
| Fiscal year (calendar Jan–Dec) | End Dec 31 | `fiscalyear_last_month='12'`, `fiscalyear_last_day=31` (confirmed / enforced) |

Shell log line: `COMPANY Horizon Retail Group LLC AED 100345678900003 12 31`

---

## 3. Tax verification (UAE)

| Check | Result |
|-------|--------|
| Standard **5% VAT** (sale) | `TAX_SALE_5_COUNT` = **8** (emirate-specific 5% sale taxes + related) |
| **Zero-rated** (0% sale) | `TAX_SALE_0_COUNT` = **4** |
| **Exempt / out-of-scope** style labels | `TAX_EXEMPT_LIKE` includes **0% EX**, **0% EXT**, **Out of Scope** |
| **VAT201** tax report engine | `l10n_ae.tax_report`: `_get_lines` returned **24** rendered lines — **no traceback** |

---

## 4. Accounting baseline verification

| Check | Result |
|-------|--------|
| Chart of accounts | **177** `account.account` records linked to the company (`CHART_ACCOUNTS 177`) |
| Fiscal positions | **8** positions for the company (Dubai, Abu Dhabi, Sharjah, Ajman, Umm Al Quwain, Ras Al-Khaima, Fujairah, Non-UAE) |
| Accounting dashboard (UI) | Screenshot `01_accounting_dashboard.png` — client loaded without `pageerror` in capture harness |
| Broken reports / tracebacks | `grep Traceback / ' ERROR '` on `gateB1_shell.txt`: **no matches** |

---

## 5. Admin password rotation

- New password generated with `secrets.token_urlsafe(24)` and written to **`projects/demo_pos_accounting/.gateB1_web_admin_password.txt`** as `ADMIN_WEB_PW=…` (file mode **600**, **gitignored**).  
- Applied with `res.users` login **`admin`** via `write({'password': …})` in the same shell session as company updates.  
- **Operational note:** rotate `admin_passwd` in the Odoo config separately if you rotate the database manager password policy; that value was **not** changed in B1.

---

## 6. POS config (validation-only label)

- **Name set / created:** `VALIDATION ONLY – Gate A POS (not an operational branch)`  
- **Evidence:** `evidence_gateB1/gateB1_pos_validation_only.txt` (`CREATED_POS_CONFIG …`)  
- **Not in scope:** no operational POS branches, no shop hardware, no sessions opened for trading.

---

## 7. Screenshot paths

All under `projects/demo_pos_accounting/evidence_gateB1/screenshots/`:

| File | Content |
|------|---------|
| `01_accounting_dashboard.png` | Accounting dashboard (`/odoo/accounting`) |
| `02_taxes.png` | Taxes list (`/odoo/taxes`) |
| `03_tax_report_vat201.png` | VAT201 / Tax Return client (`/odoo/tax-report`) |
| `04_company_settings.png` | Settings (`/odoo/settings`) — company-related configuration shell |

---

## 8. Logs summary

| Log | Purpose |
|-----|---------|
| `evidence_gateB1/gateB1_shell.txt` | Full `odoo-bin shell` stdout for company/tax/report/POS rename/password |
| `evidence_gateB1/gateB1_pos_validation_only.txt` | Shell run creating the validation-only `pos.config` |
| `evidence_gateB1/gateb1_shell_input.py` | Repeatable shell script body (checked in for audit trail) |

---

## 9. Backup paths

| Artifact | Path |
|----------|------|
| PostgreSQL (custom format) | `projects/demo_pos_accounting/backups/gateB1_demo_pos_accounting_20260513.dump` |
| Filestore archive | `projects/demo_pos_accounting/backups/gateB1_filestore_20260513.tar.gz` |

*(Patterns `backups/*.dump` / `backups/*.tar.gz` are gitignored by project policy.)*

---

## 10. Git tag

- **Tag name:** `step5_gateB1_baseline`  
- **Points to:** commit that adds this report + Gate B1 evidence artifacts (see `git show step5_gateB1_baseline`).

---

## 11. Failures / fixes

| Issue | Resolution |
|-------|------------|
| Initial `pos.config` missing in DB (0 rows) so rename loop in first shell produced no output | Ran a **second** minimal shell to create **one** `pos.config` with the required **VALIDATION ONLY** name — documented here; does not constitute a POS branch program. |
| Earlier aborted shell attempt used a wrong bash heredoc/`tee` ordering (would hang) | **Not used** for final run; final execution uses **stdin file** redirection: `odoo-bin shell … < gateb1_shell_input.py`. |

---

## 12. Final status

### **PASSED**

Gate B1 objectives met within allowed scope; no Gate B2 work performed.

---

## 13. STOP

**Do not proceed to Gate B2** until separately authorized.
