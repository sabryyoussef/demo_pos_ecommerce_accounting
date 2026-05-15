# -*- coding: utf-8 -*-
"""
Export demo_pos_accounting data from the live DB into module XML.

Run (odoo19/odoo19):
  python3 odoo-bin shell \\
    -c ../../config/projects/odoo_demo_pos_accounting.conf \\
    -d demo_pos_accounting --no-http \\
    < .../scripts/export_demo_database_xml.py

Writes: commercial_demo_story/data/demo_database/*.xml

Posted accounting, POS tickets, deliveries, and bank reconciliation are exported
via demo_bootstrap_transactions.xml (function call) — Odoo cannot import posted
account.move / paid pos.order reliably as static records.
"""
from __future__ import annotations

import re
from pathlib import Path

from lxml import etree
from lxml.builder import E
from odoo.modules.module import get_module_path

MODULE = "commercial_demo_story"
OUT_DIR = Path(get_module_path(MODULE)) / "data" / "demo_database"

SKIP_FIELD_TYPES = frozenset({"one2many", "properties", "properties_definition", "binary", "html"})
SKIP_FIELD_NAMES = frozenset(
    {
        "message_ids",
        "activity_ids",
        "message_follower_ids",
        "message_partner_ids",
        "message_attachment_count",
        "password",
        "totp_secret",
    }
)

EXPORT_SPECS = [
    (
        "product.category",
        [
            (
                "name",
                "in",
                [
                    "ALL PRODUCTS",
                    "RETAIL",
                    "BEVERAGES",
                    "FOOD",
                    "POS ITEMS",
                    "ECOM ITEMS",
                    "SERVICES",
                ],
            )
        ],
        [
            "name",
            "parent_id",
            "property_cost_method",
            "property_valuation",
            "property_account_income_categ_id",
            "property_account_expense_categ_id",
            "property_stock_valuation_account_id",
            "property_stock_journal",
        ],
        None,
    ),
    (
        "account.analytic.plan",
        [("name", "in", ["Channel", "POS Location", "Department"])],
        ["name", "sequence", "default_applicability", "parent_id"],
        None,
    ),
    (
        "account.analytic.account",
        [("code", "=like", "AN-%")],
        ["name", "code", "plan_id", "company_id"],
        lambda r: r.code or str(r.id),
    ),
    (
        "res.partner",
        [("ref", "=like", "FINCORP-%")],
        [
            "name",
            "ref",
            "company_id",
            "country_id",
            "is_company",
            "email",
            "customer_rank",
            "supplier_rank",
        ],
        lambda r: r.ref or str(r.id),
    ),
    (
        "res.users",
        [("login", "in", ["corp.sales.north", "corp.sales.south"])],
        ["name", "login", "company_id", "company_ids", "group_ids"],
        lambda r: r.login,
    ),
    (
        "crm.team",
        [("name", "=", "Corporate Direct — Horizon Retail")],
        ["name", "company_id", "use_leads", "user_id", "member_ids", "invoiced_target"],
        lambda r: r.name,
    ),
    (
        "product.template",
        [("default_code", "=like", "RET-G2%")],
        [
            "name",
            "default_code",
            "type",
            "list_price",
            "standard_price",
            "categ_id",
            "uom_id",
            "uom_po_id",
            "sale_ok",
            "purchase_ok",
            "is_storable",
            "taxes_id",
            "supplier_taxes_id",
            "description_sale",
        ],
        lambda r: r.default_code or str(r.id),
    ),
]

POS_CONFIG_FIELDS = [
    "name",
    "active",
    "company_id",
    "journal_id",
    "invoice_journal_id",
    "picking_type_id",
    "warehouse_id",
    "payment_method_ids",
    "basic_employee_ids",
    "advanced_employee_ids",
    "cash_control",
    "iface_print_skip_screen",
    "iface_tax_included",
    "group_pos_manager_id",
    "group_pos_user_id",
    "limit_categories",
]

JOURNAL_FIELDS = ["name", "code", "type", "company_id", "default_account_id"]
LOCATION_FIELDS = ["name", "usage", "location_id", "company_id", "barcode"]
PICKING_TYPE_FIELDS = [
    "name",
    "code",
    "warehouse_id",
    "sequence_code",
    "default_location_src_id",
    "default_location_dest_id",
    "company_id",
]
PAYMENT_METHOD_FIELDS = [
    "name",
    "journal_id",
    "company_id",
    "is_cash_count",
    "split_transactions",
    "use_payment_terminal",
]
PRODUCT_PRODUCT_FIELDS = ["product_tmpl_id", "default_code", "barcode", "active"]
FORCE_EXPORT_FIELDS = {
    "pos.config": frozenset(
        {
            "name",
            "active",
            "company_id",
            "journal_id",
            "invoice_journal_id",
            "picking_type_id",
            "warehouse_id",
            "payment_method_ids",
        }
    ),
    "product.product": frozenset({"product_tmpl_id", "default_code"}),
}
STOCK_QUANT_FIELDS = ["product_id", "location_id", "quantity", "inventory_quantity"]
SALE_ORDER_FIELDS = [
    "name",
    "partner_id",
    "state",
    "company_id",
    "team_id",
    "user_id",
    "pricelist_id",
    "payment_term_id",
    "client_order_ref",
]
SALE_LINE_FIELDS = [
    "order_id",
    "product_id",
    "product_uom_qty",
    "price_unit",
    "name",
    "product_uom_id",
]


def _slug(text, max_len=48):
    s = re.sub(r"[^a-zA-Z0-9_]+", "_", (text or "rec").strip()).strip("_").lower()
    return (s[:max_len] or "rec").rstrip("_")


def _dedupe_records(records, key_fn):
    if not key_fn:
        return records
    best = {}
    for rec in records.sorted("id"):
        key = key_fn(rec)
        if key not in best:
            best[key] = rec
    return records.browse([r.id for r in best.values()])


def _ensure_xmlid(env, record, local_id):
    imd = env["ir.model.data"].sudo()
    existing = imd.search([("module", "=", MODULE), ("name", "=", local_id)], limit=1)
    if existing and existing.res_id != record.id:
        existing.unlink()
    if not existing:
        imd.create(
            {
                "module": MODULE,
                "name": local_id,
                "model": record._name,
                "res_id": record.id,
                "noupdate": True,
            }
        )
    return local_id


def _record_xmlid_key(record):
    for attr in ("default_code", "ref", "code", "login", "name", "complete_name"):
        if attr in record._fields:
            val = record[attr]
            if val:
                return str(val)
    return str(record.id)


def _xmlid_for_record(env, record, *, auto_assign=False):
    if not record:
        return None
    imd = env["ir.model.data"].sudo().search(
        [("model", "=", record._name), ("res_id", "=", record.id)], limit=1
    )
    if imd:
        return f"{imd.module}.{imd.name}"
    if auto_assign:
        local = f"demo_{record._name.replace('.', '_')}_{_slug(_record_xmlid_key(record))}"
        _ensure_xmlid(env, record, local)
        return f"{MODULE}.{local}"
    return None


def _assign_demo_xmlids(env, model, records, key_fn):
    for rec in records:
        local = f"demo_{model.replace('.', '_')}_{_slug(key_fn(rec))}"
        _ensure_xmlid(env, rec, local)


def _serialize_field(record, field, default_get, *, force=False):
    name = field.name
    if name in SKIP_FIELD_NAMES or field.type in SKIP_FIELD_TYPES:
        return None
    value = record[name]
    default = default_get.get(name)
    if not force and (
        (not value and not default)
        or field.convert_to_cache(value, record)
        == field.convert_to_cache(default, record)
    ):
        return None

    if field.type == "boolean":
        return E.field(name=name, eval=str(value))
    if field.type in ("integer", "float"):
        return E.field(name=name, eval=str(value))
    if field.type == "many2one":
        if not value:
            return E.field(name=name, eval="False")
        xid = _xmlid_for_record(record.env, value, auto_assign=True)
        if not xid:
            raise ValueError(f"Missing xmlid for {value} ({value._name} id={value.id})")
        return E.field(name=name, ref=xid)
    if field.type == "many2many":
        if not value:
            return E.field(name=name, eval="[(6, 0, [])]")
        refs = []
        for v in value:
            xid = _xmlid_for_record(record.env, v, auto_assign=True)
            if not xid:
                raise ValueError(f"Missing xmlid for {v}")
            refs.append(f"ref('{xid}')")
        return E.field(name=name, eval="[(6, 0, [%s])]" % ", ".join(refs))
    if field.type in ("date", "datetime"):
        return E.field(field.to_string(value), name=name)
    if field.type == "selection":
        return E.field(str(value), name=name)
    return E.field(str(value), name=name)


def _sort_by_parent(records, parent_field="parent_id"):
    by_id = {r.id: r for r in records}
    depth_cache = {}

    def depth(rec):
        if rec.id in depth_cache:
            return depth_cache[rec.id]
        parent = rec[parent_field]
        if not parent or parent.id not in by_id:
            depth_cache[rec.id] = 0
        else:
            depth_cache[rec.id] = depth(parent) + 1
        return depth_cache[rec.id]

    return records.sorted(key=lambda r: (depth(r), r.id))


def _serialize_records(env, model_name, records, field_names):
    Model = env[model_name].sudo()
    if model_name == "product.category" and "parent_id" in Model._fields:
        records = _sort_by_parent(records)
    fields = [f for f in field_names if f in Model._fields]
    force_set = FORCE_EXPORT_FIELDS.get(model_name, frozenset())
    default_get = Model.default_get(fields)
    nodes = []
    for rec in records:
        imd = env["ir.model.data"].sudo().search(
            [("module", "=", MODULE), ("model", "=", model_name), ("res_id", "=", rec.id)],
            limit=1,
        )
        if not imd:
            continue
        field_nodes = []
        for fname in fields:
            field = Model._fields[fname]
            try:
                node = _serialize_field(
                    rec, field, default_get, force=fname in force_set
                )
            except ValueError as exc:
                print(f"WARN {model_name} {rec.id}.{fname}: {exc}")
                node = None
            if node is not None:
                field_nodes.append(node)
        if field_nodes:
            nodes.append(E.record(*field_nodes, id=imd.name, model=model_name))
    return nodes


def _write_xml(path, nodes, noupdate=True):
    path.parent.mkdir(parents=True, exist_ok=True)
    root = E.odoo(*nodes, noupdate="1") if noupdate else E.odoo(*nodes)
    content = etree.tostring(root, pretty_print=True, encoding="UTF-8", xml_declaration=True)
    path.write_bytes(content)


def _export_model(env, model_name, domain, field_names, key_fn, written):
    Model = env[model_name].sudo()
    order = "parent_id, id" if model_name == "product.category" else "id"
    records = Model.search(domain, order=order)
    records = _dedupe_records(records, key_fn)
    if not records:
        print(f"SKIP {model_name}: no records")
        return

    if model_name == "product.template":
        key_fn = lambda r: r.default_code or str(r.id)
    elif model_name == "account.analytic.account":
        key_fn = lambda r: r.code or str(r.id)
    elif model_name == "res.partner":
        key_fn = lambda r: r.ref or str(r.id)
    elif key_fn is None:
        key_fn = lambda r: r.name or str(r.id)

    _assign_demo_xmlids(env, model_name, records, key_fn)

    if model_name == "product.template":
        for tmpl in records:
            for prod in tmpl.product_variant_ids:
                local = f"demo_product_product_{_slug(tmpl.default_code)}"
                _ensure_xmlid(env, prod, local)

    nodes = _serialize_records(env, model_name, records, field_names)
    if not nodes:
        print(f"SKIP {model_name}: nothing serializable")
        return
    fname = model_name.replace(".", "_") + ".xml"
    out = OUT_DIR / fname
    _write_xml(out, nodes)
    written.append(out)
    print(f"WROTE {out} ({len(nodes)} records)")


def _gather_pos_demo(env):
    Config = env["pos.config"].sudo()
    configs = Config.search([("name", "=like", "POS-%")], order="name")
    journals = (configs.mapped("journal_id") | configs.mapped("invoice_journal_id")).filtered(
        lambda j: j and j.type in ("cash", "sale", "bank")
    )
    # POS-specific cash journals (exclude generic POSS if duplicated)
    pos_journals = env["account.journal"].sudo().search(
        [
            ("company_id", "=", env.company.id),
            "|",
            ("code", "=like", "POS%"),
            ("name", "ilike", "POS "),
        ]
    )
    journals = (journals | pos_journals).sorted("id")

    picking_types = configs.mapped("picking_type_id")
    locations = (
        picking_types.mapped("default_location_src_id")
        | picking_types.mapped("default_location_dest_id")
    )
    locations = locations.filtered(lambda l: l.usage == "internal" and "POS" in (l.complete_name or ""))
    payment_methods = configs.mapped("payment_method_ids")
    employees = configs.mapped("basic_employee_ids") | configs.mapped("advanced_employee_ids")
    pos_staff = env["hr.employee"].sudo().search(
        [
            ("company_id", "=", env.company.id),
            "|",
            ("name", "ilike", "cashier"),
            ("name", "ilike", "POS"),
        ]
    )
    employees = employees | pos_staff
    return {
        "configs": configs,
        "journals": journals,
        "locations": locations,
        "picking_types": picking_types,
        "payment_methods": payment_methods,
        "employees": employees,
    }


def _export_pos_bundle(env, written):
    bundle = _gather_pos_demo(env)
    key_journal = lambda r: r.code or str(r.id)
    key_loc = lambda r: _slug(r.complete_name or r.name)
    key_pt = lambda r: _slug(r.name or r.code or str(r.id))
    key_pm = lambda r: _slug(r.name)
    key_cfg = lambda r: _slug(r.name)

    corp_employees = env["hr.employee"].sudo().search(
        [("user_id.login", "in", ["corp.sales.north", "corp.sales.south"])]
    )
    employees = _dedupe_records(
        bundle["employees"] | corp_employees, lambda r: _slug(r.name or str(r.id))
    )
    if employees:
        _assign_demo_xmlids(env, "hr.employee", employees, lambda r: _slug(r.name or str(r.id)))
        emp_nodes = _serialize_records(
            env, "hr.employee", employees, ["name", "user_id", "company_id", "job_title"]
        )
        if emp_nodes:
            out = OUT_DIR / "hr_employee.xml"
            _write_xml(out, emp_nodes)
            written.append(out)
            print(f"WROTE {out} ({len(emp_nodes)} records)")

    for model, records, fields, key_fn in [
        ("account.journal", bundle["journals"], JOURNAL_FIELDS, key_journal),
        ("stock.location", bundle["locations"], LOCATION_FIELDS, key_loc),
        ("stock.picking.type", bundle["picking_types"], PICKING_TYPE_FIELDS, key_pt),
        ("pos.payment.method", bundle["payment_methods"], PAYMENT_METHOD_FIELDS, key_pm),
    ]:
        records = _dedupe_records(records, key_fn)
        if not records:
            print(f"SKIP {model}: empty bundle")
            continue
        _assign_demo_xmlids(env, model, records, key_fn)
        nodes = _serialize_records(env, model, records, fields)
        if nodes:
            out = OUT_DIR / f"{model.replace('.', '_')}.xml"
            _write_xml(out, nodes)
            written.append(out)
            print(f"WROTE {out} ({len(nodes)} records)")

    configs = bundle["configs"]
    _assign_demo_xmlids(env, "pos.config", configs, key_cfg)
    pos_fields = list(POS_CONFIG_FIELDS)
    nodes = _serialize_records(env, "pos.config", configs, pos_fields)
    if nodes:
        out = OUT_DIR / "pos_config.xml"
        _write_xml(out, nodes)
        written.append(out)
        print(f"WROTE {out} ({len(nodes)} records)")


def _export_product_products(env, written):
    templates = env["product.template"].sudo().search([("default_code", "=like", "RET-G2%")])
    products = templates.mapped("product_variant_ids")
    line_products = env["sale.order.line"].sudo().search([]).mapped("product_id")
    quant_products = env["stock.quant"].sudo().search([("quantity", ">", 0)]).mapped("product_id")
    products = (products | line_products | quant_products).filtered(
        lambda p: p and (p.default_code or p.product_tmpl_id.default_code)
    )
    _assign_demo_xmlids(
        env,
        "product.product",
        products,
        lambda r: f"{r.product_tmpl_id.default_code or 'p'}_{r.id}",
    )
    nodes = _serialize_records(env, "product.product", products, PRODUCT_PRODUCT_FIELDS)
    if nodes:
        out = OUT_DIR / "product_product.xml"
        _write_xml(out, nodes)
        written.append(out)
        print(f"WROTE {out} ({len(nodes)} records)")


def _export_stock_quants(env, written):
    wh = env["stock.warehouse"].search([("company_id", "=", env.company.id)], limit=1)
    if not wh:
        return
    stock_loc = wh.lot_stock_id
    products = env["product.product"].sudo().search(
        [("default_code", "=like", "RET-G2%"), ("is_storable", "=", True)]
    )
    quants = env["stock.quant"].sudo().search(
        [("location_id", "=", stock_loc.id), ("product_id", "in", products.ids), ("quantity", ">", 0)]
    )
    _assign_demo_xmlids(
        env,
        "stock.quant",
        quants,
        lambda r: f"{r.product_id.default_code}_{r.location_id.id}",
    )
    nodes = _serialize_records(env, "stock.quant", quants, STOCK_QUANT_FIELDS)
    if nodes:
        out = OUT_DIR / "stock_quant.xml"
        _write_xml(out, nodes)
        written.append(out)
        print(f"WROTE {out} ({len(nodes)} records)")


def _export_sale_orders(env, written):
    orders = env["sale.order"].sudo().search([], order="id")
    partners = orders.mapped("partner_id").filtered(
        lambda p: p and (not p.ref or not p.ref.startswith("FINCORP"))
    )
    if partners:
        _assign_demo_xmlids(
            env,
            "res.partner",
            partners,
            lambda r: _slug(r.name or str(r.id)),
        )
        partner_nodes = _serialize_records(
            env,
            "res.partner",
            partners,
            ["name", "company_id", "country_id", "email", "customer_rank"],
        )
        if partner_nodes:
            existing = OUT_DIR / "res_partner.xml"
            root = etree.parse(str(existing)).getroot() if existing.is_file() else E.odoo(noupdate="1")
            root.extend(partner_nodes)
            existing.write_bytes(
                etree.tostring(root, pretty_print=True, encoding="UTF-8", xml_declaration=True)
            )
            print(f"MERGED {len(partner_nodes)} partners into res_partner.xml")

    _assign_demo_xmlids(env, "sale.order", orders, lambda r: _slug(r.name or str(r.id)))
    order_nodes = _serialize_records(env, "sale.order", orders, SALE_ORDER_FIELDS)
    lines = orders.mapped("order_line").filtered(lambda l: not l.display_type)
    _assign_demo_xmlids(
        env,
        "sale.order.line",
        lines,
        lambda r: f"{r.order_id.name}_{r.id}",
    )
    line_nodes = _serialize_records(env, "sale.order.line", lines, SALE_LINE_FIELDS)
    if order_nodes:
        out = OUT_DIR / "sale_order.xml"
        _write_xml(out, order_nodes)
        written.append(out)
        print(f"WROTE {out} ({len(order_nodes)} records)")
    if line_nodes:
        out = OUT_DIR / "sale_order_line.xml"
        _write_xml(out, line_nodes)
        written.append(out)
        print(f"WROTE {out} ({len(line_nodes)} records)")


def _write_bootstrap_xml():
    path = OUT_DIR / "demo_bootstrap_transactions.xml"
    root = E.odoo(
        E.function(
            model="commercial.demo.operations.loader",
            name="run_all_phases",
        ),
        noupdate="1",
    )
    path.write_bytes(
        etree.tostring(root, pretty_print=True, encoding="UTF-8", xml_declaration=True)
    )
    print(f"WROTE {path}")


def main(env):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    written = []

    for spec in EXPORT_SPECS:
        model_name, domain, field_names, key_fn = spec
        _export_model(env, model_name, domain, field_names, key_fn, written)

    _export_product_products(env, written)
    _export_pos_bundle(env, written)
    _export_stock_quants(env, written)
    _export_sale_orders(env, written)
    _write_bootstrap_xml()

    print("\nAdd to __manifest__.py 'data' (before menu.xml):")
    for name in sorted(p.name for p in written):
        print(f'        "data/demo_database/{name}",')
    print('        "data/demo_database/demo_bootstrap_transactions.xml",')


main(env)
