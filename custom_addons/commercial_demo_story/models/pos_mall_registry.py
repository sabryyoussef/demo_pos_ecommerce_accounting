# -*- coding: utf-8 -*-
"""Mall registry and 390-POS classification (shared by bootstrap + UI)."""
import re

from odoo import api, models

TARGET_POS_COUNT = 390

AUH_RET_IDX = {11, 12, 13, 14, 15, 22, 23, 24, 25, 26, 27, 28}
SHJ_RET_IDX = {16, 17, 18, 19, 20, 21, 29, 30}

EXTRA_MALL_NAMES = [
    "Dubai Outlet Village",
    "Marina Walk Kiosk",
    "JBR Beach Pavilion",
    "Business Bay Tower Shop",
    "DIFC Arcade",
    "Motor City Retail",
    "Silicon Oasis Plaza",
    "Academic City Store",
    "Green Community Shop",
    "Arabian Ranches Mall",
    "Town Square Retail",
    "Al Barsha Heights",
    "Jumeirah Village Circle",
    "Discovery Gardens Unit",
    "International City Pavilion",
    "Warqa Avenue Mall",
    "Rashidiya Centre",
    "Al Qusais Plaza",
    "Horizon Express Al Nahda",
    "Horizon Express Satwa",
    "Karama Shopping Lane",
    "Bur Dubai Souk Annex",
    "Creek Harbour Retail",
    "Palm West Beach Kiosk",
    "Expo City Pavilion",
    "Al Khawaneej Mall",
    "Mushrif Village Shop",
    "Khalifa City Store",
    "Baniyas Square Retail",
    "Mussafah Community Mall",
    "Yas Acres Outlet",
    "Saadiyat Island Kiosk",
    "Reem Island Plaza",
    "Al Maryah Central",
    "Corniche Walk Shop",
    "Al Bateen Mall Annex",
    "Mina Zayed Retail",
    "Al Jimi Plaza",
    "Al Ain Central Market",
    "Fujairah Corniche Mall",
    "Dibba Bay Outlet",
    "Kalba City Centre",
    "Sharjah Waterfront",
    "Al Majaz Promenade",
    "University City Shop",
    "Ajman Corniche Retail",
    "Horizon Hub RAK",
    "Al Hamra Village Store",
    "UAQ Marine Mall",
]

PHASE_C_MALLS = [
    (3, "POS-RET-03", "City Walk"),
    (4, "POS-RET-04", "Dubai Hills Mall"),
    (5, "POS-RET-05", "Ibn Battuta Mall"),
    (6, "POS-RET-06", "Mirdif City Centre"),
    (7, "POS-RET-07", "Deira City Centre"),
    (8, "POS-RET-08", "Al Ghurair Centre"),
    (9, "POS-RET-09", "Festival City Mall"),
    (10, "POS-RET-10", "Dragon Mart 2"),
    (11, "POS-RET-11", "Abu Dhabi Mall"),
    (12, "POS-RET-12", "Yas Mall"),
    (13, "POS-RET-13", "Marina Mall AUH"),
    (14, "POS-RET-14", "Dalma Mall"),
    (15, "POS-RET-15", "Al Wahda Mall"),
    (16, "POS-RET-16", "Sharjah City Centre"),
    (17, "POS-RET-17", "Mega Mall Sharjah"),
    (18, "POS-RET-18", "Al Zahia Mall"),
    (19, "POS-RET-19", "Ajman City Centre"),
    (20, "POS-RET-20", "City Centre Fujairah"),
    (21, "POS-RET-21", "Sahara Centre"),
    (22, "POS-RET-22", "Al Raha Mall"),
    (23, "POS-RET-23", "Mushrif Mall"),
    (24, "POS-RET-24", "Madinat Jumeirah"),
    (25, "POS-RET-25", "The Dubai Frame"),
    (26, "POS-RET-26", "Al Foah Mall"),
    (27, "POS-RET-27", "Al Ain Mall"),
    (28, "POS-RET-28", "Oasis Mall Al Ain"),
    (29, "POS-RET-29", "RAK City Centre"),
    (30, "POS-RET-30", "UAQ City Centre"),
]

AUH_MALL_KW = (
    "abu dhabi",
    "auh",
    "yas ",
    "reem island",
    "khalifa city",
    "al ain",
    "mussafah",
    "maryah",
    "baniyas",
    "bateen",
    "mina zayed",
    "foah",
    "wathba",
    "saadiyat",
    "corniche walk",
)
NORTHERN_MALL_KW = (
    "sharjah",
    "ajman",
    "fujairah",
    "rak ",
    "ras al",
    "uaq",
    "umm al",
    "kalba",
    "dibba",
    "sahara centre",
    "hamra village",
)

REGION_TEAM_XMLIDS = {
    "dxb": "commercial_demo_story.demo_crm_team_pos_dubai",
    "auh": "commercial_demo_story.demo_crm_team_pos_abu_dhabi",
    "shj": "commercial_demo_story.demo_crm_team_pos_northern",
}

REGION_LABEL = {
    "dxb": "Dubai",
    "auh": "Abu Dhabi",
    "shj": "Northern UAE",
}

WAREHOUSE_SPECS = (
    ("WH-DXB-RET", "DXBR1", "dxb"),
    ("WH-AUH-RET", "AUHR1", "auh"),
    ("WH-NOR-RET", "NORR1", "shj"),
)


def mall_label_for_index(idx):
    base = EXTRA_MALL_NAMES[(idx - 31) % len(EXTRA_MALL_NAMES)]
    cycle = (idx - 31) // len(EXTRA_MALL_NAMES)
    if cycle:
        return f"{base} — Unit {cycle + 1}"
    return base


def build_target_malls():
    malls = [
        (1, "POS-DXB-01", "Dubai Mall — Flagship"),
        (2, "POS-AUH-01", "Abu Dhabi Mall — Flagship"),
    ]
    malls.extend(PHASE_C_MALLS)
    for idx in range(31, TARGET_POS_COUNT + 1):
        malls.append((idx, f"POS-RET-{idx}", mall_label_for_index(idx)))
    return malls


def region_for_shop(idx, code, mall_name):
    code_u = (code or "").upper()
    if "AUH" in code_u:
        return "auh"
    if "DXB" in code_u:
        return "dxb"
    if idx in AUH_RET_IDX:
        return "auh"
    if idx in SHJ_RET_IDX:
        return "shj"
    ml = (mall_name or "").lower()
    if any(k in ml for k in AUH_MALL_KW):
        return "auh"
    if any(k in ml for k in NORTHERN_MALL_KW):
        return "shj"
    return "dxb"


def emirate_for_shop(region, mall_name):
    ml = (mall_name or "").lower()
    if "sharjah" in ml or "sahara centre" in ml:
        return "sharjah"
    if "ajman" in ml:
        return "ajman"
    if "fujairah" in ml or "dibba" in ml:
        return "fujairah"
    if "rak " in ml or "ras al" in ml or "hamra" in ml:
        return "ras_al_khaimah"
    if "uaq" in ml or "umm al" in ml:
        return "umm_al_quwain"
    if "al ain" in ml or "jimi" in ml:
        return "al_ain"
    if region == "auh":
        return "abu_dhabi"
    if region == "shj" and "kalba" in ml:
        return "fujairah"
    if region == "shj":
        return "sharjah"
    return "dubai"


def store_format_for_shop(code, mall_name):
    if code in ("POS-DXB-01", "POS-AUH-01"):
        return "flagship"
    ml = (mall_name or "").lower()
    if "kiosk" in ml or "pavilion" in ml or "walk shop" in ml:
        return "kiosk"
    if "outlet" in ml:
        return "outlet"
    return "mall"


class CommercialDemoPosClassifier(models.AbstractModel):
    _name = "commercial.demo.pos.classifier"
    _description = "Classify 390 POS shops for demo navigation"

    @api.model
    def run_classify_390(self, *, force=False):
        """Populate demo fields on all POS configs; create regional warehouses + partners."""
        icp = self.env["ir.config_parameter"].sudo()
        flag = "demo_pos_accounting.pos_classify_390_done"
        if not force and icp.get_param(flag) == "1":
            return {"status": "skipped", "reason": "already_done"}

        comp = self.env.company
        Config = self.env["pos.config"].sudo()
        Partner = self.env["res.partner"].sudo()
        HE = self.env["hr.employee"].sudo()
        Team = self.env["crm.team"].sudo()
        Warehouse = self.env["stock.warehouse"].sudo()

        teams = {}
        for region, xmlid in REGION_TEAM_XMLIDS.items():
            teams[region] = self.env.ref(xmlid, raise_if_not_found=False)
        if not all(teams.values()):
            return {"status": "error", "reason": "missing_crm_teams"}

        wh_by_region = self._ensure_regional_warehouses(Warehouse, comp)
        clusters = self._load_cluster_managers(HE)
        mall_by_code = {code: (idx, mall) for idx, code, mall in build_target_malls()}

        Config = Config.with_context(tracking_disable=True, mail_create_nolog=True)
        cfgs = Config.search([("company_id", "=", comp.id), ("name", "=like", "POS-%")], order="name")
        by_region = {"dxb": Config.browse(), "auh": Config.browse(), "shj": Config.browse()}
        partner_by_name = {
            p.name: p
            for p in Partner.search(
                [("name", "=like", "Horizon — %"), ("company_id", "in", (comp.id, False))]
            )
        }
        pending_partners = []
        cfg_payload = []

        for cfg in cfgs:
            idx, mall = mall_by_code.get(cfg.name, (0, cfg.name))
            if not mall or mall == cfg.name:
                m = re.match(r"POS-RET-(\d+)", cfg.name or "", re.I)
                idx = int(m.group(1)) if m else idx
            region = region_for_shop(idx, cfg.name, mall)
            by_region[region] |= cfg
            emirate = emirate_for_shop(region, mall)
            store_fmt = store_format_for_shop(cfg.name, mall)
            team = teams[region]
            reg_wh = wh_by_region[region]
            partner_name = f"Horizon — {mall}"
            partner = partner_by_name.get(partner_name)
            if not partner:
                pending_partners.append(
                    {
                        "name": partner_name,
                        "company_id": comp.id,
                        "is_company": True,
                        "comment": f"POS code {cfg.name} · {REGION_LABEL[region]}",
                    }
                )
            cfg_payload.append(
                (
                    cfg,
                    {
                        "demo_mall_name": mall,
                        "demo_store_format": store_fmt,
                        "demo_emirate": emirate,
                        "demo_regional_warehouse_id": reg_wh.id,
                        "crm_team_id": team.id,
                        "receipt_header": f"{mall}\n{REGION_LABEL[region]} · {reg_wh.name}",
                        "_partner_name": partner_name,
                        "_partner": partner,
                    },
                )
            )

        if pending_partners:
            created = Partner.create(pending_partners)
            for p in created:
                partner_by_name[p.name] = p
            self.env.cr.commit()

        batch_size = 50
        updated = 0
        for cfg, vals in cfg_payload:
            partner = vals.pop("_partner") or partner_by_name.get(vals.pop("_partner_name"))
            vals["demo_location_partner_id"] = partner.id if partner else False
            cfg.write(vals)
            updated += 1
            if updated % batch_size == 0:
                self.env.cr.commit()

        cluster_assigned = self._assign_cluster_managers(by_region, clusters, batch_size=batch_size)

        icp.set_param(flag, "1")
        self.env.cr.commit()
        return {
            "status": "ok",
            "configs_updated": updated,
            "cluster_assigned": cluster_assigned,
            "warehouses": {k: v.id for k, v in wh_by_region.items()},
            "by_region": {k: len(v) for k, v in by_region.items()},
        }

    @api.model
    def _ensure_regional_warehouses(self, Warehouse, company):
        result = {}
        for wh_name, code, region in WAREHOUSE_SPECS:
            wh = Warehouse.search([("company_id", "=", company.id), ("code", "=", code)], limit=1)
            if not wh:
                wh = Warehouse.search([("company_id", "=", company.id), ("name", "=", wh_name)], limit=1)
            if not wh:
                wh = Warehouse.create(
                    {
                        "name": wh_name,
                        "code": code,
                        "company_id": company.id,
                    }
                )
            else:
                wh.write({"name": wh_name, "code": code})
            result[region] = wh
        return result

    @api.model
    def _load_cluster_managers(self, HE):
        clusters = {"dxb": [], "auh": [], "shj": []}
        for region in clusters:
            prefix = region.upper()
            for i in range(1, 5):
                name = f"Cluster Manager {prefix} {i}"
                emp = HE.search([("name", "=", name), ("company_id", "=", self.env.company.id)], limit=1)
                if emp:
                    clusters[region].append(emp)
        return clusters

    @api.model
    def _assign_cluster_managers(self, by_region, clusters, batch_size=50):
        assigned = 0
        for region, cfgs in by_region.items():
            clist = clusters.get(region) or []
            if not clist or not cfgs:
                continue
            chunk = max(1, (len(cfgs) + len(clist) - 1) // len(clist))
            for i, cfg in enumerate(cfgs.sorted(key=lambda c: c.name or "")):
                cluster = clist[min(i // chunk, len(clist) - 1)]
                cfg.write({"demo_cluster_manager_id": cluster.id})
                assigned += 1
                if assigned % batch_size == 0:
                    self.env.cr.commit()
        return assigned
