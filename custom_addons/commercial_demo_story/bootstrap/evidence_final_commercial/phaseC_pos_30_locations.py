# Phase C — 30-location POS architecture (28 new + existing POS-DXB-01 + POS-AUH-01).
# Per branch: stock location, picking type, unique cash journal + pos.payment.method,
# shared Visa/Mastercard/Stripe from template POS-DXB-01, pos.config, 2 cashiers (users+employees).
# Idempotent: demo_pos_accounting.final_phase_c_arch_done
#
# Controlled sample POS orders (6) at end — idempotent: demo_pos_accounting.final_phase_c_pos_sales_done

from pathlib import Path

from odoo import Command, fields
from odoo import api as odoo_api

for ROOT in (
    Path("/home/sabry3/sabry_backup/odoo_base/base_odoo_19/projects/demo_pos_accounting/evidence_final_commercial"),
    Path("/mnt/sabry_backup/odoo_base/base_odoo_19/projects/demo_pos_accounting/evidence_final_commercial"),
):
    if ROOT.is_dir():
        break
else:
    ROOT = Path(".")

LOG = ROOT / "phaseC_shell.txt"
lines = []


def log(msg):
    lines.append(msg)
    print(msg)


ICP = env["ir.config_parameter"].sudo()
if ICP.get_param("demo_pos_accounting.final_phase_c_arch_done") == "1":
    log("SKIP_PHASE_C_ARCH")
    LOG.write_text("\n".join(lines) + "\n", encoding="utf-8")
    raise SystemExit(0)

comp = env.company
admin = env.ref("base.user_admin")
admin_user = admin
adm = odoo_api.Environment(env.cr, admin.id, dict(env.context))
wh = env["stock.warehouse"].search([("company_id", "=", comp.id)], limit=1)
assert wh and wh.pos_type_id
base_pt = wh.pos_type_id
pl = env["product.pricelist"].search([("company_id", "in", (comp.id, False))], limit=1)
admin_emp = env["hr.employee"].search([("user_id", "=", admin.id), ("company_id", "=", comp.id)], limit=1)
assert admin_emp

pos_parent = env["stock.location"].search([("complete_name", "=", "WH-HRG-MAIN/POS")], limit=1)
assert pos_parent

cfg_tpl = adm["pos.config"].search([("name", "=", "POS-DXB-01")], limit=1)
assert cfg_tpl
pm_visa = cfg_tpl.payment_method_ids.filtered(lambda p: p.name and "Visa" in p.name)[:1]
pm_mc = cfg_tpl.payment_method_ids.filtered(lambda p: p.name and "Mastercard" in p.name)[:1]
pm_stripe = cfg_tpl.payment_method_ids.filtered(lambda p: p.name and "Stripe" in p.name)[:1]
assert pm_visa and pm_mc and pm_stripe

Journal = env["account.journal"].sudo()
PM = env["pos.payment.method"].sudo()
SL = env["stock.location"].sudo()
SPT = env["stock.picking.type"].sudo()
HE = env["hr.employee"].sudo()
User = env["res.users"].sudo()
Config = env["pos.config"].sudo()
PosOrder = adm["pos.order"].sudo()
PP = adm["product.product"].sudo()

aed = env.ref("base.AED")
inv_ref = {"invoice_reference_type": "invoice", "invoice_reference_model": "odoo"}
g_pos = env.ref("point_of_sale.group_pos_user")
g_user = env.ref("base.group_user")

# Remaining 28 malls (plan rows 3–30) — short POS codes POS-RET-03 … POS-RET-30
MALLS = [
    (3, "POS-RET-03", "City Walk"),
    (4, "POS-RET-04", "Dubai Hills Mall"),
    (5, "POS-RET-05", "Ibn Battuta Mall"),
    (6, "POS-RET-06", "Mirdif City Centre"),
    (7, "POS-RET-07", "Deira City Centre"),
    (8, "POS-RET-08", "Al Ghurair Centre"),
    (9, "POS-RET-09", "Festival City Mall"),
    (10, "POS-RET-10", "Dragon Mart 2"),
    (11, "POS-RET-11", "Abu Dhabi Mall"),
    (12, "POS-RET-12", "Yas Mall"),
    (13, "POS-RET-13", "Marina Mall AUH"),
    (14, "POS-RET-14", "Dalma Mall"),
    (15, "POS-RET-15", "Al Wahda Mall"),
    (16, "POS-RET-16", "Sharjah City Centre"),
    (17, "POS-RET-17", "Mega Mall Sharjah"),
    (18, "POS-RET-18", "Al Zahia Mall"),
    (19, "POS-RET-19", "Ajman City Centre"),
    (20, "POS-RET-20", "City Centre Fujairah"),
    (21, "POS-RET-21", "Sahara Centre"),
    (22, "POS-RET-22", "Al Raha Mall"),
    (23, "POS-RET-23", "Mushrif Mall"),
    (24, "POS-RET-24", "Madinat Jumeirah"),
    (25, "POS-RET-25", "The Dubai Frame"),
    (26, "POS-RET-26", "Al Foah Mall"),
    (27, "POS-RET-27", "Al Ain Mall"),
    (28, "POS-RET-28", "Oasis Mall Al Ain"),
    (29, "POS-RET-29", "RAK City Centre"),
    (30, "POS-RET-30", "UAQ City Centre"),
]


def ensure_journal(name, code, jtype):
    code = (code or "")[:5]
    j = Journal.search([("company_id", "=", comp.id), ("code", "=", code)], limit=1)
    vals = {"name": name, "code": code, "type": jtype, "company_id": comp.id, "currency_id": aed.id, **inv_ref}
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


def ensure_user(login, disp_name):
    u = User.search([("login", "=", login)], limit=1)
    vals = {
        "name": disp_name,
        "login": login,
        "company_id": comp.id,
        "company_ids": [(6, 0, [comp.id])],
        "group_ids": [(6, 0, [g_user.id, g_pos.id])],
    }
    if u:
        u.write(vals)
        return u
    vals["password"] = "FinalDemo2026!"
    return User.create(vals)


def ensure_emp(user, name, pin):
    e = HE.search([("user_id", "=", user.id), ("company_id", "=", comp.id)], limit=1)
    vals = {"name": name, "user_id": user.id, "company_id": comp.id, "pin": pin}
    if e:
        e.write(vals)
        return e
    return HE.create(vals)


def get_branch_picking_type(suffix, src_loc):
    code = ("R" + suffix.replace("-", ""))[:5]
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
        "receipt_header": "Horizon Retail — Executive Demo",
        "receipt_footer": "Controlled demo dataset — Final Commercial Phase",
        "basic_employee_ids": [Command.set([e.id for e in basic_emps])],
        "minimal_employee_ids": [Command.set([e.id for e in minimal_emps])],
    }
    if c:
        c.write(vals)
        return c
    return Config.create(vals)


created = 0
for idx, pos_name, mall in MALLS:
    if Config.search([("name", "=", pos_name)], limit=1):
        log(f"EXISTS_SKIP {pos_name}")
        continue
    loc_name = f"L{idx:02d}"
    loc = SL.search([("location_id", "=", pos_parent.id), ("name", "=", loc_name)], limit=1)
    if not loc:
        loc = SL.create(
            {
                "name": loc_name,
                "location_id": pos_parent.id,
                "usage": "internal",
                "company_id": comp.id,
            }
        )
    jc = f"P{idx:03}"[-5:]  # P003..P030
    jcash = ensure_journal(f"POS Cash {pos_name}", jc, "cash")
    pm_cash = ensure_pm(f"POS Cash AED {pos_name}", jcash)
    pms = pm_cash | pm_visa | pm_mc | pm_stripe
    pt = get_branch_picking_type(loc_name, loc)
    u_a = ensure_user(f"pos_ret{idx:02}_a", f"Cashier {mall} A")
    u_b = ensure_user(f"pos_ret{idx:02}_b", f"Cashier {mall} B")
    e_a = ensure_emp(u_a, f"POS Cashier {mall} — Shift A", f"{1000 + idx * 2:04d}")
    e_b = ensure_emp(u_b, f"POS Cashier {mall} — Shift B", f"{1001 + idx * 2:04d}")
    cfg = upsert_pos_config(pos_name, pt, pms, [admin_emp, e_a, e_b], [e_a, e_b])
    log(f"POS_CREATE {pos_name} id={cfg.id} loc={loc.id} cashiers={e_a.id},{e_b.id}")
    created += 1
    if created % 5 == 0:
        env.cr.commit()
        log(f"INTERMEDIATE_COMMIT created_so_far={created}")

ICP.set_param("demo_pos_accounting.final_phase_c_arch_done", "1")
env.cr.commit()
log(f"COMMIT_OK_PHASE_C_ARCH new_configs={created}")

# --- Sample POS sales (6 orders) on 6 configs ---
if ICP.get_param("demo_pos_accounting.final_phase_c_pos_sales_done") != "1":
    cfgs = (
        adm["pos.config"]
        .search([("name", "in", ["POS-DXB-01", "POS-AUH-01", "POS-RET-03", "POS-RET-11", "POS-RET-16", "POS-RET-24"])])
        .sorted(lambda c: c.name)
    )
    assert len(cfgs) == 6, cfgs.mapped("name")

    def ensure_session(cfg):
        for s in cfg.session_ids.filtered(lambda x: x.state == "opening_control" and not x.order_ids):
            s.delete_opening_control_session()
        if not cfg.current_session_id:
            cfg.open_ui()
        sess = cfg.current_session_id
        if sess.state == "opening_control":
            sess.set_opening_control(0, "Final commercial sample opening")
        if sess.state != "opened":
            raise RuntimeError(f"Session not opened {cfg.name!r} {sess.state!r}")
        return sess

    def create_paid_order(sess, line_specs, payments):
        cmds = []
        for code, qty in line_specs:
            p = PP.search([("default_code", "=", code)], limit=1)
            if not p:
                raise RuntimeError(f"Missing {code}")
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
            raise RuntimeError(order.state)
        return order

    scenarios = [
        ("POS-DXB-01", [("RET-G2-BEV-WAT500", 1), ("RET-G2-SNK-CRP40", 1)], "mixed"),
        ("POS-AUH-01", [("RET-G2-BEV-OJ1L", 1)], "cash"),
        ("POS-RET-03", [("RET-G2-SNK-OAT35", 2)], "visa"),
        ("POS-RET-11", [("RET-G2-PAR-TSH-M", 1)], "mc"),
        ("POS-RET-16", [("RET-G2-BEV-WAT500", 3)], "cash"),
        ("POS-RET-24", [("RET-G2-PAR-MUG350-BLA", 1)], "visa"),
    ]
    for cfg_name, basket, paymode in scenarios:
        cfg = cfgs.filtered(lambda c: c.name == cfg_name)
        assert len(cfg) == 1
        cfg = cfg[0]
        sess = ensure_session(cfg)
        cash = cfg.payment_method_ids.filtered(lambda p: p.type == "cash")[:1]
        visa = cfg.payment_method_ids.filtered(lambda p: p.name and "Visa" in p.name)[:1]
        mc = cfg.payment_method_ids.filtered(lambda p: p.name and "Mastercard" in p.name)[:1]
        if paymode == "mixed":
            pay = [(cash, 2.0), (visa, None)]
        elif paymode == "cash":
            pay = [(cash, None)]
        elif paymode == "visa":
            pay = [(visa, None)]
        else:
            pay = [(mc, None)]
        o = create_paid_order(sess, basket, pay)
        log(f"SAMPLE_POS_ORDER cfg={cfg_name} order={o.name!r} total={o.amount_total}")
    ICP.set_param("demo_pos_accounting.final_phase_c_pos_sales_done", "1")
    env.cr.commit()
    log("COMMIT_OK_PHASE_C_SAMPLE_SALES")

LOG.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"WROTE {LOG}")
