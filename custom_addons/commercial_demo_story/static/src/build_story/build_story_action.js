/** @odoo-module **/

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";
import { _t } from "@web/core/l10n/translation";

export class CommercialDemoBuildStoryAction extends Component {
    static template = "commercial_demo_story.BuildStoryAction";
    static props = { ...standardActionServiceProps };
    static displayName = _t("Build Story Gallery");
    static target = "current";

    get iframeSrc() {
        return "/commercial_demo_story/static/description/build_story.html";
    }
}

registry.category("actions").add(
    "commercial_demo_build_story",
    CommercialDemoBuildStoryAction
);
