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
