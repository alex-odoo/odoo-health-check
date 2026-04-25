import json
import logging
import shutil

from odoo import api, fields, models
from odoo.tools import config

_logger = logging.getLogger(__name__)

# Phase 7 will replace these defaults with values read from
# ir.config_parameter via res.config.settings.
DEFAULT_WARN_PCT = 80.0
DEFAULT_CRITICAL_PCT = 90.0


class HealthCheckResult(models.Model):
    _name = "health.check.result"
    _description = "Health Check Result"
    _order = "date desc, id desc"
    _rec_name = "check_type"

    check_type = fields.Selection(
        [
            ("disk_root", "Disk: OS Root"),
            ("disk_filestore", "Disk: Odoo Filestore"),
            ("pg_report", "PostgreSQL Monthly Report"),
        ],
        required=True,
        index=True,
    )
    date = fields.Datetime(
        required=True,
        default=fields.Datetime.now,
        index=True,
    )
    status = fields.Selection(
        [
            ("ok", "OK"),
            ("warn", "Warning"),
            ("critical", "Critical"),
            ("error", "Error"),
        ],
        required=True,
        default="ok",
        index=True,
    )
    mount_path = fields.Char(string="Mount / Path")
    total_bytes = fields.Integer()
    free_bytes = fields.Integer()
    used_pct = fields.Float(string="Used %", digits=(5, 2))
    details_json = fields.Text(
        string="Details (JSON)",
        help="Raw details, error traceback, or extra metadata as JSON.",
    )

    @api.model
    def _disk_thresholds(self):
        """Return (warn_pct, critical_pct). Phase 7 will override to read
        configurable thresholds from ir.config_parameter."""
        return (DEFAULT_WARN_PCT, DEFAULT_CRITICAL_PCT)

    @api.model
    def _classify_disk(self, used_pct):
        warn, critical = self._disk_thresholds()
        if used_pct >= critical:
            return "critical"
        if used_pct >= warn:
            return "warn"
        return "ok"

    @api.model
    def _disk_targets(self):
        """Return [(check_type, path), ...] for the disk checks.

        Filestore path is taken from `odoo.tools.config['data_dir']`,
        which on Odoo.sh and standard installs points at the per-DB
        filestore parent directory. shutil.disk_usage resolves to the
        underlying mount, so multi-mount setups work without extra logic.
        """
        data_dir = config.get("data_dir") or "/"
        return [
            ("disk_root", "/"),
            ("disk_filestore", data_dir),
        ]

    @api.model
    def _run_disk_checks(self):
        """Sample disk usage on OS root and Odoo filestore mount.

        Creates one health.check.result row per check_type. Returns the
        recordset of created rows. Never raises - any failure is captured
        as a row with status='error' so the cron itself stays green.
        """
        records = self.browse()
        for check_type, path in self._disk_targets():
            records |= self._sample_disk(check_type, path)
        return records

    @api.model
    def _sample_disk(self, check_type, path):
        try:
            usage = shutil.disk_usage(path)
            used_pct = (usage.used / usage.total * 100.0) if usage.total else 0.0
            vals = {
                "check_type": check_type,
                "status": self._classify_disk(used_pct),
                "mount_path": path,
                "total_bytes": int(usage.total),
                "free_bytes": int(usage.free),
                "used_pct": round(used_pct, 2),
            }
        except Exception as exc:  # noqa: BLE001 - infra check, must not fail the cron
            _logger.exception(
                "odoo_health_check: disk check failed for %s (%s)",
                check_type,
                path,
            )
            vals = {
                "check_type": check_type,
                "status": "error",
                "mount_path": path,
                "details_json": json.dumps(
                    {"error": str(exc), "type": type(exc).__name__}
                ),
            }
        return self.create(vals)
