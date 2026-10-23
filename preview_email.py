from datetime import date
from pathlib import Path

import pandas as pd

from src.emailer import build_html_email


# Mock/sample values for visual preview only.
sample_shortlist = pd.DataFrame(
    [
        {
            "symbol": "RELIANCE",
            "recent_friday_close": 1_428.375,
            "previous_friday_close": 1_401.120,
            "last_month_rsi": 42.618,
        },
        {
            "symbol": "INFY",
            "recent_friday_close": 1_566.250,
            "previous_friday_close": 1_532.875,
            "last_month_rsi": 40.947,
        },
        {
            "symbol": "TCS",
            "recent_friday_close": 3_214.525,
            "previous_friday_close": 3_201.200,
            "last_month_rsi": 44.382,
        },
    ]
)

html = build_html_email(
    shortlist=sample_shortlist,
    run_date=date.today(),
    preview=True,
)

output_path = Path("preview_email.html")
output_path.write_text(html, encoding="utf-8")

print(f"Created preview: {output_path.resolve()}")
