import logging
import time
import traceback

from odoo import SUPERUSER_ID, api, fields, models

_logger = logging.getLogger(__name__)


class IrCron(models.Model):
    _inherit = "ir.cron"

    # TODO: no need for extra param
    def _callback(self, cron_name, server_action_id, *extra):
        # TODO: delete this comment
        # Odoo 18 dropped the third positional `job_id` arg mid-version
        # (new signature: `_callback(self, cron_name, server_action_id)`,
        # self is a singleton via ensure_one). The *extra accepts and
        # forwards any legacy third arg so installs still on an older 18.0
        # build don't break.
        # TODO: cron_id = self.id
        cron_id = self.id if len(self) == 1 else (extra[0] if extra else None)
        history_id = self._odoo_health_log_start(cron_id)
        # TODO: no need for counter just ir.cron.history.date_end - ir.cron.history.date_start
        t0 = time.perf_counter()
        try:
            # TODO: result = super()._callback(cron_name, server_action_id)
            result = super()._callback(cron_name, server_action_id, *extra)
        except Exception:
            self._odoo_health_log_end(
                history_id, "failed", time.perf_counter() - t0, traceback.format_exc(),
            )
            raise
        self._odoo_health_log_end(history_id, "success", time.perf_counter() - t0, None)
        return result

    def method_direct_trigger(self):
        for cron in self:
            history_id = cron._odoo_health_log_start(cron.id)
            # TODO: no need for counter just ir.cron.history.date_end - ir.cron.history.date_start
            t0 = time.perf_counter()
            try:
                super(IrCron, cron).method_direct_trigger()
            except Exception:
                cron._odoo_health_log_end(
                    history_id, "failed", time.perf_counter() - t0, traceback.format_exc(),
                )
                raise
            cron._odoo_health_log_end(history_id, "success", time.perf_counter() - t0, None)
        return True

    def _odoo_health_log_start(self, cron_id):
        """Create a 'running' history record in an independent cursor.

        Independent cursor so the record survives a rollback of the cron's
        own transaction. Sudoed because crons may run under arbitrary users
        and this is infrastructure logging, not user-driven data.
        """
        # TODO: No need to make try/except for creating records
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

    def _odoo_health_log_end(self, history_id, state, duration_sec, error_traceback):
        if not history_id:
            return
        # TODO: No need to make try/except for browsing records.
        try:
            with self.pool.cursor() as new_cr:
                env = api.Environment(new_cr, SUPERUSER_ID, {})
                history = env["ir.cron.history"].browse(history_id)
                history.write({
                    "state": state,
                    "date_end": fields.Datetime.now(),
                    "duration_sec": duration_sec,
                    "error_traceback": error_traceback,
                })
                if state == "failed":
                    self._odoo_health_send_failure_email(env, history)
        except Exception:
            _logger.exception(
                "odoo_health_check: failed to finalize cron history id=%s state=%s",
                history_id,
                state,
            )

    @staticmethod
    def _odoo_health_send_failure_email(env, history):
        # TODO: No need to make try/except for this code.
        try:
            emails_param = (env["ir.config_parameter"].sudo()
                            .get_param("odoo_health_check.notify_emails") or "").strip()
            if not emails_param:
                return
            recipients = [e.strip() for e in emails_param.split(",") if e.strip()]
            if not recipients:
                return
            template = env.ref(
                "odoo_health_check.mail_template_cron_failure",
                raise_if_not_found=False,
            )
            if not template:
                _logger.warning(
                    "odoo_health_check: mail template not found, failure alert skipped"
                )
                return
            template.send_mail(
                history.id,
                force_send=False,
                email_values={"email_to": ",".join(recipients)},
            )
        except Exception:
            _logger.exception(
                "odoo_health_check: failed to enqueue cron failure email for history_id=%s",
                history.id,
            )
