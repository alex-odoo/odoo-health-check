# Quick Verification Guide - Odoo Health Check

After installing this module, run through these short checks to confirm everything works on your Odoo 18 system. Total time: about 10 minutes. You'll need administrator rights.

You should see a new **Health Check** menu at the top of Odoo, with five sub-pages: Dashboard, Cron History, Disk Checks, PG Reports, Settings.

---

## 1. The dashboard works

Go to **Health Check → Dashboard**.

You should see four sections: Cron health, OS root, Filestore, Latest PG report. Right after install some sections will say "No data yet" - that's normal, the background jobs need to run first.

Click the **Refresh** button at the top to reload the snapshot.

---

## 2. Cron history is being recorded

Odoo runs many scheduled actions automatically. This module logs each one.

Go to **Settings → Technical → Scheduled Actions**. Pick any active one (for example "Base: Auto-vacuum internal data") and click **Run Manually**.

Then open **Health Check → Cron History**. You should see a fresh row for that scheduled action with a green **Success** badge. Open the row - it shows the start/end time and how long it took (in seconds, with millisecond precision).

---

## 3. Disk monitoring is active

Go to **Settings → Technical → Scheduled Actions** and find **"Odoo Health Check: Disk usage check"**. Click **Run Manually**.

Open **Health Check → Disk Checks**. You should see two new rows: one for the OS root (`/`) and one for the Odoo filestore. Both show used percentage, free space, total space, and a status badge. On a healthy server both will be green (OK).

---

## 4. The PostgreSQL report works

The full report normally runs on the 1st of each month at 08:00 server time. To see it now, go to **Settings → Technical → Scheduled Actions** and find **"Odoo Health Check: Monthly PostgreSQL growth report"**. Click **Run Manually**.

Open **Health Check → PG Reports**. A new row appears with status OK. Open it - the **Details (JSON)** field contains the snapshot data (database name, total size, top-10 tables).

---

## 5. Email alerts work (optional)

Skip this if you don't want to set up email yet - the module works fine without it.

Go to **Health Check → Settings**.

**Cron failure alerts.** In the "Notifications" block, enter your email in **Cron Failure Emails**, save. Now whenever any scheduled action fails, you get a notification email with the full error trace.

**Disk alerts.** In the "Disk Monitoring" block:
- Set **Disk Alert Emails** to your address
- Adjust **Warning Threshold** (default 80%) and **Critical Threshold** (default 90%) if you want different sensitivity
- Save

You'll get one email when disk usage crosses from OK into warning, and one more when it crosses from warning into critical. You will **not** get a new email every hour while the disk stays in the same state - only on changes for the worse. If you free up space and the status improves, no email either.

**Monthly PG report email.** In the "PostgreSQL Monthly Report" block, enter recipients in **PG Report Emails**, save. The monthly report will be sent on the 1st of each month with a formatted HTML table showing top tables and month-over-month growth.

To test that emails are being generated, after configuring recipients, manually trigger the relevant scheduled action and check **Settings → Technical → Email → Emails** - you should see new outgoing messages.

---

## 6. History retention works

By default, cron execution history is kept for 30 days. To change this:

**Health Check → Settings → "History Retention (days)"** - set to your preferred value (or 0 to disable cleanup entirely). Cleanup runs once a day automatically.

---

## Troubleshooting

**The Health Check menu doesn't appear.**
You're probably not logged in as an administrator. The module restricts all menus to the Administration / Settings group.

**Disk Checks is empty.**
The hourly disk check hasn't fired yet. Either wait up to an hour, or trigger it manually (Settings → Technical → Scheduled Actions → "Odoo Health Check: Disk usage check" → Run Manually).

**No emails are arriving.**
Check three things:
1. Recipients are saved correctly in **Health Check → Settings**.
2. Your Odoo outgoing mail server is configured (Settings → Technical → Outgoing Mail Servers).
3. **Settings → Technical → Email → Emails** shows the messages - if they're stuck in "Outgoing", outgoing mail is the issue, not this module.

**Disk shows "Critical" but I just freed space.**
The status reflects the last sample, not the current state. Trigger the disk check manually (or wait for the next hourly run) and the dashboard will refresh.

**A scheduled action is failing repeatedly.**
That's exactly what this module is built to surface. Open **Health Check → Cron History**, filter by "Failed", click the row, read the traceback in the **Error Traceback** tab. Fix the underlying issue or disable the failing scheduled action.

---

## What this module does **not** do

- It does not page on-call (no Slack, PagerDuty, SMS - only email).
- It does not monitor remote servers - only the one Odoo is running on.
- It does not predict future disk usage - only reports current state and month-over-month deltas.
- Database row counts in the PG report are estimates from PostgreSQL's own statistics (`pg_class.reltuples`), updated by the `ANALYZE` command. They are accurate enough for trend reports but should not be used for billing or audit.

If you need any of these, that's a candidate for the upcoming Pro variant.
