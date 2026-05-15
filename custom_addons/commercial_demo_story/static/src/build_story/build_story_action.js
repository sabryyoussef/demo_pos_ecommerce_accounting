/** @odoo-module **/

import { Component, xml } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";
import { _t } from "@web/core/l10n/translation";

/**
 * Full-screen iframe for static/description/build_story.html (gates A–D gallery).
 */
class CommercialDemoBuildStoryAction extends Component {
    static template = xml`
        <div class="o_commercial_demo_build_story_wrap h-100 w-100">
            <iframe
                class="o_commercial_demo_build_story_iframe w-100 border-0"
                t-att-src="iframeSrc"
                title="Horizon Retail build story"
            />
        </div>
    `;
    static props = { ...standardActionServiceProps };
    static displayName = _t("Build Story Gallery");

    get iframeSrc() {
        return "/commercial_demo_story/static/description/build_story.html";
    }
}

registry.category("actions").add("commercial_demo_build_story", CommercialDemoBuildStoryAction);
