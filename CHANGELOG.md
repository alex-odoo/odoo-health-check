# Changelog

All notable changes to this module are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Module versioning: `<odoo_major>.0.<major>.<minor>.<patch>`.

## [18.0.1.10.3] - 2026-04-25

### Added
- 9 real screenshots in `static/description/screenshots/` captured from a
  live test18 install:
  - `01_dashboard.png` - Dashboard with 4 populated tiles (cron health,
    OS root, filestore, latest PG report)
  - `02_cron_history.png` - Cron History list with mixed Success / Failed
    badges across multiple scheduled actions
  - `03_disk_checks.png` - Disk Checks list showing OK + Warning +
    Critical status badges across both check types
  - `04_pg_reports.png` - PG Reports list with multiple monthly reports
  - `05_settings.png` - Settings page with all four blocks
  - `06_email_inbox.png` - Inbox view of all four alert types side by side
  - `07_email_disk_alert.png` - full disk alert email body (severity
    badge, metadata table, View in Disk Checks button)
  - `08_email_pg_report.png` - full monthly PG digest email body (top
    tables with Δ size + Δ rows columns, View in PG Reports button)
  - `09_email_cron_failure.png` - full cron failure email body
    (CRITICAL badge, metadata table, View in Cron History button,
    collapsed traceback)
- New "Alerts in your inbox" section in `index.html` showcasing the
  inbox view (full width) and three example email bodies in a 3-column
  grid below it

### Changed
- `index.html` now references the real screenshots in every feature
  block; the apps.odoo.com listing page is fully populated end-to-end

## [18.0.1.10.2] - 2026-04-25

### Added
- `web_icon` on the top-level "Health Check" menu, pointing at
  `static/description/icon.png` so the H+ monogram shows next to the
  menu label in the Odoo navbar (replacing the default generic icon)
- `static/description/index.html` (apps.odoo.com module page) with hero,
  4 numbered features (each with a screenshot slot), configuration
  block, technical details, "what it does NOT do" section, and support
  links. Inline-styled to the Rteam brand palette
- `README.rst` (module-level) mirroring index.html in restructured text
  so the apps.odoo.com listing has both the rich HTML page and an RST
  fallback

## [18.0.1.10.1] - 2026-04-25

### Added
- Store assets for apps.odoo.com listing (Phase 11, partial):
  - `static/description/icon.png` (128x128) - "H+" monogram in the Rteam family LETTER+ pattern: solid white H, teal #00D4AA `+` at the upper-left, navy #0A1628 background, subtle violet→teal aura. Generated via Gemini 3 Pro Image (nano banana pro) at 2048x2048 then downscaled
  - `static/description/banner.png` (1120x560, 2:1) - hero composition: H+ monogram + "Odoo Health Check" + tagline "Catch failures before your users do" on the left, four glassmorphism feature tiles on the right (CRON / DISK / GROWTH / DASHBOARD). Generated at 2752x1536, center-cropped to 2:1 ratio, downscaled
  - Both assets follow Rteam Brand Kit (#0A1628 navy + #00D4AA teal + #7C5CFC violet aura, max 3 colors + white text, no AI cliches, no third-party logos)
- `static/description/screenshots/` directory created for the 3-5 UI captures coming next (dashboard / cron history / disk checks / settings)

### Notes
- Phase 11 still has remaining work: real screenshots from test18, `static/description/index.html`, and `README.rst`
- No functional code change in this release - assets only

## [18.0.1.10.0] - 2026-04-25

### Changed
- Mail templates UX polish:
  - **Severity badge** at the top of each alert email. `mail_template_cron_failure` always shows a red `CRITICAL` badge. `mail_template_disk_alert` shows a dynamic badge: amber `WARN` or red `CRITICAL` based on the row's status. PG monthly report stays badge-less (it's a digest, not an alert)
  - **'View in Odoo' button** in every template, deep-linking via the appropriate act_window. Cron failure → "View in Cron History", disk alert → "View in Disk Checks", PG report → "View in PG Reports". Button color matches the severity badge for consistency
  - **Traceback collapsed in `<details>`** in the cron failure email. Long stacks no longer dominate the inbox preview - the recipient sees the metadata (cron name, server, time, View button) immediately and expands the trace on demand. Email clients that don't support `<details>` (older mobile clients) gracefully render the trace inline
- New helper methods for templates:
  - `ir.cron.history._action_url()` returns the deep link
  - `health.check.result._action_url()` returns the deep link, picking PG Reports vs Disk Checks action based on `check_type`
  - Both fall back to the base URL if the action xml_id is missing (defensive)

### Added
- Tests for `_action_url()` on both models, including check_type-based action routing for `health.check.result`

## [18.0.1.9.0] - 2026-04-25

### Added
- Health Check Dashboard (Phase 9)
  - New `health.check.dashboard` TransientModel - at-a-glance summary of cron health, disk usage, and the latest PostgreSQL growth report
  - 4 tiles in a single form view:
    - **Cron health** - failed crons in last 24h / 7d, total cron runs in 7d
    - **OS root** - status badge (ok / warn / critical / error / unknown), used %, free / total in GB, last sample timestamp
    - **Filestore** - same fields for the Odoo filestore mount
    - **Latest PG report** - timestamp, DB size, Δ vs previous report, largest table
  - No new stored data: `default_get` reads the latest rows from `ir.cron.history` and `health.check.result`. Open the dashboard → fresh snapshot. The Refresh button reopens the action so `default_get` fires again
  - Empty-state messages for each tile when no underlying data exists yet (fresh install, first month before pg_report cron fires)
  - New top-level menu "Health Check -> Dashboard" (sequence 5, above Cron History)
- Tests (`tests/test_dashboard.py`, 11 tests): empty state, latest-row-per-check_type, isolation, error status, human-readable summary, failure window arithmetic across 24h / 7d / outside, pg report latest-ok selection, error-row skip, first-report message, default_get integration, action_refresh shape

## [18.0.1.8.0] - 2026-04-25

### Added
- Monthly PostgreSQL growth report (Phase 8)
  - Cron `Odoo Health Check: Monthly PostgreSQL growth report` runs on the 1st of each month at 08:00 (`interval_type='months'`)
  - SQL: top-10 tables by `pg_total_relation_size`, excluding `pg_catalog` / `information_schema`. Row count uses `pg_class.reltuples` estimate (last ANALYZE) - much faster than COUNT(*) and accurate enough for trend reports
  - Snapshot stored in `health.check.result.details_json`: `{db_name, total_db_bytes, total_db_bytes_delta, tables: [{name, total_bytes, table_bytes, row_estimate, total_bytes_delta, row_estimate_delta}], previous_report_id}`. Each new run looks up the previous `pg_report` row with `status='ok'` and computes deltas vs that snapshot. New tables show `null` deltas (rendered as "new" in the email)
  - New mail template `mail_template_pg_monthly` with HTML table of top-10 tables + size + Δ size + rows + Δ rows + DB size summary. Subject: `[Odoo Health] PG monthly report: <db> (YYYY-MM)`. Uses `_get_parsed_details()`, `_human_bytes()`, `_human_delta_bytes()` template helpers on the record
  - Email is sent every run (it's a digest, not a transition alert) when `odoo_health_check.pg_report_emails` is non-empty. Empty recipients = report row still created, just no email
  - SQL failure → row with `status='error'` and traceback in `details_json`. Cron stays green
- Settings: new "PostgreSQL Monthly Report" block with `odoo_health_pg_report_emails`
- Menu: new "Health Check -> PG Reports" filtered to `check_type='pg_report'` (Disk Checks menu's domain stays `disk_root + disk_filestore`)
- Tests (`tests/test_pg_report.py`, 4 classes, 14 tests): real SQL against test DB validates query syntax + system-schema exclusion + db_size; mocked-SQL tests cover snapshot shape, MoM delta computation, new-table handling, email gating, error path, settings roundtrip, template + cron registration, byte formatters

## [18.0.1.7.0] - 2026-04-25

### Added
- Configurable disk thresholds and disk-alert email (Phase 7)
  - New settings (in Settings -> Health Check -> Disk Monitoring):
    - `odoo_health_disk_warn_pct` (default 80) - usage % above which a sample is flagged 'warn'
    - `odoo_health_disk_critical_pct` (default 90) - usage % above which a sample is flagged 'critical'
    - `odoo_health_disk_alert_emails` - comma-separated recipients for disk alerts
  - `_disk_thresholds()` now reads from `ir.config_parameter`. Falls back to defaults on missing or non-numeric values; clamps to [0, 100]; reverts to defaults if `critical < warn` (logs a warning)
  - New mail template `mail_template_disk_alert` (subject: `[Odoo Health] Disk <status>: <mount> at X.X% used`, body: status, used%, total/free in GB, time)
  - `_send_disk_alert()` enqueues an email only on worsening transitions (ok->warn, ok->critical, warn->critical). 'error' samples are skipped for both sending and previous-state lookup, so transient measurement failures don't generate spurious alerts. Improvements (critical->warn) and steady-state (warn->warn) never trigger an alert. One email per worsening transition - no per-hour spam
  - Disk alert recipients are independent of cron-failure recipients (sysadmin vs engineering routing)
- Tests (`tests/test_disk_alert.py`, 21 tests across 3 classes):
  - Threshold reading: defaults, configured values, invalid fallback, out-of-range clamp, invariant violation, classification with custom thresholds
  - Alert transitions: first-run warn / critical, warn->critical, warn->warn (no), critical->critical (no), critical->warn (no), ok (no), error (no), empty recipients (no), error-row skipped in lookup, isolation per check_type, comma-trim
  - Settings: roundtrip for warn_pct / critical_pct / alert_emails, disk alert template registered

## [18.0.1.6.1] - 2026-04-25

### Fixed
- `health.check.result.total_bytes` and `free_bytes` were `fields.Integer`,
  which maps to PostgreSQL `int4` (~2.1 GB ceiling). Any realistic volume
  triggered `psycopg2.errors.NumericValueOutOfRange` on insert. Switched
  both to `fields.Float(digits=(20, 0))` (numeric(20,0)). Caught live on
  test18 - first cron run after install raised on disk total ~50 GB
- Added regression test `test_sample_disk_handles_large_byte_counts`
  (4 TB volume) to prevent reintroduction

## [18.0.1.6.0] - 2026-04-25

### Added
- Disk usage monitoring (Phase 6)
  - New model `health.check.result` (`check_type`, `date`, `status`, `mount_path`, `total_bytes`, `free_bytes`, `used_pct`, `details_json`). Selection includes `pg_report` to avoid a second selection migration in Phase 8
  - New classmethod `health.check.result._run_disk_checks()` samples both OS root (`/`) and Odoo filestore (`odoo.tools.config['data_dir']`), creating one row per target. Per-target failures are isolated and recorded with `status='error'` so the cron itself never crashes
  - New scheduled action `Odoo Health Check: Disk usage check` runs hourly (first run 5min after install)
  - Default thresholds (used %): `<80` ok, `80-90` warn, `>=90` critical. Phase 7 will make these configurable; the seam lives in `_disk_thresholds()` for a single override point
- Views: list / form / search on `health.check.result` with status-badge decorations and Last 24h / 7d filters; new menu "Health Check -> Disk Checks" (action filtered to disk_root + disk_filestore)
- Tests (`tests/test_disk_check.py`): threshold boundaries, mocked `shutil.disk_usage` happy paths for ok / warn / critical, zero-total guard, OSError isolation per target, cron registered + active

## [18.0.1.5.1] - 2026-04-24

### Added
- Test suite covering Phases 1-5: `tests/test_history_model.py`, `test_cron_override.py`, `test_failure_email.py`, `test_config.py`
  - Model: defaults, SQL constraint, cascade delete, cleanup with retention variants (positive / zero / invalid param)
  - Overrides: `_callback` and `method_direct_trigger` on success and failure; `_callback` tolerates `history_id=None`
  - Email: enqueue on failure with recipients, skip on empty recipients, never on success, comma-separated parsing
  - Config: settings roundtrip for both params; retention cron and mail template registered and active
- Test common helper (`tests/common.py`) patches `registry.cursor` so the module's independent-cursor writes ride the test savepoint
- All tests tagged `post_install`, `-at_install`, `odoo_health_check` - run via `odoo --test-tags odoo_health_check`

### Notes
- Tests do not execute on Odoo.sh production builds. Push to a dev/staging branch to run in CI

## [18.0.1.5.0] - 2026-04-24

### Added
- Daily retention cleanup
  - New `ir.cron.history._odoo_health_cleanup()` classmethod deletes rows older than retention window in batches of 5000
  - New scheduled action `Odoo Health Check: Cron history retention cleanup` runs daily (first run 4h after install)
  - New config parameter `odoo_health_check.retention_days` (default 30). `<= 0` disables cleanup
  - Settings view gains a "Retention" block with the new field

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
