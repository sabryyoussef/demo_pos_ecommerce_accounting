# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class CrmTeam(models.Model):
    _inherit = "crm.team"

    pos_sales_target = fields.Float(
        string="POS sales target (month)",
        help="Monthly retail POS revenue target for this regional team (tax-included POS totals).",
    )
    pos_sales_month = fields.Monetary(
        string="POS sales this month",
        compute="_compute_pos_sales_month",
        currency_field="currency_id",
        help="Sum of paid POS order totals this month for locations assigned to this team.",
    )
    pos_sales_achievement_pct = fields.Float(
        string="POS achievement %",
        compute="_compute_pos_sales_month",
        digits=(16, 1),
    )

    @api.depends("pos_sales_target")
    def _compute_pos_sales_month(self):
        PosOrder = self.env["pos.order"].sudo()
        today = fields.Date.today()
        month_start = today.replace(day=1)
        next_month = month_start + relativedelta(months=1)
        for team in self:
            orders = PosOrder.search(
                [
                    ("config_id.crm_team_id", "=", team.id),
                    ("state", "in", ("paid", "done", "invoiced")),
                    ("date_order", ">=", fields.Datetime.to_string(month_start)),
                    ("date_order", "<", fields.Datetime.to_string(next_month)),
                ]
            )
            total = sum(orders.mapped("amount_total"))
            target = team.pos_sales_target or 0.0
            team.pos_sales_month = total
            team.pos_sales_achievement_pct = (total / target * 100.0) if target else 0.0
