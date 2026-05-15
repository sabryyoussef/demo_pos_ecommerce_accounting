import os

comp = env.company
ae = env.ref("base.ae")
aed = env.ref("base.AED")
dubai = env["res.country.state"].search(
    [("code", "=", "DU"), ("country_id", "=", ae.id)], limit=1
)
comp.partner_id.write(
    {
        "name": "Horizon Retail Group LLC",
        "country_id": ae.id,
        "state_id": dubai.id,
        "vat": "100345678900003",
    }
)
comp.write(
    {
        "name": "Horizon Retail Group LLC",
        "currency_id": aed.id,
        "fiscalyear_last_month": "12",
        "fiscalyear_last_day": 31,
    }
)
print(
    "COMPANY",
    comp.name,
    comp.currency_id.name,
    comp.partner_id.vat,
    comp.fiscalyear_last_month,
    comp.fiscalyear_last_day,
)

Tax = env["account.tax"]
cdom = ["|", ("company_id", "=", False), ("company_id", "=", comp.id)]
sale_5 = Tax.search([("amount", "=", 5), ("type_tax_use", "=", "sale")] + cdom)
sale_0 = Tax.search([("amount", "=", 0), ("type_tax_use", "=", "sale")] + cdom)
exempt_like = Tax.search(
    [
        ("type_tax_use", "=", "sale"),
        ("amount", "=", 0),
        "|",
        ("name", "ilike", "EX"),
        ("name", "ilike", "Out of Scope"),
    ]
    + cdom,
    limit=10,
)
print("TAX_SALE_5_COUNT", len(sale_5))
print("TAX_SALE_0_COUNT", len(sale_0))
print("TAX_EXEMPT_LIKE", exempt_like.mapped("name"))

accounts = env["account.account"].search([("company_ids", "in", comp.id)])
print("CHART_ACCOUNTS", len(accounts))

fps = env["account.fiscal.position"].search([("company_id", "=", comp.id)])
print("FISCAL_POSITIONS", len(fps), fps[:8].mapped("name"))

report = env.ref("l10n_ae.tax_report")
opts = report.get_options({})
lines = report._get_lines(opts)
print("VAT201_LINES", len(lines))

for pc in env["pos.config"].search([]):
    pc.write(
        {
            "name": "VALIDATION ONLY – Gate A POS (not an operational branch)",
        }
    )
    print("POS_RENAMED", pc.id, pc.name)

admin = env["res.users"].search([("login", "=", "admin")], limit=1)
admin.write({"password": os.environ["GATEB1_ADMIN_PW"]})
print("ADMIN_PASSWORD_ROTATED", admin.login)
