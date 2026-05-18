# -*- coding: utf-8 -*-
from odoo import fields, models


class CommercialDemoPresentation(models.Model):
    """Singleton anchor for the client-facing presentation.html (Option B)."""

    _name = "commercial.demo.presentation"
    _description = "Commercial Demo Presentation"
    _rec_name = "name"

    name = fields.Char(default="Horizon Retail — Demo Presentation", required=True)
