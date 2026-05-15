#!/usr/bin/env python3
"""Gate C1: product categories, category accounting form, settings (inventory / barcode)."""
import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8025"
OUT = Path(__file__).resolve().parent / "screenshots"
DB = "demo_pos_accounting"

ADMIN_SECRET = Path(__file__).resolve().parents[2] / ".gateB1_web_admin_password.txt"


def load_admin_password():
    admin_pw = "admin"
    if ADMIN_SECRET.exists():
        for line in ADMIN_SECRET.read_text(encoding="utf-8").splitlines():
            if line.startswith("ADMIN_WEB_PW="):
                admin_pw = line.split("=", 1)[1].strip()
                break
    return admin_pw


def login(page, password):
    page.goto(f"{BASE}/web/login?db={DB}", wait_until="domcontentloaded", timeout=120000)
    page.wait_for_selector("input#login", state="visible", timeout=120000)
    page.fill("input#login", "admin")
    page.fill("input#password", password)
    page.get_by_role("button", name="Log in").click()
    page.wait_for_selector(
        "body.o_web_client, .o_web_client, .o_action_manager",
        timeout=120000,
    )
    page.wait_for_timeout(2000)


def attach_listeners(page, report):
    def on_page_error(exc):
        report["page_errors"].append(str(exc))

    def on_console(msg):
        t = msg.text
        low = t.lower()
        if msg.type == "error" or "error" in low:
            report["console_errors"].append({"type": msg.type, "text": t[:500]})
        if "owl" in low:
            report["console_owl"].append({"type": msg.type, "text": t[:500]})

    def on_response(response):
        u = response.url
        if re.search(r"/web/dataset/call_kw|/web/action/load", u) and response.status >= 400:
            report["network_failures"].append({"url": u, "status": response.status})

    page.on("pageerror", on_page_error)
    page.on("console", on_console)
    page.on("response", on_response)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    admin_pw = load_admin_password()
    report = {"page_errors": [], "console_errors": [], "console_owl": [], "network_failures": []}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")
        ctx = browser.new_context(viewport={"width": 1400, "height": 900})
        page = ctx.new_page()
        attach_listeners(page, report)
        try:
            login(page, admin_pw)

            page.goto(f"{BASE}/odoo/action-214", wait_until="domcontentloaded", timeout=120000)
            page.wait_for_timeout(4000)
            page.screenshot(path=str(OUT / "01_product_categories_list.png"), full_page=True)

            page.goto(f"{BASE}/odoo/product.category/7", wait_until="domcontentloaded", timeout=120000)
            page.wait_for_timeout(3500)
            page.screenshot(path=str(OUT / "02_category_all_products_accounting.png"), full_page=True)

            page.goto(f"{BASE}/odoo/settings", wait_until="domcontentloaded", timeout=120000)
            page.wait_for_timeout(3000)
            inv = page.get_by_role("button", name=re.compile("Inventory", re.I))
            if inv.count():
                inv.first.click(timeout=5000)
                page.wait_for_timeout(2000)
            page.screenshot(path=str(OUT / "03_settings_inventory_valuation.png"), full_page=True)

            page.goto(f"{BASE}/odoo/settings", wait_until="domcontentloaded", timeout=120000)
            page.wait_for_timeout(2000)
            for label in ("Inventory", "Product", "Products"):
                btn = page.get_by_role("button", name=re.compile(label, re.I))
                if btn.count():
                    btn.first.click(timeout=3000)
                    page.wait_for_timeout(1500)
            page.screenshot(path=str(OUT / "04_settings_barcode_product.png"), full_page=True)

        finally:
            ctx.close()
            browser.close()

    (Path(__file__).resolve().parent / "browser_gateC1.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
