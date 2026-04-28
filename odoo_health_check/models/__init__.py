from . import ir_cron_history
from . import ir_cron
from . import health_check_result
from . import health_check_dashboard
from . import res_config_settings

# TODO: For better readability, it would be better to keep all fields in a consistent order.
#  disk_filestore_at = fields.Datetime(string="Last filestore sample", readonly=True) - first variant
#  date_start = fields.Datetime(
#      string="Started",
#      required=True,
#      default=fields.Datetime.now,
#      index=True,
#  ) - second variant

