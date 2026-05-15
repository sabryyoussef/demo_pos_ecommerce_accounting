# -*- coding: utf-8 -*-
{
    "name": "Commercial Demo Story",
    "version": "19.0.1.0.8",
    "category": "Sales",
    "summary": "Presentation dashboard, flashcards, workflow story, and safe demo helpers",
    "description": """
Commercial Demo Story
=====================
Executive-friendly navigation and narration helpers for a completed multi-channel
retail demo (corporate sales, ecommerce, POS, accounting). KPIs are read-only
aggregates. Reset only removes story rows created by **Generate Demo Story**
(marked COMM-DEMO / generated source), never posted accounting or live orders.
    """,
    "author": "Horizon Retail Demo",
    "license": "LGPL-3",
    "depends": [
        "base",
        "analytic",
        "sale",
        "account",
        "stock",
        "point_of_sale",
        "website_sale",
        "hr",
        "account_reports",
        "account_budget",
        "sales_team",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/demo_dashboard_views.xml",
        "views/demo_flashcard_views.xml",
        "views/demo_story_views.xml",
        "data/demo_dashboard.xml",
        "data/demo_actions.xml",
        "data/demo_scenarios.xml",
        "data/demo_flashcards.xml",
        "data/demo_story_steps.xml",
        "data/demo_analytic_bootstrap.xml",
        "data/demo_database/product_category.xml",
        "data/demo_database/account_analytic_plan.xml",
        "data/demo_database/account_analytic_account.xml",
        "data/demo_database/product_template.xml",
        "data/demo_database/res_partner.xml",
        "data/demo_database/crm_team.xml",
        "data/demo_database/demo_bootstrap_transactions.xml",
        "views/menu.xml",
        "views/menu_pos_accounting_prep.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "commercial_demo_story/static/src/build_story/build_story_action.js",
            "commercial_demo_story/static/src/build_story/build_story_action.scss",
        ],
    },
    "installable": True,
    "application": False,
    "pre_init_hook": "pre_init_hook",
    "post_init_hook": "post_init_hook",
}
