# Gate D4 part 2 — complete website delivery pickings for test orders (evidence only).
# Run:  python3 odoo-bin shell -c <odoo_demo_pos_accounting.conf> -d demo_pos_accounting --no-http < gateD4_shell_part2_deliver.py
# Expects gateD4_browser_result.json with sale_order_name entries.

import json
from pathlib import Path

for p in (
    Path("/home/sabry3/sabry_backup/odoo_base/base_odoo_19/projects/demo_pos_accounting/evidence_gateD4/gateD4_browser_result.json"),
    Path("/mnt/sabry_backup/odoo_base/base_odoo_19/projects/demo_pos_accounting/evidence_gateD4/gateD4_browser_result.json"),
):
    if p.is_file():
        BR = p
        break
else:
    raise RuntimeError("gateD4_browser_result.json not found")

data = json.loads(BR.read_text(encoding="utf-8"))
names = [o["sale_order_name"] for o in data.get("orders", []) if o.get("sale_order_name")]
if not names:
    raise RuntimeError("No orders in browser result")

orders = env["sale.order"].sudo().search([("name", "in", names)])
if len(orders) != len(names):
    raise RuntimeError(f"Expected {len(names)} sale orders, found {len(orders)}")

pickings = env["stock.picking"].sudo().search([("sale_id", "in", orders.ids)])
print(f"PICKINGS_FOUND ids={pickings.ids} states={pickings.mapped('state')}")

for p in pickings:
    if p.state in ("done", "cancel"):
        print(f"SKIP picking id={p.id} state={p.state}")
        continue
    for move in p.move_ids:
        for ml in move.move_line_ids:
            ml.write({"quantity": move.product_uom_qty, "picked": True})
    p.with_context(skip_sms=True).button_validate()
    print(f"DONE_PICKING id={p.id} name={p.name!r} state={p.state}")

env.cr.commit()
print("COMMIT_OK_PART2_DELIVERY")
