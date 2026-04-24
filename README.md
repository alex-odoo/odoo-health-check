# Odoo Health Check

Daily health check module for Odoo 18 Enterprise. Track cron execution, catch failures, monitor disk, receive monthly PostgreSQL growth reports.

- **Target**: Odoo 18 Enterprise (self-hosted)
- **License**: LGPL-3 (free on apps.odoo.com)
- **Module technical name**: `odoo_health_check`
- **Author**: [Rteam](https://rteam.agency)

## Features (v1.0 roadmap)

1. Cron execution history with duration + error traceback, configurable retention
2. Email alerts on cron failure via customizable mail templates
3. Disk space monitoring on OS root and Odoo filestore mount
4. Monthly PostgreSQL growth report (top tables by size and row count)

## Install

Clone the repo into your Odoo addons path, restart the server, update the app list, install "Odoo Health Check" from the Apps menu.

## Development

See `CHANGELOG.md` for version history. Contributions via pull requests on [GitHub](https://github.com/alex-odoo/odoo-health-check).

## License

LGPL-3. See [LICENSE](LICENSE).
