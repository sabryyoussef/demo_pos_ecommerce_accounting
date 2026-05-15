# -*- coding: utf-8 -*-
"""
Export demo_pos_accounting master data from the live DB into module XML.

Run from repo root (odoo19/odoo19):
  ../../venv19/bin/python3 odoo-bin shell \\
    -c ../../config/projects/odoo_demo_pos_accounting.conf \\
    -d demo_pos_accounting --no-http \\
    < ../../projects/demo_pos_accounting/custom_addons/commercial_demo_story/scripts/export_demo_database_xml.py

Writes: commercial_demo_story/data/demo_database/*.xml
"""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from lxml import etree
from lxml.builder import E
from odoo.modules.module import get_module_path

MODULE = "commercial_demo_story"
OUT_DIR = Path(get_module_path(MODULE)) / "data" / "demo_database"

# model -> (domain, field_names or None=all exportable scalars/relations)
EXPORT_SPECS = [
    (
        "product.category",
        [
            (
                "name",
                "in",
                ["ALL PRODUCTS", "RETAIL", "BEVERAGES", "FOOD", "POS ITEMS", "ECOM ITEMS", "SERVICES"],
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
    ),
    (
        "account.analytic.plan",
        [("name", "in", ["Channel", "POS Location", "Department"])],
        ["name", "sequence", "default_applicability", "parent_id"],
    ),
    (
        "account.analytic.account",
        [("code", "=like", "AN-%")],
        ["name", "code", "plan_id", "company_id"],
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
    ),
    (
        "crm.team",
        [("name", "=", "Corporate Direct — Horizon Retail")],
        ["name", "company_id", "use_leads", "user_id", "member_ids", "invoiced_target"],
    ),
]

SKIP_FIELD_TYPES = frozenset({"one2many", "properties", "properties_definition", "binary", "html"})
SKIP_FIELD_NAMES = frozenset(
    {
        "message_ids",
        "activity_ids",
        "message_follower_ids",
        "message_partner_ids",
        "message_attachment_count",
    }
)


def _slug(text, max_len=48):
    s = re.sub(r"[^a-zA-Z0-9_]+", "_", (text or "rec").strip()).strip("_").lower()
    return (s[:max_len] or "rec").rstrip("_")


def _ensure_xmlid(env, record, local_id):
    imd = env["ir.model.data"].sudo()
    full = f"{MODULE}.{local_id}"
    existing = imd.search(
        [("module", "=", MODULE), ("name", "=", local_id)], limit=1
    )
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


def _xmlid_for_record(env, record):
    if not record:
        return None
    imd = env["ir.model.data"].sudo().search(
        [("model", "=", record._name), ("res_id", "=", record.id)], limit=1
    )
    if imd:
        return f"{imd.module}.{imd.name}"
    return None


def _assign_demo_xmlids(env, model, records, key_fn):
    mapping = {}
    for rec in records:
        local = f"demo_{model.replace('.', '_')}_{_slug(key_fn(rec))}"
        _ensure_xmlid(env, rec, local)
        mapping[rec.id] = local
    return mapping


def _serialize_field(record, field, default_get):
    name = field.name
    if name in SKIP_FIELD_NAMES or field.type in SKIP_FIELD_TYPES:
        return None
    value = record[name]
    default = default_get.get(name)
    if (not value and not default) or field.convert_to_cache(value, record) == field.convert_to_cache(
        default, record
    ):
        return None

    if field.type == "boolean":
        return E.field(name=name, eval=str(value))
    if field.type in ("integer", "float"):
        return E.field(name=name, eval=str(value))
    if field.type == "many2one":
        if not value:
            return E.field(name=name, eval="False")
        xid = _xmlid_for_record(record.env, value)
        if not xid:
            raise ValueError(f"Missing xmlid for {value}")
        return E.field(name=name, ref=xid)
    if field.type == "many2many":
        if not value:
            return E.field(name=name, eval="[(6, 0, [])]")
        refs = []
        for v in value:
            xid = _xmlid_for_record(record.env, v)
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
    """Parents before children (stable)."""
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
                node = _serialize_field(rec, field, default_get)
            except ValueError:
                node = None
            if node is not None:
                field_nodes.append(node)
        if field_nodes:
            nodes.append(E.record(*field_nodes, id=imd.name, model=model_name))
    return nodes


def _write_xml(path, nodes, noupdate=True):
    path.parent.mkdir(parents=True, exist_ok=True)
    root = E.odoo(*nodes, noupdate="1") if noupdate else E.odoo(*nodes)
    content = etree.tostring(
        root, pretty_print=True, encoding="UTF-8", xml_declaration=True
    )
    path.write_bytes(content)


def main(env):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    written = []

    for model_name, domain, field_names in EXPORT_SPECS:
        Model = env[model_name].sudo()
        order = "parent_id, id" if model_name == "product.category" else "id"
        records = Model.search(domain, order=order)
        if not records:
            print(f"SKIP {model_name}: no records for {domain}")
            continue

        if model_name == "product.template":
            key_fn = lambda r: r.default_code or str(r.id)
        elif model_name == "account.analytic.account":
            key_fn = lambda r: r.code or str(r.id)
        elif model_name == "res.partner":
            key_fn = lambda r: r.ref or str(r.id)
        else:
            key_fn = lambda r: r.name or str(r.id)

        _assign_demo_xmlids(env, model_name, records, key_fn)

        # product variants inherit template xmlids context
        if model_name == "product.template":
            for tmpl in records:
                for prod in tmpl.product_variant_ids:
                    local = f"demo_product_product_{_slug(tmpl.default_code)}"
                    _ensure_xmlid(env, prod, local)

        nodes = _serialize_records(env, model_name, records, field_names)
        if not nodes:
            print(f"SKIP {model_name}: nothing serializable")
            continue

        fname = model_name.replace(".", "_") + ".xml"
        out = OUT_DIR / fname
        _write_xml(out, nodes)
        written.append(out)
        print(f"WROTE {out} ({len(nodes)} records)")

    # Manifest snippet helper
    manifest_paths = sorted(p.name for p in written)
    print("\nAdd to __manifest__.py 'data' list (before menu.xml):")
    for name in manifest_paths:
        print(f'        "data/demo_database/{name}",')


main(env)
