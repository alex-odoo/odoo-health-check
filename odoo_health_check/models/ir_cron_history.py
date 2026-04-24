import logging
import socket
from datetime import timedelta

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class IrCronHistory(models.Model):
    _name = "ir.cron.history"
    _description = "Cron Execution History"
    _order = "date_start desc"
    _rec_name = "cron_id"

    cron_id = fields.Many2one(
        "ir.cron",
        string="Scheduled Action",
        required=True,
        ondelete="cascade",
        index=True,
    )
    date_start = fields.Datetime(
        string="Started",
        required=True,
        default=fields.Datetime.now,
        index=True,
    )
    date_end = fields.Datetime(string="Ended")
    duration_sec = fields.Float(
        string="Duration (s)",
        digits=(12, 3),
        default=0.0,
        help="Measured via time.perf_counter() in the _callback override for sub-second precision.",
    )
    state = fields.Selection(
        [
            ("running", "Running"),
            ("success", "Success"),
            ("failed", "Failed"),
        ],
        required=True,
        default="running",
        index=True,
    )
    error_traceback = fields.Text(string="Error Traceback")
    server_name = fields.Char(
        string="Server",
        default=lambda _: socket.gethostname(),
        readonly=True,
    )

    _sql_constraints = [
        (
            "date_order",
            "CHECK (date_end IS NULL OR date_end >= date_start)",
            "End time must be on or after start time.",
        ),
    ]

    @api.model
    def _odoo_health_cleanup(self, batch_size=5000):
        """Delete history rows older than the configured retention window.

        Retention days comes from `odoo_health_check.retention_days`
        (default 30). A non-positive value disables cleanup.
        """
        param = self.env["ir.config_parameter"].sudo().get_param(
            "odoo_health_check.retention_days", default="30",
        )
        try:
            retention = int(param)
        except (TypeError, ValueError):
            _logger.warning(
                "odoo_health_check: invalid retention_days=%r, skipping cleanup", param,
            )
            return 0
        if retention <= 0:
            return 0
        cutoff = fields.Datetime.now() - timedelta(days=retention)
        to_delete = self.search(
            [("date_start", "<", cutoff)], limit=batch_size, order="date_start asc",
        )
        count = len(to_delete)
        if count:
            to_delete.unlink()
            _logger.info(
                "odoo_health_check: retention cleanup removed %d rows older than %s "
                "(retention=%d days)",
                count, cutoff, retention,
            )
        return count
