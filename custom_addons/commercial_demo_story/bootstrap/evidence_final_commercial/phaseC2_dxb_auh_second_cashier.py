# Phase C2 — Second cashier on legacy POS-DXB-01 and POS-AUH-01 (30×2 = 60 cashiers total).
# Idempotent: demo_pos_accounting.final_phase_c2_dxb_auh_done

from pathlib import Path

from odoo import Command

for ROOT in (
    Path("/home/sabry3/sabry_backup/odoo_base/base_odoo_19/projects/demo_pos_accounting/evidence_final_commercial"),
    Path("/mnt/sabry_backup/odoo_base/base_odoo_19/projects/demo_pos_accounting/evidence_final_commercial"),
):
    if ROOT.is_dir():
        break
else:
    ROOT = Path(".")

LOG = ROOT / "phaseC2_shell.txt"
lines = []


def log(msg):
    lines.append(msg)
    print(msg)


ICP = env["ir.config_parameter"].sudo()
FLAG = "demo_pos_accounting.final_phase_c2_dxb_auh_done"
if ICP.get_param(FLAG) == "1":
    log("SKIP_PHASE_C2_ALREADY_DONE")
    LOG.write_text("\n".join(lines) + "\n", encoding="utf-8")
    raise SystemExit(0)

comp = env.company

g_pos = env.ref("point_of_sale.group_pos_user")
g_user = env.ref("base.group_user")
User = env["res.users"].sudo()
HE = env["hr.employee"].sudo()
Config = env["pos.config"].sudo()


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


def attach_second(cfg_name, login, disp, emp_name, pin):
    cfg = Config.search([("name", "=", cfg_name), ("company_id", "=", comp.id)], limit=1)
    if not cfg:
        log(f"MISSING_CONFIG {cfg_name}")
        return
    u = ensure_user(login, disp)
    e = ensure_emp(u, emp_name, pin)
    vals = {}
    if e.id not in cfg.basic_employee_ids.ids:
        vals["basic_employee_ids"] = [Command.link(e.id)]
    if e.id not in cfg.minimal_employee_ids.ids:
        vals["minimal_employee_ids"] = [Command.link(e.id)]
    if not vals:
        log(f"ALREADY_ATTACHED {cfg_name} emp={e.id}")
        return
    cfg.write(vals)
    log(f"ATTACHED_SECOND_CASHIER {cfg_name} user={login!r} emp={e.id}")


attach_second(
    "POS-DXB-01",
    "pos.cashier.dxb_b",
    "Dubai Flagship — Cashier B",
    "POS Cashier Dubai Flagship — Shift B",
    "9002",
)
attach_second(
    "POS-AUH-01",
    "pos.cashier.auh_b",
    "Abu Dhabi Hub — Cashier B",
    "POS Cashier Abu Dhabi Hub — Shift B",
    "9003",
)

ICP.set_param(FLAG, "1")
env.cr.commit()
log("COMMIT_OK_PHASE_C2")

LOG.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"WROTE {LOG}")
