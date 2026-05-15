# Phase A — Corporate sales completion (Odoo shell).
# Quotations → confirmed SO → delivery done → invoice posted → bank payment registered.
# Two direct sales users + crm.team with monthly invoicing target (AED proxy for USD 200/day).
# Idempotent via ir.config_parameter demo_pos_accounting.final_phase_a_done

from pathlib import Path

for ROOT in (
    Path("/home/sabry3/sabry_backup/odoo_base/base_odoo_19/projects/demo_pos_accounting/evidence_final_commercial"),
    Path("/mnt/sabry_backup/odoo_base/base_odoo_19/projects/demo_pos_accounting/evidence_final_commercial"),
):
    if ROOT.is_dir():
        break
else:
    ROOT = Path(".")

LOG = ROOT / "phaseA_shell.txt"
lines = []


def log(msg):
    lines.append(msg)
    print(msg)


ICP = env["ir.config_parameter"].sudo()
FLAG = "demo_pos_accounting.final_phase_a_done"
if ICP.get_param(FLAG) == "1":
    log("SKIP_PHASE_A_ALREADY_DONE")
    LOG.write_text("\n".join(lines) + "\n", encoding="utf-8")
    raise SystemExit(0)

comp = env.company
aed = env.ref("base.AED")
admin = env.ref("base.user_admin")
wh = env["stock.warehouse"].search([("company_id", "=", comp.id)], limit=1)
assert wh

sale_man = env.ref("sales_team.group_sale_salesman_all_leads")
inv_ref = {"invoice_reference_type": "invoice", "invoice_reference_model": "odoo"}

# --- FX note: USD 200/day × 30 ≈ USD 6000/month → AED at 3.67 ≈ 22020 (rounded 22000 AED / month / salesperson)
MONTH_TARGET_AED = 22000.0

User = env["res.users"].sudo()
HE = env["hr.employee"].sudo()
Team = env["crm.team"].sudo()


def ensure_user(login, name, groups_xml_id):
    g = env.ref(groups_xml_id)
    base_user = env.ref("base.group_user")
    gids = [g.id, base_user.id]
    u = User.search([("login", "=", login)], limit=1)
    vals = {
        "name": name,
        "login": login,
        "company_ids": [(6, 0, [comp.id])],
        "company_id": comp.id,
        "group_ids": [(6, 0, gids)],
    }
    if u:
        u.write(vals)
        return u
    vals["password"] = "FinalDemo2026!"
    return User.create(vals)


def ensure_employee(user, name, job):
    e = HE.search([("user_id", "=", user.id), ("company_id", "=", comp.id)], limit=1)
    vals = {"name": name, "user_id": user.id, "company_id": comp.id, "job_title": job}
    if e:
        e.write(vals)
        return e
    return HE.create(vals)


u_north = ensure_user("corp.sales.north", "Ahmed Al Mansoori — Corporate Direct", "sales_team.group_sale_salesman_all_leads")
u_south = ensure_user("corp.sales.south", "Sarah Johnson — Corporate Direct", "sales_team.group_sale_salesman_all_leads")
emp_n = ensure_employee(u_north, "Ahmed Al Mansoori — Corporate Direct", "Direct Sales — UAE North")
emp_s = ensure_employee(u_south, "Sarah Johnson — Corporate Direct", "Direct Sales — UAE South")
log(f"USERS {u_north.login} id={u_north.id}  {u_south.login} id={u_south.id}")

team = Team.search([("name", "=", "Corporate Direct — Horizon Retail"), ("company_id", "=", comp.id)], limit=1)
tvals = {
    "name": "Corporate Direct — Horizon Retail",
    "company_id": comp.id,
    "use_leads": False,
    "user_id": u_north.id,
    "member_ids": [(6, 0, [u_north.id, u_south.id])],
    "invoiced_target": MONTH_TARGET_AED * 2,
}
if team:
    team.write(tvals)
else:
    team = Team.create(tvals)
log(f"TEAM id={team.id} invoiced_target={team.invoiced_target}")

Country = env.ref("base.ae")
Partner = env["res.partner"].sudo()


def ensure_partner(name, ref_suffix):
    ref = f"FINCORP-{ref_suffix}"
    p = Partner.search([("ref", "=", ref), ("company_id", "in", (comp.id, False))], limit=1)
    vals = {
        "name": name,
        "ref": ref,
        "company_id": comp.id,
        "country_id": Country.id,
        "is_company": True,
        "email": f"{ref.lower()}@example.invalid",
    }
    if p:
        p.write(vals)
        return p
    return Partner.create(vals)


p_alpha = ensure_partner("Final Demo Corporate Alpha LLC", "ALPHA")
p_beta = ensure_partner("Final Demo Trading Beta FZ-LLC", "BETA")
log(f"PARTNERS {p_alpha.id} {p_beta.id}")

PP = env["product.product"].sudo()


def get_product(code):
    p = PP.search([("default_code", "=", code)], limit=1)
    if not p:
        raise RuntimeError(f"Missing product {code}")
    return p


prod_water = get_product("RET-G2-BEV-WAT500")
prod_oj = get_product("RET-G2-BEV-OJ1L")

SOL = env["sale.order.line"].sudo()
SO = env["sale.order"].sudo()


def line_cmd(product, qty, discount=0):
    return (
        0,
        0,
        {
            "product_id": product.id,
            "product_uom_qty": qty,
            "price_unit": product.lst_price * (1 - discount),
        },
    )


def run_corporate_flow(partner, user, sku1, qty1, sku2, qty2, label):
    p1 = get_product(sku1)
    p2 = get_product(sku2)
    so = SO.create(
        {
            "partner_id": partner.id,
            "user_id": user.id,
            "team_id": team.id,
            "warehouse_id": wh.id,
            "company_id": comp.id,
            "client_order_ref": label,
            "order_line": [line_cmd(p1, qty1), line_cmd(p2, qty2)],
        }
    )
    assert so.state == "draft"
    so.action_confirm()
    assert so.state == "sale"
    log(f"SO_CONFIRMED id={so.id} name={so.name!r} user={user.login} total={so.amount_total}")

    for pick in so.picking_ids:
        if pick.state in ("done", "cancel"):
            continue
        for mv in pick.move_ids:
            for ml in mv.move_line_ids:
                ml.write({"quantity": mv.product_uom_qty, "picked": True})
        pick.with_context(skip_sms=True).button_validate()
    log(f"DELIVERIES_DONE so={so.name!r} pickings={so.picking_ids.mapped('state')}")

    invs = so._create_invoices()
    for inv in invs:
        inv.action_post()
    log(f"INVOICES_POSTED {invs.mapped(lambda m: (m.name, m.amount_total, m.payment_state))}")

    bank_journal = env["account.journal"].search(
        [("company_id", "=", comp.id), ("id", "=", 15)], limit=1
    ) or env["account.journal"].search(
        [("company_id", "=", comp.id), ("type", "=", "bank")], limit=1, order="id asc"
    )
    assert bank_journal
    for inv in invs:
        wiz = (
            env["account.payment.register"]
            .with_context(active_model="account.move", active_ids=inv.ids)
            .create(
                {
                    "payment_date": inv.invoice_date,
                    "journal_id": bank_journal.id,
                    "amount": inv.amount_residual,
                }
            )
        )
        wiz.action_create_payments()
    for inv in invs:
        inv.invalidate_recordset()
    log(f"PAYMENTS_REGISTERED {[ (i.name, i.payment_state) for i in invs ]}")
    return so


run_corporate_flow(p_alpha, u_north, "RET-G2-BEV-WAT500", 5, "RET-G2-SNK-OAT35", 10, "FIN-A-NORTH-001")
run_corporate_flow(p_beta, u_south, "RET-G2-BEV-OJ1L", 3, "RET-G2-BEV-WAT500", 4, "FIN-B-SOUTH-001")

ICP.set_param(FLAG, "1")
env.cr.commit()
log("COMMIT_OK_PHASE_A")

LOG.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"WROTE {LOG}")
