import json
import logging
import shutil

from odoo import api, fields, models
from odoo.tools import config

_logger = logging.getLogger(__name__)

DEFAULT_WARN_PCT = 80.0
DEFAULT_CRITICAL_PCT = 90.0

# severity ordering for transition detection
_SEVERITY = {"ok": 0, "warn": 1, "critical": 2}


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
    # Float(digits=(20,0)) maps to PostgreSQL numeric(20,0) which holds any
    # realistic disk size in bytes. fields.Integer is int4 (~2.1 GB ceiling)
    # and overflows on any non-trivial volume.
    total_bytes = fields.Float(digits=(20, 0))
    free_bytes = fields.Float(digits=(20, 0))
    used_pct = fields.Float(string="Used %", digits=(5, 2))
    details_json = fields.Text(
        string="Details (JSON)",
        help="Raw details, error traceback, or extra metadata as JSON.",
    )

    @api.model
    def _disk_thresholds(self):
        """Return (warn_pct, critical_pct) read from ir.config_parameter.

        Falls back to defaults on missing or non-numeric values. Clamps
        to [0, 100]. If the warn/critical invariant is violated
        (critical < warn), reverts both to defaults and logs.
        """
        Params = self.env["ir.config_parameter"].sudo()
        try:
            warn = float(
                Params.get_param(
                    "odoo_health_check.disk_warn_pct", DEFAULT_WARN_PCT,
                )
            )
        except (TypeError, ValueError):
            warn = DEFAULT_WARN_PCT
        try:
            critical = float(
                Params.get_param(
                    "odoo_health_check.disk_critical_pct", DEFAULT_CRITICAL_PCT,
                )
            )
        except (TypeError, ValueError):
            critical = DEFAULT_CRITICAL_PCT
        warn = max(0.0, min(100.0, warn))
        critical = max(0.0, min(100.0, critical))
        if critical < warn:
            _logger.warning(
                "odoo_health_check: disk thresholds invariant violated "
                "(warn=%s critical=%s), falling back to defaults",
                warn, critical,
            )
            return (DEFAULT_WARN_PCT, DEFAULT_CRITICAL_PCT)
        return (warn, critical)

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
                "total_bytes": float(usage.total),
                "free_bytes": float(usage.free),
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
        record = self.create(vals)
        record._send_disk_alert()
        return record

    def _send_disk_alert(self):
        """Enqueue a disk alert email if status worsened since last sample.

        Sends only on transitions where severity strictly increased
        (ok -> warn, ok -> critical, warn -> critical). 'error' rows
        never trigger an alert and are skipped when looking up the
        previous state, so a transient measurement failure between two
        ok samples doesn't generate spurious alerts.

        Wrapped in try/except: any failure is logged, never propagates.
        Disabled when `odoo_health_check.disk_alert_emails` is empty.
        """
        self.ensure_one()
        if self.status not in ("warn", "critical"):
            return
        try:
            recipients = self._get_disk_alert_recipients()
            if not recipients:
                return
            prev = self.search(
                [
                    ("check_type", "=", self.check_type),
                    ("status", "!=", "error"),
                    ("id", "!=", self.id),
                ],
                order="date desc, id desc",
                limit=1,
            )
            prev_status = prev.status if prev else "ok"
            if _SEVERITY[self.status] <= _SEVERITY[prev_status]:
                return
            template = self.env.ref(
                "odoo_health_check.mail_template_disk_alert",
                raise_if_not_found=False,
            )
            if not template:
                _logger.warning(
                    "odoo_health_check: disk alert template missing, skipping alert"
                )
                return
            template.send_mail(
                self.id,
                force_send=False,
                email_values={"email_to": ",".join(recipients)},
            )
        except Exception:
            _logger.exception(
                "odoo_health_check: failed to enqueue disk alert for result_id=%s",
                self.id,
            )

    @api.model
    def _get_disk_alert_recipients(self):
        raw = self.env["ir.config_parameter"].sudo().get_param(
            "odoo_health_check.disk_alert_emails", default="",
        ) or ""
        return [e.strip() for e in raw.split(",") if e.strip()]
