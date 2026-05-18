# -*- coding: utf-8 -*-
from odoo import _, api, models

REGION_TEAM_XMLIDS = {
    "dxb": "commercial_demo_story.demo_crm_team_pos_dubai",
    "auh": "commercial_demo_story.demo_crm_team_pos_abu_dhabi",
    "shj": "commercial_demo_story.demo_crm_team_pos_northern",
}

CLUSTER_REGION_CODES = ("DXB", "AUH", "SHJ")


class PosConfig(models.Model):
    _inherit = "pos.config"

    @api.model
    def _domain_for_pos_manager_user(self, user=None):
        """Return a domain of POS configs visible to this manager in the demo hierarchy."""
        user = user or self.env.user
        Employee = self.env["hr.employee"].sudo()
        employee = Employee.search([("user_id", "=", user.id)], limit=1)
        base = [("name", "=like", "POS-%")]

        if not employee:
            if user.has_group("point_of_sale.group_pos_manager"):
                return base
            return [("id", "=", 0)]

        name = employee.name or ""

        if "Regional POS Manager" in name:
            if "Dubai" in name:
                team = self.env.ref(REGION_TEAM_XMLIDS["dxb"], raise_if_not_found=False)
            elif "Abu Dhabi" in name:
                team = self.env.ref(REGION_TEAM_XMLIDS["auh"], raise_if_not_found=False)
            elif "Northern" in name:
                team = self.env.ref(REGION_TEAM_XMLIDS["shj"], raise_if_not_found=False)
            else:
                team = False
            if team:
                return base + [("crm_team_id", "=", team.id)]
            return base + [("demo_regional_manager_id", "=", employee.id)]

        if name.startswith("Cluster Manager "):
            return base + [("demo_cluster_manager_id", "=", employee.id)]

        if user.has_group("point_of_sale.group_pos_manager"):
            return base

        return [("id", "=", 0)]

    @api.model
    def _config_domain_for_cluster_name(self, cluster_name):
        return [("name", "=like", "POS-%"), ("demo_cluster_manager_id.name", "=", cluster_name)]

    @api.model
    def _config_domain_for_region_team(self, region_key):
        team = self.env.ref(REGION_TEAM_XMLIDS[region_key], raise_if_not_found=False)
        if not team:
            return [("id", "=", 0)]
        return [("name", "=like", "POS-%"), ("crm_team_id", "=", team.id)]

    @api.model
    def action_open_pos_hierarchy_window(self, *, name, domain, group_by_cluster=False):
        ctx = {}
        if group_by_cluster:
            ctx["search_default_group_by_cluster_manager"] = 1
        return {
            "type": "ir.actions.act_window",
            "name": name,
            "res_model": "pos.config",
            "view_mode": "list,form",
            "search_view_id": self.env.ref("point_of_sale.view_pos_config_search").id,
            "domain": domain,
            "context": ctx,
        }

    @api.model
    def action_open_my_pos_shops(self):
        return self.action_open_pos_hierarchy_window(
            name=_("My POS shops"),
            domain=self._domain_for_pos_manager_user(),
            group_by_cluster=True,
        )


class PosOrder(models.Model):
    _inherit = "pos.order"

    @api.model
    def _domain_for_pos_manager_user(self, user=None):
        configs = self.env["pos.config"].search(
            self.env["pos.config"]._domain_for_pos_manager_user(user)
        )
        return [("config_id", "in", configs.ids)]
