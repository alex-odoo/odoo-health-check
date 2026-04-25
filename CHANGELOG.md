# Changelog

All notable changes to this module are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Module versioning: `<odoo_major>.0.<major>.<minor>.<patch>`.

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
  test18 — first cron run after install raised on disk total ~50 GB
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
