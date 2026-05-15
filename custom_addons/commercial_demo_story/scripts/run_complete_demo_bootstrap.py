# -*- coding: utf-8 -*-
"""Force full demo rebuild (clears demo_pos_accounting.* flags, runs all scripts).

cd odoo19/odoo19
../../venv19/bin/python3 odoo-bin shell \\
  -c ../../config/projects/odoo_demo_pos_accounting.conf \\
  -d demo_pos_accounting --no-http \\
  < .../scripts/run_complete_demo_bootstrap.py
"""
env["commercial.demo.operations.loader"].run_all_phases_force()
print("COMPLETE_DEMO_BOOTSTRAP_DONE")
