# -*- coding: utf-8 -*-
"""Re-run POS orders phase only (390 paid tickets). Clears scale_390_orders_done first.

cd odoo19/odoo19
python3 odoo-bin shell -c ../../config/projects/odoo_demo_pos_accounting.conf \\
  -d demo_pos_accounting --no-http < .../scripts/run_scale_390_orders.py
"""
from pathlib import Path

ICP = env["ir.config_parameter"].sudo()
ICP.set_param("demo_pos_accounting.scale_390_orders_done", "0")
env.cr.commit()

for script in (
    Path("/home/sabry3/sabry_backup/odoo_base/base_odoo_19/projects/demo_pos_accounting/custom_addons/commercial_demo_story/bootstrap/evidence_final_commercial/phaseC_scale_390.py"),
    Path("/mnt/sabry_backup/odoo_base/base_odoo_19/projects/demo_pos_accounting/custom_addons/commercial_demo_story/bootstrap/evidence_final_commercial/phaseC_scale_390.py"),
):
    if script.is_file():
        break
else:
    raise FileNotFoundError("phaseC_scale_390.py not found")

code = script.read_text(encoding="utf-8")
globs = {"env": env, "cr": env.cr, "uid": env.uid, "context": env.context, "__name__": "__main__", "__file__": str(script)}
exec(compile(code, str(script), "exec"), globs)
print("SCALE_390_ORDERS_RERUN_DONE")
