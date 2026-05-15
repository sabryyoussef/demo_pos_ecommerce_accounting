# Runtime topology — `demo_pos_accounting` (Gate A final)

**Captured:** 2026-05-13 (host inspection + Odoo startup log + live PID 25820)

## 1. Authoritative paths (canonical `readlink -f`)

| Role | Path |
|------|------|
| **Workspace / process cwd** | `/mnt/sabry_backup/odoo_base/base_odoo_19` (equivalent to `/home/sabry3/sabry_backup/odoo_base/base_odoo_19` on this host; same checkout) |
| **Odoo entrypoint (`odoo-bin`)** | `/home/sabry3/odoo_ssd/odoo19/odoo19/odoo-bin` |
| **Community addons** | `/home/sabry3/odoo_ssd/odoo19/odoo19/addons` |
| **Enterprise addons** | `/home/sabry3/odoo_ssd/odoo19/odoo19/enterprise` |
| **Project `data_dir` (filestore + extra addons)** | `/mnt/sabry_backup/odoo_base/base_odoo_19/projects/demo_pos_accounting/.filestore` |
| **Config file (runtime `-c`)** | `/home/sabry3/sabry_backup/odoo_base/base_odoo_19/config/projects/odoo_demo_pos_accounting.conf` → resolves to same inode as `/mnt/sabry_backup/odoo_base/base_odoo_19/config/projects/odoo_demo_pos_accounting.conf` |
| **Python interpreter (venv)** | `./venv19/bin/python3` → `/usr/bin/python3.12` (venv uses system 3.12) |
| **Project `custom_addons` (on disk only)** | `/mnt/sabry_backup/odoo_base/base_odoo_19/projects/demo_pos_accounting/custom_addons` (only `.gitkeep`; **not** on `addons_path` — see `ADDONS_PATH_INTEGRITY.txt`) |

**Why two “roots” (`/home/.../sabry_backup` vs `/mnt/sabry_backup`)?** Same bind mount / symlink layout: config and project data are addressed under `sabry_backup` while the running shell’s cwd is `/mnt/sabry_backup/...`. Odoo source under `…/odoo19/odoo19` is a symlink chain to **`/home/sabry3/odoo_ssd/odoo19/odoo19`** — that SSD tree is the **single physical Odoo 19 + Enterprise codebase** in use.

## 2. Effective `addons_path` at runtime (Odoo-expanded)

From `runtime_odoo_8025.log` (order preserved):

1. `/home/sabry3/odoo_ssd/odoo19/odoo19/odoo/addons` — core Odoo namespace  
2. `…/projects/demo_pos_accounting/.filestore/addons/19.0` — extra addons dir under `data_dir`  
3. `/home/sabry3/odoo_ssd/odoo19/odoo19/addons` — community  
4. `/home/sabry3/odoo_ssd/odoo19/odoo19/enterprise` — enterprise  

Config file sets **only** community + enterprise; Odoo injects (1) and (2) automatically.

## 3. Live process (representative)

- **Command:** `./venv19/bin/python3 odoo19/odoo19/odoo-bin -c /home/sabry3/sabry_backup/odoo_base/base_odoo_19/config/projects/odoo_demo_pos_accounting.conf -d demo_pos_accounting --http-port=8025`  
- **HTTP:** `127.0.0.1:8025`  
- **DB:** PostgreSQL `demo_pos_accounting` @ `localhost:5432`, user `odoo19`

## 4. Credentials note (operational)

- **`admin_passwd` in config:** database manager master password (not the internal user login).  
- **Internal user `admin`:** default web/XML-RPC password is **`admin`** on this DB until you change it (verified via XML-RPC `authenticate` during evidence). **Rotate before any non-local exposure.**

## 5. Intentional stability rules

1. Always start Odoo from the **same checkout** (`base_odoo_19`) with **this** `-c` file and **this** DB.  
2. Do not point another Odoo major version at `demo_pos_accounting` without a migration plan.  
3. When the first real custom module is added under `projects/demo_pos_accounting/custom_addons/`, append that directory to `addons_path` in the config (Odoo 19 skips directories with no valid addon subtree).
