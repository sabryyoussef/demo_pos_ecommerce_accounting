# Gate C2 — controlled demo retail catalog (10–20 templates), variants, POS/eCom flags.
# No stock moves, no SO/PO/invoices, no POS orders, no inventory adjustments.

from pathlib import Path

from odoo import Command

for LOG in (
    Path("/home/sabry3/sabry_backup/odoo_base/base_odoo_19/projects/demo_pos_accounting/evidence_gateC2/gateC2_shell.txt"),
    Path("/mnt/sabry_backup/odoo_base/base_odoo_19/projects/demo_pos_accounting/evidence_gateC2/gateC2_shell.txt"),
):
    if LOG.parent.is_dir():
        break
else:
    LOG = Path("gateC2_shell.txt")

lines = []


def log(msg):
    lines.append(msg)
    print(msg)


comp = env.company.sudo()
PT = env["product.template"].sudo().with_context(disable_auto_revaluation=True)
PP = env["product.product"].sudo().with_context(disable_auto_revaluation=True)
PAV = env["product.attribute.value"].sudo()
PosCat = env["pos.category"].sudo()

sm0 = env["stock.move"].sudo().search_count([])
am0 = env["account.move"].sudo().search_count([])
sq0 = env["stock.quant"].sudo().search_count([])
pv0 = env["product.value"].sudo().search_count([])
tmpl0 = PT.search_count([])

log(f"BASELINE stock_move={sm0} account_move={am0} stock_quant={sq0} product_value={pv0} product_template={tmpl0}")

PREFIX = "RET-G2-"
if PP.search_count([("default_code", "=ilike", f"{PREFIX}%")]):
    log("SKIP_CREATE_ALREADY_HAVE_RET_G2_PRODUCTS")
    LOG.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"WROTE {LOG}")
    raise SystemExit(0)

# --- Gate C1 retail categories (named hierarchy) ---
PC = env["product.category"].sudo()


def categ(*names):
    cur = None
    for n in names:
        dom = [("name", "=", n)]
        if cur:
            dom.append(("parent_id", "=", cur.id))
        else:
            dom.append(("parent_id", "=", False))
        nxt = PC.search(dom, limit=1)
        if not nxt:
            raise RuntimeError(f"Missing product.category {n!r} under {cur.name if cur else 'root'}")
        cur = nxt
    return cur


categ_retail = categ("ALL PRODUCTS", "RETAIL")
categ_bev = categ("ALL PRODUCTS", "RETAIL", "BEVERAGES")
categ_food = categ("ALL PRODUCTS", "RETAIL", "FOOD")
categ_srv = categ("ALL PRODUCTS", "SERVICES")
categ_ecom = categ("ALL PRODUCTS", "ECOM ITEMS")

sale_tax = comp.account_sale_tax_id
purchase_tax = comp.account_purchase_tax_id
u_unit = env.ref("uom.product_uom_unit")

attr_size = env["product.attribute"].sudo().search([("name", "=", "size")], limit=1) or env["product.attribute"].sudo().browse(7)
attr_color = env["product.attribute"].sudo().search([("name", "=", "color")], limit=1) or env["product.attribute"].sudo().browse(1)


def ensure_pav(attr, name, **extra):
    v = PAV.search([("attribute_id", "=", attr.id), ("name", "=", name)], limit=1)
    if v:
        return v
    vals = {"attribute_id": attr.id, "name": name, **extra}
    return PAV.create(vals)


v_s = ensure_pav(attr_size, "S")
v_m = ensure_pav(attr_size, "M")
v_l = ensure_pav(attr_size, "L")
v_blk = ensure_pav(attr_color, "Black", html_color="#1a1a1a")
v_slv = ensure_pav(attr_color, "Silver", html_color="#c0c0c0")
log(f"ATTR_VALUES size=({v_s.id},{v_m.id},{v_l.id}) color=({v_blk.id},{v_slv.id})")


def ensure_pos(name, seq=10):
    c = PosCat.search([("name", "=", name)], limit=1)
    if c:
        return c
    return PosCat.create({"name": name, "sequence": seq})


pc_bev = ensure_pos("Beverages", 10)
pc_snk = ensure_pos("Snacks", 20)
pc_gen = ensure_pos("General", 30)
pc_app = ensure_pos("Apparel", 40)
pc_srv = ensure_pos("Services", 50)
log(f"POS_CATEGORIES ids=({pc_bev.id},{pc_snk.id},{pc_gen.id},{pc_app.id},{pc_srv.id})")

# Barcode block: synthetic 13-digit codes, unique (629 001 0000xxx — demo block; not GS1-registered).
BC = iter(range(6290010001011, 6290010001300))


def next_bc():
    return str(next(BC))


def base_tmpl_vals(
    name,
    code,
    categ,
    list_price,
    standard_price,
    *,
    ptype="consu",
    pos=True,
    ecom=False,
    purchase=True,
    pos_cats=None,
    uom=None,
):
    uom = uom or u_unit
    vals = {
        "name": name,
        "type": ptype,
        "categ_id": categ.id,
        "list_price": list_price,
        "standard_price": standard_price,
        "sale_ok": True,
        "purchase_ok": purchase if ptype != "service" else False,
        "available_in_pos": pos,
        "is_storable": False,
        "uom_id": uom.id,
        "taxes_id": [Command.set([sale_tax.id])] if sale_tax else [Command.clear()],
        "supplier_taxes_id": [Command.set([purchase_tax.id])] if (purchase and purchase_tax) else [Command.clear()],
        "pos_categ_ids": [Command.set([x.id for x in (pos_cats or [])])] if pos_cats else [Command.clear()],
    }
    if env["ir.module.module"].search([("name", "=", "website_sale"), ("state", "=", "installed")], limit=1):
        vals["is_published"] = bool(ecom)
    if ptype == "service":
        vals["purchase_ok"] = False
    return vals


created = []

# --- Simple goods (single variant each) ---
simple = [
    (
        "Still Spring Water 500 ml",
        f"{PREFIX}BEV-WAT500",
        categ_bev,
        2.0,
        0.9,
        {"pos_cats": [pc_bev], "ecom": True},
    ),
    (
        "Sparkling Mineral Water 330 ml",
        f"{PREFIX}BEV-SPK330",
        categ_bev,
        2.5,
        1.1,
        {"pos_cats": [pc_bev], "ecom": False},
    ),
    (
        "Orange Juice Not From Concentrate 1 L",
        f"{PREFIX}BEV-OJ1L",
        categ_bev,
        8.5,
        4.2,
        {"pos_cats": [pc_bev], "ecom": True},
    ),
    (
        "Lemon Flavour Iced Tea 500 ml",
        f"{PREFIX}BEV-TEA500",
        categ_bev,
        3.5,
        1.5,
        {"pos_cats": [pc_bev], "ecom": False},
    ),
    (
        "Salted Potato Crisps 40 g",
        f"{PREFIX}SNK-CRP40",
        categ_food,
        3.0,
        1.4,
        {"pos_cats": [pc_snk], "ecom": False},
    ),
    (
        "Dry Roasted Almonds 100 g",
        f"{PREFIX}SNK-ALM100",
        categ_food,
        12.0,
        6.5,
        {"pos_cats": [pc_snk], "ecom": True},
    ),
    (
        "Dark Chocolate Tablet 45 g",
        f"{PREFIX}SNK-CHO45",
        categ_food,
        4.5,
        2.0,
        {"pos_cats": [pc_snk], "ecom": False},
    ),
    (
        "Soft Oat Granola Bar 35 g",
        f"{PREFIX}SNK-OAT35",
        categ_food,
        2.8,
        1.2,
        {"pos_cats": [pc_snk], "ecom": True},
    ),
    (
        "Cotton Carry Bag",
        f"{PREFIX}RTL-BAG01",
        categ_retail,
        1.5,
        0.5,
        {"pos_cats": [pc_gen], "ecom": False},
    ),
    (
        "Alkaline AA Batteries 4-Pack",
        f"{PREFIX}RTL-BAT4",
        categ_retail,
        6.0,
        3.2,
        {"pos_cats": [pc_gen], "ecom": False},
    ),
    (
        "USB-C Sync Cable 1 m",
        f"{PREFIX}RTL-USB1M",
        categ_ecom,
        18.0,
        7.5,
        {"pos_cats": [pc_gen], "ecom": True, "purchase": True},
    ),
]

for title, code, cat, lp, cost, extra in simple:
    vals = base_tmpl_vals(title, code, cat, lp, cost, **extra)
    t = PT.create(vals)
    v = t.product_variant_ids[:1]
    bc = next_bc()
    v.write({"default_code": code, "barcode": bc})
    created.append((t.id, code, bc))
    log(f"CREATE_SIMPLE tmpl={t.id} code={code} barcode={bc}")

# --- Services ---
srv_wrap = PT.create(
    base_tmpl_vals(
        "Gift Wrapping",
        f"{PREFIX}SRV-WRAP",
        categ_srv,
        5.0,
        0.0,
        ptype="service",
        pos=True,
        ecom=False,
        purchase=False,
        pos_cats=[pc_srv],
    )
)
wvar = srv_wrap.product_variant_ids[:1]
wbc = next_bc()
wvar.write({"default_code": f"{PREFIX}SRV-WRAP", "barcode": wbc})
created.append((srv_wrap.id, f"{PREFIX}SRV-WRAP", wbc))
log(f"CREATE_SERVICE tmpl={srv_wrap.id} code={PREFIX}SRV-WRAP")

srv_del = PT.create(
    base_tmpl_vals(
        "Local Same-Day Delivery",
        f"{PREFIX}SRV-DEL",
        categ_srv,
        15.0,
        0.0,
        ptype="service",
        pos=False,
        ecom=True,
        purchase=False,
        pos_cats=[],
    )
)
dvar = srv_del.product_variant_ids[:1]
dbc = next_bc()
dvar.write({"default_code": f"{PREFIX}SRV-DEL", "barcode": dbc})
created.append((srv_del.id, f"{PREFIX}SRV-DEL", dbc))
log(f"CREATE_SERVICE tmpl={srv_del.id} code={PREFIX}SRV-DEL ecom_only")

# --- T-shirt variants (Size S/M/L) ---
shirt = PT.create(
    {
        **base_tmpl_vals(
            "Cotton Crew Neck T-Shirt",
            f"{PREFIX}PAR-TSH",
            categ_retail,
            49.0,
            22.0,
            pos=True,
            ecom=True,
            purchase=True,
            pos_cats=[pc_app],
        ),
        "attribute_line_ids": [
            Command.create(
                {
                    "attribute_id": attr_size.id,
                    "value_ids": [Command.set([v_s.id, v_m.id, v_l.id])],
                }
            )
        ],
    }
)
for pv in shirt.product_variant_ids:
    pavs = pv.product_template_attribute_value_ids.mapped("product_attribute_value_id")
    sz = pavs.filtered(lambda x: x.attribute_id == attr_size)[:1]
    suffix = sz.name or "X"
    code = f"{PREFIX}PAR-TSH-{suffix}"
    bc = next_bc()
    pv.write({"default_code": code, "barcode": bc})
    log(f"CREATE_VARIANT shirt variant={pv.id} code={code} barcode={bc}")
created.append((shirt.id, f"{PREFIX}PAR-TSH-*", "multi"))

# --- Mug variants (Color Black / Silver) ---
mug = PT.create(
    {
        **base_tmpl_vals(
            "Insulated Travel Mug 350 ml",
            f"{PREFIX}PAR-MUG350",
            categ_retail,
            65.0,
            28.0,
            pos=True,
            ecom=True,
            purchase=True,
            pos_cats=[pc_gen],
        ),
        "attribute_line_ids": [
            Command.create(
                {
                    "attribute_id": attr_color.id,
                    "value_ids": [Command.set([v_blk.id, v_slv.id])],
                }
            )
        ],
    }
)
for pv in mug.product_variant_ids:
    pavs = pv.product_template_attribute_value_ids.mapped("product_attribute_value_id")
    col = pavs.filtered(lambda x: x.attribute_id == attr_color)[:1]
    slug_map = {"Black": "BLK", "Silver": "SIL"}
    slug = slug_map.get((col.name or "").strip(), ((col.name or "X")[:3]).upper())
    code = f"{PREFIX}PAR-MUG350-{slug}"
    bc = next_bc()
    pv.write({"default_code": code, "barcode": bc})
    log(f"CREATE_VARIANT mug variant={pv.id} code={code} barcode={bc}")
created.append((mug.id, f"{PREFIX}PAR-MUG350-*", "multi"))

# --- POS domain smoke (config 5 = POS-DXB-01) ---
pos_cfg = env["pos.config"].sudo().browse(5)
if pos_cfg.exists():
    dom = env["product.template"]._load_pos_data_domain({}, pos_cfg)
    n_pos = PT.search_count(dom)
    log(f"POS_LOAD_DOMAIN_COUNT config={pos_cfg.id} templates={n_pos}")
else:
    log("POS_CONFIG_5_MISSING_SKIP_DOMAIN")

assert env["stock.move"].sudo().search_count([]) == sm0
assert env["account.move"].sudo().search_count([]) == am0
assert env["stock.quant"].sudo().search_count([]) == sq0
assert env["product.value"].sudo().search_count([]) == pv0

# Barcode uniqueness
bc_ids = PP.search([("barcode", "!=", False), ("barcode", "!=", "")])
seen = {}
for p in bc_ids:
    b = p.barcode
    if b in seen and seen[b] != p.id:
        raise RuntimeError(f"Duplicate barcode {b!r} products {seen[b]} {p.id}")
    seen[b] = p.id

# default_code uniqueness (non-empty)
codes = PP.search([("default_code", "!=", False), ("default_code", "!=", "")])
code_set = {}
for p in codes:
    c = (p.default_code or "").strip()
    if not c:
        continue
    if c in code_set and code_set[c] != p.id:
        raise RuntimeError(f"Duplicate default_code {c!r} products {code_set[c]} {p.id}")
    code_set[c] = p.id

log(f"UNIQUENESS_OK barcodes_distinct={len(seen)} default_codes_distinct={len(code_set)}")

env.cr.commit()
log("COMMIT_OK")
log(f"CREATED_SUMMARY templates_delta={PT.search_count([]) - tmpl0}")

LOG.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"WROTE {LOG}")
