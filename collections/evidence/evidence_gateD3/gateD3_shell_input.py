# Gate D3 — reconciliation REVIEW only (no writes, no new sales, no stock changes).
# Validates D2 POS orders/sessions/moves/taxes/payments against manifest + ORM checks.

import json
from pathlib import Path

from odoo.tools import float_compare, float_is_zero

for LOG, MAN_D2, MAN_D3 in (
    (
        Path("/home/sabry3/sabry_backup/odoo_base/base_odoo_19/projects/demo_pos_accounting/evidence_gateD3/gateD3_shell.txt"),
        Path("/home/sabry3/sabry_backup/odoo_base/base_odoo_19/projects/demo_pos_accounting/evidence_gateD2/gateD2_manifest.json"),
        Path("/home/sabry3/sabry_backup/odoo_base/base_odoo_19/projects/demo_pos_accounting/evidence_gateD3/gateD3_review_manifest.json"),
    ),
    (
        Path("/mnt/sabry_backup/odoo_base/base_odoo_19/projects/demo_pos_accounting/evidence_gateD3/gateD3_shell.txt"),
        Path("/mnt/sabry_backup/odoo_base/base_odoo_19/projects/demo_pos_accounting/evidence_gateD2/gateD2_manifest.json"),
        Path("/mnt/sabry_backup/odoo_base/base_odoo_19/projects/demo_pos_accounting/evidence_gateD3/gateD3_review_manifest.json"),
    ),
):
    if LOG.parent.is_dir():
        break
else:
    LOG = Path("gateD3_shell.txt")
    MAN_D2 = Path("evidence_gateD2/gateD2_manifest.json")
    MAN_D3 = Path("gateD3_review_manifest.json")

lines = []


def log(msg):
    lines.append(msg)
    print(msg)


if not MAN_D2.is_file():
    raise RuntimeError(f"Missing D2 manifest: {MAN_D2}")

d2 = json.loads(MAN_D2.read_text(encoding="utf-8"))
oids = d2["pos_order_ids"]
sid_dxb = d2["pos_session_ids"]["POS-DXB-01"]
sid_auh = d2["pos_session_ids"]["POS-AUH-01"]
mv_dxb = d2["session_account_move_ids"]["POS-DXB-01"]
mv_auh = d2["session_account_move_ids"]["POS-AUH-01"]
picks = d2["stock_picking_ids"]

PO = env["pos.order"].sudo()
Sess = env["pos.session"].sudo()
AM = env["account.move"].sudo()
AML = env["account.move.line"].sudo()
Pay = env["pos.payment"].sudo()
SM = env["stock.move"].sudo()
SP = env["stock.picking"].sudo()
Quant = env["stock.quant"].sudo()
PP = env["product.product"].sudo()

orders = PO.browse(oids)
if len(orders) != 3 or any(not o.exists() for o in orders):
    raise RuntimeError("D2 pos_order ids missing")
for o in orders:
    if o.state != "done":
        raise RuntimeError(f"Order {o.id} state={o.state!r} expected done")
log(f"POS_ORDERS_OK ids={oids} states=done")

tot_orders = sum(orders.mapped("amount_total"))
tot_tax = sum(orders.mapped("amount_tax"))
tot_paid = sum(orders.mapped("amount_paid"))
payments = orders.payment_ids
tot_pay = sum(payments.mapped("amount"))
log(f"POS_TOTALS amount_total={tot_orders} amount_tax={tot_tax} amount_paid={tot_paid} sum_payments={tot_pay}")
if float_compare(tot_orders, tot_paid, precision_rounding=orders[:1].currency_id.rounding):
    raise RuntimeError("Order totals vs amount_paid mismatch")
if float_compare(tot_orders, tot_pay, precision_rounding=orders[:1].currency_id.rounding):
    raise RuntimeError("Order totals vs sum(pos.payment) mismatch")

sess_dxb = Sess.browse(sid_dxb)
sess_auh = Sess.browse(sid_auh)
for s in (sess_dxb, sess_auh):
    if s.state != "closed":
        raise RuntimeError(f"Session {s.id} not closed: {s.state!r}")
    if not s.move_id or s.move_id.state != "posted":
        raise RuntimeError(f"Session {s.id} move missing or not posted")
    bal = sum(s.move_id.line_ids.mapped("balance"))
    if not float_is_zero(bal, precision_rounding=0.0001):
        raise RuntimeError(f"Session move {s.move_id.id} unbalanced: {bal}")
log(f"SESSIONS_OK dxb_move={sess_dxb.move_id.id} auh_move={sess_auh.move_id.id} balanced")

if sess_dxb.move_id.id != mv_dxb or sess_auh.move_id.id != mv_auh:
    raise RuntimeError("Manifest session move ids out of sync with database")

# Posted session + combine payment moves linked by ref to session name
combine = AM.search(
    [
        ("state", "=", "posted"),
        ("ref", "ilike", sess_dxb.name),
    ]
) | AM.search(
    [
        ("state", "=", "posted"),
        ("ref", "ilike", sess_auh.name),
    ]
)
stmt_moves = (sess_dxb.statement_line_ids | sess_auh.statement_line_ids).mapped("move_id").filtered(lambda m: m)
checked = sess_dxb.move_id | sess_auh.move_id | combine | stmt_moves
for m in checked:
    if m.state != "posted":
        continue
    b = sum(m.line_ids.mapped("balance"))
    if not float_is_zero(b, precision_rounding=0.0001):
        raise RuntimeError(f"Move {m.id} {m.name!r} unbalanced: {b}")
log(f"POSTED_MOVE_BALANCE_OK checked_moves={sorted(checked.ids)}")

# Orphan AML (no move)
orph = AML.search_count([("move_id", "=", False)])
if orph:
    raise RuntimeError(f"Orphan account.move.line count={orph}")

# Exactly one posted session move per session ref (main POSS entry)
for nm in (sess_dxb.name, sess_auh.name):
    c = AM.search_count([("ref", "=", nm), ("state", "=", "posted")])
    if c != 1:
        raise RuntimeError(f"Expected 1 posted move with ref={nm!r}, found {c}")
log("DUPLICATE_SESSION_MAIN_MOVE_CHECK_OK")

# Pickings
for pk in SP.browse(picks):
    if pk.state != "done":
        raise RuntimeError(f"Picking {pk.id} not done")
    if not pk.move_ids:
        raise RuntimeError(f"Picking {pk.id} has no stock moves")
log(f"PICKINGS_OK ids={picks}")

# Internal net stock for D2 SKUs
codes = ["RET-G2-BEV-WAT500", "RET-G2-SNK-CRP40", "RET-G2-PAR-TSH-M", "RET-G2-PAR-MUG350-BLA"]
for code in codes:
    p = PP.search([("default_code", "=", code)], limit=1)
    quants = Quant.search([("product_id", "=", p.id), ("location_id.usage", "=", "internal")])
    net = sum(quants.mapped("quantity"))
    if float_compare(net, 0.0, precision_rounding=1e-6) < 0:
        raise RuntimeError(f"Net negative internal for {code}: {net}")
    log(f"STOCK_NET_INTERNAL_OK {code}={net}")

# AVCO
for code in codes:
    p = PP.search([("default_code", "=", code)], limit=1)
    if p.categ_id.property_cost_method != "average":
        raise RuntimeError(f"{code} cost method {p.categ_id.property_cost_method!r}")

# Card combine moves exist for DXB session (aggregated bank payments)
visa_pay = sum(payments.filtered(lambda x: "Visa" in (x.payment_method_id.name or "")).mapped("amount"))
mc_pay = sum(payments.filtered(lambda x: "Mastercard" in (x.payment_method_id.name or "")).mapped("amount"))
visa_moves = AM.search([("name", "ilike", "PPVISA%"), ("ref", "ilike", sess_dxb.name)])
mc_moves = AM.search([("name", "ilike", "PMCARD%"), ("ref", "ilike", sess_dxb.name)])
if len(visa_moves) != 1 or len(mc_moves) != 1:
    raise RuntimeError(f"Expected single combine move for visa/mc, got {visa_moves.ids} {mc_moves.ids}")
log(f"PAY_COMBINE_LINKED visa_pay={visa_pay} mc_pay={mc_pay} visa_move={visa_moves.id} mc_move={mc_moves.id}")

# Build manifest for Playwright / SQL doc
cash_via_stmt = sorted(stmt_moves.ids)
log(f"CASH_STATEMENT_MOVES ids={cash_via_stmt}")

out = {
    **d2,
    "review_gate": "D3",
    "combine_move_ids": {"visa": visa_moves.id, "mastercard": mc_moves.id},
    "cash_statement_move_ids": cash_via_stmt,
    "journal_entry_urls": {
        "session_dxb": mv_dxb,
        "session_auh": mv_auh,
        "combine_visa": visa_moves.id,
        "combine_mc": mc_moves.id,
    },
    "ir_actions": {
        "accounting_entries": 292,
        "stock_valuation": 574,
        "stock_moves_analysis": 443,
        "pos_orders_analysis": 665,
        "sales_analysis": 679,
        "tax_return": 598,
    },
}
MAN_D3.parent.mkdir(parents=True, exist_ok=True)
MAN_D3.write_text(json.dumps(out, indent=2), encoding="utf-8")
log(f"WROTE {MAN_D3}")

log("REVIEW_COMPLETE_NO_DB_WRITES")
LOG.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"WROTE {LOG}")
