import socket

from odoo import fields, models


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
