{
    "name": "Odoo Health Check",
    "version": "18.0.1.10.4",
    "summary": "Cron execution history, disk monitoring, monthly PostgreSQL growth reports",
    "description": """
Odoo Health Check
=================

Daily health check for your Odoo 18 Enterprise self-hosted installation.

Features
--------
* Cron execution history with duration and error traceback
* Email alert on every failed cron run
* Disk space monitoring on OS root and Odoo filestore mount
* Monthly PostgreSQL growth report (top tables by size, row count)

Targeted at Odoo 18 Enterprise. Community may work but is not tested.
""",
    "author": "Rteam",
    "website": "https://rteam.agency",
    "license": "LGPL-3",
    "category": "Administration",
    "depends": ["base", "mail"],
    "data": [
        "security/ir.model.access.csv",
        "data/mail_template_data.xml",
        "data/ir_cron_data.xml",
        "views/ir_cron_history_views.xml",
        "views/health_check_result_views.xml",
        "views/health_check_dashboard_views.xml",
        "views/res_config_settings_views.xml",
        "views/menu.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
