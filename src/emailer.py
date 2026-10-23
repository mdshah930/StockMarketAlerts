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


def _format_value(value) -> str:
    """Format prices and RSI values to exactly three decimals."""
    return f"{float(value):.3f}"


def _prepare_display_dataframe(shortlist: pd.DataFrame) -> pd.DataFrame:
    """Prepare shortlisted stocks for display."""
    display_df = shortlist.copy()

    display_df = display_df.rename(columns=DISPLAY_COLUMNS)

    numeric_columns = [
        "Recent Friday Close",
        "Previous Friday Close",
        "Last Month RSI",
    ]

    for column in numeric_columns:
        if column in display_df.columns:
            display_df[column] = display_df[column].map(_format_value)

    return display_df


def _build_stock_table(shortlist: pd.DataFrame) -> str:
    """Build an email-safe HTML table."""
    if shortlist.empty:
        return """
        <table
            role="presentation"
            width="100%"
            cellpadding="0"
            cellspacing="0"
            border="0"
            style="border-collapse: collapse;"
        >
            <tr>
                <td
                    style="
                        padding: 28px 20px;
                        text-align: center;
                        color: #667085;
                        font-size: 14px;
                        background-color: #ffffff;
                        border: 1px solid #e5e7eb;
                    "
                >
                    No NIFTY 50 stocks satisfied both screening conditions.
                </td>
            </tr>
        </table>
        """

    display_df = _prepare_display_dataframe(shortlist)

    headers = list(display_df.columns)

    header_cells = "".join(
        f"""
        <th
            style="
                padding: 13px 12px;
                text-align: {'left' if header == 'Symbol' else 'right'};
                color: #ffffff;
                background-color: #172033;
                border-bottom: 3px solid #f2b84b;
                font-size: 12px;
                font-weight: 700;
                letter-spacing: 0.2px;
                white-space: nowrap;
            "
        >
            {escape(header)}
        </th>
        """
        for header in headers
    )

    body_rows = []

    for row_number, (_, row) in enumerate(display_df.iterrows()):
        background_color = "#ffffff" if row_number % 2 == 0 else "#f8fafc"

        cells = []

        for header in headers:
            value = escape(str(row[header]))

            if header == "Symbol":
                cell_html = f"""
                <td
                    style="
                        padding: 14px 12px;
                        text-align: left;
                        background-color: {background_color};
                        border-bottom: 1px solid #e8edf3;
                        color: #172033;
                        font-size: 14px;
                        font-weight: 700;
                        white-space: nowrap;
                    "
                >
                    <span
                        style="
                            display: inline-block;
                            padding: 5px 9px;
                            color: #1769aa;
                            background-color: #eef7ff;
                            border: 1px solid #cfe8fb;
                            border-radius: 999px;
                            font-size: 12px;
                            font-weight: 700;
                            letter-spacing: 0.2px;
                        "
                    >
                        {value}
                    </span>
                </td>
                """
            elif header == "Last Month RSI":
                cell_html = f"""
                <td
                    style="
                        padding: 14px 12px;
                        text-align: right;
                        background-color: {background_color};
                        border-bottom: 1px solid #e8edf3;
                        color: #7a4b00;
                        font-size: 14px;
                        font-weight: 700;
                        white-space: nowrap;
                    "
                >
                    <span
                        style="
                            display: inline-block;
                            min-width: 52px;
                            padding: 5px 8px;
                            color: #8a5700;
                            background-color: #fff6df;
                            border: 1px solid #f4d58a;
                            border-radius: 999px;
                            text-align: center;
                        "
                    >
                        {value}
                    </span>
                </td>
                """
            else:
                cell_html = f"""
                <td
                    style="
                        padding: 14px 12px;
                        text-align: right;
                        background-color: {background_color};
                        border-bottom: 1px solid #e8edf3;
                        color: #344054;
                        font-size: 14px;
                        white-space: nowrap;
                    "
                >
                    {value}
                </td>
                """

            cells.append(cell_html)

        body_rows.append(f"<tr>{''.join(cells)}</tr>")

    return f"""
    <div style="overflow-x: auto;">
        <table
            role="table"
            width="100%"
            cellpadding="0"
            cellspacing="0"
            border="0"
            style="
                width: 100%;
                border-collapse: collapse;
                border: 1px solid #e5e7eb;
                background-color: #ffffff;
                font-family: Arial, Helvetica, sans-serif;
            "
        >
            <thead>
                <tr>{header_cells}</tr>
            </thead>
            <tbody>
                {''.join(body_rows)}
            </tbody>
        </table>
    </div>
    """


def build_html_email(
    shortlist: pd.DataFrame,
    run_date: date,
    preview: bool = False,
) -> str:
    """Build the complete HTML email."""
    stock_count = len(shortlist)
    preview_label = (
        """
        <div
            style="
                margin-bottom: 16px;
                padding: 10px 12px;
                color: #7a4b00;
                background-color: #fff6df;
                border: 1px solid #f4d58a;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 700;
            "
        >
            PREVIEW — using mock/sample values only
        </div>
        """
        if preview
        else ""
    )

    table_html = _build_stock_table(shortlist)

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>StockMarketAlerts</title>
    </head>

    <body
        style="
            margin: 0;
            padding: 0;
            background-color: #f3f5f8;
            color: #172033;
            font-family: Arial, Helvetica, sans-serif;
        "
    >
        <table
            role="presentation"
            width="100%"
            cellpadding="0"
            cellspacing="0"
            border="0"
            style="
                width: 100%;
                border-collapse: collapse;
                background-color: #f3f5f8;
            "
        >
            <tr>
                <td align="center" style="padding: 28px 12px;">
                    <table
                        role="presentation"
                        width="680"
                        cellpadding="0"
                        cellspacing="0"
                        border="0"
                        style="
                            width: 100%;
                            max-width: 680px;
                            border-collapse: collapse;
                        "
                    >
                        <tr>
                            <td
                                style="
                                    padding: 28px 28px 24px;
                                    background-color: #172033;
                                    border-radius: 10px 10px 0 0;
                                    border-bottom: 5px solid #f2b84b;
                                "
                            >
                                <div
                                    style="
                                        color: #f2b84b;
                                        font-size: 12px;
                                        font-weight: 700;
                                        letter-spacing: 1.2px;
                                        text-transform: uppercase;
                                    "
                                >
                                    StockMarketAlerts
                                </div>

                                <div
                                    style="
                                        margin-top: 8px;
                                        color: #ffffff;
                                        font-size: 25px;
                                        font-weight: 700;
                                        line-height: 1.25;
                                    "
                                >
                                    NIFTY 50 Market Shortlist
                                </div>

                                <div
                                    style="
                                        margin-top: 8px;
                                        color: #cbd5e1;
                                        font-size: 13px;
                                    "
                                >
                                    Daily screening report · {escape(run_date.isoformat())}
                                </div>
                            </td>
                        </tr>

                        <tr>
                            <td
                                style="
                                    padding: 24px 28px 28px;
                                    background-color: #ffffff;
                                    border-radius: 0 0 10px 10px;
                                "
                            >
                                {preview_label}

                                <table
                                    role="presentation"
                                    width="100%"
                                    cellpadding="0"
                                    cellspacing="0"
                                    border="0"
                                    style="
                                        width: 100%;
                                        border-collapse: collapse;
                                        margin-bottom: 20px;
                                    "
                                >
                                    <tr>
                                        <td
                                            style="
                                                padding: 14px 16px;
                                                background-color: #f8fafc;
                                                border: 1px solid #e5e7eb;
                                                border-radius: 7px;
                                            "
                                        >
                                            <div
                                                style="
                                                    color: #667085;
                                                    font-size: 11px;
                                                    font-weight: 700;
                                                    letter-spacing: 0.5px;
                                                    text-transform: uppercase;
                                                "
                                            >
                                                Shortlisted stocks
                                            </div>

                                            <div
                                                style="
                                                    margin-top: 4px;
                                                    color: #172033;
                                                    font-size: 24px;
                                                    font-weight: 700;
                                                "
                                            >
                                                {stock_count}
                                            </div>
                                        </td>
                                    </tr>
                                </table>

                                <div
                                    style="
                                        margin-bottom: 16px;
                                        color: #475467;
                                        font-size: 13px;
                                        line-height: 1.6;
                                    "
                                >
                                    Stocks shown below satisfy both conditions:
                                    recent Friday closing price greater than the
                                    previous Friday closing price, and last completed
                                    month RSI between <strong>40.000</strong> and
                                    <strong>45.000</strong>.
                                </div>

                                {table_html}

                                <div
                                    style="
                                        margin-top: 22px;
                                        padding-top: 16px;
                                        color: #98a2b3;
                                        border-top: 1px solid #eaecf0;
                                        font-size: 11px;
                                        line-height: 1.5;
                                    "
                                >
                                    Generated automatically by StockMarketAlerts.
                                </div>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """


def _build_plain_text(shortlist: pd.DataFrame) -> str:
    """Build the plain-text email fallback."""
    if shortlist.empty:
        return "No NIFTY 50 stocks satisfied both screening conditions."

    display_df = _prepare_display_dataframe(shortlist)

    return (
        "NIFTY 50 Stock Screening Results\n\n"
        + display_df.to_string(index=False)
    )


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

    html_body = build_html_email(
        shortlist=shortlist,
        run_date=run_date,
    )

    plain_text = _build_plain_text(shortlist)

    subject = (
        f"StockMarketAlerts | NIFTY 50 shortlist | "
        f"{run_date.isoformat()} | {len(shortlist)} stock(s)"
    )

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = smtp_username
    message["To"] = recipient
    message.set_content(plain_text)
    message.add_alternative(html_body, subtype="html")

    with smtplib.SMTP_SSL(smtp_host, smtp_port) as smtp:
        smtp.login(smtp_username, smtp_password)
        smtp.send_message(message)
