# Phase B — eCommerce employee + additional website-channel sale orders (ORM, controlled).
# Idempotent: demo_pos_accounting.final_phase_b_done

from pathlib import Path

for ROOT in (
    Path("/home/sabry3/sabry_backup/odoo_base/base_odoo_19/projects/demo_pos_accounting/evidence_final_commercial"),
    Path("/mnt/sabry_backup/odoo_base/base_odoo_19/projects/demo_pos_accounting/evidence_final_commercial"),
):
    if ROOT.is_dir():
        break
else:
    ROOT = Path(".")

LOG = ROOT / "phaseB_shell.txt"
lines = []


def log(msg):
    lines.append(msg)
    print(msg)


ICP = env["ir.config_parameter"].sudo()
if ICP.get_param("demo_pos_accounting.final_phase_b_done") == "1":
    log("SKIP_PHASE_B")
    LOG.write_text("\n".join(lines) + "\n", encoding="utf-8")
    raise SystemExit(0)

comp = env.company
wh = env["stock.warehouse"].search([("company_id", "=", comp.id)], limit=1)
website = env["website"].search([("company_id", "=", comp.id)], limit=1)
assert website

User = env["res.users"].sudo()
HE = env["hr.employee"].sudo()
g_sales = env.ref("sales_team.group_sale_salesman_all_leads")
g_user = env.ref("base.group_user")

u_eco = User.search([("login", "=", "ecom.sales.coord")], limit=1)
vals = {
    "name": "Laila Nasser — eCommerce Sales",
    "login": "ecom.sales.coord",
    "company_id": comp.id,
    "company_ids": [(6, 0, [comp.id])],
    "group_ids": [(6, 0, [g_user.id, g_sales.id])],
}
if u_eco:
    u_eco.write(vals)
else:
    vals["password"] = "FinalDemo2026!"
    u_eco = User.create(vals)

emp = HE.search([("user_id", "=", u_eco.id), ("company_id", "=", comp.id)], limit=1)
ev = {"name": "Laila Nasser — eCommerce Sales", "user_id": u_eco.id, "company_id": comp.id, "job_title": "eCommerce Sales Coordinator"}
if emp:
    emp.write(ev)
else:
    emp = HE.create(ev)
log(f"ECOM_USER id={u_eco.id} EMP id={emp.id}")

Partner = env["res.partner"].sudo()
ae = env.ref("base.ae")
pub = website.user_id.partner_id
partner = Partner.search([("email", "=", "gate4_ecommerce_flow@example.invalid")], limit=1)
if not partner:
    partner = Partner.create(
        {
            "name": "Gate eCommerce Customer",
            "email": "gate4_ecommerce_flow@example.invalid",
            "country_id": ae.id,
            "company_id": comp.id,
        }
    )

PP = env["product.product"].sudo()
SO = env["sale.order"].sudo()


def getp(code):
    p = PP.search([("default_code", "=", code)], limit=1)
    if not p:
        raise RuntimeError(code)
    return p


def mk_web_order(ref, codes_qtys):
    lines = []
    for code, qty in codes_qtys:
        p = getp(code)
        lines.append(
            (
                0,
                0,
                {
                    "product_id": p.id,
                    "product_uom_qty": qty,
                    "price_unit": p.lst_price,
                },
            )
        )
    so = SO.create(
        {
            "partner_id": partner.id,
            "warehouse_id": wh.id,
            "company_id": comp.id,
            "website_id": website.id,
            "user_id": u_eco.id,
            "client_order_ref": ref,
            "order_line": lines,
        }
    )
    so.action_confirm()
    for pick in so.picking_ids:
        if pick.state in ("done", "cancel"):
            continue
        for mv in pick.move_ids:
            for ml in mv.move_line_ids:
                ml.write({"quantity": mv.product_uom_qty, "picked": True})
        pick.with_context(skip_sms=True).button_validate()
    log(f"WEB_SO id={so.id} name={so.name!r} ref={ref} total={so.amount_total} state={so.state}")
    return so


mk_web_order("FIN-WEB-MUG", [("RET-G2-PAR-MUG350-BLA", 1)])
mk_web_order("FIN-WEB-SHIRT", [("RET-G2-PAR-TSH-M", 1)])

ICP.set_param("demo_pos_accounting.final_phase_b_done", "1")
env.cr.commit()
log("COMMIT_OK_PHASE_B")
LOG.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"WROTE {LOG}")
