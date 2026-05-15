# Gate B3 — warehouse + stock locations (structure only). Requires: env.cr.commit() at end.

Wh = env["stock.warehouse"].sudo()
Loc = env["stock.location"].sudo()
comp = env.company

moves_before = env["stock.move"].sudo().search_count([])
quants_nonzero = env["stock.quant"].sudo().search_count([("quantity", "!=", 0)])

wh = Wh.search([("company_id", "=", comp.id)], order="id", limit=1)
assert wh, "No warehouse for company"

# Main warehouse: display name WH-HRG-MAIN; short code max 5 chars (Odoo constraint).
wh.write({"name": "WH-HRG-MAIN", "code": "HRG01"})
# stock.warehouse._update_name_and_code renames the view parent of Stock to `code`; fix display root.
wh.view_location_id.write({"name": "WH-HRG-MAIN"})

root = wh.view_location_id
assert root.name == "WH-HRG-MAIN", root.name


def get_child(parent, name):
    return Loc.search([("location_id", "=", parent.id), ("name", "=", name)], limit=1)


def ensure_loc(parent, name, usage="internal"):
    loc = get_child(parent, name)
    if loc:
        if loc.usage != usage:
            loc.write({"usage": usage})
        return loc
    return Loc.create(
        {
            "name": name,
            "location_id": parent.id,
            "usage": usage,
            "company_id": comp.id,
        }
    )


# Required structure (Stock already exists under root)
stock = wh.lot_stock_id
assert stock.name == "Stock", stock.name
print("STOCK_LOC", stock.id, stock.complete_name)

ensure_loc(root, "ECOM-OUT", "internal")
ensure_loc(root, "SALES-OUT", "internal")

pos = get_child(root, "POS")
if not pos:
    # Use internal (not view) so complete_name stays WH-HRG-MAIN/POS/... per hierarchy rules.
    pos = Loc.create(
        {
            "name": "POS",
            "location_id": root.id,
            "usage": "internal",
            "company_id": comp.id,
        }
    )
elif pos.usage != "internal":
    pos.write({"usage": "internal"})

ensure_loc(pos, "DXB-01", "internal")
ensure_loc(pos, "AUH-01", "internal")

ensure_loc(root, "RET-CUSTOMER", "internal")
ensure_loc(root, "RET-ECOM", "internal")
ensure_loc(root, "RET-POS", "internal")
ensure_loc(root, "LOSS-DAMAGE", "internal")
ensure_loc(root, "ADJUSTMENT", "inventory")

expected_suffixes = [
    "WH-HRG-MAIN/Stock",
    "WH-HRG-MAIN/ECOM-OUT",
    "WH-HRG-MAIN/SALES-OUT",
    "WH-HRG-MAIN/POS",
    "WH-HRG-MAIN/POS/DXB-01",
    "WH-HRG-MAIN/POS/AUH-01",
    "WH-HRG-MAIN/RET-CUSTOMER",
    "WH-HRG-MAIN/RET-ECOM",
    "WH-HRG-MAIN/RET-POS",
    "WH-HRG-MAIN/LOSS-DAMAGE",
    "WH-HRG-MAIN/ADJUSTMENT",
]
for cn in expected_suffixes:
    loc = Loc.search([("complete_name", "=", cn)], limit=1)
    assert loc, "Missing location %s" % cn
    print("OK", cn, "id=", loc.id)

# Duplicate names under same parent
for parent in root | pos:
    names = Loc.search([("location_id", "=", parent.id)]).mapped("name")
    assert len(names) == len(set(names)), "Duplicate child name under parent %s" % parent.complete_name

moves_after = env["stock.move"].sudo().search_count([])
quants_nonzero_after = env["stock.quant"].sudo().search_count([("quantity", "!=", 0)])
print("STOCK_MOVE_COUNT_BEFORE_AFTER", moves_before, moves_after)
print("QUANT_NONZERO_BEFORE_AFTER", quants_nonzero, quants_nonzero_after)
assert moves_after == moves_before
assert quants_nonzero_after == quants_nonzero

print("DETAIL_LOC_ID_STOCK", wh.lot_stock_id.id)
print("WAREHOUSE", wh.id, wh.name, wh.code)

env.cr.commit()
print("COMMIT_OK")
