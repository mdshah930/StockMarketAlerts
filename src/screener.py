from datetime import date
from typing import Dict, List, Tuple

import pandas as pd
import yfinance as yf
from ta.momentum import RSIIndicator


HISTORICAL_PERIOD = "5y"
RSI_PERIOD = 14
RSI_MIN = 40
RSI_MAX = 45


def _clean_close_series(data: pd.DataFrame) -> pd.Series:
    """Return a clean daily close-price Series."""
    if data.empty or "Close" not in data.columns:
        raise ValueError("No usable Close price data was returned")

    close = data["Close"]

    # Defensive handling in case yfinance returns a one-column DataFrame.
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    close = pd.to_numeric(close, errors="coerce").dropna()

    if close.empty:
        raise ValueError("Close price data is empty after cleaning")

    index = pd.to_datetime(close.index)

    # Remove timezone information, if present.
    if index.tz is not None:
        index = index.tz_localize(None)

    close.index = index.normalize()
    close = close[~close.index.duplicated(keep="last")]
    close = close.sort_index()

    return close


def _get_latest_two_friday_closes(
    close: pd.Series,
    run_date: date,
) -> Tuple[float, float]:
    """Return recent Friday close and previous Friday close."""
    close = close[close.index <= pd.Timestamp(run_date)]

    friday_closes = close[close.index.dayofweek == 4]

    if len(friday_closes) < 2:
        raise ValueError("Fewer than two Friday closing prices are available")

    recent_friday_close = float(friday_closes.iloc[-1])
    previous_friday_close = float(friday_closes.iloc[-2])

    return recent_friday_close, previous_friday_close


def _get_last_completed_month_rsi(
    close: pd.Series,
    run_date: date,
) -> float:
    """
    Calculate RSI from monthly closes and return the last completed
    month's RSI.

    The current calendar month is deliberately excluded.
    """
    monthly_close = close.groupby(close.index.to_period("M")).last()

    current_month = pd.Timestamp(run_date).to_period("M")
    completed_months = monthly_close[monthly_close.index < current_month]

    # RSI with a 14-month window requires at least 15 monthly observations
    # before the first non-null RSI value is available.
    if len(completed_months) < RSI_PERIOD + 1:
        raise ValueError(
            f"At least {RSI_PERIOD + 1} completed monthly closes are required"
        )

    monthly_rsi = RSIIndicator(
        close=completed_months,
        window=RSI_PERIOD,
        fillna=False,
    ).rsi()

    monthly_rsi = monthly_rsi.dropna()

    if monthly_rsi.empty:
        raise ValueError("Could not calculate monthly RSI")

    return float(monthly_rsi.iloc[-1])


def screen_symbol(symbol: str, run_date: date) -> Dict[str, float]:
    """Fetch data and calculate screening values for one NSE symbol."""
    yahoo_symbol = f"{symbol}.NS"

    ticker = yf.Ticker(yahoo_symbol)
    data = ticker.history(
        period=HISTORICAL_PERIOD,
        interval="1d",
        auto_adjust=False,
        actions=False,
    )

    close = _clean_close_series(data)

    recent_friday_close, previous_friday_close = (
        _get_latest_two_friday_closes(close, run_date)
    )

    last_month_rsi = _get_last_completed_month_rsi(close, run_date)

    return {
        "symbol": symbol,
        "recent_friday_close": recent_friday_close,
        "previous_friday_close": previous_friday_close,
        "last_month_rsi": last_month_rsi,
    }


def screen_nifty50(
    symbols: List[str],
    run_date: date,
) -> Tuple[List[Dict[str, float]], Dict[str, str]]:
    """
    Screen all NIFTY 50 symbols.

    Returns:
        shortlist: Stocks satisfying both conditions.
        failures: Symbols for which data or calculations failed.
    """
    shortlist = []
    failures = {}

    for symbol in symbols:
        try:
            result = screen_symbol(symbol, run_date)

            price_condition = (
                result["recent_friday_close"]
                > result["previous_friday_close"]
            )

            rsi_condition = (
                RSI_MIN <= result["last_month_rsi"] <= RSI_MAX
            )

            if price_condition and rsi_condition:
                shortlist.append(result)

            print(
                f"{symbol}: "
                f"recent Friday={result['recent_friday_close']:.2f}, "
                f"previous Friday={result['previous_friday_close']:.2f}, "
                f"last month RSI={result['last_month_rsi']:.2f}, "
                f"shortlisted={price_condition and rsi_condition}"
            )

        except Exception as exc:
            failures[symbol] = str(exc)
            print(f"{symbol}: failed - {exc}")

    return shortlist, failures
