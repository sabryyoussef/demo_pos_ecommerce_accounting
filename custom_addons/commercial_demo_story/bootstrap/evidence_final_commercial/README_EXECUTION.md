# Final commercial operations — execution order

Run from the **repository root** (directory containing `config/` and `projects/`), with PostgreSQL up and Odoo config `config/projects/odoo_demo_pos_accounting.conf`. Adjust the Python binary if your `venv19` lives elsewhere.

```bash
REPO=/path/to/base_odoo_19
cd "$REPO/odoo19/odoo19"
"$REPO/venv19/bin/python3" odoo-bin shell -c "$REPO/config/projects/odoo_demo_pos_accounting.conf" -d demo_pos_accounting --no-http < "$REPO/projects/demo_pos_accounting/evidence_final_commercial/phaseA_corporate_sales.py"
"$REPO/venv19/bin/python3" odoo-bin shell -c "$REPO/config/projects/odoo_demo_pos_accounting.conf" -d demo_pos_accounting --no-http < "$REPO/projects/demo_pos_accounting/evidence_final_commercial/phaseB_ecommerce_ops.py"
"$REPO/venv19/bin/python3" odoo-bin shell -c "$REPO/config/projects/odoo_demo_pos_accounting.conf" -d demo_pos_accounting --no-http < "$REPO/projects/demo_pos_accounting/evidence_final_commercial/phaseC_pos_30_locations.py"
"$REPO/venv19/bin/python3" odoo-bin shell -c "$REPO/config/projects/odoo_demo_pos_accounting.conf" -d demo_pos_accounting --no-http < "$REPO/projects/demo_pos_accounting/evidence_final_commercial/phaseC2_dxb_auh_second_cashier.py"
"$REPO/venv19/bin/python3" odoo-bin shell -c "$REPO/config/projects/odoo_demo_pos_accounting.conf" -d demo_pos_accounting --no-http < "$REPO/projects/demo_pos_accounting/evidence_final_commercial/phaseD_bank_reconciliation.py"
```

**Idempotency:** each phase uses `ir.config_parameter` flags under `demo_pos_accounting.final_phase_*` (see scripts).

**Rollback:** restore PostgreSQL dump taken before this phase; clear `ir.config_parameter` keys starting with `demo_pos_accounting.final_`.

**Passwords (demo only):** scripts set `FinalDemo2026!` for newly created internal users (`corp.sales.*`, `ecom.sales.coord`, `pos_ret**_*`). Change in production; do not commit secrets.
