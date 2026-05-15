# Gate D4 part 1 — ensure small eCommerce catalog slice (5 RET-G2 templates) published; record baselines.
# No sale orders created here. Commits publication only.

import json
from pathlib import Path

for LOG, MAN in (
    (
        Path("/home/sabry3/sabry_backup/odoo_base/base_odoo_19/projects/demo_pos_accounting/evidence_gateD4/gateD4_part1_shell.txt"),
        Path("/home/sabry3/sabry_backup/odoo_base/base_odoo_19/projects/demo_pos_accounting/evidence_gateD4/gateD4_manifest.json"),
    ),
    (
        Path("/mnt/sabry_backup/odoo_base/base_odoo_19/projects/demo_pos_accounting/evidence_gateD4/gateD4_part1_shell.txt"),
        Path("/mnt/sabry_backup/odoo_base/base_odoo_19/projects/demo_pos_accounting/evidence_gateD4/gateD4_manifest.json"),
    ),
):
    if LOG.parent.is_dir():
        break
else:
    LOG = Path("gateD4_part1_shell.txt")
    MAN = Path("gateD4_manifest.json")

lines = []


def log(msg):
    lines.append(msg)
    print(msg)


if not env["ir.module.module"].search([("name", "=", "website_sale"), ("state", "=", "installed")], limit=1):
    raise RuntimeError("website_sale not installed")

# COD is hidden on the website unless the selected carrier allows it (delivery.payment_provider override).
for carrier in env["delivery.carrier"].sudo().search([("active", "=", True)]):
    if not carrier.allow_cash_on_delivery:
        carrier.write({"allow_cash_on_delivery": True})
        log(f"ALLOW_COD_ON_CARRIER id={carrier.id}")

PT = env["product.template"].sudo()
PP = env["product.product"].sudo()

# Exactly 5 SKUs / templates for Gate D4 (subset of RET-G2; already eCom-enabled in Gate C2)
SKUS = [
    "RET-G2-BEV-WAT500",
    "RET-G2-BEV-OJ1L",
    "RET-G2-SNK-OAT35",
    "RET-G2-PAR-TSH-M",
    "RET-G2-PAR-MUG350-BLA",
]
tmpls = PT.browse(())
paths = {}
for sku in SKUS:
    p = PP.search([("default_code", "=", sku)], limit=1)
    if not p:
        raise RuntimeError(f"Missing product {sku}")
    t = p.product_tmpl_id
    tmpls |= t
    url = p.website_url or t.website_url
    if not url:
        raise RuntimeError(f"No website_url for {sku}")
    paths[sku] = url

# website_sale: is_published on template
for t in tmpls:
    if not t.is_published:
        t.write({"is_published": True})
        log(f"PUBLISH tmpl_id={t.id} name={t.name!r}")
    else:
        log(f"ALREADY_PUBLISHED tmpl_id={t.id}")

SO = env["sale.order"].sudo()
AM = env["account.move"].sudo()
SM = env["stock.move"].sudo()

so_max = SO.search([], order="id desc", limit=1).id if SO.search_count([]) else 0
ae = env.ref("base.ae")
st = env["res.country.state"].sudo().search([("country_id", "=", ae.id), ("code", "=", "DXB")], limit=1)
if not st:
    st = env["res.country.state"].sudo().search([("country_id", "=", ae.id), ("name", "ilike", "Dubai")], limit=1)
if not st:
    raise RuntimeError("No Dubai state for AE")
manifest = {
    "gate": "D4_part1",
    "test_email": "gate4_ecommerce_flow@example.invalid",
    "product_template_ids": sorted(tmpls.ids),
    "product_slugs_paths": paths,
    "shop_paths": {
        "water": paths["RET-G2-BEV-WAT500"],
        "oj": paths["RET-G2-BEV-OJ1L"],
        "oat": paths["RET-G2-SNK-OAT35"],
    },
    "baseline_sale_order_max_id": so_max,
    "baseline_sale_order_count": SO.search_count([]),
    "baseline_account_move_count": AM.search_count([]),
    "baseline_stock_move_count": SM.search_count([]),
    "payment_cod_provider_id": 22,
    "payment_cod_method_radio_id_hint": 215,
    "country_ae_id": ae.id,
    "state_dubai_id": st.id,
}
MAN.parent.mkdir(parents=True, exist_ok=True)
MAN.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
log(f"WROTE_MANIFEST {MAN}")

env.cr.commit()
log("COMMIT_OK_PART1_PUBLICATION")

LOG.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"WROTE {LOG}")
