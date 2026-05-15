#!/usr/bin/env python3
"""Headless browser evidence for Gate A (Playwright)."""
import json
import os
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8025"
OUT = Path(__file__).resolve().parent
SHOT = OUT.parent / "screenshots"
ADMIN = "admin"


def project_root() -> Path:
    here = Path(__file__).resolve()
    for anc in here.parents:
        if (anc / ".gateB1_web_admin_password.txt").exists():
            return anc
    for anc in here.parents:
        if anc.name == "demo_pos_accounting":
            return anc
    return here.parents[4]


def load_admin_pw() -> str:
    sec = project_root() / ".gateB1_web_admin_password.txt"
    if sec.exists():
        for line in sec.read_text(encoding="utf-8").splitlines():
            if line.startswith("ADMIN_WEB_PW="):
                return line.split("=", 1)[1].strip()
    return os.environ.get("GATEA_WEB_PASSWORD", "admin")


def hide_database_expiration_banner(page) -> None:
    page.evaluate(
        """() => {
        document.querySelectorAll('.database_expiration_panel').forEach((el) => {
            el.style.setProperty('display', 'none', 'important');
        });
    }"""
    )


# res.users admin password (default after DB init). DB master password is unrelated.
PW = load_admin_pw()


def main() -> int:
    report = {
        "base_url": BASE,
        "console": [],
        "page_errors": [],
        "network_failures": [],
        "subscription_panel": {},
        "urls_visited": [],
        "authenticated": False,
        "blocking_subscription": None,
    }

    def on_console(msg):
        report["console"].append({"type": msg.type, "text": msg.text})

    def on_page_error(exc):
        report["page_errors"].append(str(exc))

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")
        context = browser.new_context(
            viewport={"width": 1400, "height": 900},
            ignore_https_errors=True,
        )
        page = context.new_page()
        page.on("console", on_console)
        page.on("pageerror", on_page_error)

        def track_response(response):
            url = response.url
            if re.search(
                r"/web/|/point_of_sale/|/pos/|/mail/|/web/assets/",
                url,
            ) and not re.search(r"/web/login", url):
                if response.status >= 400:
                    report["network_failures"].append(
                        {"url": url, "status": response.status}
                    )

        page.on("response", track_response)

        # --- Login (db-scoped URL avoids website-only /web/login shell) ---
        page.goto(
            f"{BASE}/web/login?db=demo_pos_accounting&redirect=/odoo",
            wait_until="domcontentloaded",
            timeout=120000,
        )
        page.fill("input#login, input[name='login']", ADMIN)
        page.fill("input#password, input[name='password']", PW)
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
        page.wait_for_timeout(3000)
        hide_database_expiration_banner(page)
        report["urls_visited"].append(page.url)
        report["authenticated"] = "/web/login" not in page.url
        page.screenshot(path=str(SHOT / "01_after_login_web.png"), full_page=False)

        # --- Web client home ---
        page.goto(f"{BASE}/odoo", wait_until="domcontentloaded", timeout=120000)
        report["urls_visited"].append(page.url)
        page.wait_for_selector(
            "body.o_web_client, .o_web_client, .o_action_manager",
            timeout=120000,
        )
        page.wait_for_timeout(2000)
        # Subscription / expiration banner (web_enterprise) — record then hide for clean PNGs
        panel = page.locator(".database_expiration_panel")
        report["subscription_panel"]["count"] = panel.count()
        if panel.count():
            report["subscription_panel"]["outer_html_snippet"] = (
                panel.first.inner_html()[:2000]
            )
            cls = panel.first.get_attribute("class") or ""
            report["subscription_panel"]["class"] = cls
            report["blocking_subscription"] = bool(
                re.search(r"alert-danger|alert-warning", cls)
            )
        hide_database_expiration_banner(page)
        page.screenshot(path=str(SHOT / "02_odoo_home.png"), full_page=False)
        page.screenshot(path=str(SHOT / "03_home_with_banner_check.png"))

        # --- Accounting ---
        page.goto(
            f"{BASE}/odoo/accounting", wait_until="domcontentloaded", timeout=120000
        )
        report["urls_visited"].append(page.url)
        page.wait_for_selector(
            "body.o_web_client, .o_web_client, .o_action_manager",
            timeout=120000,
        )
        page.wait_for_timeout(2500)
        hide_database_expiration_banner(page)
        page.screenshot(path=str(SHOT / "04_accounting_dashboard.png"), full_page=False)

        # --- POS (may redirect if no config) ---
        page.goto(
            f"{BASE}/pos/ui?config_id=1", wait_until="domcontentloaded", timeout=120000
        )
        report["urls_visited"].append(page.url)
        page.wait_for_timeout(5000)
        page.screenshot(path=str(SHOT / "05_pos_ui.png"), full_page=True)

        browser.close()

    # OWL / Odoo client errors in console
    owl_errors = [c for c in report["console"] if "owl" in c["text"].lower()]
    report["owl_console_lines"] = owl_errors[:50]

    (OUT / "browser_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
