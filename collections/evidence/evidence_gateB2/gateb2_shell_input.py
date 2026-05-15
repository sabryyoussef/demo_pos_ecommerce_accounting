# Gate B2 — analytic control layer (idempotent get-or-create).

Plan = env["account.analytic.plan"].sudo()
Account = env["account.analytic.account"].sudo()
comp = env.company


def get_or_create_root_plan(name, sequence):
    p = Plan.search([("name", "=", name), ("parent_id", "=", False)], limit=1)
    if p:
        return p
    return Plan.create(
        {
            "name": name,
            "parent_id": False,
            "sequence": sequence,
            "default_applicability": "optional",
        }
    )


def get_or_create_account(plan, name, code):
    dom = [("plan_id", "=", plan.id), ("code", "=", code), ("company_id", "=", comp.id)]
    a = Account.search(dom, limit=1)
    if a:
        return a
    return Account.create(
        {
            "name": name,
            "code": code,
            "plan_id": plan.id,
            "company_id": comp.id,
        }
    )


plan_channel = get_or_create_root_plan("Channel", 20)
plan_pos = get_or_create_root_plan("POS Location", 30)
plan_dept = get_or_create_root_plan("Department", 40)

print(
    "PLANS",
    plan_channel.id,
    plan_channel.name,
    "|",
    plan_pos.id,
    plan_pos.name,
    "|",
    plan_dept.id,
    plan_dept.name,
)

accounts_spec = [
    (plan_channel, "AN-CH-CORP", "AN-CH-CORP"),
    (plan_channel, "AN-CH-ECOM", "AN-CH-ECOM"),
    (plan_channel, "AN-CH-POS", "AN-CH-POS"),
    (plan_pos, "AN-POS-DXB-01", "AN-POS-DXB-01"),
    (plan_pos, "AN-POS-AUH-01", "AN-POS-AUH-01"),
    (plan_dept, "AN-DPT-SALES", "AN-DPT-SALES"),
    (plan_dept, "AN-DPT-OPS", "AN-DPT-OPS"),
    (plan_dept, "AN-DPT-HR", "AN-DPT-HR"),
]

created = []
for pl, nm, cd in accounts_spec:
    acc = get_or_create_account(pl, nm, cd)
    created.append(acc)
    assert acc.plan_id.id == pl.id, (acc.name, acc.plan_id, pl)
    print("ACCOUNT", cd, "-> plan", pl.name, "(id=%s)" % pl.id)

print("ACCOUNT_TOTAL_COMPANY", Account.search_count([("company_id", "=", comp.id)]))

# VAT201 still loads (no regression)
report = env.ref("l10n_ae.tax_report")
opts = report.get_options({})
lines = report._get_lines(opts)
print("VAT201_LINES", len(lines))

plans_json = Plan.get_relevant_plans()
print("GET_RELEVANT_PLANS_KEYS", list(plans_json.keys()) if isinstance(plans_json, dict) else type(plans_json))

# odoo-bin shell with stdin: Odoo always calls cr.rollback() after exec() unless we commit.
env.cr.commit()
print("COMMIT_OK")
