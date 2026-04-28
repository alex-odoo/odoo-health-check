"""Migration for the TransientModel -> Model conversion of
health.check.dashboard (1.10.x -> 1.11.0). The DB table is reused
as-is; any leftover transient rows from prior versions get dropped
so the singleton record from data XML loads cleanly."""

def migrate(cr, version):
    cr.execute(
        "SELECT to_regclass('public.health_check_dashboard')"
    )
    if cr.fetchone()[0] is None:
        return
    cr.execute("DELETE FROM health_check_dashboard")
