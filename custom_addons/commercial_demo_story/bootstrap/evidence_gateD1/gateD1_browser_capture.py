#!/usr/bin/env python3
"""Gate D1: inventory adjustment (quants), on-hand, valuation moves, journal entries, POS."""
import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8025"
OUT = Path(__file__).resolve().parent / "screenshots"
DB = "demo_pos_accounting"

ADMIN_SECRET = Path(__file__).resolve().parents[2] / ".gateB1_web_admin_password.txt"
DEMO_PW = Path(__file__).resolve().parents[2] / ".gateB6_demo_passwords.txt"


def load_passwords():
    admin_pw = "admin"
    if ADMIN_SECRET.exists():
        for line in ADMIN_SECRET.read_text(encoding="utf-8").splitlines():
            if line.startswith("ADMIN_WEB_PW="):
                admin_pw = line.split("=", 1)[1].strip()
                break
    cashier = ""
    for path in (DEMO_PW, Path("/mnt/sabry_backup/odoo_base/base_odoo_19/projects/demo_pos_accounting/.gateB6_demo_passwords.txt")):
        if path.is_file():
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.startswith("pos.cashier.dxb="):
                    cashier = line.split("=", 1)[1].strip()
            break
    return admin_pw, cashier


def login(page, user, password):
    page.goto(f"{BASE}/web/login?db={DB}", wait_until="domcontentloaded", timeout=120000)
    page.wait_for_selector("input#login", state="visible", timeout=120000)
    page.fill("input#login", user)
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
    admin_pw, cashier_pw = load_passwords()
    report = {"page_errors": [], "console_errors": [], "console_owl": [], "network_failures": []}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")
        ctx = browser.new_context(viewport={"width": 1400, "height": 900})
        page = ctx.new_page()
        attach_listeners(page, report)
        try:
            login(page, "admin", admin_pw)

            page.goto(f"{BASE}/odoo/action-436", wait_until="domcontentloaded", timeout=120000)
            page.wait_for_timeout(4500)
            page.screenshot(path=str(OUT / "01_inventory_quant_adjustment.png"), full_page=True)

            page.goto(f"{BASE}/odoo/product.template/25", wait_until="domcontentloaded", timeout=120000)
            page.wait_for_timeout(3500)
            page.screenshot(path=str(OUT / "02_product_on_hand_general.png"), full_page=True)

            page.goto(f"{BASE}/odoo/action-574", wait_until="domcontentloaded", timeout=120000)
            page.wait_for_timeout(4000)
            page.screenshot(path=str(OUT / "03_stock_move_valuation.png"), full_page=True)

            page.goto(f"{BASE}/odoo/account.move/1", wait_until="domcontentloaded", timeout=120000)
            page.wait_for_timeout(3000)
            page.screenshot(path=str(OUT / "04_account_move_stock_journal_1.png"), full_page=True)

            page.goto(f"{BASE}/odoo/account.move/2", wait_until="domcontentloaded", timeout=120000)
            page.wait_for_timeout(3000)
            page.screenshot(path=str(OUT / "05_account_move_stock_journal_2.png"), full_page=True)

        finally:
            ctx.close()

        if cashier_pw:
            ctx2 = browser.new_context(viewport={"width": 1400, "height": 900})
            page2 = ctx2.new_page()
            attach_listeners(page2, report)
            try:
                login(page2, "pos.cashier.dxb", cashier_pw)
                page2.goto(f"{BASE}/pos/ui/5/login?config_id=5", wait_until="domcontentloaded", timeout=120000)
                page2.wait_for_timeout(6000)
                page2.screenshot(path=str(OUT / "06_pos_products_with_stock.png"), full_page=False)
            finally:
                ctx2.close()

        browser.close()

    (Path(__file__).resolve().parent / "browser_gateD1.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
