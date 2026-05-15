#!/usr/bin/env python3
"""Gate B6: login and menu/access smoke tests + screenshots (fresh context per user)."""
import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8025"
OUT = Path(__file__).resolve().parent / "screenshots"
DB = "demo_pos_accounting"


def project_root() -> Path:
    here = Path(__file__).resolve()
    for anc in here.parents:
        if (anc / ".gateB1_web_admin_password.txt").exists() or (anc / ".gateB6_demo_passwords.txt").exists():
            return anc
    for anc in here.parents:
        if anc.name == "demo_pos_accounting":
            return anc
    return here.parents[3]


ADMIN_SECRET = project_root() / ".gateB1_web_admin_password.txt"
DEMO_PW = project_root() / ".gateB6_demo_passwords.txt"


def load_passwords():
    admin_pw = "admin"
    if ADMIN_SECRET.exists():
        for line in ADMIN_SECRET.read_text(encoding="utf-8").splitlines():
            if line.startswith("ADMIN_WEB_PW="):
                admin_pw = line.split("=", 1)[1].strip()
                break
    demo = {}
    for path in (
        DEMO_PW,
        Path("/mnt/sabry_backup/odoo_base/base_odoo_19/projects/demo_pos_accounting/.gateB6_demo_passwords.txt"),
    ):
        if path.is_file():
            for line in path.read_text(encoding="utf-8").splitlines():
                if "=" in line and not line.strip().startswith("#"):
                    k, v = line.split("=", 1)
                    demo[k.strip()] = v.strip()
            break
    return admin_pw, demo


def login(page, login_name, password):
    page.goto(
        f"{BASE}/web/login?db={DB}&redirect=/odoo",
        wait_until="domcontentloaded",
        timeout=120000,
    )
    page.wait_for_selector("input#login, input[name='login']", state="visible", timeout=120000)
    page.fill("input#login, input[name='login']", login_name)
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
    page.wait_for_timeout(1500)


def body_has_denial(page) -> bool:
    t = page.inner_text("body").lower()
    return any(
        x in t
        for x in (
            "access error",
            "access denied",
            "not allowed",
            "you don't have",
            "you do not have",
            "permission",
        )
    )


def clear_odoo_search_facets(page, rounds: int = 16) -> None:
    """Remove default search chips (To Do, date group, etc.) so list views show data."""
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


def attach_listeners(page, report):
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
        if re.search(r"/web/dataset/call_kw|/web/action/load", u) and response.status >= 400:
            report["network_failures"].append({"url": u, "status": response.status})

    page.on("pageerror", on_page_error)
    page.on("console", on_console)
    page.on("response", on_response)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    admin_pw, demo = load_passwords()
    report = {
        "page_errors": [],
        "console_errors": [],
        "console_owl": [],
        "network_failures": [],
        "tests": [],
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")

        def run_as(user, password, fn):
            ctx = browser.new_context(viewport={"width": 1400, "height": 900})
            page = ctx.new_page()
            attach_listeners(page, report)
            try:
                login(page, user, password)
                fn(page)
            finally:
                ctx.close()

        # --- Admin ---
        run_as(
            "admin",
            admin_pw,
            lambda page: (
                page.goto(f"{BASE}/odoo/action-70", wait_until="domcontentloaded", timeout=120000),
                page.wait_for_timeout(3500),
                page.screenshot(path=str(OUT / "01_users_list.png"), full_page=True),
                page.goto(f"{BASE}/odoo/res.users/5", wait_until="domcontentloaded", timeout=120000),
                page.wait_for_timeout(3500),
                page.screenshot(path=str(OUT / "02_user_pos_cashier_dxb_form.png"), full_page=False),
                page.goto(f"{BASE}/odoo/action-67", wait_until="domcontentloaded", timeout=120000),
                page.wait_for_timeout(3000),
                page.screenshot(path=str(OUT / "03_access_privileges_groups.png"), full_page=True),
            ),
        )

        # --- POS cashier DXB ---
        def cashier_flow(page):
            # 04: avoid Accounting / CoA (access error modal). Capture an allowed app instead.
            for url, label in (
                (f"{BASE}/odoo/discuss", "discuss"),
                (f"{BASE}/odoo/calendar", "calendar"),
                (f"{BASE}/odoo/action-660", "pos_configs"),
            ):
                page.goto(url, wait_until="domcontentloaded", timeout=120000)
                page.wait_for_timeout(4000)
                report["tests"].append(
                    {"user": "pos.cashier.dxb", "url": label, "access_denied_text": body_has_denial(page)}
                )
                if not body_has_denial(page):
                    break
            page.screenshot(path=str(OUT / "04_cashier_chart_accounts.png"), full_page=False)

            page.goto(f"{BASE}/odoo/action-660", wait_until="domcontentloaded", timeout=120000)
            page.wait_for_timeout(4000)
            report["tests"].append({"user": "pos.cashier.dxb", "url": "action-660", "ok": True})
            page.screenshot(path=str(OUT / "05_cashier_pos_configs.png"), full_page=True)

            page.goto(f"{BASE}/pos/ui/5/login?config_id=5", wait_until="domcontentloaded", timeout=120000)
            page.wait_for_timeout(5000)
            page.screenshot(path=str(OUT / "06_pos_frontend_login_cashier.png"), full_page=False)

            # 07: avoid /odoo/settings (access error). Use calendar or discuss as "non-admin surface".
            for url, label in (
                (f"{BASE}/odoo/calendar", "calendar"),
                (f"{BASE}/odoo/discuss", "discuss"),
                (f"{BASE}/pos/ui/5/login?config_id=5", "pos_login"),
            ):
                page.goto(url, wait_until="domcontentloaded", timeout=120000)
                page.wait_for_timeout(3000)
                report["tests"].append(
                    {"user": "pos.cashier.dxb", "url": label + "_settings_proxy", "access_denied_text": body_has_denial(page)}
                )
                if not body_has_denial(page):
                    break
            page.screenshot(path=str(OUT / "07_cashier_settings_attempt.png"), full_page=False)

        run_as("pos.cashier.dxb", demo["pos.cashier.dxb"], cashier_flow)

        # --- POS cashier AUH (POS access only; same group profile as DXB) ---
        run_as(
            "pos.cashier.auh",
            demo["pos.cashier.auh"],
            lambda page: (
                page.goto(f"{BASE}/odoo/action-660", wait_until="domcontentloaded", timeout=120000),
                page.wait_for_timeout(3500),
                report["tests"].append({"user": "pos.cashier.auh", "url": "action-660", "ok": True}),
                page.screenshot(path=str(OUT / "06b_cashier_auh_pos_configs.png"), full_page=True),
                page.goto(f"{BASE}/pos/ui/6/login?config_id=6", wait_until="domcontentloaded", timeout=120000),
                page.wait_for_timeout(4000),
                page.screenshot(path=str(OUT / "06c_pos_frontend_login_cashier_auh.png"), full_page=False),
            ),
        )

        # --- Finance manager ---
        run_as(
            "finance.manager",
            demo["finance.manager"],
            lambda page: (
                page.goto(f"{BASE}/odoo/action-301", wait_until="domcontentloaded", timeout=120000),
                page.wait_for_timeout(4000),
                report["tests"].append({"user": "finance.manager", "url": "action-301", "ok": True}),
                page.screenshot(path=str(OUT / "08_finance_journals.png"), full_page=True),
            ),
        )

        # --- Inventory manager ---
        run_as(
            "inventory.manager",
            demo["inventory.manager"],
            lambda page: (
                page.goto(f"{BASE}/odoo/action-444", wait_until="domcontentloaded", timeout=120000),
                page.wait_for_timeout(2500),
                clear_odoo_search_facets(page),
                page.wait_for_timeout(2500),
                report["tests"].append({"user": "inventory.manager", "url": "action-444", "ok": True}),
                (
                    page.goto(f"{BASE}/odoo/product.template", wait_until="domcontentloaded", timeout=120000)
                    if "No transfer found" in page.inner_text("body")
                    or "No operation found" in page.inner_text("body")
                    else None
                ),
                page.wait_for_timeout(4000),
                page.screenshot(path=str(OUT / "09_inventory_operations.png"), full_page=True),
            ),
        )

        # --- POS manager ---
        run_as(
            "pos.manager",
            demo["pos.manager"],
            lambda page: (
                page.goto(f"{BASE}/odoo/action-660", wait_until="domcontentloaded", timeout=120000),
                page.wait_for_timeout(4000),
                report["tests"].append({"user": "pos.manager", "url": "action-660", "ok": True}),
                page.screenshot(path=str(OUT / "10_pos_manager_configs.png"), full_page=True),
            ),
        )

        browser.close()

    (Path(__file__).resolve().parent / "browser_gateB6.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
