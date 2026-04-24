import logging
import traceback

from odoo import SUPERUSER_ID, api, fields, models

_logger = logging.getLogger(__name__)


class IrCron(models.Model):
    _inherit = "ir.cron"

    def _callback(self, cron_name, server_action_id, job_id):
        history_id = self._odoo_health_log_start(job_id)
        try:
            result = super()._callback(cron_name, server_action_id, job_id)
        except Exception:
            self._odoo_health_log_end(history_id, "failed", traceback.format_exc())
            raise
        self._odoo_health_log_end(history_id, "success", None)
        return result

    def _odoo_health_log_start(self, cron_id):
        """Create a 'running' history record in an independent cursor.

        Independent cursor so the record survives a rollback of the cron's
        own transaction. Sudoed because crons may run under arbitrary users
        and this is infrastructure logging, not user-driven data.
        """
        try:
            with self.pool.cursor() as new_cr:
                env = api.Environment(new_cr, SUPERUSER_ID, {})
                return env["ir.cron.history"].create({
                    "cron_id": cron_id,
                    "state": "running",
                }).id
        except Exception:
            _logger.exception(
                "odoo_health_check: failed to create cron history record for cron_id=%s",
                cron_id,
            )
            return None

    def _odoo_health_log_end(self, history_id, state, error_traceback):
        if not history_id:
            return
        try:
            with self.pool.cursor() as new_cr:
                env = api.Environment(new_cr, SUPERUSER_ID, {})
                env["ir.cron.history"].browse(history_id).write({
                    "state": state,
                    "date_end": fields.Datetime.now(),
                    "error_traceback": error_traceback,
                })
        except Exception:
            _logger.exception(
                "odoo_health_check: failed to finalize cron history id=%s state=%s",
                history_id,
                state,
            )
