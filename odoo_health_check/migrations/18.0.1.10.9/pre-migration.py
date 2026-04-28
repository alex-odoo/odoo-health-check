"""Migration kept for upgrades from 18.0.1.10.8 (or earlier) to >=1.10.9.

The 1.10.9 release changed the dashboard action's xmlid model from
`ir.actions.act_window` to `ir.actions.server`. Odoo refuses to update
a record under an existing xmlid when the model attribute changes,
raising:

    ParseError: For external id <xmlid> when trying to create/update
    a record of model X found record of different model Y

This pre-migration deletes the old act_window row (and its ir_model_data
entry) so the new server-action record loads cleanly under the same
xmlid. The fetchone guard makes it safe to re-run on already-migrated
DBs.

DO NOT delete this file just because the version is "old". apps.odoo.com
ships every release as an in-place upgrade for installed users; users
upgrading from the 1.10.8-era LGPL-3 release would fail without this
script, even years from now.
"""

def migrate(cr, version):
    cr.execute("""
        SELECT res_id FROM ir_model_data
        WHERE module = 'odoo_health_check'
          AND name = 'health_check_dashboard_action'
          AND model = 'ir.actions.act_window'
    """)
    row = cr.fetchone()
    if not row:
        return
    cr.execute("DELETE FROM ir_act_window WHERE id = %s", (row[0],))
    cr.execute("""
        DELETE FROM ir_model_data
        WHERE module = 'odoo_health_check'
          AND name = 'health_check_dashboard_action'
    """)
