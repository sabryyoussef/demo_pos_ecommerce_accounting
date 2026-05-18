# -*- coding: utf-8 -*-
import logging

from odoo import api, models

_logger = logging.getLogger(__name__)

# Plain-text descriptions (no RST). Used when DB still holds old README content.
_MODULE_DESCRIPTIONS = {
    "commercial_demo_story": (
        "Executive navigation and narration for a multi-channel retail demo "
        "(B2B, eCommerce, POS, accounting). KPIs are read-only. Reset removes only "
        "generated COMM-DEMO story steps, never live transactions."
    ),
    "pos_close_all_sessions": (
        "Wizard under Point of Sale to close all non-closed sessions "
        "(opening, open, or closing control). Optionally cancel draft orders first."
    ),
}


class IrModuleModule(models.Model):
    _inherit = "ir.module.module"

    @api.model
    def _commercial_demo_sync_module_descriptions(self):
        """Replace legacy README text in ir.module.module.description (Odoo.sh RST fix)."""
        for name, desc in _MODULE_DESCRIPTIONS.items():
            mod = self.sudo().search([("name", "=", name)], limit=1)
            if mod and (not mod.description or len(mod.description) > 300):
                mod.description = desc

    @api.depends("name", "description")
    def _get_desc(self):
        # Legacy DB rows may still store README.md as description; RST parse breaks registry.
        for module in self:
            if (
                module.name in _MODULE_DESCRIPTIONS
                and module.description
                and len(module.description) > 300
            ):
                module.description = _MODULE_DESCRIPTIONS[module.name]
        try:
            super()._get_desc()
        except Exception:
            _logger.warning(
                "description_html fallback (parse failed) for: %s",
                ", ".join(self.mapped("name")),
                exc_info=True,
            )
            for module in self:
                module.description_html = False
