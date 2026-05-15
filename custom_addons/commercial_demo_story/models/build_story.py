# -*- coding: utf-8 -*-
from odoo import fields, models


class CommercialDemoBuildStory(models.Model):
    """Singleton anchor for the embedded build_story.html gallery (no custom JS)."""

    _name = "commercial.demo.build.story"
    _description = "Commercial Demo Build Story Gallery"
    _rec_name = "name"

    name = fields.Char(default="Horizon Retail — Build Story", required=True)
