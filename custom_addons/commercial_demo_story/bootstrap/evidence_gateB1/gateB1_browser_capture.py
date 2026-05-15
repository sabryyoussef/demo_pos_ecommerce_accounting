#!/usr/bin/env python3
"""Gate B1 screenshots: accounting, taxes, VAT report, companies."""
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8025"
OUT = Path(__file__).resolve().parent / "screenshots"
SECRET = Path(__file__).resolve().parents[2] / ".gateB1_web_admin_password.txt"
ADMIN = "admin"
PW = "admin"
if SECRET.exists():
    for line in SECRET.read_text(encoding="utf-8").splitlines():
        if line.startswith("ADMIN_WEB_PW="):
            PW = line.split("=", 1)[1].strip()
            break


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1400, "height": 900})
        page = ctx.new_page()
        page.goto(
            f"{BASE}/web/login?db=demo_pos_accounting",
            wait_until="domcontentloaded",
            timeout=120000,
        )
        page.fill("input#login, input[name='login']", ADMIN)
        page.fill("input#password, input[name='password']", PW)
        page.get_by_role("button", name="Log in").click()
        page.wait_for_selector(
            "body.o_web_client, .o_web_client, .o_action_manager",
            timeout=120000,
        )
        page.wait_for_timeout(2000)

        shots = [
            ("01_accounting_dashboard.png", f"{BASE}/odoo/accounting"),
            ("02_taxes.png", f"{BASE}/odoo/taxes"),
            ("03_tax_report_vat201.png", f"{BASE}/odoo/tax-report"),
            ("04_company_settings.png", f"{BASE}/odoo/settings"),
        ]
        for fname, url in shots:
            page.goto(url, wait_until="domcontentloaded", timeout=120000)
            page.wait_for_selector(
                "body.o_web_client, .o_web_client, .o_action_manager",
                timeout=120000,
            )
            page.wait_for_timeout(3500)
            page.screenshot(path=str(OUT / fname), full_page=fname.startswith("03"))

        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
