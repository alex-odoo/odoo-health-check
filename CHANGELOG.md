# Changelog

All notable changes to this module are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Module versioning: `<odoo_major>.0.<major>.<minor>.<patch>`.

## [18.0.1.4.0] - 2026-04-24

### Added
- Email alert on cron failure
  - New dependency: `mail`
  - `mail.template` `mail_template_cron_failure` with HTML body (cron name, start/end, duration, server, traceback)
  - `res.config.settings` extension with `odoo_health_notify_emails` (stored in `ir.config_parameter` key `odoo_health_check.notify_emails`)
  - Settings view block "Health Check" with Notifications setting
  - New menu: Health Check -> Settings (opens inline settings form scoped to our block)
  - Email is enqueued (`force_send=False`) in the failure branch of `_odoo_health_log_end`; skipped silently when the setting is empty
  - Any failure inside the email path is caught and logged - never propagates to the cron runner

## [18.0.1.3.0] - 2026-04-24

### Changed
- `duration_sec` now measured via `time.perf_counter()` inside the cron overrides (sub-second precision)
- Dropped the computed `duration_sec` from `date_end - date_start`, since Odoo Datetime fields are second-granular and many system crons complete in <1s

## [18.0.1.2.1] - 2026-04-24

### Added
- `ir.cron.method_direct_trigger` override: manual "Run Manually" clicks now also write history rows
  - Needed because the manual trigger path bypasses `_callback` and would otherwise be invisible in the audit trail

## [18.0.1.2.0] - 2026-04-24

### Added
- `ir.cron._callback` override: every scheduled action execution writes an `ir.cron.history` row
  - 'running' row created before the call; finalized to 'success' or 'failed' (with full traceback) after
  - History writes use an independent database cursor so a cron rollback or failure does not erase the audit trail
  - Writes are sudoed; logging failures are swallowed and logged, never propagate to the cron runner

## [18.0.1.1.0] - 2026-04-24

### Added
- `ir.cron.history` model storing one record per scheduled action run
  - Fields: cron_id (m2o ir.cron), date_start, date_end, duration_sec (computed), state (running/success/failed), error_traceback, server_name
  - SQL constraint: end time must be on or after start time
- Access rights restricted to `base.group_system` (Settings/Administration)
- List, form, and search views with status badge decorations, Last 24h / Last 7d filters, group-by by cron / state / server / day
- Top-level "Health Check" menu with "Cron History" submenu

## [18.0.1.0.0] - 2026-04-24

### Added
- Initial scaffold: empty installable module targeting Odoo 18
- Manifest with metadata, LGPL-3 license, `base` dependency
- Repository layout: README, CHANGELOG, LICENSE, .gitignore
