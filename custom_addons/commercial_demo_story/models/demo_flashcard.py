# -*- coding: utf-8 -*-
from odoo import api, fields, models


class CommercialDemoFlashcard(models.Model):
    _name = "commercial.demo.flashcard"
    _description = "Commercial Demo Flashcard"
    _order = "sequence, id"

    sequence = fields.Integer(default=10)
    name = fields.Char(required=True, translate=True)
    short_text = fields.Html(string="Short explanation", sanitize_attributes=True, translate=True)
    business_value = fields.Text(string="Business value", translate=True)
    action_xmlid = fields.Char(
        string="Related action (XML ID)",
        help="Technical xml_id, e.g. sale.action_quotations. Used by Open Related.",
    )
    icon_class = fields.Char(
        string="Icon class",
        default="fa fa-lightbulb-o",
        help="FontAwesome class for kanban (backend webclient).",
    )
    active = fields.Boolean(default=True)

    def action_open_related(self):
        self.ensure_one()
        if not self.action_xmlid:
            return {"type": "ir.actions.act_window_close"}
        return self.env["ir.actions.actions"]._for_xml_id(self.action_xmlid)
