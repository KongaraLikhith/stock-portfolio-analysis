import yfinance as yf
import pandas as pd

def fetch_stock_data(tickers, start_date, end_date):
    """
    Fetch historical stock prices (Adj Close preferred) for given tickers and date range.
    Returns a DataFrame with dates as index and tickers as columns.
    """

    data = yf.download(tickers, start=start_date, end=end_date)

    # Drop empty columns upfront (invalid tickers)
    data = data.dropna(axis=1, how='all')

    if data.empty:
        return pd.DataFrame()

    # Select Adj Close or Close
    if isinstance(data.columns, pd.MultiIndex):
        if "Adj Close" in data.columns.get_level_values(0):
            data = data["Adj Close"]
        else:
            data = data["Close"]
    else:
        # Single ticker path
        if "Adj Close" in data.columns:
            data = data[["Adj Close"]]
        else:
            data = data[["Close"]]

    # ---- FIXED COLUMN FLATTENING ----
    if isinstance(data.columns, pd.MultiIndex):
        # Multi-ticker, extract ticker symbols
        data.columns = data.columns.get_level_values(1)
    else:
        # Single ticker → tickers is a list
        if len(tickers) == 1:
            data.columns = [tickers[0].upper()]
        else:
            # yfinance may still give weird format → fallback
            data.columns = [str(c).upper() for c in data.columns]

    # Fill missing values
    data = data.fillna(method='ffill').fillna(method='bfill')

    # Remove bad tickers again
    data = data.dropna(axis=1, how='all')
    if data.empty:
        return pd.DataFrame()

    # Apply date range
    data = data.loc[start_date:end_date]

    return data
