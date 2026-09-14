import os
import smtplib
import ssl
import time
from datetime import datetime, timezone, timedelta
from email.message import EmailMessage
from html import escape
from pathlib import Path


DB_DIR = Path(os.getenv("GEOIP_DB_DIR", "/usr/share/GeoIP"))
DB_FILES = os.getenv(
    "GEOIP_ALERT_FILES",
    "GeoLite2-Country.mmdb,GeoLite2-City.mmdb,GeoLite2-ASN.mmdb",
).split(",")
MAX_AGE_HOURS = float(os.getenv("GEOIP_ALERT_MAX_AGE_HOURS", "72"))
CHECK_INTERVAL_SECONDS = int(os.getenv("GEOIP_ALERT_CHECK_INTERVAL_SECONDS", "3600"))
RESEND_INTERVAL_SECONDS = int(os.getenv("GEOIP_ALERT_RESEND_INTERVAL_SECONDS", "21600"))
HEALTHY_EMAIL_INTERVAL_SECONDS = int(
    os.getenv("GEOIP_HEALTHY_EMAIL_INTERVAL_SECONDS", "86400")
)

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USERNAME)
SMTP_TO = os.getenv("SMTP_TO", "")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() in {"1", "true", "yes"}

IST = timezone(timedelta(hours=5, minutes=30))


def format_datetime(timestamp):
    dt = datetime.fromtimestamp(timestamp, timezone.utc)
    gmt = dt.strftime("%B %d, %Y %I:%M %p")
    # ist = dt.astimezone(IST).strftime("%I:%M %p")
    return f"{gmt} GMT"


def render_html_body(status, lines):
    is_healthy = status == "healthy"
    theme_color = "#137333" if is_healthy else "#b42318"
    badge_bg = "#e6f4ea" if is_healthy else "#fce8e6"
    badge_color = "#137333" if is_healthy else "#b42318"
    title = "GeoIP databases are healthy" if is_healthy else "GeoIP database update alert"
    summary = (
        "All expected GeoIP database files are present and fresh."
        if is_healthy
        else "GeoIP database update appears stale or incomplete."
    )
    section_title = "Checked databases" if is_healthy else "Affected databases"
    items = "\n".join(f"<li>{escape(line)}</li>" for line in lines)
    checked_at = format_datetime(time.time())

    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{escape(title)}</title>
    <style>
      @keyframes pulse {{
        0% {{ transform: scale(1); opacity: 1; }}
        50% {{ transform: scale(1.08); opacity: 0.82; }}
        100% {{ transform: scale(1); opacity: 1; }}
      }}
    </style>
  </head>
  <body style="margin:0; padding:0; background:#f4f6f8; font-family:Arial, Helvetica, sans-serif; color:#17202a;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f4f6f8; padding:24px 0;">
      <tr>
        <td align="center">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:640px; background:#ffffff; border:1px solid #d9e1e8;">
            <tr>
              <td style="padding:24px 28px; background:{theme_color}; color:#ffffff;">
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                  <tr>
                    <td>
                      <h1 style="margin:0; font-size:22px; line-height:1.3;">{escape(title)}</h1>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
            <tr>
              <td style="padding:24px 28px;">
                <p style="margin:0 0 18px; font-size:15px; line-height:1.6;">
                  {escape(summary)}
                </p>

                <p style="display:inline-block; margin:0 0 18px; padding:8px 12px; border-radius:999px; background:{badge_bg}; color:{badge_color}; font-size:13px; font-weight:bold;">
                  Status: {escape(status.upper())}
                </p>

                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin:0 0 22px; border-collapse:collapse;">
                  <tr>
                    <td style="padding:10px 12px; border:1px solid #d9e1e8; font-size:14px; font-weight:bold;">Checked at</td>
                    <td style="padding:10px 12px; border:1px solid #d9e1e8; font-size:14px;">{escape(checked_at)}</td>
                  </tr>
                  <tr>
                    <td style="padding:10px 12px; border:1px solid #d9e1e8; font-size:14px; font-weight:bold;">Freshness threshold</td>
                    <td style="padding:10px 12px; border:1px solid #d9e1e8; font-size:14px;">{escape(str(MAX_AGE_HOURS))} hours</td>
                  </tr>
                </table>

                <h2 style="margin:0 0 10px; font-size:16px; line-height:1.4;">{escape(section_title)}</h2>
                <ul style="margin:0 0 22px; padding-left:22px; font-size:14px; line-height:1.6;">
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
                f"{name}: {age_hours:.1f} hours old, last modified {modified}"
            )

    return stale


def healthy_databases():
    healthy = []

    for name in [item.strip() for item in DB_FILES if item.strip()]:
        db_path = DB_DIR / name
        if not db_path.exists():
            continue

        age_hours = (time.time() - db_path.stat().st_mtime) / 3600
        modified = format_datetime(db_path.stat().st_mtime)
        healthy.append(
            f"{name}: {age_hours:.1f} hours old, last modified {modified}"
        )

    return healthy


def send_email(status, lines):
    if not all([SMTP_HOST, SMTP_FROM, SMTP_TO]):
        print("Email skipped: SMTP_HOST, SMTP_FROM, and SMTP_TO are required", flush=True)
        return

    msg = EmailMessage()
    msg["Subject"] = (
        "GeoIP databases are healthy"
        if status == "healthy"
        else "GeoIP database update alert"
    )
    msg["From"] = SMTP_FROM
    msg["To"] = SMTP_TO
    msg.set_content(render_html_body(status, lines), subtype="html")

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as smtp:
        if SMTP_USE_TLS:
            smtp.starttls(context=ssl.create_default_context())
        if SMTP_USERNAME or SMTP_PASSWORD:
            smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
        smtp.send_message(msg)


def main():
    last_alert_sent_at = 0.0
    last_healthy_sent_at = 0.0

    while True:
        stale = stale_databases()
        now = time.time()
        if stale:
            should_send = time.time() - last_alert_sent_at >= RESEND_INTERVAL_SECONDS
            print(
            f"[{format_datetime(now)}] GeoIP alert condition found: "
            + "; ".join(stale),
            flush=True,
        )
            if should_send:
                send_email("alert", stale)
                last_alert_sent_at = time.time()
        else:
            print(f"[{format_datetime(time.time())}] GeoIP databases are fresh", flush=True)
            last_alert_sent_at = 0.0

            should_send = (
                time.time() - last_healthy_sent_at >= HEALTHY_EMAIL_INTERVAL_SECONDS
            )
            if should_send:
                send_email("healthy", healthy_databases())
                last_healthy_sent_at = time.time()

        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
