# Changelog

All notable changes to this module are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Module versioning: `<odoo_major>.0.<major>.<minor>.<patch>`.

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
