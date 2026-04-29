from . import ir_cron_history
from . import ir_cron
from . import health_check_result
from . import health_check_dashboard
from . import res_config_settings

# TODO: in all files please make field to the same logic
#  date_start = fields.Datetime(
#      string="Started",
#      required=True,
#      default=fields.Datetime.now,
#      index=True,
#  )
# TODO:We are publishing the module to the Odoo Store.
#  It hasn’t been used anywhere before, so why do we need a history of old migrations?
# TODO: again why we need extra param in _callback of ir.crom model if we make for current version of odoo on for 18
