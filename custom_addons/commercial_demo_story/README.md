# Commercial Demo Story (Odoo 19)

Presentation helper module for a **completed** multi-channel retail demo (corporate sales, ecommerce, POS, inventory, accounting).

## Features

- **Demo Dashboard** (`commercial.demo.dashboard`): live KPI counters (corporate SO subset, ecommerce SOs, POS orders/locations, cashier users, products, paid invoices, reconciled inbound payments, revenue sum, top POS product/location/salesperson). Buttons open native Odoo actions (Sales, POS, Website shop, Invoices, Inventory, P/L, POS sessions, Executive summary).
- **Demo Flashcards** (`commercial.demo.flashcard`): ten narrated cards with “Open related” shortcuts.
- **Demo Story** (`commercial.demo.story.step`): twelve ordered presenter steps shipped with the module.
- **Generate / Reset Demo Story**: **Generate** creates an extra `[COMM-DEMO] …` storyline (duplicate presenter path). **Reset** (administrators only) deletes **only** rows with `story_source = generated`. Shipped module steps and all transactional data stay intact.
- **Demo Scenarios** (`commercial.demo.scenario`): short scenario blurbs for the presenter.
- **POS and Accounting Prep** (second root menu): grouped shortcuts to POS branches/sessions/payments, accounting journals/invoices/payments/bank statements, inventory and analysis, plus links back to the Commercial Demo hub.

## Complete demo dataset (install)

- **Master data** (XML): categories, RET-G2 products, FINCORP partners, analytics, CRM team in ``data/demo_database/``.
- **Analytic postings**: ``data/demo_analytic_bootstrap.xml`` (Python).
- **Transactional demo** (30 POS, orders, accounting): ``bootstrap/*.py`` via ``post_init_hook`` on first install only.

Posted moves and POS tickets are not stored as XML. Bootstrap scripts recreate flows (idempotent flags under ``demo_pos_accounting.*``).

### Fresh database

1. Create DB with Sales, POS, Inventory, Accounting, Website, HR (and Enterprise budget if needed).
2. Install **Commercial Demo Story** (post-install runs gates B1–D4 and phases A–D, including 30 POS).
3. Demo passwords for new users: ``FinalDemo2026!`` (change before sharing).

### Re-run full pipeline on existing DB

Use ``scripts/run_complete_demo_bootstrap.py`` via ``odoo-bin shell`` (see module README on GitHub for full command).

### Exact clone of current DB

Use ``scripts/export_demo_database_dump.sh`` then ``pg_restore``.

### Re-export master data XML

Use ``scripts/export_demo_database_xml.py`` via ``odoo-bin shell``.

## Installation

1. Ensure `commercial_demo_story` is on the addons path (this repo uses `projects/demo_pos_accounting/custom_addons` appended in `config/projects/odoo_demo_pos_accounting.conf`).
2. Update the app list, install **Commercial Demo Story**.
3. **Restart the Odoo process** that serves the HTTP port (e.g. 8025). Until workers reload the registry, you can get `RPC_ERROR 404` / `KeyError: 'commercial.demo.dashboard'` because `web/controllers/dataset.py` resolves `request.registry[model]` before each JSON-RPC call — a long-running server started *before* the addon path or install will not know the model.
4. Confirm startup logs list your `custom_addons` directory in `addons paths:`.
5. Menu: **Commercial Demo** (root) → submenus.
6. Menu: **POS and Accounting Prep** (second root) → POS / Accounting / Inventory and products / Analysis / Commercial demo hub.

## Troubleshooting

### `RPC_ERROR 404` / `KeyError: 'commercial.demo.dashboard'` / OwlError on dashboard

1. **Restart Odoo** (all workers if `workers > 0`). This is the usual fix after installing or changing `addons_path`.
2. Verify the instance uses the intended config file:  
   `grep addons_path config/projects/odoo_demo_pos_accounting.conf`  
   must include `.../projects/demo_pos_accounting/custom_addons`.
3. With the server **stopped**, run once:  
   `odoo-bin -c .../odoo_demo_pos_accounting.conf -d demo_pos_accounting -u commercial_demo_story --stop-after-init`  
   then start the server again.
4. Confirm you are on database `demo_pos_accounting` (or whatever matches `dbfilter`).

## Safety

- No mass deletion of `sale.order`, `pos.order`, `account.move`, etc.
- Reset targets **only** `commercial.demo.story.step` records created by **Generate Demo Story** (`story_source = generated`).
- Do not use Reset expecting to clean transactional demo data.

## Validation checklist

1. Module installs without traceback.
2. Menus render; dashboard form opens on singleton `res_id`.
3. Flashcards kanban/list load; story list ordered by sequence.
4. Dashboard navigation buttons return actions (requires dependent apps as in `depends`).
5. Administrators: Reset clears generated steps only.

## Screenshots

86 evidence PNGs are under ``static/description/screenshots/`` (gates A–D). See ``static/description/screenshots_index.md`` and ``static/description/index.html`` for the Odoo Apps page.

## Install log

See `install_log.txt` in this directory after running the install command from your environment.
