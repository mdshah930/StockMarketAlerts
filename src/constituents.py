from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
NIFTY50_FILE = PROJECT_ROOT / "data" / "static" / "ind_nifty50list.csv"


def load_nifty50_symbols(file_path=NIFTY50_FILE):
    """
    Load and validate the NIFTY 50 symbols from the NSE CSV file.

    Returns:
        list[str]: NSE symbols such as RELIANCE, TCS, and INFY.
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"NIFTY 50 file was not found: {file_path}")

    df = pd.read_csv(file_path)

    if "Symbol" not in df.columns:
        raise ValueError(
            f"Expected a 'Symbol' column. Found columns: {df.columns.tolist()}"
        )

    symbols = (
        df["Symbol"]
        .dropna()
        .astype(str)
        .str.strip()
        .str.upper()
    )

    symbols = symbols[symbols != ""].drop_duplicates().tolist()

    if len(symbols) != 50:
        raise ValueError(
            f"Expected 50 NIFTY 50 symbols, but found {len(symbols)}"
        )

    return symbols


def to_yahoo_symbols(symbols):
    """
    Convert NSE symbols to Yahoo Finance symbols.

    Example:
        RELIANCE -> RELIANCE.NS
    """
    return [f"{symbol}.NS" for symbol in symbols]


if __name__ == "__main__":
    nifty50_symbols = load_nifty50_symbols()
    yahoo_symbols = to_yahoo_symbols(nifty50_symbols)

    print(f"Loaded {len(nifty50_symbols)} NIFTY 50 symbols")
    print("\nNSE symbols:")
    print(", ".join(nifty50_symbols))

    print("\nYahoo Finance symbols:")
    print(", ".join(yahoo_symbols))
