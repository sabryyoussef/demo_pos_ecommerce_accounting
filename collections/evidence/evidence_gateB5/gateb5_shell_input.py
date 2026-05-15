# Gate B5 — POS operational structure (no sales). Requires env.cr.commit().

from odoo import Command

comp = env.company
wh = env["stock.warehouse"].search([("company_id", "=", comp.id)], limit=1)
loc_dxb = env["stock.location"].search([("complete_name", "=", "WH-HRG-MAIN/POS/DXB-01")], limit=1)
loc_auh = env["stock.location"].search([("complete_name", "=", "WH-HRG-MAIN/POS/AUH-01")], limit=1)
assert loc_dxb and loc_auh, (loc_dxb, loc_auh)

PM = env["pos.payment.method"].sudo()
Journal = env["account.journal"].sudo()
aed = env.ref("base.AED")
inv_ref = {"invoice_reference_type": "invoice", "invoice_reference_model": "odoo"}


def ensure_journal(display_name, code, jtype):
    code = (code or "")[:5]
    j = Journal.search([("company_id", "=", comp.id), ("code", "=", code)], limit=1)
    vals = {
        "name": display_name,
        "code": code,
        "type": jtype,
        "company_id": comp.id,
        "currency_id": aed.id,
        **inv_ref,
    }
    if j:
        j.write(vals)
        return j
    return Journal.create(vals)


def ensure_pm(name, journal):
    m = PM.search([("company_id", "=", comp.id), ("name", "=", name)], limit=1)
    vals = {"name": name, "journal_id": journal.id, "company_id": comp.id}
    if m:
        m.write(vals)
        return m
    return PM.create(vals)


# Odoo forbids sharing the same *cash* payment method across two pos.config; duplicate cash journal+method for AUH.
pm_cash_dxb = PM.search([("company_id", "=", comp.id), ("name", "=", "POS Cash AED")], limit=1)
assert pm_cash_dxb, "Gate B4 cash payment method POS Cash AED missing"
j_cash_auh = ensure_journal("POS-CASH-AUH", "PCAHU", "cash")
pm_cash_auh = ensure_pm("POS Cash AED AUH", j_cash_auh)
pm_bank = PM.search(
    [
        ("company_id", "=", comp.id),
        ("name", "in", ("POS Visa AED", "POS Mastercard AED", "POS Stripe AED")),
    ]
)
assert len(pm_bank) == 3, pm_bank.mapped("name")
pms_dxb = pm_cash_dxb | pm_bank
pms_auh = pm_cash_auh | pm_bank

pl = env["product.pricelist"].search([("company_id", "in", (comp.id, False))], limit=1)
admin_user = env.ref("base.user_admin")
admin_emp = env["hr.employee"].search([("user_id", "=", admin_user.id), ("company_id", "=", comp.id)], limit=1)
assert admin_emp, "Administrator employee required for POS manager linkage"

HE = env["hr.employee"].sudo()

def get_cashier(name, pin):
    e = HE.search([("name", "=", name), ("company_id", "=", comp.id)], limit=1)
    vals = {"name": name, "company_id": comp.id, "pin": pin}
    if e:
        e.write(vals)
        return e
    return HE.create(vals)


cashier_dxb = get_cashier("POS Cashier DXB-01", "9182")
cashier_auh = get_cashier("POS Cashier AUH-01", "8273")

base_pt = wh.pos_type_id
assert base_pt, "Warehouse needs pos_type_id"

SPT = env["stock.picking.type"].sudo()


def get_branch_pos_picking_type(suffix, src_loc):
    code = ("P" + suffix.replace("-", ""))[:5]
    existing = SPT.search(
        [("warehouse_id", "=", wh.id), ("sequence_code", "=", code), ("code", "=", "outgoing")], limit=1
    )
    if existing:
        existing.write(
            {
                "name": "PoS Orders %s" % suffix,
                "default_location_src_id": src_loc.id,
                "default_location_dest_id": base_pt.default_location_dest_id.id,
            }
        )
        return existing
    return base_pt.copy(
        {
            "name": "PoS Orders %s" % suffix,
            "default_location_src_id": src_loc.id,
            "default_location_dest_id": base_pt.default_location_dest_id.id,
            "sequence_code": code,
        }
    )


pt_dxb = get_branch_pos_picking_type("DXB-01", loc_dxb)
pt_auh = get_branch_pos_picking_type("AUH-01", loc_auh)
print("PICKING_TYPES", pt_dxb.id, pt_dxb.sequence_code, pt_auh.id, pt_auh.sequence_code)

Config = env["pos.config"].sudo()

moves_before = env["account.move"].sudo().search_count([])
stock_before = env["stock.move"].sudo().search_count([])
so_before = env["sale.order"].sudo().search_count([])
po_before = env["pos.order"].sudo().search_count([])


def upsert_pos_config(name, picking_type, payment_methods, basic_emps, minimal_emps):
    c = Config.search([("name", "=", name), ("company_id", "=", comp.id)], limit=1)
    vals = {
        "name": name,
        "company_id": comp.id,
        "warehouse_id": wh.id,
        "picking_type_id": picking_type.id,
        "payment_method_ids": [Command.set(payment_methods.ids)],
        "pricelist_id": pl.id,
        "module_pos_hr": True,
        "restrict_price_control": True,
        "set_maximum_difference": True,
        "amount_authorized_diff": 0.01,
        "order_edit_tracking": True,
        "receipt_header": "VALIDATION ONLY — Gate B5",
        "receipt_footer": "No live operations. Training / structure baseline.",
        "basic_employee_ids": [Command.set([e.id for e in basic_emps])],
        "minimal_employee_ids": [Command.set([e.id for e in minimal_emps])],
    }
    if c:
        c.write(vals)
        return c
    return Config.create(vals)


cfg_dxb = upsert_pos_config(
    "POS-DXB-01",
    pt_dxb,
    pms_dxb,
    [admin_emp, cashier_dxb],
    [cashier_dxb],
)
cfg_auh = upsert_pos_config(
    "POS-AUH-01",
    pt_auh,
    pms_auh,
    [admin_emp, cashier_auh],
    [cashier_auh],
)
print("POS_CONFIG", cfg_dxb.id, cfg_auh.id)

# No live Stripe keys
ICP = env["ir.config_parameter"].sudo()
for key in ("payment_stripe.publishable_key", "payment_stripe.secret_key"):
    if ICP.get_param(key):
        ICP.set_param(key, "")
        print("CLEARED_PARAM", key)

Session = env["pos.session"].sudo()


def open_and_close_empty_session(cfg):
    moves0 = env["account.move"].sudo().search_count([])
    stock0 = env["stock.move"].sudo().search_count([])
    po0 = env["pos.order"].sudo().search_count([])
    sess = Session.create({"config_id": cfg.id, "user_id": admin_user.id})
    print("SESSION_CREATE", cfg.name, sess.id, sess.state)
    sess.set_opening_control(0, "Gate B5 structural open")
    assert sess.state == "opened", sess.state
    sess.action_pos_session_closing_control()
    sess.action_pos_session_close()
    assert sess.state == "closed", sess.state
    moves1 = env["account.move"].sudo().search_count([])
    stock1 = env["stock.move"].sudo().search_count([])
    po1 = env["pos.order"].sudo().search_count([])
    print("SESSION_CLOSE_COUNTS", cfg.name, "move", moves0, moves1, "stock_move", stock0, stock1, "pos_order", po0, po1)
    assert moves1 == moves0
    assert stock1 == stock0
    assert po1 == po0
    return sess


open_and_close_empty_session(cfg_dxb)
open_and_close_empty_session(cfg_auh)

moves_after = env["account.move"].sudo().search_count([])
stock_after = env["stock.move"].sudo().search_count([])
so_after = env["sale.order"].sudo().search_count([])
po_after = env["pos.order"].sudo().search_count([])
print(
    "TOTAL_COUNTS",
    "move",
    moves_before,
    moves_after,
    "stock_move",
    stock_before,
    stock_after,
    "sale_order",
    so_before,
    so_after,
    "pos_order",
    po_before,
    po_after,
)
assert moves_after == moves_before
assert stock_after == stock_before
assert so_after == so_before
assert po_after == po_before

env.cr.commit()
print("COMMIT_OK")
