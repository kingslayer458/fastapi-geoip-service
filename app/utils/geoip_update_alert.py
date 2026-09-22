import os
import smtplib
import ssl
import time
from datetime import datetime, timezone
from email.message import EmailMessage
from html import escape
from pathlib import Path


DB_DIR = Path(os.getenv("GEOIP_DB_DIR", "/usr/share/GeoIP"))
DB_FILES = os.getenv("GEOIP_ALERT_FILES","GeoLite2-Country.mmdb,GeoLite2-City.mmdb,GeoLite2-ASN.mmdb").split(",")

MAX_AGE_HOURS = float(os.getenv("GEOIP_ALERT_MAX_AGE_HOURS", "72"))
CHECK_INTERVAL_SECONDS = int(os.getenv("GEOIP_ALERT_CHECK_INTERVAL_SECONDS", "3600"))
RESEND_INTERVAL_SECONDS = int(os.getenv("GEOIP_ALERT_RESEND_INTERVAL_SECONDS", "21600"))

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USERNAME)
SMTP_TO = os.getenv("SMTP_TO", "")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() in {
    "1",
    "true",
    "yes",
}


def format_datetime(timestamp):
    dt = datetime.fromtimestamp(timestamp, timezone.utc)
    gmt = dt.strftime("%B %d, %Y %I:%M %p")
    return f"{gmt} GMT"


def render_html_body(lines):
    title = "GeoIP database update alert"
    summary = "GeoIP database update appears stale or incomplete."
    items = "\n".join(f"<li>{escape(line)}</li>" for line in lines)
    checked_at = format_datetime(time.time())

    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{escape(title)}</title>
  </head>

  <body style="margin:0; padding:0; background:#f4f6f8; font-family:Arial, Helvetica, sans-serif; color:#17202a;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0"
           style="background:#f4f6f8; padding:24px 0;">
      <tr>
        <td align="center">

          <table role="presentation" width="100%" cellspacing="0" cellpadding="0"
                 style="max-width:640px; background:#ffffff; border:1px solid #d9e1e8;">

            <tr>
              <td style="padding:24px 28px; background:#b42318; color:#ffffff;">
                <h1 style="margin:0; font-size:22px; line-height:1.3;">
                  {escape(title)}
                </h1>
              </td>
            </tr>

            <tr>
              <td style="padding:24px 28px;">

                <p style="margin:0 0 18px; font-size:15px; line-height:1.6;">
                  {escape(summary)}
                </p>

                <p style="display:inline-block; margin:0 0 18px; padding:8px 12px;
                          border-radius:999px; background:#fce8e6; color:#b42318;
                          font-size:13px; font-weight:bold;">
                  Status: ALERT
                </p>

                <table role="presentation" width="100%" cellspacing="0" cellpadding="0"
                       style="margin:0 0 22px; border-collapse:collapse;">
                  <tr>
                    <td style="padding:10px 12px; border:1px solid #d9e1e8;
                               font-size:14px; font-weight:bold;">
                      Checked at
                    </td>
                    <td style="padding:10px 12px; border:1px solid #d9e1e8;
                               font-size:14px;">
                      {escape(checked_at)}
                    </td>
                  </tr>

                  <tr>
                    <td style="padding:10px 12px; border:1px solid #d9e1e8;
                               font-size:14px; font-weight:bold;">
                      Freshness threshold
                    </td>
                    <td style="padding:10px 12px; border:1px solid #d9e1e8;
                               font-size:14px;">
                      {escape(str(MAX_AGE_HOURS))} hours
                    </td>
                  </tr>
                </table>

                <h2 style="margin:0 0 10px; font-size:16px;">
                  Affected databases
                </h2>

                <ul style="margin:0 0 22px; padding-left:22px;
                           font-size:14px; line-height:1.6;">
                  {items}
                </ul>

              </td>
            </tr>

          </table>

        </td>
      </tr>
    </table>
  </body>
</html>"""


def stale_databases():
    now = time.time()
    stale = []

    for name in [item.strip() for item in DB_FILES if item.strip()]:
        db_path = DB_DIR / name

        if not db_path.exists():
            stale.append(f"{name}: missing")
            continue

        age_hours = (now - db_path.stat().st_mtime) / 3600

        if age_hours > MAX_AGE_HOURS:
            modified = format_datetime(db_path.stat().st_mtime)

            stale.append(
                f"{name}: {age_hours:.1f} hours old, "
                f"last modified {modified}"
            )

    return stale


def send_email(lines):
    if not all([SMTP_HOST, SMTP_FROM, SMTP_TO]):
        print("Email skipped: SMTP_HOST, SMTP_FROM, and SMTP_TO are required",flush=True,)
        return

    msg = EmailMessage()
    msg["Subject"] = "GeoIP database update alert"
    msg["From"] = SMTP_FROM
    msg["To"] = SMTP_TO

    msg.set_content(render_html_body(lines), subtype="html")

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as smtp:
        if SMTP_USE_TLS:
            smtp.starttls(context=ssl.create_default_context())

        if SMTP_USERNAME or SMTP_PASSWORD:
            smtp.login(SMTP_USERNAME, SMTP_PASSWORD)

        smtp.send_message(msg)


def main():
    last_alert_sent_at = 0.0

    while True:
        stale = stale_databases()
        now = time.time()

        if stale:
            print(f"[{format_datetime(now)}] GeoIP alert condition found: " + "; ".join(stale),flush=True)

            should_send = (now - last_alert_sent_at >= RESEND_INTERVAL_SECONDS)

            if should_send:
                send_email(stale)
                last_alert_sent_at = time.time()

        else:
            print(
                f"[{format_datetime(now)}] GeoIP databases are fresh",
                flush=True,
            )

            # Reset so a future stale condition sends an alert immediately.
            last_alert_sent_at = 0.0

        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()