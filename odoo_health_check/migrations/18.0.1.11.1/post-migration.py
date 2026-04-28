"""Update cron code on existing installs after the 1.11.0 method rename.

ir_cron_data.xml has noupdate="1" so users keep their per-instance
toggles (active flag, nextcall override, etc). The trade-off: the
`code` field of the linked ir.actions.server is also pinned, which
means when we renamed the cron methods from _run_disk_checks /
_run_pg_report / _odoo_health_cleanup to _cron_check_disk /
_cron_pg_report / _cron_cleanup_history in 1.11.0, existing installs
kept calling the old names and crashed at every cron tick:

    AttributeError: 'health.check.result' object has no attribute
    '_run_disk_checks'

Fresh installs are fine because they get the new cron records with
the new code from the XML. This migration brings existing installs
in line by rewriting the server-action code on each of the three
crons via xmlid lookup. Idempotent: re-running on an already-fixed
DB is a no-op.
"""

CRONS = {
    "ir_cron_history_retention_cleanup": "model._cron_cleanup_history()",
    "ir_cron_health_disk_check":         "model._cron_check_disk()",
    "ir_cron_health_pg_report":          "model._cron_pg_report()",
}


def migrate(cr, version):
    for xmlid, new_code in CRONS.items():
        cr.execute(
            """
            SELECT cron.ir_actions_server_id
            FROM ir_cron AS cron
            JOIN ir_model_data AS imd
              ON imd.model = 'ir.cron' AND imd.res_id = cron.id
            WHERE imd.module = 'odoo_health_check' AND imd.name = %s
            """,
            (xmlid,),
        )
        row = cr.fetchone()
        if not row:
            continue
        cr.execute(
            "UPDATE ir_act_server SET code = %s WHERE id = %s",
            (new_code, row[0]),
        )
