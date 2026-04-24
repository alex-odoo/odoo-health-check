from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    odoo_health_notify_emails = fields.Char(
        string="Cron Failure Notification Emails",
        config_parameter="odoo_health_check.notify_emails",
        help="Comma-separated list of recipients that receive an email "
             "every time a scheduled action fails. Leave empty to disable.",
    )
