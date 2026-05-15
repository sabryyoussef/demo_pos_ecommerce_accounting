# -*- coding: utf-8 -*-
from odoo import fields, models


class CommercialDemoScenario(models.Model):
    _name = "commercial.demo.scenario"
    _description = "Commercial Demo Scenario"

    name = fields.Char(required=True, translate=True)
    description = fields.Text(translate=True)
    active = fields.Boolean(default=True)
