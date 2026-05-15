# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class CommercialDemoDashboard(models.Model):
    _name = "commercial.demo.dashboard"
    _description = "Commercial Demo Dashboard"

    name = fields.Char(default="Commercial Demo", required=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    refresh_token = fields.Integer(string="Refresh counter", default=0)

    # --- KPIs (non-stored; recomputed when refresh_token changes or form opened) ---
    kpi_corporate_so_count = fields.Integer(compute="_compute_kpis")
    kpi_ecommerce_so_count = fields.Integer(compute="_compute_kpis")
    kpi_pos_order_count = fields.Integer(compute="_compute_kpis")
    kpi_pos_location_count = fields.Integer(compute="_compute_kpis")
    kpi_cashier_user_count = fields.Integer(compute="_compute_kpis")
    kpi_product_count = fields.Integer(compute="_compute_kpis")
    kpi_paid_invoice_count = fields.Integer(compute="_compute_kpis")
    kpi_reconciled_payment_count = fields.Integer(compute="_compute_kpis")
    kpi_total_revenue = fields.Monetary(compute="_compute_kpis", currency_field="currency_id")
    kpi_top_product_label = fields.Char(compute="_compute_kpis", string="Top product (POS qty)")
    kpi_top_pos_location_label = fields.Char(compute="_compute_kpis", string="Top POS location (sales)")
    kpi_top_salesperson_label = fields.Char(compute="_compute_kpis", string="Top salesperson (SO total)")

    currency_id = fields.Many2one(related="company_id.currency_id", readonly=True)

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

    def action_open_dashboard_reports(self):
        """Prefer executive summary when account_reports is installed."""
        return self._safe_action("account_reports.action_account_report_exec_summary")

    def action_open_pos(self):
        return self._safe_action("point_of_sale.action_client_pos_menu")

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
