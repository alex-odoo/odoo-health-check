from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    odoo_health_notify_emails = fields.Char(
        string="Cron Failure Notification Emails",
        config_parameter="odoo_health_check.notify_emails",
        help="Comma-separated list of recipients that receive an email "
             "every time a scheduled action fails. Leave empty to disable.",
    )
    odoo_health_retention_days = fields.Integer(
        string="History Retention (days)",
        config_parameter="odoo_health_check.retention_days",
        default=30,
        help="Cron execution history rows older than this are deleted daily. "
             "Set to 0 or negative to disable cleanup.",
    )
