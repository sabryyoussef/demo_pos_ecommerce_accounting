# -*- coding: utf-8 -*-
{
    "name": "POS Close All Sessions",
    "version": "19.0.1.0.0",
    "category": "Sales/Point of Sale",
    "summary": "Close every open POS session in one click",
    "description": """
Adds a wizard under Point of Sale to close all sessions that are not closed yet
(opening control, in progress, or closing control). Optional: cancel draft orders first.
    """,
    "author": "Horizon Retail Demo",
    "license": "LGPL-3",
    "depends": ["point_of_sale"],
    "data": [
        "security/ir.model.access.csv",
        "wizard/pos_close_all_sessions_wizard_views.xml",
        "views/menu.xml",
    ],
    "installable": True,
    "application": False,
}
