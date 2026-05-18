# -*- coding: utf-8 -*-
from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import UserError

# Phase I — PIN-only cashiers (no res.users): (shop label, employee name, PIN, pos.config id)
DEMO_PIN_CASHIER_ROWS = [
    ("POS-DXB-01 — Dubai Flagship", "Demo Cashier — Dubai Flagship", "3001", 5),
    ("POS-RET-04 — Dubai Hills", "Demo Cashier — Dubai Hills", "3002", 8),
    ("POS-RET-11 — Abu Dhabi Mall", "Demo Cashier — Abu Dhabi Mall", "3003", 15),
    ("POS-RET-16 — Sharjah City Centre", "Demo Cashier — Sharjah City Centre", "3004", 20),
    ("POS-RET-24 — Madinat Jumeirah", "Demo Cashier — Madinat Jumeirah", "3005", 28),
]


class CommercialDemoDashboard(models.Model):
    _name = "commercial.demo.dashboard"
    _description = "Commercial Demo Dashboard"

    name = fields.Char(default="Demo Command Center", required=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    refresh_token = fields.Integer(string="Refresh counter", default=0)

    # --- KPIs (non-stored; recomputed when refresh_token changes or form opened) ---
    kpi_corporate_so_count = fields.Integer(string="Corporate B2B orders", compute="_compute_kpis")
    kpi_ecommerce_so_count = fields.Integer(string="eCommerce orders", compute="_compute_kpis")
    kpi_pos_order_count = fields.Integer(string="POS tickets (all shops)", compute="_compute_kpis")
    kpi_pos_location_count = fields.Integer(string="POS shops configured", compute="_compute_kpis")
    kpi_cashier_user_count = fields.Integer(string="POS users (with login)", compute="_compute_kpis")
    kpi_product_count = fields.Integer(string="Products for sale", compute="_compute_kpis")
    kpi_paid_invoice_count = fields.Integer(string="Paid customer invoices", compute="_compute_kpis")
    kpi_reconciled_payment_count = fields.Integer(string="Reconciled bank payments", compute="_compute_kpis")
    kpi_total_revenue = fields.Monetary(
        string="Total paid invoice revenue",
        compute="_compute_kpis",
        currency_field="currency_id",
    )
    kpi_top_product_label = fields.Char(compute="_compute_kpis", string="Best-selling product (POS)")
    kpi_top_pos_location_label = fields.Char(compute="_compute_kpis", string="Top shop by POS sales")
    kpi_top_salesperson_label = fields.Char(compute="_compute_kpis", string="Top B2B salesperson")
    kpi_top_pos_cashier_label = fields.Char(compute="_compute_kpis", string="Top PIN cashier (POS)")
    kpi_top_pos_team_label = fields.Char(compute="_compute_kpis", string="Top regional sales team")
    kpi_pos_teams_invoiced_label = fields.Char(
        compute="_compute_kpis",
        string="Regions — B2B target progress",
    )
    kpi_pos_teams_pos_sales_label = fields.Char(
        compute="_compute_kpis",
        string="Regions — retail POS target progress",
    )
    kpi_open_pos_sessions = fields.Integer(string="Open POS sessions now", compute="_compute_kpis")

    currency_id = fields.Many2one(related="company_id.currency_id", readonly=True)
    dashboard_presenter_html = fields.Html(
        string="Presenter overview",
        compute="_compute_dashboard_presenter_html",
        sanitize=False,
    )
    pin_cashier_presentation_html = fields.Html(
        string="PIN cashier walkthrough",
        compute="_compute_pin_cashier_presentation_html",
        sanitize=False,
    )

    def _demo_web_base_url(self):
        base = self.env["ir.config_parameter"].sudo().get_param("web.base.url") or ""
        return (base or "http://127.0.0.1:8025").rstrip("/")

    @api.depends(
        "refresh_token",
        "kpi_corporate_so_count",
        "kpi_ecommerce_so_count",
        "kpi_pos_order_count",
        "kpi_pos_location_count",
        "kpi_total_revenue",
        "kpi_open_pos_sessions",
        "kpi_pos_teams_pos_sales_label",
        "kpi_top_pos_cashier_label",
        "currency_id",
    )
    def _compute_dashboard_presenter_html(self):
        for rec in self:
            sym = rec.currency_id.symbol or ""
            revenue = rec.kpi_total_revenue or 0.0
            rec.dashboard_presenter_html = Markup(
                """
                <div class="alert alert-info mb-3" role="alert">
                    <strong>Horizon Retail demo</strong>
                    Main figures are in the counters at the top. Press <strong>Refresh KPIs</strong> before presenting.
                </div>
                <div class="row g-3 mb-3">
                    <div class="col-md-4">
                        <div class="card h-100">
                            <div class="card-header fw-bold">Sales channels</div>
                            <div class="card-body py-2">
                                <ul class="mb-0">
                                    <li><strong>Corporate B2B:</strong> {corp} confirmed orders</li>
                                    <li><strong>eCommerce:</strong> {ecom} web orders</li>
                                    <li><strong>POS retail:</strong> {pos_orders} tickets</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card h-100">
                            <div class="card-header fw-bold">Regional POS targets (this month)</div>
                            <div class="card-body py-2"><p class="mb-0">{pos_targets}</p></div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card h-100">
                            <div class="card-header fw-bold">Top performers</div>
                            <div class="card-body py-2">
                                <ul class="mb-0">
                                    <li><strong>Best shop:</strong> {top_shop}</li>
                                    <li><strong>Best PIN cashier:</strong> {top_cashier}</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="card mb-0">
                    <div class="card-header fw-bold">Suggested 5-minute presenter flow</div>
                    <div class="card-body">
                        <ol class="mb-0">
                            <li><strong>Snapshot</strong> — click the stat counters at the top of this form.</li>
                            <li><strong>390 shops</strong> — Quick navigation → All 390 POS shops → Group by Sales Team.</li>
                            <li><strong>PIN cashiers</strong> — open a till below, employee + PIN, one sale.</li>
                            <li><strong>Manager view</strong> — Manager hierarchy or POS orders by employee.</li>
                            <li><strong>Finance</strong> — P&amp;L or Executive summary in Quick navigation.</li>
                        </ol>
                    </div>
                </div>
                """
            ).format(
                pos_shops=rec.kpi_pos_location_count,
                pos_orders=rec.kpi_pos_order_count,
                revenue=f"{sym}{revenue:,.0f}",
                open_sessions=rec.kpi_open_pos_sessions,
                corp=rec.kpi_corporate_so_count,
                ecom=rec.kpi_ecommerce_so_count,
                pos_targets=rec.kpi_pos_teams_pos_sales_label or "—",
                top_shop=rec.kpi_top_pos_location_label or "—",
                top_cashier=rec.kpi_top_pos_cashier_label or "—",
            )

    @api.depends("refresh_token")
    def _compute_pin_cashier_presentation_html(self):
        for rec in self:
            base = rec._demo_web_base_url()
            rows = []
            for idx, (shop, employee, pin, config_id) in enumerate(DEMO_PIN_CASHIER_ROWS, start=1):
                pos_url = f"{base}/pos/ui?config_id={config_id}"
                rows.append(
                    "<tr>"
                    f"<td>{idx}</td><td>{shop}</td><td><strong>{employee}</strong></td>"
                    f'<td><code>{pin}</code></td>'
                    f'<td><a href="{pos_url}" target="_blank" rel="noopener">Open POS</a></td>'
                    "</tr>"
                )
            rec.pin_cashier_presentation_html = Markup(
                '<div class="alert alert-secondary mb-3">'
                "<strong>Phase I — PIN cashiers (no Odoo login)</strong><br/>"
                "Cashiers exist only as <em>employees</em> on the till. You stay logged in as "
                "<code>admin</code> in the backend while opening POS in a new tab.</div>"
                "<ol style='margin:0.5rem 0 1rem 1.25rem;'>"
                "<li>Click <strong>Open POS</strong> for a shop below.</li>"
                "<li>On the till: choose the employee name → enter the PIN → add a product → pay.</li>"
                "<li>Back in Odoo: Point of Sale → Orders → filter or group by <strong>Employee</strong>.</li>"
                "</ol>"
                "<table class='table table-sm table-striped o_table'>"
                "<thead><tr><th>#</th><th>Shop</th><th>Employee</th><th>PIN</th><th>POS</th></tr></thead>"
                f"<tbody>{''.join(rows)}</tbody></table>"
                "<p class='text-muted mb-0'>Build Story: "
                '<a href="/commercial_demo_story/static/description/build_story.html#gate-pin-cashiers-no-user" '
                'target="_blank" rel="noopener">PIN cashiers — no system user (Phase I)</a></p>'
            )

    @api.depends("refresh_token", "company_id")
    def _compute_kpis(self):
        pos_group = self.env.ref("point_of_sale.group_pos_user", raise_if_not_found=False)
        for rec in self:
            comp = rec.company_id or rec.env.company

            SaleOrder = rec.env["sale.order"].sudo()
            corp_domain = [
                ("state", "in", ("sale", "done")),
                ("company_id", "=", comp.id),
                "|",
                "|",
                ("client_order_ref", "ilike", "FIN-A-%"),
                ("client_order_ref", "ilike", "FIN-B-%"),
                ("partner_id.ref", "in", ("FINCORP-ALPHA", "FINCORP-BETA")),
            ]
            rec.kpi_corporate_so_count = SaleOrder.search_count(corp_domain)

            ecom_domain = [
                ("state", "in", ("sale", "done")),
                ("company_id", "=", comp.id),
                ("website_id", "!=", False),
            ]
            rec.kpi_ecommerce_so_count = SaleOrder.search_count(ecom_domain)

            PosOrder = rec.env["pos.order"].sudo()
            rec.kpi_pos_order_count = PosOrder.search_count([("company_id", "=", comp.id)])

            rec.kpi_pos_location_count = rec.env["pos.config"].sudo().search_count(
                [("company_id", "=", comp.id)]
            )

            if pos_group:
                rec.kpi_cashier_user_count = rec.env["res.users"].sudo().search_count(
                    [
                        ("company_ids", "in", [comp.id]),
                        ("all_group_ids", "in", [pos_group.id]),
                        ("login", "!=", "pos.manager"),
                    ]
                )
            else:
                rec.kpi_cashier_user_count = 0

            rec.kpi_product_count = rec.env["product.template"].sudo().search_count(
                [("sale_ok", "=", True), ("company_id", "in", (comp.id, False))]
            )

            Move = rec.env["account.move"].sudo()
            rec.kpi_paid_invoice_count = Move.search_count(
                [
                    ("company_id", "=", comp.id),
                    ("move_type", "=", "out_invoice"),
                    ("state", "=", "posted"),
                    ("payment_state", "=", "paid"),
                ]
            )

            Payment = rec.env["account.payment"].sudo()
            rec.kpi_reconciled_payment_count = Payment.search_count(
                [
                    ("company_id", "=", comp.id),
                    ("payment_type", "=", "inbound"),
                    ("state", "=", "paid"),
                    ("is_reconciled", "=", True),
                ]
            )

            paid_invs = Move.search(
                [
                    ("company_id", "=", comp.id),
                    ("move_type", "=", "out_invoice"),
                    ("state", "=", "posted"),
                    ("payment_state", "=", "paid"),
                ]
            )
            rec.kpi_total_revenue = sum(paid_invs.mapped("amount_total_signed"))

            Line = rec.env["pos.order.line"].sudo()
            line_groups = Line._read_group(
                [("order_id.company_id", "=", comp.id)],
                ["product_id"],
                ["qty:sum"],
                limit=1,
                order="qty:sum desc",
            )
            if line_groups and line_groups[0][0]:
                prod = line_groups[0][0]
                rec.kpi_top_product_label = prod.display_name
            else:
                rec.kpi_top_product_label = "—"

            pos_groups = PosOrder._read_group(
                [("company_id", "=", comp.id)],
                ["config_id"],
                ["amount_total:sum"],
                limit=1,
                order="amount_total:sum desc",
            )
            if pos_groups and pos_groups[0][0]:
                cfg = pos_groups[0][0]
                rec.kpi_top_pos_location_label = cfg.display_name
            else:
                rec.kpi_top_pos_location_label = "—"

            so_groups = SaleOrder._read_group(
                [
                    ("state", "in", ("sale", "done")),
                    ("company_id", "=", comp.id),
                    ("user_id", "!=", False),
                ],
                ["user_id"],
                ["amount_total:sum"],
                limit=1,
                order="amount_total:sum desc",
            )
            if so_groups and so_groups[0][0]:
                user = so_groups[0][0]
                rec.kpi_top_salesperson_label = user.display_name
            else:
                rec.kpi_top_salesperson_label = "—"

            cashier_groups = PosOrder._read_group(
                [
                    ("company_id", "=", comp.id),
                    ("employee_id", "!=", False),
                    ("state", "in", ("paid", "done", "invoiced")),
                ],
                ["employee_id"],
                ["amount_total:sum"],
                limit=1,
                order="amount_total:sum desc",
            )
            if cashier_groups and cashier_groups[0][0]:
                rec.kpi_top_pos_cashier_label = cashier_groups[0][0].display_name
            else:
                rec.kpi_top_pos_cashier_label = "—"

            team_totals = {}
            for order in PosOrder.search(
                [
                    ("company_id", "=", comp.id),
                    ("config_id.crm_team_id", "!=", False),
                    ("state", "in", ("paid", "done", "invoiced")),
                ]
            ):
                team = order.config_id.crm_team_id
                team_totals[team.id] = team_totals.get(team.id, 0.0) + order.amount_total
            if team_totals:
                best_team_id = max(team_totals, key=team_totals.get)
                team = rec.env["crm.team"].browse(best_team_id)
                sym = rec.currency_id.symbol or ""
                rec.kpi_top_pos_team_label = f"{team.name} ({sym}{team_totals[best_team_id]:,.0f})"
            else:
                rec.kpi_top_pos_team_label = "—"

            pos_team_names = ("POS — Dubai", "POS — Abu Dhabi", "POS — Northern UAE")
            teams = rec.env["crm.team"].sudo().search(
                [("name", "in", pos_team_names), ("company_id", "in", (comp.id, False))]
            )
            parts = []
            for team in teams:
                target = team.invoiced_target or 0.0
                invoiced = team.invoiced or 0.0
                pct = (invoiced / target * 100.0) if target else 0.0
                short = (team.name or "").replace("POS — ", "")
                parts.append(f"{short} {pct:.0f}%")
            rec.kpi_pos_teams_invoiced_label = " | ".join(parts) if parts else "—"

            pos_parts = []
            for team in teams:
                target = team.pos_sales_target or 0.0
                achieved = team.pos_sales_month
                pct = (achieved / target * 100.0) if target else 0.0
                short = (team.name or "").replace("POS — ", "")
                pos_parts.append(f"{short} {pct:.0f}%")
            rec.kpi_pos_teams_pos_sales_label = " | ".join(pos_parts) if pos_parts else "—"

            rec.kpi_open_pos_sessions = rec.env["pos.session"].sudo().search_count(
                [
                    ("config_id.company_id", "=", comp.id),
                    ("state", "in", ("opening_control", "opened", "closing_control")),
                ]
            )

    def action_refresh_kpis(self):
        self.ensure_one()
        self.refresh_token += 1
        return True

    def _safe_action(self, xmlid):
        try:
            return self.env["ir.actions.actions"]._for_xml_id(xmlid)
        except ValueError:
            raise UserError(_("Missing or unknown action: %s") % xmlid) from None

    def action_open_sales(self):
        return self._safe_action("sale.action_orders")

    def action_open_pos_orders(self):
        return self._safe_action("point_of_sale.action_pos_pos_form")

    def action_open_ecommerce_orders(self):
        return self._safe_action("website_sale.action_orders_ecommerce")

    def action_open_invoices(self):
        return self._safe_action("account.action_move_out_invoice_type")

    def action_open_inventory(self):
        return self._safe_action("stock.action_picking_tree_all")

    def action_open_accounting_reports(self):
        return self._safe_action("account_reports.action_account_report_pl")

    def action_open_pos_sessions(self):
        return self._safe_action("point_of_sale.action_pos_session")

    def action_open_pos_sales_teams(self):
        return self._safe_action("sales_team.crm_team_action_pipeline")

    def action_open_spreadsheet_sales(self):
        """Enterprise: Spreadsheet app → Sales dashboard (uses posted SO / invoice data)."""
        dash = self.env.ref(
            "spreadsheet_dashboard_sale.spreadsheet_dashboard_sales",
            raise_if_not_found=False,
        )
        if not dash:
            raise UserError(
                _("Install spreadsheet_dashboard_sale to open the Sales spreadsheet dashboard.")
            )
        return {
            "type": "ir.actions.client",
            "tag": "action_spreadsheet_dashboard",
            "name": dash.name,
            "params": {"spreadsheet_id": dash.id},
        }

    def action_open_pos_employee_report(self):
        return self._safe_action("point_of_sale.action_report_pos_order_all")

    def action_open_dashboard_reports(self):
        """Prefer executive summary when account_reports is installed."""
        return self._safe_action("account_reports.action_account_report_exec_summary")

    def action_open_pos(self):
        return self._safe_action("point_of_sale.action_client_pos_menu")

    def action_open_client_presentation(self):
        return self._safe_action("commercial_demo_story.action_commercial_demo_presentation")

    def action_open_pos_scale_390(self):
        return self._safe_action("commercial_demo_story.action_pos_config_scale_all")

    def action_open_my_pos_hierarchy(self):
        return self._safe_action("commercial_demo_story.action_pos_config_my_hierarchy")

    def action_open_close_all_sessions(self):
        return self._safe_action("pos_close_all_sessions.action_pos_close_all_sessions_wizard")

    def action_open_demo_story(self):
        return self._safe_action("commercial_demo_story.action_commercial_demo_story")

    def action_open_flashcards(self):
        return self._safe_action("commercial_demo_story.action_commercial_demo_flashcards")

    def action_open_pos_pin_demo(self):
        """Open POS UI for a Phase I demo config (context: pos_config_id)."""
        self.ensure_one()
        config_id = self.env.context.get("pos_config_id")
        if not config_id:
            raise UserError(_("Missing pos_config_id in action context."))
        base = self._demo_web_base_url()
        return {
            "type": "ir.actions.act_url",
            "url": f"{base}/pos/ui?config_id={int(config_id)}",
            "target": "new",
        }

    def action_open_website_shop(self):
        return self._safe_action("website_sale.action_open_website")

    def action_reset_demo_story(self):
        if not self.env.user.has_group("base.group_system"):
            raise UserError(_("Only administrators can reset generated demo story steps."))
        Story = self.env["commercial.demo.story.step"].sudo()
        Story.search([("story_source", "=", "generated")]).unlink()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Demo story"),
                "message": _("Removed COMM-DEMO generated story steps. Shipped steps are preserved."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_generate_demo_story(self):
        self.ensure_one()
        Story = self.env["commercial.demo.story.step"].sudo()
        Story.search([("story_source", "=", "generated")]).unlink()

        blueprint = [
            (
                10,
                "[COMM-DEMO] Executive opens dashboard",
                "Open Commercial Demo → Demo Dashboard and scan KPI tiles.",
                "Welcome the audience and state that all figures are live aggregates from this database.",
                "commercial.demo.dashboard",
                "commercial_demo_story.action_commercial_demo_dashboard",
            ),
            (
                20,
                "[COMM-DEMO] Review total commercial performance",
                "Interpret revenue, paid invoices, and channel split at a high level.",
                "Tie corporate, ecommerce, and POS to one chart of accounts.",
                "",
                "account_reports.action_account_report_pl",
            ),
            (
                30,
                "[COMM-DEMO] Corporate sales quotation",
                "Show how B2B deals start as quotations with salesperson attribution.",
                "Open Sales → Quotations and highlight pipeline hygiene.",
                "sale.order",
                "sale.action_quotations",
            ),
            (
                40,
                "[COMM-DEMO] Confirm sales order",
                "Walk through confirm → delivery reservation.",
                "Mention stock impact and AVCO in one sentence.",
                "sale.order",
                "sale.action_orders",
            ),
            (
                50,
                "[COMM-DEMO] Invoice and payment",
                "Posted customer invoice and bank payment visibility.",
                "Stay on accounting impact; do not delete posted moves in a live demo.",
                "account.move",
                "account.action_move_out_invoice_type",
            ),
            (
                60,
                "[COMM-DEMO] eCommerce order",
                "Website orders feeding the same warehouse and tax engine.",
                "Open ecommerce orders filtered for the web channel.",
                "sale.order",
                "website_sale.action_orders_ecommerce",
            ),
            (
                70,
                "[COMM-DEMO] Delivery and stock movement",
                "Transfers from stock to customer or POS locations.",
                "Use outgoing pickings as the concrete document.",
                "stock.picking",
                "stock.action_picking_tree_outgoing",
            ),
            (
                75,
                "[COMM-DEMO] PIN cashiers — no system user (Phase I)",
                "Five shops: employee + PIN only on POS; no res.users per cashier.",
                "Use the dashboard PIN guide: open each POS link, select demo cashier, enter PIN 3001–3005. "
                "Contrast with Gate B6 user-linked cashiers.",
                "commercial.demo.dashboard",
                "commercial_demo_story.action_commercial_demo_dashboard",
            ),
            (
                80,
                "[COMM-DEMO] POS session and ticket",
                "Session control, cashier attribution, mixed tenders.",
                "Open orders list; optionally launch the POS client.",
                "pos.order",
                "point_of_sale.action_pos_pos_form",
            ),
            (
                90,
                "[COMM-DEMO] Payment journals",
                "Per-POS cash journals and card methods mapping to accounting.",
                "Explain traceability without deep live reconciliation unless time allows.",
                "account.journal",
                "account.action_account_journal_form",
            ),
            (
                100,
                "[COMM-DEMO] Bank reconciliation",
                "Statement lines matched to liquidity from customer payments.",
                "Reference FIN-DEMO-RECON lines if present in this database.",
                "account.bank.statement.line",
                "account.action_bank_statement_tree",
            ),
            (
                110,
                "[COMM-DEMO] Targets vs actual",
                "CRM team invoicing targets versus realized invoicing.",
                "Open sales teams and compare target widgets.",
                "crm.team",
                "sales_team.crm_team_action_pipeline",
            ),
            (
                120,
                "[COMM-DEMO] Top performers",
                "POS by location, products from POS lines, salesperson from orders.",
                "Close with POS analysis or executive summary.",
                "pos.order",
                "point_of_sale.action_report_pos_order_all",
            ),
        ]
        for seq, title, desc, script, model_name, axml in blueprint:
            Story.create(
                {
                    "sequence": seq,
                    "name": title,
                    "description": desc,
                    "presenter_script": script,
                    "related_model_name": model_name,
                    "action_xmlid": axml,
                    "story_source": "generated",
                }
            )
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Demo story"),
                "message": _("Generated COMM-DEMO presenter steps. Administrators can use Reset to remove them."),
                "type": "success",
                "sticky": False,
            },
        }
