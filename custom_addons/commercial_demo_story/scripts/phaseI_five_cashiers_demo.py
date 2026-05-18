# Phase I — Focused demo: 5 PIN-only cashiers on 5 POS configs (presentation layer).
# Idempotent: demo_pos_accounting.phase_i_five_cashiers_done
# Optional orders: demo_pos_accounting.phase_i_five_cashiers_orders_done
#
# Run:
#   odoo-bin shell -c .../odoo_demo_pos_accounting.conf -d demo_pos_accounting --no-http \
#     < .../scripts/phaseI_five_cashiers_demo.py

from pathlib import Path

from odoo import Command, fields

FLAG = "demo_pos_accounting.phase_i_five_cashiers_done"
FLAG_ORDERS = "demo_pos_accounting.phase_i_five_cashiers_orders_done"
LOG_PATH = Path(
    "/home/sabry3/sabry_backup/odoo_base/base_odoo_19/projects/demo_pos_accounting/docs"
) / "phaseI_five_cashiers_shell.txt"

lines = []


def log(msg):
    lines.append(msg)
    print(msg)


ICP = env["ir.config_parameter"].sudo()
if ICP.get_param(FLAG) == "1" and ICP.get_param(FLAG_ORDERS) == "1":
    log("SKIP_PHASE_I_ALREADY_DONE")
    LOG_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    raise SystemExit(0)

employees_done = ICP.get_param(FLAG) == "1"

comp = env.company
adm = env.ref("base.user_admin").with_user(env.ref("base.user_admin")).with_company(comp)
HE = env["hr.employee"].sudo()
Config = env["pos.config"].sudo()
Session = env["pos.session"].sudo()
PosOrder = env["pos.order"].sudo()
PosPayment = env["pos.make.payment"].sudo()
PP = env["product.product"].sudo()

# (employee_name, pin, config_name, config_id)
CASHIERS = [
    ("Demo Cashier — Dubai Flagship", "3001", "POS-DXB-01", 5),
    ("Demo Cashier — Dubai Hills", "3002", "POS-RET-04", 8),
    ("Demo Cashier — Abu Dhabi Mall", "3003", "POS-RET-11", 15),
    ("Demo Cashier — Sharjah City Centre", "3004", "POS-RET-16", 20),
    ("Demo Cashier — Madinat Jumeirah", "3005", "POS-RET-24", 28),
]

ORDER_BASKETS = [
    [("RET-G2-BEV-WAT500", 2)],
    [("RET-G2-BEV-OJ1L", 1), ("RET-G2-SNK-CRP40", 1)],
    [("RET-G2-BEV-WAT500", 1), ("RET-G2-SNK-OAT35", 1)],
    [("RET-G2-SNK-CRP40", 2)],
    [("RET-G2-BEV-WAT500", 1), ("RET-G2-SNK-OAT35", 1)],
]


def safe_user_group_names(user):
    """Inspect groups without assuming groups_id (Odoo 19 may use group_ids)."""
    field_name = None
    for candidate in ("group_ids", "groups_id"):
        if candidate in user._fields:
            field_name = candidate
            break
    if not field_name:
        return []
    groups = user[field_name]
    if "full_name" in groups._fields:
        return groups.mapped("full_name")
    return groups.mapped("name")


def ensure_employee(name, pin):
    emp = HE.search([("name", "=", name), ("company_id", "in", (comp.id, False))], limit=1)
    vals = {
        "name": name,
        "company_id": comp.id,
        "pin": pin,
        "user_id": False,
    }
    if emp:
        emp.write(vals)
        log(f"EMPLOYEE_UPDATED id={emp.id} name={name!r} pin={pin} user_id={emp.user_id.id or False}")
    else:
        emp = HE.create(vals)
        log(f"EMPLOYEE_CREATED id={emp.id} name={name!r} pin={pin}")
    if emp.user_id:
        emp.write({"user_id": False})
        log(f"EMPLOYEE_USER_CLEARED id={emp.id}")
    return emp


def pos_manager_employee():
    u = env["res.users"].sudo().search([("login", "=", "pos.manager")], limit=1)
    if not u:
        return HE.browse()
    emp = HE.search([("user_id", "=", u.id)], limit=1)
    return emp


def assign_config(cfg, cashier, mgr_emp):
    assert cfg.exists(), f"Missing pos.config id={cfg.id}"
    # Demo cashiers must be on basic (not minimal): Odoo hides "Open Register" for _role minimal.
    # advanced_employee_ids is auto-merged by pos_hr with all PoS Manager employees — cannot trim further.
    basic = cashier | mgr_emp if mgr_emp else cashier
    cfg.write(
        {
            "module_pos_hr": True,
            "minimal_employee_ids": [Command.clear()],
            "basic_employee_ids": [Command.set(basic.ids)],
        }
    )
    log(
        f"CONFIG_ASSIGNED {cfg.name!r} id={cfg.id} minimal=[] "
        f"basic={[e.name for e in cfg.basic_employee_ids]} advanced={[e.name for e in cfg.advanced_employee_ids]}"
    )


def close_stale_sessions(cfg):
    """Close only opening/closing sessions — never force-close opened sessions with draft orders."""
    for sess in Session.search(
        [
            ("config_id", "=", cfg.id),
            ("state", "in", ("opening_control", "closing_control")),
        ]
    ):
        label = sess.name
        try:
            if sess.state == "opening_control" and not sess.order_ids:
                sess.delete_opening_control_session()
                log(f"SESSION_DELETED {label}")
                continue
            if sess.state == "opening_control":
                sess.set_opening_control(0, "Phase I demo")
                sess.action_pos_session_open()
            if sess.state == "closing_control":
                sess.action_pos_session_close()
            if sess.exists():
                log(f"SESSION_CLOSED {label} state={sess.state}")
        except Exception as exc:
            log(f"SESSION_WARN {label}: {exc}")


def ensure_session(cfg):
    sess = Session.search([("config_id", "=", cfg.id), ("state", "=", "opened")], limit=1)
    if sess:
        log(f"SESSION_REUSE {sess.name} id={sess.id}")
        return sess
    close_stale_sessions(cfg)
    if Session.search_count([("config_id", "=", cfg.id), ("state", "=", "opened")]):
        raise RuntimeError(f"Open session still exists for {cfg.name}")
    sess = Session.create({"config_id": cfg.id, "user_id": adm.id})
    if sess.state == "opening_control":
        sess.set_opening_control(0, "Phase I sample sale")
    if sess.state != "opened":
        sess.action_pos_session_open()
    return sess


def create_sample_order(cfg, cashier, basket, order_label):
    existing = PosOrder.search(
        [
            ("session_id.config_id", "=", cfg.id),
            ("employee_id", "=", cashier.id),
            ("floating_order_name", "=", order_label),
        ],
        limit=1,
    )
    if existing:
        log(f"ORDER_SKIP_EXISTS {order_label} id={existing.id} state={existing.state}")
        return existing

    sess = ensure_session(cfg)
    cmds = []
    for code, qty in basket:
        p = PP.search([("default_code", "=", code)], limit=1)
        if not p:
            raise RuntimeError(f"Missing product {code}")
        cmds.append(
            Command.create(
                {
                    "product_id": p.id,
                    "qty": qty,
                    "price_unit": p.lst_price,
                    "price_subtotal": p.lst_price * qty,
                    "price_subtotal_incl": 0,
                    "tax_ids": [(6, 0, p.taxes_id.ids)],
                }
            )
        )
    order = PosOrder.with_user(adm).create(
        {
            "amount_total": 0,
            "amount_paid": 0,
            "amount_tax": 0,
            "amount_return": 0,
            "date_order": fields.Datetime.to_string(fields.Datetime.now()),
            "session_id": sess.id,
            "company_id": comp.id,
            "employee_id": cashier.id,
            "floating_order_name": order_label,
            "general_customer_note": "DEMO-PHASEI sample sale",
            "lines": cmds,
        }
    )
    order.lines._onchange_amount_line_all()
    order._compute_prices()
    cash = sess.config_id.payment_method_ids.filtered(lambda m: m.type == "cash")[:1]
    if not cash:
        raise RuntimeError(f"No cash payment method on {cfg.name}")
    ctx = {"active_ids": order.ids, "active_id": order.id}
    wiz = PosPayment.with_user(adm).with_context(**ctx).create({"payment_method_id": cash.id})
    wiz.with_context(**ctx).check()
    order.invalidate_recordset()
    if order.state != "paid":
        raise RuntimeError(f"Order {order_label} not paid: {order.state}")
    log(
        f"ORDER_CREATED {order_label} id={order.id} cfg={cfg.name!r} cashier={cashier.name!r} "
        f"total={order.amount_total} employee_id={order.employee_id.id}"
    )
    draft_left = PosOrder.search_count([("session_id", "=", sess.id), ("state", "=", "draft")])
    if draft_left:
        log(f"SESSION_LEFT_OPEN cfg={cfg.name!r} draft_orders={draft_left} (Phase H table prep)")
    else:
        try:
            if sess.state == "opened":
                sess.action_pos_session_closing_control()
            if sess.exists() and sess.state in ("opened", "closing_control"):
                sess.action_pos_session_close()
            log(f"SESSION_CLOSED_AFTER_ORDER cfg={cfg.name!r}")
        except Exception as exc:
            log(f"SESSION_CLOSE_WARN cfg={cfg.name!r}: {exc}")
    return order


# --- Main: employees + config assignment ---
mgr_emp = pos_manager_employee()
log(f"POS_MANAGER_EMPLOYEE id={mgr_emp.id if mgr_emp else False} name={mgr_emp.name if mgr_emp else '-'}")

cashier_records = []
if not employees_done:
    for name, pin, cfg_name, cfg_id in CASHIERS:
        emp = ensure_employee(name, pin)
        cfg = Config.browse(cfg_id)
        if not cfg.exists() or cfg.name != cfg_name:
            cfg = Config.search([("name", "=", cfg_name)], limit=1)
        if not cfg:
            raise RuntimeError(f"POS config not found: {cfg_name!r} id={cfg_id}")
        assign_config(cfg, emp, mgr_emp)
        cashier_records.append((emp, cfg))
    ICP.set_param(FLAG, "1")
    env.cr.commit()
    log("COMMIT_OK_PHASE_I_EMPLOYEES")
else:
    log("SKIP_EMPLOYEES_ALREADY_DONE")
    for name, _pin, cfg_name, cfg_id in CASHIERS:
        emp = HE.search([("name", "=", name)], limit=1)
        cfg = Config.browse(cfg_id)
        if not cfg.exists():
            cfg = Config.search([("name", "=", cfg_name)], limit=1)
        cashier_records.append((emp, cfg))

# --- Optional sample orders ---
if ICP.get_param(FLAG_ORDERS) != "1":
    try:
        for idx, (emp, cfg) in enumerate(cashier_records):
            label = f"DEMO-PHASEI-{cfg.name.replace(' ', '-')}"
            create_sample_order(cfg, emp, ORDER_BASKETS[idx], label)
        ICP.set_param(FLAG_ORDERS, "1")
        env.cr.commit()
        log("COMMIT_OK_PHASE_I_ORDERS")
    except Exception as exc:
        log(f"ORDERS_FAILED {exc.__class__.__name__}: {exc}")
        log("ORDERS_SKIPPED — employees/config assignment still valid")
        env.cr.rollback()
        env.cr.commit()

# --- Verification ---
log("--- VERIFICATION ---")
for emp, cfg in cashier_records:
    emp.invalidate_recordset()
    cfg.invalidate_recordset()
    log(
        f"VERIFY employee={emp.name!r} pin={emp.pin} user_id={emp.user_id.id or False} "
        f"config={cfg.name!r} id={cfg.id} allowed_minimal={[e.name for e in cfg.minimal_employee_ids]}"
    )

missing_user = HE.search_count(
    [("name", "in", [c[0] for c in CASHIERS]), ("user_id", "!=", False)]
)
assert missing_user == 0, f"Demo cashiers must have no user_id, found {missing_user}"
log(f"VERIFY no_user_id_count={missing_user} (expect 0)")

for name, _pin, cfg_name, cfg_id in CASHIERS:
    emp = HE.search([("name", "=", name)], limit=1)
    cfg = Config.browse(cfg_id)
    assert emp, f"Missing employee {name}"
    assert not emp.user_id, f"{name} still has user"
    assert emp in cfg.minimal_employee_ids, f"{name} not on {cfg_name} minimal employees"
    log(f"VERIFY_OK {name} -> {cfg_name}")

admin = env.ref("base.user_admin")
groups = safe_user_group_names(admin)
log(f"VERIFY admin={admin.login} group_field_sample={groups[:5] if groups else 'n/a'}")

order_count = PosOrder.search_count(
    [
        ("floating_order_name", "=like", "DEMO-PHASEI-%"),
        ("state", "in", ("paid", "done", "invoiced")),
    ]
)
log(f"VERIFY phase_i_orders={order_count}")

log("VERIFY port=8025 (see odoo_demo_pos_accounting.conf http_port)")
log("DONE_PHASE_I")

LOG_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"WROTE {LOG_PATH}")
