# Gate D2 — controlled POS sales (1–3 orders), POS-DXB-01 + POS-AUH-01, RET-G2 stock, mixed payments.
# Uses admin env (open_ui / sessions). No refunds, no invoices, no mass sales.

import json
from pathlib import Path

from odoo import Command, fields
from odoo import api as odoo_api
from odoo.tools import float_compare, float_is_zero

for LOG, MAN in (
    (
        Path("/home/sabry3/sabry_backup/odoo_base/base_odoo_19/projects/demo_pos_accounting/evidence_gateD2/gateD2_shell.txt"),
        Path("/home/sabry3/sabry_backup/odoo_base/base_odoo_19/projects/demo_pos_accounting/evidence_gateD2/gateD2_manifest.json"),
    ),
    (
        Path("/mnt/sabry_backup/odoo_base/base_odoo_19/projects/demo_pos_accounting/evidence_gateD2/gateD2_shell.txt"),
        Path("/mnt/sabry_backup/odoo_base/base_odoo_19/projects/demo_pos_accounting/evidence_gateD2/gateD2_manifest.json"),
    ),
):
    if LOG.parent.is_dir():
        break
else:
    LOG = Path("gateD2_shell.txt")
    MAN = Path("gateD2_manifest.json")

lines = []


def log(msg):
    lines.append(msg)
    print(msg)


ICP = env["ir.config_parameter"].sudo()
FLAG = "demo_pos_accounting.gate_d2_pos_sales_done"
if ICP.get_param(FLAG) == "1":
    log("SKIP_ALREADY_DONE_ICP_FLAG")
    LOG.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"WROTE {LOG}")
    raise SystemExit(0)

admin = env.ref("base.user_admin")
adm = odoo_api.Environment(env.cr, admin.id, dict(env.context))

loc_stock = env["stock.location"].browse(5)
if not loc_stock.exists() or "HRG-MAIN/Stock" not in (loc_stock.complete_name or ""):
    raise RuntimeError(f"Expected WH-HRG-MAIN/Stock at id 5, got {loc_stock.complete_name!r}")

cfg_dxb = adm["pos.config"].search([("name", "=", "POS-DXB-01")], limit=1)
cfg_auh = adm["pos.config"].search([("name", "=", "POS-AUH-01")], limit=1)
if not cfg_dxb or not cfg_auh:
    raise RuntimeError("POS-DXB-01 or POS-AUH-01 not found")

# Resolve payment methods (names from demo setup)
cash_dxb = cfg_dxb.payment_method_ids.filtered(lambda p: p.type == "cash")[:1]
visa_dxb = cfg_dxb.payment_method_ids.filtered(lambda p: p.name and "Visa" in p.name)[:1]
mc_dxb = cfg_dxb.payment_method_ids.filtered(lambda p: p.name and "Mastercard" in p.name)[:1]
cash_auh = cfg_auh.payment_method_ids.filtered(lambda p: p.type == "cash")[:1]
if not cash_dxb or not visa_dxb or not mc_dxb or not cash_auh:
    raise RuntimeError(
        f"Missing payment methods: cash_dxb={cash_dxb.id} visa={visa_dxb.id} mc={mc_dxb.id} cash_auh={cash_auh.id}"
    )

PosOrder = adm["pos.order"].sudo()
Move = adm["stock.move"].sudo()
Quant = adm["stock.quant"].sudo()
AM = adm["account.move"].sudo()
PP = adm["product.product"].sudo()

po0 = PosOrder.search_count([])
sm0 = Move.search_count([])
am0 = AM.search_count([])

log(f"BASELINE pos_order={po0} stock_move={sm0} account_move={am0}")


def ensure_session(cfg):
    for s in cfg.session_ids.filtered(lambda x: x.state == "opening_control" and not x.order_ids):
        s.delete_opening_control_session()
    if not cfg.current_session_id:
        cfg.open_ui()
    sess = cfg.current_session_id
    if sess.state == "opening_control":
        sess.set_opening_control(0, "Gate D2 opening")
    if sess.state != "opened":
        raise RuntimeError(f"Session not opened: config={cfg.name!r} state={sess.state!r}")
    return sess


def create_paid_order(sess, line_specs, payments):
    """line_specs: list of (default_code, qty). payments: list of (payment_method_record, amount or None)."""
    cmds = []
    products = PP.browse(())
    for code, qty in line_specs:
        p = PP.search([("default_code", "=", code)], limit=1)
        if not p:
            raise RuntimeError(f"Missing product {code!r}")
        products |= p
        cmds.append(
            Command.create(
                {
                    "product_id": p.id,
                    "qty": qty,
                    "price_unit": p.lst_price,
                    "price_subtotal": p.lst_price * qty,
                    "tax_ids": [(6, 0, p.taxes_id.ids)],
                    "price_subtotal_incl": 0,
                }
            )
        )
    order = adm["pos.order"].create(
        {
            "amount_total": 0,
            "amount_paid": 0,
            "amount_tax": 0,
            "amount_return": 0,
            "date_order": fields.Datetime.to_string(fields.Datetime.now()),
            "company_id": adm.company.id,
            "session_id": sess.id,
            "lines": cmds,
        }
    )
    order.lines._onchange_amount_line_all()
    order._compute_prices()
    ctx = {"active_ids": order.ids, "active_id": order.id}
    for pm, amt in payments:
        vals = {"payment_method_id": pm.id}
        if amt is not None:
            vals["amount"] = amt
        w = adm["pos.make.payment"].with_context(**ctx).create(vals)
        w.with_context(**ctx).check()
    order.invalidate_recordset()
    if order.state != "paid":
        raise RuntimeError(f"Order not paid: {order.name!r} state={order.state!r}")
    return order, products


sess_dxb = ensure_session(cfg_dxb)
sess_auh = ensure_session(cfg_auh)
log(f"SESSION_OPEN dxb_id={sess_dxb.id} name={sess_dxb.name!r} auh_id={sess_auh.id} name={sess_auh.name!r}")

# --- Three controlled orders ---
# 1) DXB: beverage + snack, mixed cash + Visa
o1, prods1 = create_paid_order(
    sess_dxb,
    [("RET-G2-BEV-WAT500", 2), ("RET-G2-SNK-CRP40", 1)],
    [(cash_dxb, 3.0), (visa_dxb, None)],
)
log(
    f"ORDER_1_DXB_COMBO id={o1.id} name={o1.name!r} total={o1.amount_total} tax={o1.amount_tax} "
    f"payments={o1.payment_ids.mapped(lambda p: (p.payment_method_id.name, p.amount))} pickings={o1.picking_ids.ids}"
)

# 2) AUH: apparel variant M, full cash AUH
o2, prods2 = create_paid_order(sess_auh, [("RET-G2-PAR-TSH-M", 1)], [(cash_auh, None)])
log(
    f"ORDER_2_AUH_APPAREL id={o2.id} name={o2.name!r} total={o2.amount_total} tax={o2.amount_tax} "
    f"payments={o2.payment_ids.mapped(lambda p: (p.payment_method_id.name, p.amount))} pickings={o2.picking_ids.ids}"
)

# 3) DXB: mug variant Black, Mastercard single pay
o3, prods3 = create_paid_order(sess_dxb, [("RET-G2-PAR-MUG350-BLA", 1)], [(mc_dxb, None)])
log(
    f"ORDER_3_DXB_MUG id={o3.id} name={o3.name!r} total={o3.amount_total} tax={o3.amount_tax} "
    f"payments={o3.payment_ids.mapped(lambda p: (p.payment_method_id.name, p.amount))} pickings={o3.picking_ids.ids}"
)

# --- Inventory: internal locations must not show net negative per sold SKU ---
# (Exclude single-quant artifacts: enforce sum(quantity) >= 0 across all internal locations.)
sold_products = (prods1 | prods2 | prods3).ids
for pid in sold_products:
    quants = Quant.search([("product_id", "=", pid), ("location_id.usage", "=", "internal")])
    net = sum(quants.mapped("quantity"))
    if float_compare(net, 0.0, precision_rounding=1e-6) < 0:
        raise RuntimeError(f"Net negative internal qty for product_id={pid}: net={net}")

internal_locs = env["stock.location"].sudo().search([("usage", "=", "internal")])
for p in prods1 | prods2 | prods3:
    q = Quant.search([("location_id", "in", internal_locs.ids), ("product_id", "=", p.id)])
    on_hand = sum(q.mapped("quantity"))
    log(f"ON_HAND_INTERNAL_SUM code={p.default_code!r} qty={on_hand}")

# --- Pickings / moves ---
for o in (o1, o2, o3):
    for pk in o.picking_ids:
        if pk.state != "done":
            raise RuntimeError(f"Picking not done: picking={pk.id} state={pk.state!r} order={o.name!r}")
log("PICKINGS_ALL_DONE")

# --- Mixed payment sanity ---
if len(o1.payment_ids) != 2:
    raise RuntimeError(f"Order1 expected 2 payments, got {len(o1.payment_ids)}")
if float_compare(o1.amount_paid, o1.amount_total, precision_rounding=o1.currency_id.rounding):
    raise RuntimeError("Order1 amount_paid != amount_total")

# --- AVCO (average cost) on categories ---
for p in prods1 | prods2 | prods3:
    cm = p.categ_id.property_cost_method
    if cm != "average":
        raise RuntimeError(f"Expected AVCO (average) on {p.default_code!r}, got {cm!r}")
log("COST_METHOD_AVCO_OK")

# --- Close sessions (session-level accounting move) ---
for lab, sess in (("DXB", sess_dxb), ("AUH", sess_auh)):
    r = sess.action_pos_session_closing_control()
    if isinstance(r, dict):
        raise RuntimeError(f"{lab} close returned wizard dict: {r!r}")
    sess.invalidate_recordset()
    if sess.state != "closed":
        raise RuntimeError(f"{lab} session not closed: state={sess.state!r}")
    if not sess.move_id:
        raise RuntimeError(f"{lab} session has no move_id")
    if sess.move_id.state != "posted":
        raise RuntimeError(f"{lab} session move not posted: {sess.move_id.state!r}")
    bal = sum(sess.move_id.line_ids.mapped("balance"))
    if not float_is_zero(bal, precision_rounding=0.0001):
        raise RuntimeError(f"{lab} session move unbalanced: balance_sum={bal}")
    tax_lines = sess.move_id.line_ids.filtered(lambda l: l.tax_line_id or l.tax_ids)
    log(f"SESSION_CLOSED_{lab} session_id={sess.id} move_id={sess.move_id.id} tax_related_lines={len(tax_lines)}")

# Orders -> done after session posting
for o in (o1, o2, o3):
    o.invalidate_recordset()
    if o.state != "done":
        raise RuntimeError(f"Order {o.name!r} expected done, got {o.state!r}")

# --- Payment journal linkage (session move aggregates; per-payment moves may be empty) ---
for pay in o1.payment_ids | o2.payment_ids | o3.payment_ids:
    log(
        f"PAY id={pay.id} method={pay.payment_method_id.name!r} type={pay.payment_method_id.type!r} "
        f"amount={pay.amount} account_move_id={pay.account_move_id.id if pay.account_move_id else False}"
    )

# --- Deltas ---
po1 = PosOrder.search_count([])
sm1 = Move.search_count([])
am1 = AM.search_count([])
log(f"AFTER pos_order={po1} (+{po1 - po0}) stock_move={sm1} (+{sm1 - sm0}) account_move={am1} (+{am1 - am0})")

assert po1 - po0 == 3

water = PP.search([("default_code", "=", "RET-G2-BEV-WAT500")], limit=1)
manifest = {
    "pos_order_ids": [o1.id, o2.id, o3.id],
    "pos_session_ids": {"POS-DXB-01": sess_dxb.id, "POS-AUH-01": sess_auh.id},
    "session_account_move_ids": {"POS-DXB-01": sess_dxb.move_id.id, "POS-AUH-01": sess_auh.move_id.id},
    "stock_picking_ids": (o1.picking_ids | o2.picking_ids | o3.picking_ids).ids,
    "water_product_id": water.id,
    "water_template_id": water.product_tmpl_id.id,
    "stock_location_id": loc_stock.id,
    "config_ids": {"POS-DXB-01": cfg_dxb.id, "POS-AUH-01": cfg_auh.id},
}
MAN.parent.mkdir(parents=True, exist_ok=True)
MAN.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
log(f"WROTE_MANIFEST {MAN}")

ICP.set_param(FLAG, "1")
env.cr.commit()
log("COMMIT_OK_ICP_FLAG_SET")

LOG.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"WROTE {LOG}")
