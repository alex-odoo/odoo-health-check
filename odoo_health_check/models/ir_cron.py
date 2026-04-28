import logging
import traceback

from odoo import SUPERUSER_ID, api, fields, models

_logger = logging.getLogger(__name__)


class IrCron(models.Model):
    _inherit = "ir.cron"

    def _callback(self, cron_name, server_action_id, *extra):
        # *extra absorbs and forwards a third positional arg the Odoo 18
        # stable branch passed mid-version (between 1.10.7 and 1.10.9).
        # Removing it would break installs still running an older 18.0
        # build that calls the old signature. Keep until 19.0 port.
        cron_id = self.id if len(self) == 1 else (extra[0] if extra else None)
        history_id = self._odoo_health_log_start(cron_id)
        try:
            result = super()._callback(cron_name, server_action_id, *extra)
        except Exception:
            self._odoo_health_log_end(history_id, "failed", traceback.format_exc())
            raise
        self._odoo_health_log_end(history_id, "success", None)
        return result

    def method_direct_trigger(self):
        for cron in self:
            history_id = cron._odoo_health_log_start(cron.id)
            try:
                super(IrCron, cron).method_direct_trigger()
            except Exception:
                cron._odoo_health_log_end(history_id, "failed", traceback.format_exc())
                raise
            cron._odoo_health_log_end(history_id, "success", None)
        return True

    def _odoo_health_log_start(self, cron_id):
        """Create a 'running' history record in an independent cursor.

        Independent cursor so the record survives a rollback of the cron's
        own transaction. Try/except is intentional: this is infrastructure
        logging and must never crash the monitored cron, so a deadlock or
        connection drop on the history write is logged and absorbed.
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
        # Same separate-cursor + try/except rationale as _odoo_health_log_start.
        try:
            with self.pool.cursor() as new_cr:
                env = api.Environment(new_cr, SUPERUSER_ID, {})
                history = env["ir.cron.history"].browse(history_id)
                history.write({
                    "state": state,
                    "date_end": fields.Datetime.now(),
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
        # Narrow try/except: only the actual SMTP/queue write needs guarding.
        # A transient mail server hiccup must not roll back the cron history
        # row that's already been written above.
        try:
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
