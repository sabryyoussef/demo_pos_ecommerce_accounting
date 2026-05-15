#!/usr/bin/env python3
"""Gate B5 screenshots: POS configs, config form (payment methods), POS UI, sessions, POS settings action."""
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
        "pos_config_dxb_id": None,
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
        if re.search(r"/web/|/bus/|/pos/", u) and response.status >= 400:
            report["network_failures"].append({"url": u, "status": response.status})

    cfg_dxb = psql_scalar("SELECT id FROM pos_config WHERE name = 'POS-DXB-01' LIMIT 1")
    report["pos_config_dxb_id"] = cfg_dxb

    with sync_playwright() as p:
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

        # 1) POS configurations (list)
        page.goto(f"{BASE}/odoo/action-660", wait_until="domcontentloaded", timeout=120000)
        page.wait_for_timeout(4000)
        report["urls"].append(page.url)
        page.screenshot(path=str(OUT / "01_pos_configurations_list.png"), full_page=True)

        # 2) POS-DXB-01 form (payment methods + warehouse visible)
        if cfg_dxb.isdigit():
            page.goto(
                f"{BASE}/odoo/pos.config/{cfg_dxb}",
                wait_until="domcontentloaded",
                timeout=120000,
            )
            page.wait_for_timeout(4500)
            report["urls"].append(page.url)
            page.screenshot(path=str(OUT / "02_pos_config_dxb_form.png"), full_page=True)

        # 3) Payment methods menu (shows linkage journals; visible in POS context)
        page.goto(f"{BASE}/odoo/action-657", wait_until="domcontentloaded", timeout=120000)
        page.wait_for_timeout(3500)
        report["urls"].append(page.url)
        page.screenshot(path=str(OUT / "03_pos_payment_methods.png"), full_page=True)

        # 4) POS frontend (may prompt to open a session; no sale)
        if cfg_dxb.isdigit():
            page.goto(
                f"{BASE}/pos/ui?config_id={cfg_dxb}",
                wait_until="domcontentloaded",
                timeout=120000,
            )
            page.wait_for_timeout(6000)
            report["urls"].append(page.url)
            page.screenshot(path=str(OUT / "04_pos_frontend.png"), full_page=False)

        # 5) Sessions
        page.goto(f"{BASE}/odoo/action-662", wait_until="domcontentloaded", timeout=120000)
        page.wait_for_timeout(4000)
        report["urls"].append(page.url)
        page.screenshot(path=str(OUT / "05_pos_sessions_list.png"), full_page=True)

        # 6) POS configuration / settings entry (action 640)
        page.goto(f"{BASE}/odoo/action-640", wait_until="domcontentloaded", timeout=120000)
        page.wait_for_timeout(4000)
        report["urls"].append(page.url)
        page.screenshot(path=str(OUT / "06_pos_settings_action.png"), full_page=True)

        browser.close()

    (Path(__file__).resolve().parent / "browser_gateB5.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
