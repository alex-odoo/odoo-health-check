import socket

from odoo import api, fields, models


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
        compute="_compute_duration",
        store=True,
        digits=(12, 3),
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

    @api.depends("date_start", "date_end")
    def _compute_duration(self):
        for rec in self:
            if rec.date_start and rec.date_end:
                rec.duration_sec = (rec.date_end - rec.date_start).total_seconds()
            else:
                rec.duration_sec = 0.0
