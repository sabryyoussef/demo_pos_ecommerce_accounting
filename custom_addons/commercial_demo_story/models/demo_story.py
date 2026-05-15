# -*- coding: utf-8 -*-
from odoo import _, fields, models
from odoo.exceptions import UserError


class CommercialDemoStoryStep(models.Model):
    _name = "commercial.demo.story.step"
    _description = "Commercial Demo Story Step"
    _order = "sequence, id"

    STORY_SOURCE_MODULE = "module"
    STORY_SOURCE_GENERATED = "generated"

    sequence = fields.Integer(default=10)
    name = fields.Char(required=True, translate=True)
    description = fields.Text(translate=True)
    presenter_script = fields.Text(
        string="Presenter script",
        translate=True,
        help="Suggested wording for live demo narration.",
    )
    related_model_name = fields.Char(string="Related model (technical)")
    related_record_ref = fields.Char(
        string="Related record ref",
        help="Optional ir.model.data xml_id of a record to inspect.",
    )
    action_xmlid = fields.Char(
        string="Primary action (XML ID)",
        help="Action opened by the Open Step Action button.",
    )
    story_source = fields.Selection(
        [
            (STORY_SOURCE_MODULE, "Shipped with module"),
            (STORY_SOURCE_GENERATED, "COMM-DEMO generated"),
        ],
        default=STORY_SOURCE_MODULE,
        required=True,
        index=True,
    )
    active = fields.Boolean(default=True)

    def action_open_step_action(self):
        self.ensure_one()
        if not self.action_xmlid:
            raise UserError(_("This step has no primary action configured."))
        return self.env["ir.actions.actions"]._for_xml_id(self.action_xmlid)

    def action_open_related_record(self):
        self.ensure_one()
        if not self.related_record_ref:
            raise UserError(_("No related record reference is set on this step."))
        rec = self.env.ref(self.related_record_ref, raise_if_not_found=False)
        if not rec:
            raise UserError(_("The referenced record was not found: %s") % self.related_record_ref)
        return {
            "type": "ir.actions.act_window",
            "res_model": rec._name,
            "res_id": rec.id,
            "view_mode": "form",
            "target": "current",
        }
