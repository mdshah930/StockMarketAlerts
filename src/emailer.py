import os
import smtplib
from datetime import date
from email.message import EmailMessage
from html import escape
from typing import Optional

import pandas as pd


DISPLAY_COLUMNS = {
    "symbol": "Symbol",
    "recent_friday_close": "Recent Friday Close",
    "previous_friday_close": "Previous Friday Close",
    "last_month_rsi": "Last Month RSI",
}


def _prepare_display_dataframe(shortlist: pd.DataFrame) -> pd.DataFrame:
    """Rename columns and format numeric values for email display."""
    display_df = shortlist.copy()

    display_df = display_df.rename(columns=DISPLAY_COLUMNS)

    for column in [
        "Recent Friday Close",
        "Previous Friday Close",
        "Last Month RSI",
    ]:
        if column in display_df.columns:
            display_df[column] = display_df[column].map(
                lambda value: f"{float(value):.2f}"
            )

    return display_df


def _build_html_table(shortlist: pd.DataFrame) -> str:
    """Build a readable HTML table."""
    if shortlist.empty:
        return (
            "<p>No NIFTY 50 stocks satisfied both screening conditions.</p>"
        )

    display_df = _prepare_display_dataframe(shortlist)

    return display_df.to_html(
        index=False,
        border=0,
        classes="stock-table",
        justify="center",
    )


def _build_plain_text(shortlist: pd.DataFrame) -> str:
    """Build a plain-text fallback version of the email."""
    if shortlist.empty:
        return "No NIFTY 50 stocks satisfied both screening conditions."

    display_df = _prepare_display_dataframe(shortlist)
    return display_df.to_string(index=False)


def send_screening_email(
    shortlist: pd.DataFrame,
    run_date: date,
    recipient: Optional[str] = None,
) -> None:
    """Send the screening results by email."""
    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "465"))
    smtp_username = os.environ.get("SMTP_USERNAME")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    recipient = recipient or os.environ.get("ALERT_RECIPIENT")

    missing = []

    if not smtp_username:
        missing.append("SMTP_USERNAME")

    if not smtp_password:
        missing.append("SMTP_PASSWORD")

    if not recipient:
        missing.append("ALERT_RECIPIENT")

    if missing:
        raise RuntimeError(
            "Missing email configuration: " + ", ".join(missing)
        )

    html_table = _build_html_table(shortlist)
    plain_text = _build_plain_text(shortlist)

    count = len(shortlist)
    subject = (
        f"StockMarketAlerts | NIFTY 50 shortlist | "
        f"{run_date.isoformat()} | {count} stock(s)"
    )

    html_body = f"""
    <html>
      <body>
        <h2>NIFTY 50 Stock Screening Results</h2>
        <p><strong>Run date:</strong> {escape(run_date.isoformat())}</p>
        <p>
          Conditions:
          recent Friday close greater than previous Friday close, and
          last completed month RSI between 40 and 45.
        </p>
        {html_table}
      </body>
    </html>
    """

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = smtp_username
    message["To"] = recipient
    message.set_content(plain_text)
    message.add_alternative(html_body, subtype="html")

    with smtplib.SMTP_SSL(smtp_host, smtp_port) as smtp:
        smtp.login(smtp_username, smtp_password)
        smtp.send_message(message)
