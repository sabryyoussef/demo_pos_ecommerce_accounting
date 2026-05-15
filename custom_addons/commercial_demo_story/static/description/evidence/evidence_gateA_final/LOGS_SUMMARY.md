# Logs summary — Gate A final evidence

| Artifact | Scope |
|----------|--------|
| `evidence_gateA/01_init_base_web.log` | Initial `-i base,web,web_enterprise,mail,contacts` |
| `evidence_gateA/02_install_gateA_modules.log` | Full Gate A batch install (~177 modules) |
| `evidence_gateA/03_enable_variants_shell.log` | Shell: product variants |
| `evidence_gateA_final/runtime_odoo_8025.log` | Current HTTP server (8025) after `addons_path` correction |

**Automated grep (install batch):** no `Traceback` / no ` ERROR ` lines in `02_install_gateA_modules.log`.

**Runtime log (8025):** no `Traceback` / no ` ERROR ` in `runtime_odoo_8025.log` for the captured window.

**Known non-fatal Odoo 19 CLI warning:** `--without-demo=all` syntax (use documented 19.0 form in future runs).
