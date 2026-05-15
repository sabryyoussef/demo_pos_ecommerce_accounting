# -*- coding: utf-8 -*-
"""Module install hooks (Odoo.sh-safe: no pos.config deletion on upgrade)."""

MODULE = "commercial_demo_story"

# Records created by bootstrap scripts must NOT stay in ir.model.data for this module,
# or Odoo upgrade will DELETE them when they are absent from XML data files.
# Models exported in data/demo_database/*.xml are NOT listed here.
_PROTECTED_MODELS = (
    "pos.session",
    "pos.order",
    "pos.payment",
    "account.move",
    "account.payment",
    "stock.picking",
    "stock.move",
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
    """Mark bootstrap complete when demo_bootstrap_transactions.xml already ran."""
    ICP = env["ir.config_parameter"].sudo()
    flag = "commercial_demo_story.bootstrap_completed"
    if ICP.get_param(flag) == "1":
        return
    # Fallback if XML function did not run (e.g. partial install).
    env["commercial.demo.operations.loader"].run_all_phases()
    ICP.set_param(flag, "1")
