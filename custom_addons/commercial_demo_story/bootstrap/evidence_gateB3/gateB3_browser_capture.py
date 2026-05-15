#!/usr/bin/env python3
"""Gate B3 screenshots: warehouses list, locations list, location form."""
import json
import os
import re
import subprocess
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


def psql_scalar(sql: str) -> str:
    r = subprocess.run(
        [
            "psql",
            "-h",
            "localhost",
            "-U",
            "odoo19",
            "-d",
            "demo_pos_accounting",
            "-tAc",
            sql,
        ],
        capture_output=True,
        text=True,
        env={**os.environ, "PGPASSWORD": "odoo19"},
        check=True,
    )
    return (r.stdout or "").strip()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    report = {
        "page_errors": [],
        "console_errors": [],
        "console_owl": [],
        "network_failures": [],
        "urls": [],
        "detail_loc_id": None,
    }

    def on_page_error(exc):
        report["page_errors"].append(str(exc))

    def on_console(msg):
        t = msg.text
        low = t.lower()
        if msg.type == "error" or "error" in low:
            report["console_errors"].append({"type": msg.type, "text": t[:400]})
        if "owl" in low:
            report["console_owl"].append({"type": msg.type, "text": t[:400]})

    def on_response(response):
        u = response.url
        if re.search(r"/web/|/bus/", u) and response.status >= 400:
            report["network_failures"].append({"url": u, "status": response.status})

    stock_loc_id = psql_scalar(
        "SELECT id FROM stock_location WHERE complete_name = 'WH-HRG-MAIN/Stock' LIMIT 1"
    )
    report["detail_loc_id"] = stock_loc_id

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1400, "height": 900})
        page = ctx.new_page()
        page.on("pageerror", on_page_error)
        page.on("console", on_console)
        page.on("response", on_response)

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

        # 1) Warehouses
        page.goto(f"{BASE}/odoo/action-440", wait_until="domcontentloaded", timeout=120000)
        page.wait_for_timeout(4000)
        report["urls"].append(page.url)
        page.screenshot(path=str(OUT / "01_warehouses.png"), full_page=False)

        # 2) Locations (multi-record)
        page.goto(f"{BASE}/odoo/action-480", wait_until="domcontentloaded", timeout=120000)
        page.wait_for_timeout(2500)
        search = page.locator(
            "input.o_searchview_input, .o_searchview input[type='text'], .o_searchview .o_input"
        )
        if search.count():
            search.first.click()
            search.first.fill("WH-HRG-MAIN")
            page.keyboard.press("Enter")
            page.wait_for_timeout(3500)
        report["urls"].append(page.url)
        page.screenshot(path=str(OUT / "02_locations_list.png"), full_page=True)

        # 3) Location detail (Stock)
        if stock_loc_id.isdigit():
            page.goto(
                f"{BASE}/web#id={stock_loc_id}&model=stock.location&view_type=form",
                wait_until="domcontentloaded",
                timeout=120000,
            )
            page.wait_for_timeout(4000)
            report["urls"].append(page.url)
            page.screenshot(path=str(OUT / "03_location_detail_stock.png"), full_page=False)

        browser.close()

    (Path(__file__).resolve().parent / "browser_gateB3.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
