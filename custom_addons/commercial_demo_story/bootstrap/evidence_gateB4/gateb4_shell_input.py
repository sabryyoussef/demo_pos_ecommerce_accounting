# Gate B4 — journals + POS payment methods (structure only). Requires env.cr.commit().

comp = env.company
aed = env.ref("base.AED")
Journal = env["account.journal"].sudo()
PM = env["pos.payment.method"].sudo()

inv_ref = {"invoice_reference_type": "invoice", "invoice_reference_model": "odoo"}

moves_before = env["account.move"].sudo().search_count([])
stmt_before = env["account.bank.statement"].sudo().search_count([])
pay_before = env["account.payment"].sudo().search_count([])


def get_or_create_journal(display_name, code, jtype):
    code = (code or "")[:5]
    j = Journal.search([("company_id", "=", comp.id), ("code", "=", code)], limit=1)
    vals = {
        "name": display_name,
        "code": code,
        "type": jtype,
        "company_id": comp.id,
        "currency_id": aed.id,
        **inv_ref,
    }
    if j:
        j.write(vals)
        return j
    return Journal.create(vals)


# Journals (code max 5 chars on account.journal; full names as requested.)
j_bnk_main = get_or_create_journal("BNK-MAIN-AED", "BMAIN", "bank")
j_pos_cash = get_or_create_journal("POS-CASH-AED", "PCASH", "cash")
# pos.payment.method only allows journals type 'cash' or 'bank' (not 'credit').
j_pos_visa = get_or_create_journal("POS-VISA-AED", "PVISA", "bank")
j_pos_mc = get_or_create_journal("POS-MC-AED", "MCARD", "bank")
j_stripe = get_or_create_journal("ACQ-STRIPE-AED", "AQSTR", "bank")

print(
    "JOURNALS",
    j_bnk_main.id,
    j_bnk_main.code,
    j_pos_cash.id,
    j_pos_visa.id,
    j_pos_mc.id,
    j_stripe.id,
)


def get_or_create_pm(label, journal):
    pm = PM.search([("company_id", "=", comp.id), ("name", "=", label)], limit=1)
    vals = {"name": label, "journal_id": journal.id, "company_id": comp.id}
    if pm:
        pm.write(vals)
        return pm
    return PM.create(vals)


pm_cash = get_or_create_pm("POS Cash AED", j_pos_cash)
pm_visa = get_or_create_pm("POS Visa AED", j_pos_visa)
pm_mc = get_or_create_pm("POS Mastercard AED", j_pos_mc)
pm_stripe = get_or_create_pm("POS Stripe AED", j_stripe)

print(
    "POS_PAYMENT_METHODS",
    pm_cash.id,
    pm_visa.id,
    pm_mc.id,
    pm_stripe.id,
)

# No live credentials: ensure Stripe-related params are empty / not set for demo keys
ICP = env["ir.config_parameter"].sudo()
for key in ("payment_stripe.publishable_key", "payment_stripe.secret_key"):
    if ICP.get_param(key):
        ICP.set_param(key, "")
        print("CLEARED_PARAM", key)

# Duplicate journal codes per company
from collections import Counter

codes = Journal.search([("company_id", "=", comp.id)]).mapped("code")
dupes = [c for c, n in Counter(codes).items() if n > 1]
assert not dupes, dupes

moves_after = env["account.move"].sudo().search_count([])
stmt_after = env["account.bank.statement"].sudo().search_count([])
pay_after = env["account.payment"].sudo().search_count([])
print(
    "COUNTS_BEFORE_AFTER",
    "move",
    moves_before,
    moves_after,
    "stmt",
    stmt_before,
    stmt_after,
    "payment",
    pay_before,
    pay_after,
)
assert moves_after == moves_before
assert stmt_after == stmt_before
assert pay_after == pay_before

env.cr.commit()
print("COMMIT_OK")
