# -*- coding: utf-8 -*-
"""Compare data/demo_database/*.xml with live DB records. Run via odoo-bin shell."""
from __future__ import annotations

import re
from pathlib import Path

from lxml import etree

MODULE = "commercial_demo_story"

FLOAT_FIELDS = {"list_price", "standard_price", "invoiced_target"}
BOOL_FIELDS = {"is_storable", "is_company", "purchase_ok"}
SKIP_FIELDS = {"supplier_taxes_id", "taxes_id"}  # often empty in export


def _parse_field(el):
    name = el.get("name")
    if el.get("ref"):
        return name, ("ref", el.get("ref"))
    if el.get("eval") is not None:
        return name, ("eval", el.get("eval"))
    return name, ("text", el.text or "")


def _eval_literal(expr):
    expr = (expr or "").strip()
    if expr in ("True", "False"):
        return expr == "True"
    if expr.startswith("[") or expr.startswith("("):
        return expr
    try:
        if "." in expr:
            return float(expr)
        return int(expr)
    except ValueError:
        return expr


def _module_root(env):
    import odoo.modules.module as module_util

    return Path(module_util.get_module_path(MODULE))


def _load_xml_records(xml_dir):
    records = []
    for path in sorted(xml_dir.glob("*.xml")):
        root = etree.parse(str(path)).getroot()
        for rec in root.findall("record"):
            fields = {}
            for f in rec.findall("field"):
                fname, val = _parse_field(f)
                fields[fname] = val
            records.append(
                {
                    "file": path.name,
                    "xml_id": f"{MODULE}.{rec.get('id')}",
                    "model": rec.get("model"),
                    "fields": fields,
                }
            )
    return records


def _resolve_ref(env, ref):
    if "." not in ref:
        ref = f"{MODULE}.{ref}"
    rec = env.ref(ref, raise_if_not_found=False)
    return rec.id if rec else None


def _xml_value(env, spec):
    kind, raw = spec
    if kind == "ref":
        return _resolve_ref(env, raw)
    if kind == "eval":
        return _eval_literal(raw)
    return raw


def _db_value(rec, fname):
    if fname not in rec._fields:
        return "<missing field>"
    val = rec[fname]
    if val is False and rec._fields[fname].type == "boolean":
        return False
    if hasattr(val, "id"):
        return val.id
    if hasattr(val, "ids"):
        return sorted(val.ids)
    return val


def _format_val(v):
    if isinstance(v, float):
        return round(v, 4)
    return v


def _values_equal(xml_v, db_v, fname):
    if fname in SKIP_FIELDS:
        return True
    xv, dv = _format_val(xml_v), _format_val(db_v)
    if fname in FLOAT_FIELDS and isinstance(xv, (int, float)) and isinstance(dv, (int, float)):
        return abs(float(xv) - float(dv)) < 0.011
    return xv == dv


def compare(env):
    module_root = _module_root(env)
    xml_dir = module_root / "data" / "demo_database"
    lines = []
    xml_recs = _load_xml_records(xml_dir)
    diffs = []
    missing_xmlid = []
    ok = 0

    for xr in xml_recs:
        try:
            rec = env.ref(xr["xml_id"])
        except ValueError:
            missing_xmlid.append(xr)
            continue

        row_diffs = []
        for fname, spec in xr["fields"].items():
            if fname == "name" and xr["model"] == "account.analytic.account":
                # XML export used code as name for some accounts; DB has display title
                db_name = rec.name
                xml_name = _xml_value(env, spec) if spec[0] != "ref" else db_name
                if spec[0] == "text" and db_name != xml_name:
                    # also accept if xml matches code field
                    if getattr(rec, "code", None) == xml_name:
                        continue
            xml_v = _xml_value(env, spec)
            db_v = _db_value(rec, fname)
            if not _values_equal(xml_v, db_v, fname):
                row_diffs.append((fname, xml_v, db_v))

        if row_diffs:
            diffs.append((xr, rec, row_diffs))
        else:
            ok += 1

    lines.append("=" * 72)
    lines.append("XML vs DATABASE — commercial_demo_story/data/demo_database/")
    lines.append("=" * 72)
    lines.append(f"XML records parsed: {len(xml_recs)}")
    lines.append(f"Match (all compared fields): {ok}")
    lines.append(f"Field mismatches: {len(diffs)}")
    lines.append(f"XML id not in DB: {len(missing_xmlid)}")
    lines.append("")

    if missing_xmlid:
        lines.append("--- XML ids not found in ir.model.data ---")
        for xr in missing_xmlid:
            lines.append(f"  {xr['xml_id']} ({xr['model']}) in {xr['file']}")
        lines.append("")

    if diffs:
        lines.append("--- Field differences (XML → DB) ---")
        for xr, rec, row_diffs in diffs:
            lines.append(f"\n[{xr['file']}] {xr['xml_id']} → {rec.display_name} (id={rec.id})")
            for fname, xv, dv in row_diffs:
                lines.append(f"  {fname}: xml={xv!r}  db={dv!r}")

    # Natural-key coverage: DB demo rows not covered by XML files
    lines.append("")
    lines.append("--- DB records by domain key NOT fully represented in XML ---")
    checks = [
        (
            "product.template RET-G2",
            env["product.template"].sudo().search([("default_code", "=like", "RET-G2%")]),
            "default_code",
        ),
        (
            "res.partner FINCORP",
            env["res.partner"].sudo().search([("ref", "=like", "FINCORP-%")]),
            "ref",
        ),
        (
            "crm.team Corporate Direct",
            env["crm.team"].sudo().search([("name", "=", "Corporate Direct — Horizon Retail")]),
            "name",
        ),
        (
            "account.analytic.account AN-*",
            env["account.analytic.account"].sudo().search([("code", "=like", "AN-%")]),
            "code",
        ),
        (
            "pos.config POS-*",
            env["pos.config"].sudo().search([("name", "=like", "POS-%")]),
            "name",
        ),
    ]
    xml_pt_codes = set()
    for r in xml_recs:
        if r["model"] != "product.template" or "default_code" not in r["fields"]:
            continue
        spec = r["fields"]["default_code"]
        xml_pt_codes.add(_xml_value(env, spec) if isinstance(spec, tuple) else spec)

    for label, recs, key in checks:
        if label.startswith("product.template"):
            db_keys = set(recs.mapped("default_code"))
            extra = db_keys - xml_pt_codes
            missing = xml_pt_codes - db_keys
            lines.append(f"\n{label}: DB={len(db_keys)} XML={len(xml_pt_codes)}")
            if extra:
                lines.append(f"  In DB only ({len(extra)}): {sorted(extra)[:15]}{'...' if len(extra)>15 else ''}")
            if missing:
                lines.append(f"  In XML only ({len(missing)}): {sorted(missing)}")
            continue
        lines.append(f"\n{label}: count={len(recs)} (XML file has partial export)")

    # Transactional demo (not in XML by design)
    lines.append("")
    lines.append("--- Transactional demo in DB (not in demo_database XML) ---")
    stats = [
        ("pos.config", env["pos.config"].sudo().search_count([("name", "=like", "POS-%")])),
        ("pos.order", env["pos.order"].sudo().search_count([])),
        ("sale.order (non-cancel)", env["sale.order"].sudo().search_count([("state", "!=", "cancel")])),
        ("account.move posted", env["account.move"].sudo().search_count([("state", "=", "posted")])),
        ("account.payment", env["account.payment"].sudo().search_count([])),
        ("stock.quant qty>0", env["stock.quant"].sudo().search_count([("quantity", ">", 0)])),
    ]
    for name, cnt in stats:
        lines.append(f"  {name}: {cnt}")

    # Analytic account name vs code check
    lines.append("")
    lines.append("--- Analytic accounts: XML name field vs DB ---")
    for xr in xml_recs:
        if xr["model"] != "account.analytic.account":
            continue
        rec = env.ref(xr["xml_id"], raise_if_not_found=False)
        if not rec:
            continue
        xml_name = xr["fields"].get("name", ("", ""))[1]
        if rec.name != xml_name and rec.code == xml_name:
            lines.append(f"  {rec.code}: XML name={xml_name!r} but DB name={rec.name!r} (export quirk)")

    report = "\n".join(lines)
    print(report)
    out = module_root / "data" / "demo_database" / "XML_VS_DB_REPORT.txt"
    out.write_text(report + "\n", encoding="utf-8")
    print(f"\nWrote {out}")


compare(env)
