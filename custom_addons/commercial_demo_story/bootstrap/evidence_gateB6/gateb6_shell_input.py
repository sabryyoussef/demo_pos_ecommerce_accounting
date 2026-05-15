# Gate B6 — operational users & least-privilege groups. Requires env.cr.commit().

import secrets
from pathlib import Path

from odoo import Command

comp = env.company
User = env["res.users"].sudo()
HE = env["hr.employee"].sudo()
Config = env["pos.config"].sudo()

for PWFILE in (
    Path("/mnt/sabry_backup/odoo_base/base_odoo_19/projects/demo_pos_accounting/.gateB6_demo_passwords.txt"),
    Path("/home/sabry3/sabry_backup/odoo_base/base_odoo_19/projects/demo_pos_accounting/.gateB6_demo_passwords.txt"),
):
    if PWFILE.parent.is_dir():
        break
else:
    PWFILE = Path(".").resolve() / "projects/demo_pos_accounting/.gateB6_demo_passwords.txt"

moves_before = env["account.move"].sudo().search_count([])
stock_before = env["stock.move"].sudo().search_count([])


def ref_gid(xmlid):
    return env.ref(xmlid).id


def ensure_user(login, display_name, group_xmlids):
    """Internal user + explicit groups (base.group_user added if missing)."""
    gids = sorted({ref_gid(x) for x in group_xmlids})
    bu = ref_gid("base.group_user")
    if bu not in gids:
        gids.append(bu)
    pw = secrets.token_urlsafe(16)
    u = User.search([("login", "=", login)], limit=1)
    vals = {
        "name": display_name,
        "login": login,
        "password": pw,
        "group_ids": [Command.set(gids)],
        "company_id": comp.id,
        "company_ids": [Command.set([comp.id])],
        "active": True,
    }
    if u:
        u.write(vals)
        return u, pw
    return User.create(vals), pw


passwords = {}

u_dxb, p_dxb = ensure_user(
    "pos.cashier.dxb",
    "POS Cashier DXB",
    ["point_of_sale.group_pos_user"],
)
passwords["pos.cashier.dxb"] = p_dxb

u_auh, p_auh = ensure_user(
    "pos.cashier.auh",
    "POS Cashier AUH",
    ["point_of_sale.group_pos_user"],
)
passwords["pos.cashier.auh"] = p_auh

u_pmgr, p_pmgr = ensure_user(
    "pos.manager",
    "POS Manager",
    ["point_of_sale.group_pos_manager"],
)
passwords["pos.manager"] = p_pmgr

u_imgr, p_imgr = ensure_user(
    "inventory.manager",
    "Inventory Manager",
    ["stock.group_stock_manager"],
)
passwords["inventory.manager"] = p_imgr

u_fmgr, p_fmgr = ensure_user(
    "finance.manager",
    "Finance Manager",
    ["account.group_account_user", "account.group_account_manager"],
)
passwords["finance.manager"] = p_fmgr

PWFILE.write_text(
    "\n".join(f"{login}={pw}" for login, pw in sorted(passwords.items())) + "\n",
    encoding="utf-8",
)
print("PASSWORDS_WRITTEN", str(PWFILE))

# Link POS cashiers (Gate B5 employees) to operational users + PINs
emp_dxb = HE.search([("name", "=", "POS Cashier DXB-01"), ("company_id", "=", comp.id)], limit=1)
emp_auh = HE.search([("name", "=", "POS Cashier AUH-01"), ("company_id", "=", comp.id)], limit=1)
assert emp_dxb and emp_auh
emp_dxb.write({"user_id": u_dxb.id, "pin": "9182"})
emp_auh.write({"user_id": u_auh.id, "pin": "8273"})
print("EMPLOYEES", emp_dxb.id, emp_auh.id)

# Manager employee for pos.manager (PoS HR manager role)
emp_pm = HE.search([("user_id", "=", u_pmgr.id)], limit=1)
if not emp_pm:
    emp_pm = HE.create(
        {
            "name": "POS Manager Demo",
            "company_id": comp.id,
            "user_id": u_pmgr.id,
            "pin": "7364",
        }
    )
else:
    emp_pm.write({"company_id": comp.id, "pin": "7364"})
print("EMP_POS_MANAGER", emp_pm.id)

# POS configs: least-privilege employee sets (no Administrator on cashier paths)
cfg_dxb = Config.search([("name", "=", "POS-DXB-01")], limit=1)
cfg_auh = Config.search([("name", "=", "POS-AUH-01")], limit=1)
assert cfg_dxb and cfg_auh
cfg_dxb.write(
    {
        "basic_employee_ids": [Command.set([emp_pm.id, emp_dxb.id])],
        "minimal_employee_ids": [Command.set([emp_dxb.id])],
    }
)
cfg_auh.write(
    {
        "basic_employee_ids": [Command.set([emp_pm.id, emp_auh.id])],
        "minimal_employee_ids": [Command.set([emp_auh.id])],
    }
)
print("POS_CONFIGS_UPDATED", cfg_dxb.id, cfg_auh.id)

for login, u in [
    ("pos.cashier.dxb", u_dxb),
    ("pos.cashier.auh", u_auh),
    ("pos.manager", u_pmgr),
    ("inventory.manager", u_imgr),
    ("finance.manager", u_fmgr),
]:
    assert not u.has_group("base.group_system"), login

moves_after = env["account.move"].sudo().search_count([])
stock_after = env["stock.move"].sudo().search_count([])
assert moves_after == moves_before and stock_after == stock_before

env.cr.commit()
print("COMMIT_OK")
