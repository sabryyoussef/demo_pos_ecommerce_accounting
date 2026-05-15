#!/usr/bin/env python3
"""Gate D4: website shop → product → cart → checkout → COD → confirmation (2 small orders)."""
import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8025"
DB = "demo_pos_accounting"
ROOT = Path(__file__).resolve().parent
OUT = ROOT / "screenshots"
MAN = ROOT / "gateD4_manifest.json"
RESULT = ROOT / "gateD4_browser_result.json"
ADMIN_SECRET = Path(__file__).resolve().parents[2] / ".gateB1_web_admin_password.txt"


def load_admin_pw():
    pw = "admin"
    if ADMIN_SECRET.exists():
        for line in ADMIN_SECRET.read_text(encoding="utf-8").splitlines():
            if line.startswith("ADMIN_WEB_PW="):
                pw = line.split("=", 1)[1].strip()
                break
    return pw


def dburl(path: str) -> str:
    sep = "&" if "?" in path else "?"
    return f"{BASE}{path}{sep}db={DB}"


def attach(page, rep):
    def on_page_error(exc):
        rep["page_errors"].append(str(exc))

    def on_console(msg):
        t = msg.text
        low = t.lower()
        if msg.type == "error" or "error" in low:
            rep["console_errors"].append({"type": msg.type, "text": t[:500]})
        if "owl" in low:
            rep["console_owl"].append({"type": msg.type, "text": t[:500]})

    page.on("pageerror", on_page_error)
    page.on("console", on_console)


def fill_address(page, m):
    page.wait_for_selector("#o_name", timeout=120000)
    page.fill("#o_name", "Gate D4 eCommerce Test")
    page.fill("#o_email", m["test_email"])
    page.fill("#o_phone", "+971500000004")
    page.fill("#o_street", "Gate D4 Test Street 1")
    page.fill("#o_city", "Dubai")
    page.fill("#o_zip", "00000")
    page.select_option("#o_country_id", str(m["country_ae_id"]))
    page.wait_for_timeout(800)
    if page.locator("#o_state_id").count():
        page.select_option("#o_state_id", str(m["state_dubai_id"]))
    # Website sale: address submit is wired to a[name="website_sale_main_button"] (not #save_address)
    btn = page.locator('a[name="website_sale_main_button"]')
    btn.first.wait_for(state="visible", timeout=120000)
    btn.first.click()
    page.wait_for_load_state("networkidle", timeout=120000)
    page.wait_for_timeout(3000)


def click_checkout_continue(page):
    chk = page.locator('a[href^="/shop/checkout"]')
    if chk.count():
        chk.first.click()
        page.wait_for_load_state("networkidle", timeout=120000)
        page.wait_for_timeout(3000)
        return
    btn = page.locator('a[name="website_sale_main_button"]')
    if btn.count():
        btn.first.click()
        page.wait_for_timeout(3000)
        return
    alt = page.get_by_role("link", name=re.compile(r"Continue|Checkout|Payment|Delivery", re.I))
    if alt.count():
        alt.first.click()
        page.wait_for_timeout(3000)


def complete_checkout_before_payment(page):
    """On /shop/checkout: wait for delivery rate RPCs, select carrier, then open payment."""
    if "/shop/checkout" not in page.url:
        return
    page.wait_for_selector("#shop_checkout", timeout=120000)
    if not page.locator('input[name="o_delivery_radio"]').count():
        pay_link = page.locator('a[href^="/shop/payment"]')
        if pay_link.count():
            pay_link.first.click()
            page.wait_for_load_state("networkidle", timeout=120000)
            page.wait_for_timeout(4000)
        return
    # Radios are disabled until get_delivery_rate succeeds (see website_sale checkout.js).
    page.wait_for_function(
        """() => Array.from(document.querySelectorAll('input[name="o_delivery_radio"]')).some(r => !r.disabled)""",
        timeout=120000,
    )
    page.locator('input[name="o_delivery_radio"]:not([disabled])').first.click()
    page.wait_for_timeout(3000)
    pay_link = page.locator('a[href^="/shop/payment"]')
    if pay_link.count():
        pay_link.first.click()
        page.wait_for_load_state("networkidle", timeout=120000)
        page.wait_for_timeout(4000)


def pay_cod(page, m):
    page.wait_for_timeout(2000)
    page.wait_for_selector(
        '#o_payment_methods, input[name="o_payment_radio"], #o_payment_form',
        timeout=120000,
    )
    cod = page.locator('input[name="o_payment_radio"][data-payment-method-code="cash_on_delivery"]')
    if cod.count():
        cod.first.click(force=True)
    else:
        rid = m.get("payment_cod_method_radio_id_hint", 215)
        radio = page.locator(f"#o_payment_method_{rid}")
        if radio.count():
            radio.first.click(force=True)
        else:
            page.locator(
                f'input[name="o_payment_radio"][data-provider-id="{m["payment_cod_provider_id"]}"]'
            ).first.click(force=True)
    page.wait_for_timeout(1500)
    sub = page.locator('button[name="o_payment_submit_button"]')
    sub.first.click()
    page.wait_for_url(re.compile(r"/shop/confirmation"), timeout=180000)
    page.wait_for_timeout(4000)


def extract_order_name(page):
    el = page.locator("#order_name")
    if el.count():
        txt = el.first.inner_text()
        m = re.search(r"S\d+(?:/\d{4}/\d+)?", txt)
        if m:
            return m.group(0).strip()
    m2 = re.search(r"S\d+(?:/\d{4}/\d+)?", page.content())
    return m2.group(0).strip() if m2 else ""


def checkout_flow(page, m, paths, rep, tag):
    """paths: list of product website paths (relative)."""
    for p in paths:
        page.goto(dburl(p), wait_until="domcontentloaded", timeout=120000)
        page.wait_for_timeout(2500)
        page.wait_for_selector("#add_to_cart", state="visible", timeout=120000)
        page.click("#add_to_cart")
        page.wait_for_timeout(2500)

    page.goto(dburl("/shop/cart"), wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(3000)
    page.screenshot(path=str(OUT / f"cart_{tag}.png"), full_page=True)

    click_checkout_continue(page)

    if "/shop/address" in page.url:
        fill_address(page, m)

    # Delivery + further steps until payment
    for _ in range(8):
        if "/shop/payment" in page.url:
            break
        if "/shop/checkout" in page.url:
            complete_checkout_before_payment(page)
            continue
        if page.locator('button[name="o_payment_submit_button"]').count():
            break
        click_checkout_continue(page)
        page.wait_for_timeout(2000)
        if "/shop/address" in page.url:
            fill_address(page, m)

    if "/shop/payment" not in page.url:
        # Last resort: direct payment URL (session must have valid cart)
        page.goto(dburl("/shop/payment"), wait_until="domcontentloaded", timeout=120000)
        page.wait_for_timeout(5000)

    page.screenshot(path=str(OUT / f"checkout_payment_{tag}.png"), full_page=True)
    pay_cod(page, m)
    page.screenshot(path=str(OUT / f"confirmation_{tag}.png"), full_page=True)
    name = extract_order_name(page)
    rep["orders"].append({"tag": tag, "sale_order_name": name, "url": page.url})
    if not name:
        raise RuntimeError(f"Could not parse order name from confirmation ({tag})")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    if not MAN.exists():
        print("Missing gateD4_manifest.json — run part1 first", file=sys.stderr)
        return 2
    m = json.loads(MAN.read_text(encoding="utf-8"))
    paths = m["product_slugs_paths"]

    rep = {"page_errors": [], "console_errors": [], "console_owl": [], "orders": []}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")
        ctx = browser.new_context(viewport={"width": 1400, "height": 900})
        page = ctx.new_page()
        attach(page, rep)
        try:
            page.goto(dburl("/shop"), wait_until="domcontentloaded", timeout=120000)
            page.wait_for_timeout(4000)
            page.screenshot(path=str(OUT / "01_website_shop.png"), full_page=True)

            page.goto(dburl(paths["RET-G2-BEV-WAT500"]), wait_until="domcontentloaded", timeout=120000)
            page.wait_for_timeout(3000)
            page.screenshot(path=str(OUT / "02_product_page_water.png"), full_page=True)

            # Order A: water + oat
            checkout_flow(
                page,
                m,
                [paths["RET-G2-BEV-WAT500"], paths["RET-G2-SNK-OAT35"]],
                rep,
                "order_a",
            )

            # Order B: OJ only (cart is cleared after order)
            page.goto(dburl("/shop"), wait_until="domcontentloaded", timeout=120000)
            page.wait_for_timeout(2000)
            checkout_flow(page, m, [paths["RET-G2-BEV-OJ1L"]], rep, "order_b")

        finally:
            ctx.close()

        # Admin: sale orders + first SO form + stock picking from SO
        ctx2 = browser.new_context(viewport={"width": 1400, "height": 900})
        page2 = ctx2.new_page()
        attach(page2, rep)
        try:
            page2.goto(f"{BASE}/web/login?db={DB}", wait_until="domcontentloaded", timeout=120000)
            page2.fill("input#login", "admin")
            page2.fill("input#password", load_admin_pw())
            page2.get_by_role("button", name="Log in").click()
            page2.wait_for_selector("body.o_web_client", timeout=120000)
            page2.wait_for_timeout(3000)

            # Resolve latest website SO ids via DB — use action list filtered by origin
            page2.goto(f"{BASE}/odoo/action-694?db={DB}", wait_until="domcontentloaded", timeout=120000)
            page2.wait_for_timeout(4000)
            page2.screenshot(path=str(OUT / "10_sales_orders_list.png"), full_page=True)

            # Open newest sale order (first row) if link exists
            link = page2.locator("tr.o_data_row td[name='name'] a, .o_list_table tr td a").first
            if link.count():
                link.click()
                page2.wait_for_timeout(4000)
                page2.screenshot(path=str(OUT / "11_sale_order_form.png"), full_page=True)

                # Picking smart button or inventory tab — try Delivery
                del_btn = page2.get_by_role("button", name=re.compile("Delivery", re.I))
                if del_btn.count():
                    del_btn.first.click()
                    page2.wait_for_timeout(3000)
                    page2.screenshot(path=str(OUT / "12_stock_picking_from_so.png"), full_page=True)

            page2.goto(f"{BASE}/odoo/action-292?db={DB}", wait_until="domcontentloaded", timeout=120000)
            page2.wait_for_timeout(3500)
            page2.screenshot(path=str(OUT / "13_journal_entries.png"), full_page=True)

        finally:
            ctx2.close()
        browser.close()

    RESULT.write_text(json.dumps(rep, indent=2), encoding="utf-8")
    print(f"WROTE {RESULT}")
    if rep["page_errors"] or rep["console_errors"] or rep["console_owl"]:
        print("BROWSER_ISSUES", rep, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
