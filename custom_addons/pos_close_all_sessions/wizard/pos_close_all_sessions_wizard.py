# -*- coding: utf-8 -*-
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

OPEN_STATES = ("opening_control", "opened", "closing_control")


class PosCloseAllSessionsWizard(models.TransientModel):
    _name = "pos.close.all.sessions.wizard"
    _description = "Close all open POS sessions"

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
    )
    cancel_draft_orders = fields.Boolean(
        string="Cancel draft orders first",
        default=True,
        help="Draft orders block session closing. Enable for unattended bulk close.",
    )
    abandon_opening_control = fields.Boolean(
        string="Remove empty opening-control sessions",
        default=True,
        help="Delete sessions stuck in Opening Control with no orders.",
    )
    open_session_count = fields.Integer(
        string="Open sessions",
        compute="_compute_open_session_count",
    )
    log = fields.Text(string="Result", readonly=True)

    @api.depends("company_id")
    def _compute_open_session_count(self):
        Session = self.env["pos.session"].sudo()
        for wizard in self:
            wizard.open_session_count = Session.search_count(wizard._session_domain())

    def _session_domain(self):
        domain = [("state", "in", OPEN_STATES)]
        if self.company_id:
            domain.append(("company_id", "=", self.company_id.id))
        return domain

    def action_close_all_sessions(self):
        self.ensure_one()
        if not self.env.user.has_group("point_of_sale.group_pos_manager"):
            raise UserError(_("Only POS managers can close all sessions."))

        Session = self.env["pos.session"].sudo()
        sessions = Session.search(self._session_domain(), order="config_id, id")
        if not sessions:
            self.log = _("No open sessions found.")
            return self._reopen_wizard()

        lines = []
        ok = failed = skipped = 0

        for session in sessions:
            label = f"{session.config_id.name} [{session.name}]"
            try:
                with self.env.cr.savepoint():
                    status, msg = self._close_one_session(session)
                if status == "ok":
                    ok += 1
                    lines.append(f"OK  {label}: {msg}")
                elif status == "skip":
                    skipped += 1
                    lines.append(f"SKIP {label}: {msg}")
                else:
                    failed += 1
                    lines.append(f"FAIL {label}: {msg}")
            except Exception as exc:
                failed += 1
                lines.append(f"FAIL {label}: {exc}")
                _logger.exception("Bulk close failed for session %s", session.id)

            if (ok + failed + skipped) % 20 == 0:
                self.env.cr.commit()

        summary = _(
            "Done: %(ok)s closed, %(skip)s skipped, %(fail)s failed (total %(total)s).",
            ok=ok,
            skip=skipped,
            fail=failed,
            total=len(sessions),
        )
        self.log = summary + "\n\n" + "\n".join(lines)
        self.env.cr.commit()
        return self._reopen_wizard()

    def _close_one_session(self, session):
        if session.state == "closed":
            return "skip", _("already closed")

        if session.state == "opening_control":
            if not session.order_ids and self.abandon_opening_control:
                session.unlink()
                return "ok", _("removed (opening control, no orders)")
            if session.order_ids and self.cancel_draft_orders:
                session.order_ids.filtered(lambda o: o.state == "draft").write(
                    {"state": "cancel"}
                )
            if session.state == "opening_control":
                session._set_opening_control_data(0, _("Bulk close (admin)"))
                session = session.browse(session.id)

        if self.cancel_draft_orders:
            drafts = session.get_session_orders().filtered(lambda o: o.state == "draft")
            if drafts:
                drafts.write({"state": "cancel"})

        if session.state == "closing_control":
            session.action_pos_session_validate()
            return "ok", _("closed (was in closing control)")

        if session.state == "opened":
            result = session.action_pos_session_closing_control()
            if isinstance(result, dict):
                balancing = session._get_balancing_account()
                session.action_pos_session_close(balancing, 0, {})
            session = session.browse(session.id)
            if session.state == "closed":
                return "ok", _("closed")
            if session.state == "closing_control":
                session.action_pos_session_validate()
                return "ok", _("closed after validation")
            return "skip", _("still open (check cash control / accounting)")

        return "skip", _("state %(state)s not handled", state=session.state)

    def _reopen_wizard(self):
        return {
            "type": "ir.actions.act_window",
            "name": _("Close all POS sessions"),
            "res_model": self._name,
            "view_mode": "form",
            "res_id": self.id,
            "target": "new",
        }
