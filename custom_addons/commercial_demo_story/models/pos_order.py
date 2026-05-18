# -*- coding: utf-8 -*-
from odoo import fields, models


class PosOrder(models.Model):
    _inherit = "pos.order"

    config_crm_team_id = fields.Many2one(
        "crm.team",
        string="POS sales team",
        related="config_id.crm_team_id",
        store=True,
        readonly=True,
    )
    config_demo_store_format = fields.Selection(
        related="config_id.demo_store_format",
        store=True,
        readonly=True,
    )
    config_demo_cluster_manager_id = fields.Many2one(
        "hr.employee",
        related="config_id.demo_cluster_manager_id",
        store=True,
        readonly=True,
    )
    config_demo_regional_manager_id = fields.Many2one(
        "hr.employee",
        related="config_id.demo_regional_manager_id",
        store=True,
        readonly=True,
    )
    config_demo_regional_warehouse_id = fields.Many2one(
        "stock.warehouse",
        related="config_id.demo_regional_warehouse_id",
        store=True,
        readonly=True,
    )


class PosSession(models.Model):
    _inherit = "pos.session"

    config_crm_team_id = fields.Many2one(
        "crm.team",
        string="POS sales team",
        related="config_id.crm_team_id",
        store=True,
        readonly=True,
    )
    config_demo_cluster_manager_id = fields.Many2one(
        "hr.employee",
        related="config_id.demo_cluster_manager_id",
        store=True,
        readonly=True,
    )
    config_demo_regional_manager_id = fields.Many2one(
        "hr.employee",
        related="config_id.demo_regional_manager_id",
        store=True,
        readonly=True,
    )


class ReportPosOrder(models.Model):
    _inherit = "report.pos.order"

    config_crm_team_id = fields.Many2one(
        "crm.team",
        string="POS sales team",
        readonly=True,
    )

    def _select(self):
        return super()._select() + ", pc.crm_team_id AS config_crm_team_id"

    def _from(self):
        return super()._from() + """
                LEFT JOIN pos_config pc ON (pc.id = ps.config_id)
        """
