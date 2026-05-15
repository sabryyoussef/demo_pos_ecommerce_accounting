#!/usr/bin/env python3
"""Gate B2 screenshots: analytic plans, accounts, P&L, analytic reporting, pivot."""
import json
import os
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
    report = {
        "page_errors": [],
        "console_errors": [],
        "console_owl": [],
        "network_failures": [],
        "urls": [],
        "ui_checks": {},
    }

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
        if re.search(r"/web/|/bus/|/mail/", u) and response.status >= 400:
            report["network_failures"].append({"url": u, "status": response.status})

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

        shots = [
            ("01_analytic_plans.png", f"{BASE}/odoo/analytic-plans", False),
            ("02_analytic_accounts.png", f"{BASE}/odoo/analytic-accounts", False),
            ("03_profit_and_loss.png", f"{BASE}/odoo/profit-and-loss", True),
            ("04_analytic_reporting.png", f"{BASE}/odoo/analytic-report", True),
        ]
        for fname, url, full in shots:
            page.goto(url, wait_until="domcontentloaded", timeout=120000)
            page.wait_for_selector(
                "body.o_web_client, .o_web_client, .o_action_manager",
                timeout=120000,
            )
            page.wait_for_timeout(4500)
            report["urls"].append(page.url)
            page.screenshot(path=str(OUT / fname), full_page=full)

        # P&L: open column / options if present; detect analytic dimensions in UI
        page.goto(f"{BASE}/odoo/profit-and-loss", wait_until="domcontentloaded", timeout=120000)
        page.wait_for_timeout(3000)
        for label in ("Columns", "Options", "Filters"):
            btn = page.get_by_role("button", name=re.compile(label, re.I))
            if btn.count():
                btn.first.click(timeout=3000)
                page.wait_for_timeout(800)
                break
        body = page.locator("body").inner_text()
        report["ui_checks"]["pnl_text_has_analytic_hint"] = bool(
            re.search(r"analytic|Analytic|dimension|channel|department", body, re.I)
        ) or page.get_by_text("Analytic", exact=False).count() > 0

        # Analytic accounts: search helps if default list is grouped/paginated
        page.goto(f"{BASE}/odoo/analytic-accounts", wait_until="domcontentloaded", timeout=120000)
        page.wait_for_timeout(2000)
        search = page.locator(
            "input.o_searchview_input, .o_searchview input[type='text'], .o_searchview .o_input"
        )
        if search.count():
            search.first.click()
            search.first.fill("AN-CH-CORP")
            page.keyboard.press("Enter")
            page.wait_for_timeout(2500)
        action_text = ""
        if page.locator(".o_action_manager").count():
            action_text = page.locator(".o_action_manager").first.inner_text()
        report["ui_checks"]["accounts_action_has_AN_CH"] = "AN-CH" in action_text
        corp = page.get_by_text("AN-CH-CORP", exact=False)
        report["ui_checks"]["accounts_list_has_AN_CH_CORP"] = corp.count() > 0
        if corp.count():
            corp.first.wait_for(state="visible", timeout=15000)

        # Strong UI proof: open persisted analytic account form (pass GATEB2_AN_ACCOUNT_ID from host)
        aid = os.environ.get("GATEB2_AN_ACCOUNT_ID")
        if aid and aid.isdigit():
            page.goto(
                f"{BASE}/odoo/analytic-accounts/{aid}",
                wait_until="domcontentloaded",
                timeout=120000,
            )
            page.wait_for_timeout(3000)
            html = page.content()
            if "AN-CH-CORP" not in html:
                page.goto(
                    f"{BASE}/web#id={aid}&model=account.analytic.account&view_type=form",
                    wait_until="domcontentloaded",
                    timeout=120000,
                )
                page.wait_for_timeout(4000)
                html = page.content()
            report["ui_checks"]["account_form_html_has_AN_CH_CORP"] = "AN-CH-CORP" in html
            detail = page.get_by_text("AN-CH-CORP", exact=False)
            report["ui_checks"]["account_form_has_AN_CH_CORP"] = detail.count() > 0
            page.screenshot(
                path=str(OUT / "06_analytic_account_detail.png"), full_page=False
            )

        # Pivot on analytic items (supports pivot view mode)
        page.goto(f"{BASE}/odoo/analytic-items", wait_until="domcontentloaded", timeout=120000)
        page.wait_for_selector(
            "body.o_web_client, .o_web_client, .o_action_manager",
            timeout=120000,
        )
        page.wait_for_timeout(2000)
        pivot_btn = page.locator(
            "button.o_switch_view.o_pivot, .o_cp_switch_buttons button[data-mode='pivot'], [data-tooltip='Pivot'], button[aria-label*='Pivot' i]"
        )
        if pivot_btn.count():
            pivot_btn.first.click()
            page.wait_for_timeout(3000)
        report["ui_checks"]["analytic_items_pivot_visible"] = page.locator(
            ".o_pivot, table.o_pivot"
        ).count() > 0
        page.screenshot(path=str(OUT / "05_analytic_items_pivot.png"), full_page=False)

        browser.close()

    (Path(__file__).resolve().parent / "browser_gateB2.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
