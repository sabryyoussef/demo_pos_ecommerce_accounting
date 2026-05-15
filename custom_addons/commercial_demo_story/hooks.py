# -*- coding: utf-8 -*-
"""Module install hooks (Odoo.sh-safe: no pos.config deletion on upgrade)."""

MODULE = "commercial_demo_story"

# Records created by bootstrap scripts must NOT stay in ir.model.data for this module,
# or Odoo upgrade will DELETE them when they are absent from XML data files.
_PROTECTED_MODELS = (
    "pos.config",
    "pos.session",
    "pos.order",
    "pos.payment",
    "sale.order",
    "account.move",
    "account.payment",
    "stock.picking",
    "stock.move",
    "res.users",
    "hr.employee",
)


def _unlink_module_xmlids(env, models):
    IMD = env["ir.model.data"].sudo()
    stale = IMD.search([("module", "=", MODULE), ("model", "in", list(models))])
    if stale:
        stale.unlink()


def pre_init_hook(env):
    """Before install: drop stale xmlids so Odoo won't DELETE live demo rows."""
    _unlink_module_xmlids(env, _PROTECTED_MODELS)


def post_init_hook(env):
    """After first install only: run full demo bootstrap (not on every upgrade)."""
    ICP = env["ir.config_parameter"].sudo()
    flag = "commercial_demo_story.bootstrap_completed"
    if ICP.get_param(flag) == "1":
        return
    env["commercial.demo.operations.loader"].run_all_phases()
    ICP.set_param(flag, "1")
