#!/usr/bin/env python3
"""Gate B4 screenshots: journals list, journal form, POS payment methods list."""
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
        "journal_detail_id": None,
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

    j_visa = psql_scalar(
        "SELECT id FROM account_journal WHERE code = 'PVISA' AND company_id = 1 LIMIT 1"
    )
    report["journal_detail_id"] = j_visa

    with sync_playwright() as p:
        # Prefer system Chrome/Chromium (avoid multi-hundred-MB Playwright browser download in CI).
        browser = p.chromium.launch(headless=True, channel="chrome")
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

        # 1) Journals (account.action_account_journal_form → id 301)
        page.goto(f"{BASE}/odoo/action-301", wait_until="domcontentloaded", timeout=120000)
        page.wait_for_timeout(4000)
        report["urls"].append(page.url)
        page.screenshot(path=str(OUT / "01_journals_list.png"), full_page=True)

        # 2) Journal form (POS-VISA-AED)
        if j_visa.isdigit():
            page.goto(
                f"{BASE}/web#id={j_visa}&model=account.journal&view_type=form",
                wait_until="domcontentloaded",
                timeout=120000,
            )
            page.wait_for_timeout(4000)
            report["urls"].append(page.url)
            page.screenshot(path=str(OUT / "02_journal_pos_visa_detail.png"), full_page=False)

        # 3) POS payment methods (point_of_sale.action_payment_methods_tree → 657)
        page.goto(f"{BASE}/odoo/action-657", wait_until="domcontentloaded", timeout=120000)
        page.wait_for_timeout(4000)
        report["urls"].append(page.url)
        page.screenshot(path=str(OUT / "03_pos_payment_methods.png"), full_page=True)

        browser.close()

    (Path(__file__).resolve().parent / "browser_gateB4.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
