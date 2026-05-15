# Phase D — Simulated bank statement lines matching corporate inbound payments (FINCORP partners).
# Reconciles payment liquidity with statement suspense (same pattern as account/tests/test_account_payment.py).
# Idempotent: demo_pos_accounting.final_phase_d_done

from pathlib import Path

from odoo import fields

for ROOT in (
    Path("/home/sabry3/sabry_backup/odoo_base/base_odoo_19/projects/demo_pos_accounting/evidence_final_commercial"),
    Path("/mnt/sabry_backup/odoo_base/base_odoo_19/projects/demo_pos_accounting/evidence_final_commercial"),
):
    if ROOT.is_dir():
        break
else:
    ROOT = Path(".")

LOG = ROOT / "phaseD_shell.txt"
lines = []


def log(msg):
    lines.append(msg)
    print(msg)


ICP = env["ir.config_parameter"].sudo()
FLAG = "demo_pos_accounting.final_phase_d_done"
if ICP.get_param(FLAG) == "1":
    log("SKIP_PHASE_D_ALREADY_DONE")
    LOG.write_text("\n".join(lines) + "\n", encoding="utf-8")
    raise SystemExit(0)

comp = env.company
Partner = env["res.partner"].sudo()
Payment = env["account.payment"].sudo()
BSLine = env["account.bank.statement.line"].sudo()

partners = Partner.search(
    [("ref", "in", ("FINCORP-ALPHA", "FINCORP-BETA")), ("company_id", "in", (comp.id, False))]
)
assert partners, "FINCORP partners missing — run Phase A first"

payments = Payment.search(
    [
        ("company_id", "=", comp.id),
        ("partner_id", "in", partners.ids),
        ("payment_type", "=", "inbound"),
        ("state", "in", ("posted", "in_process", "paid")),
    ],
    order="id asc",
)
log(f"PAYMENTS_FOUND count={len(payments)} ids={payments.ids}")

# Repair orphan in_process payments (no journal entry) left by register-payment edge cases without outstanding account.
for pay in payments.filtered(lambda p: not p.move_id):
    if not pay.outstanding_account_id:
        pay.outstanding_account_id = pay._get_outstanding_account("inbound").id
        log(f"REPAIR_SET_OUTSTANDING pay={pay.name!r} outstanding_id={pay.outstanding_account_id.id}")
    pay._generate_journal_entry()
    if pay.move_id and pay.move_id.state == "draft":
        pay.move_id.action_post()
        log(f"REPAIR_POSTED_MOVE pay={pay.name!r} move={pay.move_id.name!r}")
    # Link payment move counterpart to invoice receivable (same domain as account.payment.register._reconcile_payments)
    domain = [
        ("parent_state", "=", "posted"),
        ("account_type", "in", pay._get_valid_payment_account_types()),
        ("reconciled", "=", False),
    ]
    payment_lines = pay.move_id.line_ids.filtered_domain(domain)
    for inv in pay.reconciled_invoice_ids:
        inv_lines = inv.line_ids.filtered_domain(
            [("parent_state", "=", "posted"), ("account_type", "in", ("asset_receivable",)), ("reconciled", "=", False)]
        )
        for account in payment_lines.account_id:
            (
                payment_lines
                + inv_lines.filtered(lambda l, acc=account: l.account_id == acc and not l.reconciled)
            ).filtered_domain([("account_id", "=", account.id), ("reconciled", "=", False)]).reconcile()
    pay.invalidate_recordset()
    log(f"REPAIR_RECONCILED_INVOICES pay={pay.name!r} invoices={pay.reconciled_invoice_ids.mapped('name')}")

reconciled = 0
for pay in payments:
    ref = f"FIN-DEMO-RECON-{pay.name}"
    existing = BSLine.search(
        [("journal_id", "=", pay.journal_id.id), ("payment_ref", "=", ref), ("company_id", "=", comp.id)], limit=1
    )
    if existing:
        log(f"SKIP_ST_LINE_EXISTS pay={pay.name!r} st_line={existing.id}")
        continue
    pay_date = pay.date or fields.Date.context_today(pay)
    st_line = BSLine.create(
        {
            "date": pay_date,
            "journal_id": pay.journal_id.id,
            "partner_id": pay.partner_id.id,
            "amount": pay.amount,
            "payment_ref": ref,
        }
    )
    _liq_st, st_suspense, _other = st_line.with_context(skip_account_move_synchronization=True)._seek_for_lines()
    pay_liquidity, _pc, _pw = pay._seek_for_lines()
    if not pay_liquidity or not st_suspense:
        log(f"ABORT_NO_LINES pay={pay.name!r} liq={bool(pay_liquidity)} susp={bool(st_suspense)}")
        raise SystemExit(1)
    st_suspense.write({"account_id": pay_liquidity[0].account_id.id})
    (st_suspense + pay_liquidity).reconcile()
    pay.invalidate_recordset()
    log(f"RECONCILED pay={pay.name!r} amount={pay.amount} st_line={st_line.id} is_matched={pay.is_matched}")
    reconciled += 1

ICP.set_param(FLAG, "1")
env.cr.commit()
log(f"COMMIT_OK_PHASE_D reconciled_count={reconciled}")

LOG.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"WROTE {LOG}")
