# Gate D1 — opening inventory at WH-HRG-MAIN/Stock via inventory adjustment only (inventory_mode).
# No POS/PO/SO/invoices. Physical RET-G2 goods only (services excluded).

from pathlib import Path

from odoo.tools import float_compare

for LOG in (
    Path("/home/sabry3/sabry_backup/odoo_base/base_odoo_19/projects/demo_pos_accounting/evidence_gateD1/gateD1_shell.txt"),
    Path("/mnt/sabry_backup/odoo_base/base_odoo_19/projects/demo_pos_accounting/evidence_gateD1/gateD1_shell.txt"),
):
    if LOG.parent.is_dir():
        break
else:
    LOG = Path("gateD1_shell.txt")

lines = []


def log(msg):
    lines.append(msg)
    print(msg)


ICP = env["ir.config_parameter"].sudo()
FLAG = "demo_pos_accounting.gate_d1_opening_inventory_done"
if ICP.get_param(FLAG) == "1":
    log("SKIP_ALREADY_DONE_ICP_FLAG")
    LOG.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"WROTE {LOG}")
    raise SystemExit(0)

comp = env.company
loc = env["stock.location"].browse(5)
if not loc.exists() or "HRG-MAIN/Stock" not in (loc.complete_name or ""):
    raise RuntimeError(f"Expected WH-HRG-MAIN/Stock at id 5, got {loc.complete_name!r}")

# Perpetual inventory posting requires valuation accounts on internal stock + inventory adjustment locations.
loc_inv = env["stock.location"].browse(11)
if not loc_inv.exists() or loc_inv.usage != "inventory":
    raise RuntimeError("Expected global Inventory adjustment location id 11")
acc_sv = comp.account_stock_valuation_id
if not acc_sv:
    raise RuntimeError("Company has no account_stock_valuation_id")
if not loc.valuation_account_id:
    loc.write({"valuation_account_id": acc_sv.id})
if not loc_inv.valuation_account_id:
    loc_inv.write({"valuation_account_id": acc_sv.id})
log(f"LOCATION_VALUATION_ACCOUNTS stock={loc.id} inv_adj={loc_inv.id} account={acc_sv.id}")

PP = env["product.product"].sudo()
PT = env["product.template"].sudo()
Move = env["stock.move"].sudo()
Quant = env["stock.quant"].sudo()
AM = env["account.move"].sudo()
PV = env["product.value"].sudo()

sm0 = Move.search_count([])
sq0 = Quant.search_count([])
am0 = AM.search_count([])
pv0 = PV.search_count([])

log(f"BASELINE stock_move={sm0} stock_quant={sq0} account_move={am0} product_value={pv0}")
log(f"LOCATION id={loc.id} name={loc.complete_name!r}")

goods = PP.search(
    [
        ("default_code", "=ilike", "RET-G2%"),
        ("product_tmpl_id.type", "=", "consu"),
    ]
)
if not goods:
    raise RuntimeError("No RET-G2 consumable products found")

# Enable stock tracking on templates (required for quants / valuation).
tmpls = goods.product_tmpl_id
tmpls.write({"is_storable": True})
log(f"IS_STORABLE_TRUE templates={sorted(tmpls.ids)}")

# Opening quantities (WH-HRG-MAIN/Stock only). Services excluded.
QTY = {
    "RET-G2-BEV-WAT500": 24.0,
    "RET-G2-BEV-SPK330": 48.0,
    "RET-G2-BEV-OJ1L": 24.0,
    "RET-G2-BEV-TEA500": 48.0,
    "RET-G2-SNK-CRP40": 12.0,
    "RET-G2-SNK-ALM100": 24.0,
    "RET-G2-SNK-CHO45": 12.0,
    "RET-G2-SNK-OAT35": 24.0,
    "RET-G2-RTL-BAG01": 12.0,
    "RET-G2-RTL-BAT4": 24.0,
    "RET-G2-RTL-USB1M": 12.0,
    "RET-G2-PAR-TSH-S": 10.0,
    "RET-G2-PAR-TSH-M": 10.0,
    "RET-G2-PAR-TSH-L": 5.0,
    "RET-G2-PAR-MUG350-BLA": 6.0,
    "RET-G2-PAR-MUG350-SIL": 12.0,
}

missing = set(QTY) - set(goods.mapped("default_code"))
if missing:
    raise RuntimeError(f"Missing SKUs for opening qty: {sorted(missing)}")

SQ = env["stock.quant"].sudo().with_context(inventory_mode=True)
to_apply = env["stock.quant"]
for code, qty in sorted(QTY.items()):
    p = goods.filtered(lambda x: x.default_code == code)
    p.ensure_one()
    gathered = SQ._gather(p, loc, strict=True)
    if gathered:
        q = gathered[0].sudo()
        q.inventory_quantity = qty
        q.user_id = env.user.id
    else:
        q = SQ.create(
            {
                "product_id": p.id,
                "location_id": loc.id,
                "inventory_quantity": qty,
            }
        )
    to_apply |= q
    log(f"INV_SET code={code} qty={qty} quant_id={q.id}")

res = to_apply.action_apply_inventory()
if res and isinstance(res, dict):
    raise RuntimeError(f"Inventory conflict wizard returned: {res!r}")

sm1 = Move.search_count([])
sq1 = Quant.search_count([])
am1 = AM.search_count([])
pv1 = PV.search_count([])

log(f"AFTER stock_move={sm1} (+{sm1 - sm0}) stock_quant={sq1} (+{sq1 - sq0})")
log(f"AFTER account_move={am1} (+{am1 - am0}) product_value={pv1} (+{pv1 - pv0})")

assert am1 > am0, "Expected posted stock journal entries for perpetual opening inventory"

# No negative on-hand at main stock for Gate C2 goods
bad = Quant.search(
    [
        ("location_id", "=", loc.id),
        ("product_id", "in", goods.ids),
        ("quantity", "<", 0),
    ]
)
if bad:
    raise RuntimeError(f"Negative stock quants: {bad.ids}")

for q in Quant.search([("location_id", "=", loc.id), ("product_id", "in", goods.ids)]):
    if float_compare(q.quantity, 0.0, precision_rounding=q.product_uom_id.rounding or 0.0001) < 0:
        raise RuntimeError(f"Negative qty quant {q.id}")

# POS domain count (unchanged expectation: still 14 templates)
pos_cfg = env["pos.config"].sudo().browse(5)
if pos_cfg.exists():
    dom = env["product.template"].sudo()._load_pos_data_domain({}, pos_cfg)
    n_pos = PT.search_count(dom)
    log(f"POS_VISIBLE_TEMPLATES config={pos_cfg.id} count={n_pos}")

ICP.set_param(FLAG, "1")
env.cr.commit()
log("COMMIT_OK_ICP_FLAG_SET")

LOG.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"WROTE {LOG}")
