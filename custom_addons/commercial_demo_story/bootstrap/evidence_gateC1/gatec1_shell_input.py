# Gate C1 — product category hierarchy + category accounting (AVCO) + company defaults.
# No new products, no stock moves, no account moves, no product_value rows.

from pathlib import Path

from odoo import Command

for LOG in (
    Path("/home/sabry3/sabry_backup/odoo_base/base_odoo_19/projects/demo_pos_accounting/evidence_gateC1/gateC1_shell.txt"),
    Path("/mnt/sabry_backup/odoo_base/base_odoo_19/projects/demo_pos_accounting/evidence_gateC1/gateC1_shell.txt"),
):
    if LOG.parent.is_dir():
        break
else:
    LOG = Path("gateC1_shell.txt")

lines = []


def log(msg):
    lines.append(msg)
    print(msg)


comp = env.company.sudo()
PC = env["product.category"].sudo()

tmpl_before = env["product.template"].sudo().search_count([])
sm_before = env["stock.move"].sudo().search_count([])
pv_before = env["product.value"].sudo().search_count([])
am_before = env["account.move"].sudo().search_count([])

log(f"BASELINE product_template={tmpl_before} stock_move={sm_before} product_value={pv_before} account_move={am_before}")

income = comp.income_account_id
expense = comp.expense_account_id
stock_val = comp.account_stock_valuation_id
stock_j = comp.account_stock_journal_id
if not all((income, expense, stock_val, stock_j)):
    raise RuntimeError("Missing company stock/income/expense accounts for category properties")
log(
    f"COMPANY_ACCOUNTS income={income.id} expense={expense.id} stock_valuation={stock_val.id} stock_journal={stock_j.id}"
)


def ensure_category(name, parent, valuation):
    dom = [("name", "=", name), ("parent_id", "=", parent.id if parent else False)]
    rec = PC.search(dom, limit=1)
    vals = {
        "name": name,
        "parent_id": parent.id if parent else False,
        "property_cost_method": "average",
        "property_valuation": valuation,
        "property_account_income_categ_id": income.id,
        "property_account_expense_categ_id": expense.id,
        "property_stock_valuation_account_id": stock_val.id,
        "property_stock_journal": stock_j.id,
    }
    if rec:
        rec.write(vals)
        log(f"CATEGORY_UPDATE id={rec.id} name={name!r} valuation={valuation}")
        return rec
    c = PC.create(vals)
    log(f"CATEGORY_CREATE id={c.id} name={name!r} valuation={valuation}")
    return c


root = ensure_category("ALL PRODUCTS", None, "real_time")
retail = ensure_category("RETAIL", root, "real_time")
ensure_category("FOOD", retail, "real_time")
ensure_category("BEVERAGES", retail, "real_time")
ensure_category("SERVICES", root, "periodic")
ensure_category("POS ITEMS", root, "real_time")
ensure_category("ECOM ITEMS", root, "real_time")

comp.write(
    {
        "cost_method": "average",
        "inventory_valuation": "real_time",
    }
)
log("COMPANY_DEFAULTS cost_method=average inventory_valuation=real_time")

services_leaf = PC.search([("name", "=", "SERVICES"), ("parent_id", "=", root.id)], limit=1)
if services_leaf:
    services_leaf.write({"property_valuation": "periodic"})
    log("SERVICES_ENFORCED_PERIODIC")

variant_g = env.ref("product.group_product_variant")
bu = env.ref("base.group_user")
if variant_g not in bu.implied_ids:
    bu.write({"implied_ids": [Command.link(variant_g.id)]})
    log("VARIANT_GROUP_LINKED_TO_INTERNAL_USER")
else:
    log("VARIANT_GROUP_ALREADY_IMPLIED_ON_INTERNAL_USER")

tmpl_after = env["product.template"].sudo().search_count([])
sm_after = env["stock.move"].sudo().search_count([])
pv_after = env["product.value"].sudo().search_count([])
am_after = env["account.move"].sudo().search_count([])

log(f"AFTER product_template={tmpl_after} stock_move={sm_after} product_value={pv_after} account_move={am_after}")

assert tmpl_after == tmpl_before, "Gate C1 must not create product.template rows"
assert sm_after == sm_before, "Gate C1 must not create stock.move rows"
assert pv_after == pv_before, "Gate C1 must not create product.value rows"
assert am_after == am_before, "Gate C1 must not create account.move rows"

env.cr.commit()
log("COMMIT_OK")

LOG.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"WROTE {LOG}")
