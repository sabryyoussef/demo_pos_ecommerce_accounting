# Screenshots (bundled)

Copied from `collections/evidence/*/screenshots/` for README and documentation.

| Folder | Topic | Count |
|--------|--------|------:|
| `evidence_gateA_final/` | Web shell, accounting, POS entry | 5 |
| `evidence_gateB1/` | Company, taxes, VAT201 | 4 |
| `evidence_gateB2/` | Analytic plans, P&amp;L, reporting | 6 |
| `evidence_gateB3/` | Warehouse, stock locations | 3 |
| `evidence_gateB4/` | Journals, POS payment methods | 3 |
| `evidence_gateB5/` | POS configurations, frontend, sessions | 6 |
| `evidence_gateB6/` | Users, cashiers, role checks | 12 |
| `evidence_gateC1/` | Product categories, valuation settings | 4 |
| `evidence_gateC2/` | RET-G2 catalog, variants, POS shop | 5 |
| `evidence_gateD1/` | Opening inventory | 6 |
| `evidence_gateD2/` | POS sales flow | 9 |
| `evidence_gateD3/` | POS reconciliation review | 11 |
| `evidence_gateD4/` | eCommerce publish & checkout | 12 |
| `evidence_pos_hierarchy/` | POS teams, HR hierarchy, contacts, competition | 11 |

**Total:** 97 PNG files under `static/description/screenshots/`.

Regenerate from collections after new captures:

```bash
SRC=projects/demo_pos_accounting/collections
DEST=projects/demo_pos_accounting/custom_addons/commercial_demo_story/static/description/screenshots
# POS hierarchy captures (Playwright):
# cp -f bootstrap/evidence_pos_hierarchy/screenshots/*.png "$DEST/evidence_pos_hierarchy/"

find "$SRC/evidence" -type f -iname '*.png' | while read -r f; do
  subdir=$(dirname "$f" | sed "s|$SRC/evidence/||;s|/screenshots||")
  mkdir -p "$DEST/$subdir"
  cp -f "$f" "$DEST/$subdir/$(basename "$f")"
done
```
