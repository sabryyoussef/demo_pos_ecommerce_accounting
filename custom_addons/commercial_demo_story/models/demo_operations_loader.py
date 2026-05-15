# -*- coding: utf-8 -*-
"""
Full demo dataset install: gates B1–B6, C1–C2, D1–D4, final phases A–D.

Recreates on a fresh database:
- Company / warehouse / journals / analytics
- RET-G2 catalog, opening stock
- POS-DXB-01, POS-AUH-01, POS-RET-03 … POS-RET-30 (30 locations)
- Corporate SO → delivery → invoice → payment
- eCommerce orders, POS tickets, bank reconciliation, COMM-DEMO analytic moves

Posted accounting and POS orders are **not** loaded from XML (Odoo cannot reliably
import posted moves). They are created by these idempotent scripts.
"""

from pathlib import Path

from odoo import api, models

# (subdir under bootstrap/ or collections/evidence/, filename)
COMPLETE_DEMO_SCRIPTS = [
    ("evidence_gateB1", "gateb1_shell_input.py"),
    ("evidence_gateB2", "gateb2_shell_input.py"),
    ("evidence_gateB3", "gateb3_shell_input.py"),
    ("evidence_gateB4", "gateb4_shell_input.py"),
    ("evidence_gateB5", "gateb5_shell_input.py"),
    ("evidence_gateB6", "gateb6_shell_input.py"),
    ("evidence_gateC1", "gatec1_shell_input.py"),
    ("evidence_gateC2", "gatec2_shell_input.py"),
    ("evidence_gateD1", "gateD1_shell_input.py"),
    ("evidence_gateD2", "gateD2_shell_input.py"),
    # D3 is read-only reconciliation (needs D2 manifest); skip on automated install.
    ("evidence_gateD4", "gateD4_shell_part1_publish.py"),
    # D4 part2 needs gateD4_browser_result.json from Playwright; optional.
    ("evidence_final_commercial", "phaseA_corporate_sales.py"),
    ("evidence_final_commercial", "phaseB_ecommerce_ops.py"),
    ("evidence_final_commercial", "phaseC_pos_30_locations.py"),
    ("evidence_final_commercial", "phaseC2_dxb_auh_second_cashier.py"),
    ("evidence_final_commercial", "phaseD_bank_reconciliation.py"),
]

DEMO_ICP_PREFIXES = (
    "demo_pos_accounting.final_",
    "demo_pos_accounting.gate_",
)


def _module_bootstrap_root():
    return Path(__file__).resolve().parent.parent / "bootstrap"


def _project_root():
    return Path(__file__).resolve().parents[3]


def _resolve_script(subdir, filename):
    module_path = _module_bootstrap_root() / subdir / filename
    if module_path.is_file():
        return module_path
    project_path = _project_root() / "collections" / "evidence" / subdir / filename
    if project_path.is_file():
        return project_path
    return None


def _collect_scripts():
    found = []
    missing = []
    for subdir, filename in COMPLETE_DEMO_SCRIPTS:
        path = _resolve_script(subdir, filename)
        if path:
            found.append(path)
        else:
            missing.append(f"{subdir}/{filename}")
    return found, missing


def _run_shell_script(env, path):
    # Optional: browser-captured eCommerce delivery step.
    if path.name == "gateD4_shell_part2_deliver.py":
        browser_json = path.parent / "gateD4_browser_result.json"
        if not browser_json.is_file():
            return "skipped_missing_browser_json"

    code = path.read_text(encoding="utf-8")
    globs = {
        "env": env,
        "cr": env.cr,
        "uid": env.uid,
        "context": env.context,
        "__name__": "__main__",
        "__file__": str(path),
    }
    try:
        exec(compile(code, str(path), "exec"), globs)
    except SystemExit:
        pass
    return "ok"


def _run_shell_script_optional(env, path):
    try:
        return _run_shell_script(env, path)
    except Exception as exc:
        return f"error:{exc.__class__.__name__}:{exc}"


def _clear_demo_flags(env):
    ICP = env["ir.config_parameter"].sudo()
    keys = ICP.search([("key", "=like", "demo_pos_accounting.%")]).mapped("key")
    for key in keys:
        ICP.set_param(key, "")
    return keys


def run_demo_operations(env, *, force=False):
    if force:
        cleared = _clear_demo_flags(env)
        env.cr.commit()
    else:
        cleared = []

    scripts, missing = _collect_scripts()
    if not scripts:
        return {
            "status": "skipped",
            "reason": "no bootstrap scripts found",
            "module_bootstrap": str(_module_bootstrap_root()),
            "project_root": str(_project_root()),
            "missing": missing,
        }

    results = {}
    for path in scripts:
        results[path.name] = _run_shell_script_optional(env, path)
        env.cr.commit()

    # Optional D4 part2 after part1 when browser artifact exists.
    d4p2 = _resolve_script("evidence_gateD4", "gateD4_shell_part2_deliver.py")
    if d4p2 and d4p2 not in scripts:
        results[d4p2.name] = _run_shell_script_optional(env, d4p2)
        env.cr.commit()

    env["ir.config_parameter"].sudo().set_param(
        "commercial_demo_story.bootstrap_completed", "1"
    )
    return {
        "status": "ok",
        "force": force,
        "cleared_flags": cleared,
        "results": results,
        "missing": missing,
    }


class CommercialDemoOperationsLoader(models.AbstractModel):
    _name = "commercial.demo.operations.loader"
    _description = "Full commercial demo bootstrap (POS, sales, accounting)"

    @api.model
    def run_all_phases(self):
        """Called from data/demo_operations_bootstrap.xml on module install."""
        return run_demo_operations(self.env, force=False)

    @api.model
    def run_all_phases_force(self):
        """Re-run entire pipeline (clears demo_pos_accounting.* ICP flags first)."""
        return run_demo_operations(self.env, force=True)
