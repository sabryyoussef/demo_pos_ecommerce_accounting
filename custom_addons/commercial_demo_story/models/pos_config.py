# -*- coding: utf-8 -*-
from odoo import fields, models


class PosConfig(models.Model):
    _inherit = "pos.config"

    demo_mall_name = fields.Char(
        string="Mall / location",
        index=True,
        help="Human-readable shop name for demos (e.g. Dubai Hills Mall).",
    )
    demo_store_format = fields.Selection(
        [
            ("flagship", "Flagship"),
            ("mall", "Mall"),
            ("kiosk", "Kiosk"),
            ("outlet", "Outlet"),
        ],
        string="Store format",
        index=True,
    )
    demo_emirate = fields.Selection(
        [
            ("dubai", "Dubai"),
            ("abu_dhabi", "Abu Dhabi"),
            ("sharjah", "Sharjah"),
            ("ajman", "Ajman"),
            ("fujairah", "Fujairah"),
            ("ras_al_khaimah", "Ras Al Khaimah"),
            ("umm_al_quwain", "Umm Al Quwain"),
            ("al_ain", "Al Ain"),
        ],
        string="Emirate",
        index=True,
    )
    demo_regional_warehouse_id = fields.Many2one(
        "stock.warehouse",
        string="Regional supply warehouse",
        index=True,
        help="Distribution center for this shop's region (demo classification).",
    )
    demo_cluster_manager_id = fields.Many2one(
        "hr.employee",
        string="Cluster manager",
        index=True,
    )
    demo_regional_manager_id = fields.Many2one(
        "hr.employee",
        string="Regional manager",
        related="demo_cluster_manager_id.parent_id",
        store=True,
        readonly=True,
        index=True,
    )
    demo_location_partner_id = fields.Many2one(
        "res.partner",
        string="Shop location",
        ondelete="set null",
    )
    demo_display_title = fields.Char(
        string="Display title",
        compute="_compute_demo_display_title",
        store=True,
    )

    def _compute_demo_display_title(self):
        for cfg in self:
            mall = cfg.demo_mall_name or cfg.name
            code = cfg.name or ""
            cfg.demo_display_title = f"{mall} ({code})" if mall != code else mall
