import argparse
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
from dotenv import load_dotenv

from src.constituents import load_nifty50_symbols
from src.emailer import send_screening_email
from src.screener import screen_nifty50


PROJECT_ROOT = Path(__file__).resolve().parent
TIMEZONE = ZoneInfo("Asia/Kolkata")

OUTPUT_COLUMNS = [
    "symbol",
    "recent_friday_close",
    "previous_friday_close",
    "last_month_rsi",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--no-email",
        action="store_true",
        help="Run the screening but do not send an email",
    )
    args = parser.parse_args()

    load_dotenv(PROJECT_ROOT / ".env")

    run_date = datetime.now(TIMEZONE).date()
    symbols = load_nifty50_symbols()

    print(f"Running NIFTY 50 screening for {run_date}")
    print(f"Loaded {len(symbols)} symbols")

    shortlist, failures = screen_nifty50(
        symbols=symbols,
        run_date=run_date,
    )

    shortlist_df = pd.DataFrame(shortlist, columns=OUTPUT_COLUMNS)

    print("\nShortlisted stocks:")
    if shortlist_df.empty:
        print("No stocks satisfied both conditions.")
    else:
        print(shortlist_df.to_string(index=False))

    print(f"\nShortlisted count: {len(shortlist_df)}")
    print(f"Failed symbols: {len(failures)}")

    if failures:
        print("\nFailed symbols:")
        for symbol, reason in failures.items():
            print(f"- {symbol}: {reason}")

    if args.no_email:
        print("\nEmail skipped because --no-email was provided.")
    else:
        send_screening_email(
            shortlist=shortlist_df,
            run_date=run_date,
        )
        print("\nEmail sent successfully.")


if __name__ == "__main__":
    main()
