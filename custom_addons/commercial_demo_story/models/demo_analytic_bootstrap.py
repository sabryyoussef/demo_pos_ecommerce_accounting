# -*- coding: utf-8 -*-
"""Idempotent demo analytic plans, accounts, and posted journal lines for reporting."""

from datetime import timedelta

from odoo import Command, api, fields, models


def _get_or_create_root_plan(env, name, sequence):
    Plan = env["account.analytic.plan"].sudo()
    plan = Plan.search([("name", "=", name), ("parent_id", "=", False)], limit=1)
    if plan:
        return plan
    return Plan.create(
        {
            "name": name,
            "parent_id": False,
            "sequence": sequence,
            "default_applicability": "optional",
        }
    )


def _get_or_create_account(env, company, plan, name, code):
    Account = env["account.analytic.account"].sudo()
    dom = [("plan_id", "=", plan.id), ("code", "=", code), ("company_id", "=", company.id)]
    acc = Account.search(dom, limit=1)
    if acc:
        return acc
    return Account.create(
        {
            "name": name,
            "code": code,
            "plan_id": plan.id,
            "company_id": company.id,
        }
    )


def _bootstrap_plans_and_accounts(env, company):
    plan_channel = _get_or_create_root_plan(env, "Channel", 20)
    plan_pos = _get_or_create_root_plan(env, "POS Location", 30)
    plan_dept = _get_or_create_root_plan(env, "Department", 40)
    specs = [
        (plan_channel, "Corporate / HQ", "AN-CH-CORP"),
        (plan_channel, "E-commerce", "AN-CH-ECOM"),
        (plan_channel, "POS retail", "AN-CH-POS"),
        (plan_pos, "Dubai Mall — POS 01", "AN-POS-DXB-01"),
        (plan_pos, "Abu Dhabi — POS 01", "AN-POS-AUH-01"),
        (plan_dept, "Sales", "AN-DPT-SALES"),
        (plan_dept, "Operations", "AN-DPT-OPS"),
        (plan_dept, "HR", "AN-DPT-HR"),
    ]
    accounts = {}
    for plan, title, code in specs:
        accounts[code] = _get_or_create_account(env, company, plan, title, code)
    return accounts


def _pick_credit_account(env, company):
    bank_journal = env["account.journal"].sudo().search(
        [("company_id", "=", company.id), ("type", "=", "bank")], limit=1
    )
    if bank_journal and bank_journal.default_account_id:
        return bank_journal.default_account_id
    return (
        env["account.account"]
        .sudo()
        .search(
            [
                ("company_ids", "in", company.ids),
                ("account_type", "=", "asset_current"),
            ],
            limit=1,
        )
    )


def _pick_expense_account(env, company):
    return (
        env["account.account"]
        .sudo()
        .search(
            [
                ("company_ids", "in", company.ids),
                ("account_type", "=", "expense"),
            ],
            limit=1,
        )
    )


def _pick_income_account(env, company):
    return (
        env["account.account"]
        .sudo()
        .search(
            [
                ("company_ids", "in", company.ids),
                ("account_type", "=", "income"),
            ],
            limit=1,
        )
    )


DEMO_BUDGET_NAME = "COMM-DEMO - Analytic OPEX Budget"


def _budget_line_vals_for_account(acc, budget_amount):
    """Map analytic account to the correct budget.line column (project vs x_plan*)."""
    fname = acc.plan_id.root_id._column_name()
    return {fname: acc.id, "budget_amount": budget_amount}


def _bootstrap_budget_analytic(env, company, accounts):
    """Enterprise account_budget: open expense budget vs demo POS/channel/dept accounts."""
    if "budget.analytic" not in env.registry:
        return {"status": "skipped", "reason": "account_budget_not_installed"}
    Budget = env["budget.analytic"].sudo()
    if Budget.search([("name", "=", DEMO_BUDGET_NAME)], limit=1):
        return {"status": "already_present"}
    fy = company.compute_fiscalyear_dates(fields.Date.today())
    line_specs = [
        (accounts["AN-POS-DXB-01"], 3500.0),
        (accounts["AN-POS-AUH-01"], 2000.0),
        (accounts["AN-CH-CORP"], 5000.0),
        (accounts["AN-CH-ECOM"], 3000.0),
        (accounts["AN-DPT-SALES"], 2000.0),
    ]
    budget = Budget.create(
        {
            "name": DEMO_BUDGET_NAME,
            "date_from": fy["date_from"],
            "date_to": fy["date_to"],
            "budget_type": "expense",
            "company_id": company.id,
            "budget_line_ids": [
                Command.create(_budget_line_vals_for_account(acc, amt))
                for acc, amt in line_specs
            ],
        }
    )
    budget.action_budget_confirm()
    return {"status": "created", "budget_id": budget.id}


def _bootstrap_demo_moves(env, company, accounts):
    """Posted misc entries with analytic_distribution (idempotent by move ref)."""
    Move = env["account.move"].sudo()
    if Move.search([("ref", "=", "COMM-DEMO-ANALYTIC-01")], limit=1):
        return {"status": "already_present"}
    expense = _pick_expense_account(env, company)
    income = _pick_income_account(env, company)
    credit_acc = _pick_credit_account(env, company)
    if not expense or not credit_acc:
        return {"status": "skipped", "reason": "missing_expense_or_credit_account"}
    journal = env["account.journal"].sudo().search(
        [("company_id", "=", company.id), ("type", "=", "general")],
        order="sequence, id",
        limit=1,
    )
    if not journal:
        return {"status": "skipped", "reason": "no_general_journal"}

    today = fields.Date.context_today(company)
    ad_dxb = {str(accounts["AN-POS-DXB-01"].id): 100.0}
    ad_auh = {str(accounts["AN-POS-AUH-01"].id): 100.0}
    ad_split_channel = {
        str(accounts["AN-CH-CORP"].id): 55.0,
        str(accounts["AN-CH-ECOM"].id): 45.0,
    }
    ad_pos_dept = {
        str(accounts["AN-POS-DXB-01"].id): 70.0,
        str(accounts["AN-DPT-SALES"].id): 30.0,
    }

    specs = [
        {
            "ref": "COMM-DEMO-ANALYTIC-01",
            "narration": "Demo analytic — POS Dubai (retail expense)",
            "days_ago": 25,
            "lines": [
                (
                    "Store supplies — DXB POS",
                    expense,
                    1850.0,
                    0.0,
                    ad_dxb,
                ),
                ("Offset", credit_acc, 0.0, 1850.0, False),
            ],
        },
        {
            "ref": "COMM-DEMO-ANALYTIC-02",
            "narration": "Demo analytic — POS Abu Dhabi",
            "days_ago": 18,
            "lines": [
                ("Local marketing — AUH POS", expense, 920.0, 0.0, ad_auh),
                ("Offset", credit_acc, 0.0, 920.0, False),
            ],
        },
        {
            "ref": "COMM-DEMO-ANALYTIC-03",
            "narration": "Demo analytic — split channel (corporate vs eCommerce)",
            "days_ago": 12,
            "lines": [
                ("Shared logistics charge", expense, 2400.0, 0.0, ad_split_channel),
                ("Offset", credit_acc, 0.0, 2400.0, False),
            ],
        },
        {
            "ref": "COMM-DEMO-ANALYTIC-04",
            "narration": "Demo analytic — POS + department on one line",
            "days_ago": 7,
            "lines": [
                ("Promo materials — sales at DXB", expense, 640.0, 0.0, ad_pos_dept),
                ("Offset", credit_acc, 0.0, 640.0, False),
            ],
        },
    ]
    if income:
        specs.append(
            {
                "ref": "COMM-DEMO-ANALYTIC-05",
                "narration": "Demo analytic — other income with channel tag",
                "days_ago": 3,
                "lines": [
                    ("Counterparty", credit_acc, 3100.0, 0.0, False),
                    (
                        "Miscellaneous channel income (demo)",
                        income,
                        0.0,
                        3100.0,
                        {str(accounts["AN-CH-POS"].id): 100.0},
                    ),
                ],
            }
        )

    for spec in specs:
        move_date = today - timedelta(days=spec["days_ago"])
        line_cmds = []
        for name, acc, debit, credit, analytic in spec["lines"]:
            vals = {
                "name": name,
                "account_id": acc.id,
                "debit": debit,
                "credit": credit,
            }
            if analytic:
                vals["analytic_distribution"] = analytic
            line_cmds.append(Command.create(vals))
        move = Move.create(
            {
                "move_type": "entry",
                "journal_id": journal.id,
                "company_id": company.id,
                "date": move_date,
                "ref": spec["ref"],
                "narration": spec["narration"],
                "line_ids": line_cmds,
            }
        )
        move.action_post()

    return {"status": "created", "moves": len(specs)}


def bootstrap_demo_analytic_data(env):
    """Plans, accounts, posted analytic moves, and (if Enterprise) analytic budgets."""
    company = env.company
    accounts = _bootstrap_plans_and_accounts(env, company)
    moves_info = _bootstrap_demo_moves(env, company, accounts)
    budget_info = _bootstrap_budget_analytic(env, company, accounts)
    return {"moves": moves_info, "budget": budget_info}


class CommercialDemoAnalyticLoader(models.AbstractModel):
    _name = "commercial.demo.analytic.loader"
    _description = "Loads idempotent analytic demo data (plans, accounts, posted lines)"

    @api.model
    def run_bootstrap(self):
        return bootstrap_demo_analytic_data(self.env)
