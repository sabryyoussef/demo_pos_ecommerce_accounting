# Run: odoo-bin shell -c ... -d demo_pos_accounting --no-http < run_classify_390_pos.py
result = env["commercial.demo.pos.classifier"].run_classify_390(force=True)
print("CLASSIFY_RESULT", result)
