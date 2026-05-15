#!/usr/bin/env python3
"""Gate D3: read-only reconciliation screenshots (Accounting, POS session, moves, reports)."""
import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8025"
OUT = Path(__file__).resolve().parent / "screenshots"
DB = "demo_pos_accounting"
MAN = Path(__file__).resolve().parent / "gateD3_review_manifest.json"


def project_root() -> Path:
    here = Path(__file__).resolve()
    for anc in here.parents:
        if (anc / ".gateB1_web_admin_password.txt").exists():
            return anc
    for anc in here.parents:
        if anc.name == "demo_pos_accounting":
            return anc
    return here.parents[3]


ADMIN_SECRET = project_root() / ".gateB1_web_admin_password.txt"


def clear_odoo_search_facets(page, rounds: int = 16) -> None:
    for _ in range(rounds):
        btn = page.locator(".o_searchview_facet .o_facet_remove").first
        if btn.count() == 0:
            break
        try:
            if not btn.is_visible(timeout=500):
                break
            btn.click(timeout=3000)
            page.wait_for_timeout(400)
        except Exception:
            break


def load_admin_pw():
    admin_pw = "admin"
    if ADMIN_SECRET.exists():
        for line in ADMIN_SECRET.read_text(encoding="utf-8").splitlines():
            if line.startswith("ADMIN_WEB_PW="):
                admin_pw = line.split("=", 1)[1].strip()
                break
    return admin_pw


def login(page, user, password):
    page.goto(
        f"{BASE}/web/login?db={DB}&redirect=/odoo",
        wait_until="domcontentloaded",
        timeout=120000,
    )
    page.wait_for_selector("input#login, input[name='login']", state="visible", timeout=120000)
    page.fill("input#login, input[name='login']", user)
    page.fill("input#password, input[name='password']", password)
    page.get_by_role("button", name=re.compile("log in", re.I)).first.click()
    page.wait_for_timeout(2500)
    if "/web/login" in page.url and "wrong login" in page.inner_text("body").lower():
        page.fill("input#password, input[name='password']", "admin")
        page.get_by_role("button", name=re.compile("log in", re.I)).first.click()
        page.wait_for_timeout(2500)
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
    if not MAN.exists():
        print("MISSING gateD3_review_manifest.json — run gateD3_shell_input.py first", file=sys.stderr)
        return 2
    m = json.loads(MAN.read_text(encoding="utf-8"))
    sid_dxb = m["pos_session_ids"]["POS-DXB-01"]
    j = m["journal_entry_urls"]
    act = m["ir_actions"]

    admin_pw = load_admin_pw()
    report = {"page_errors": [], "console_errors": [], "console_owl": [], "network_failures": []}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")
        ctx = browser.new_context(viewport={"width": 1600, "height": 950})
        page = ctx.new_page()
        attach_listeners(page, report)
        try:
            login(page, "admin", admin_pw)

            page.goto(f"{BASE}/odoo", wait_until="domcontentloaded", timeout=120000)
            page.wait_for_timeout(4000)
            page.screenshot(path=str(OUT / "01_accounting_dashboard_home.png"), full_page=False)

            page.goto(f"{BASE}/odoo/pos.session/{sid_dxb}", wait_until="domcontentloaded", timeout=120000)
            page.wait_for_timeout(4000)
            page.screenshot(path=str(OUT / "02_pos_session_dxb_accounting.png"), full_page=True)

            page.goto(f"{BASE}/odoo/account.move/{j['session_dxb']}", wait_until="domcontentloaded", timeout=120000)
            page.wait_for_timeout(4500)
            page.screenshot(path=str(OUT / "03_journal_entry_session_dxb.png"), full_page=True)

            page.goto(f"{BASE}/odoo/account.move/{j['combine_visa']}", wait_until="domcontentloaded", timeout=120000)
            page.wait_for_timeout(4000)
            page.screenshot(path=str(OUT / "04_payment_move_combine_visa.png"), full_page=True)

            page.goto(f"{BASE}/odoo/account.move/{j['combine_mc']}", wait_until="domcontentloaded", timeout=120000)
            page.wait_for_timeout(4000)
            page.screenshot(path=str(OUT / "05_payment_move_combine_mastercard.png"), full_page=True)

            page.goto(f"{BASE}/odoo/action-{act['tax_return']}", wait_until="domcontentloaded", timeout=120000)
            page.wait_for_timeout(3000)
            clear_odoo_search_facets(page)
            page.wait_for_timeout(3000)
            page.screenshot(path=str(OUT / "06_tax_return_report_action.png"), full_page=True)

            page.goto(f"{BASE}/odoo/action-{act['stock_valuation']}", wait_until="domcontentloaded", timeout=120000)
            page.wait_for_timeout(4500)
            page.screenshot(path=str(OUT / "07_inventory_valuation_moves.png"), full_page=True)

            page.goto(f"{BASE}/odoo/action-{act['stock_moves_analysis']}", wait_until="domcontentloaded", timeout=120000)
            page.wait_for_timeout(4500)
            page.screenshot(path=str(OUT / "08_stock_moves_analysis.png"), full_page=True)

            page.goto(f"{BASE}/odoo/action-{act['pos_orders_analysis']}", wait_until="domcontentloaded", timeout=120000)
            page.wait_for_timeout(4500)
            page.screenshot(path=str(OUT / "09_pos_orders_analysis.png"), full_page=True)

            page.goto(f"{BASE}/odoo/action-{act['sales_analysis']}", wait_until="domcontentloaded", timeout=120000)
            page.wait_for_timeout(4500)
            page.screenshot(path=str(OUT / "10_sales_reporting_analysis.png"), full_page=True)

            page.goto(f"{BASE}/odoo/action-{act['accounting_entries']}", wait_until="domcontentloaded", timeout=120000)
            page.wait_for_timeout(4500)
            page.screenshot(path=str(OUT / "11_journal_entries_list.png"), full_page=True)

        finally:
            ctx.close()
        browser.close()

    out = Path(__file__).resolve().parent / "browser_gateD3.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"WROTE {out}")
    if report["page_errors"] or report["console_errors"] or report["console_owl"]:
        print("WARNINGS", report, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
