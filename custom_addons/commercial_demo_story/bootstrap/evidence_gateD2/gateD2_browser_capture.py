#!/usr/bin/env python3
"""Gate D2: POS order (lines + payments), session, accounting move, picking, product qty, POS shop smoke."""
import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8025"
OUT = Path(__file__).resolve().parent / "screenshots"
DB = "demo_pos_accounting"
MANIFEST = Path(__file__).resolve().parent / "gateD2_manifest.json"

ADMIN_SECRET = Path(__file__).resolve().parents[2] / ".gateB1_web_admin_password.txt"
DEMO_PW = Path(__file__).resolve().parents[2] / ".gateB6_demo_passwords.txt"


def load_passwords():
    admin_pw = "admin"
    if ADMIN_SECRET.exists():
        for line in ADMIN_SECRET.read_text(encoding="utf-8").splitlines():
            if line.startswith("ADMIN_WEB_PW="):
                admin_pw = line.split("=", 1)[1].strip()
                break
    cashier_dxb = ""
    cashier_auh = ""
    for path in (DEMO_PW, Path("/mnt/sabry_backup/odoo_base/base_odoo_19/projects/demo_pos_accounting/.gateB6_demo_passwords.txt")):
        if path.is_file():
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.startswith("pos.cashier.dxb="):
                    cashier_dxb = line.split("=", 1)[1].strip()
                if line.startswith("pos.cashier.auh="):
                    cashier_auh = line.split("=", 1)[1].strip()
            break
    return admin_pw, cashier_dxb, cashier_auh


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
    if not MANIFEST.exists():
        print("MISSING gateD2_manifest.json — run gateD2_shell_input.py first", file=sys.stderr)
        return 2
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    o1, o2, o3 = m["pos_order_ids"]
    sid_dxb, sid_auh = m["pos_session_ids"]["POS-DXB-01"], m["pos_session_ids"]["POS-AUH-01"]
    mv_dxb, mv_auh = m["session_account_move_ids"]["POS-DXB-01"], m["session_account_move_ids"]["POS-AUH-01"]
    pick0 = m["stock_picking_ids"][0]
    tmpl_water = m["water_template_id"]
    cfg_dxb = m["config_ids"]["POS-DXB-01"]

    admin_pw, cashier_dxb, cashier_auh = load_passwords()
    report = {"page_errors": [], "console_errors": [], "console_owl": [], "network_failures": []}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")

        ctx = browser.new_context(viewport={"width": 1400, "height": 900})
        page = ctx.new_page()
        attach_listeners(page, report)
        try:
            login(page, "admin", admin_pw)

            # POS "cart" proxy: paid order lines + payments (receipt data)
            page.goto(f"{BASE}/odoo/pos.order/{o1}", wait_until="domcontentloaded", timeout=120000)
            page.wait_for_timeout(4000)
            page.screenshot(path=str(OUT / "01_pos_order_combo_lines_payments.png"), full_page=True)

            page.goto(f"{BASE}/odoo/pos.order/{o3}", wait_until="domcontentloaded", timeout=120000)
            page.wait_for_timeout(3500)
            page.screenshot(path=str(OUT / "02_pos_order_mug_payments.png"), full_page=True)

            page.goto(f"{BASE}/odoo/pos.session/{sid_dxb}", wait_until="domcontentloaded", timeout=120000)
            page.wait_for_timeout(3500)
            page.screenshot(path=str(OUT / "03_pos_session_dxb_closed.png"), full_page=True)

            page.goto(f"{BASE}/odoo/account.move/{mv_dxb}", wait_until="domcontentloaded", timeout=120000)
            page.wait_for_timeout(4000)
            page.screenshot(path=str(OUT / "04_account_move_pos_session_dxb.png"), full_page=True)

            page.goto(f"{BASE}/odoo/stock.picking/{pick0}", wait_until="domcontentloaded", timeout=120000)
            page.wait_for_timeout(3500)
            page.screenshot(path=str(OUT / "05_stock_picking_pos_sale.png"), full_page=True)

            page.goto(f"{BASE}/odoo/product.template/{tmpl_water}", wait_until="domcontentloaded", timeout=120000)
            page.wait_for_timeout(3500)
            inv = page.get_by_role("tab", name=re.compile("Inventory|On Hand|Quantity", re.I))
            if inv.count():
                inv.first.click(timeout=5000)
                page.wait_for_timeout(1500)
            page.screenshot(path=str(OUT / "06_product_water_on_hand.png"), full_page=True)

        finally:
            ctx.close()

        # POS frontend floor (post-session: login may start new opening control or floor)
        if cashier_dxb:
            ctx2 = browser.new_context(viewport={"width": 1400, "height": 900})
            page2 = ctx2.new_page()
            attach_listeners(page2, report)
            try:
                login(page2, "pos.cashier.dxb", cashier_dxb)
                page2.goto(f"{BASE}/pos/ui/{cfg_dxb}/login?config_id={cfg_dxb}", wait_until="domcontentloaded", timeout=120000)
                page2.wait_for_timeout(8000)
                page2.screenshot(path=str(OUT / "07_pos_shop_floor_dxb.png"), full_page=False)
            finally:
                ctx2.close()

        if cashier_auh:
            ctx3 = browser.new_context(viewport={"width": 1400, "height": 900})
            page3 = ctx3.new_page()
            attach_listeners(page3, report)
            try:
                login(page3, "pos.cashier.auh", cashier_auh)
                page3.goto(f"{BASE}/odoo/pos.session/{sid_auh}", wait_until="domcontentloaded", timeout=120000)
                page3.wait_for_timeout(3500)
                page3.screenshot(path=str(OUT / "08_pos_session_auh_closed.png"), full_page=True)
                page3.goto(f"{BASE}/odoo/account.move/{mv_auh}", wait_until="domcontentloaded", timeout=120000)
                page3.wait_for_timeout(3500)
                page3.screenshot(path=str(OUT / "09_account_move_pos_session_auh.png"), full_page=True)
            finally:
                ctx3.close()

        browser.close()

    rep_path = Path(__file__).resolve().parent / "browser_gateD2.json"
    rep_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"WROTE {rep_path}")
    if report["page_errors"] or report["console_errors"] or report["console_owl"]:
        print("WARNINGS_IN_BROWSER_REPORT", report)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
