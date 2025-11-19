# utils/alerts.py
import pandas as pd
from datetime import datetime, timedelta
import yfinance as yf

def check_portfolio_drop(portfolio_value: pd.Series, threshold_pct: float):
    """
    Checks if the portfolio dropped below a given threshold from its initial value.

    Returns:
        alert_message (str or None)
    """
    if portfolio_value.empty:
        return None

    drop_pct = (portfolio_value / portfolio_value.iloc[0] - 1) * 100
    min_drop = drop_pct.min()

    if min_drop <= -threshold_pct:
        return f"Portfolio dropped by {abs(min_drop):.2f}% which exceeds your threshold of {threshold_pct}%"
    return None


def check_stock_drops(data: pd.DataFrame, tickers: list, threshold_pct: float):
    """
    Checks if any stock dropped more than threshold_pct in a single day.
    
    Returns:
        List of alert messages for stocks
    """
    alerts = []
    if data.empty:
        return alerts

    daily_change = data.pct_change() * 100
    for ticker in tickers:
        if ticker in daily_change.columns:
            min_change = daily_change[ticker].min()
            if min_change <= -threshold_pct:
                alerts.append(
                    f"{ticker} dropped by {abs(min_change):.2f}% in a single day, exceeding your threshold of {threshold_pct}%"
                )
    return alerts


def get_latest_market_changes(tickers):
    """
    Fetch today's and yesterday's prices for given tickers,
    and compute daily % change (works for single or multiple tickers).
    """
    if not tickers:
        return pd.DataFrame()

    try:
        data = yf.download(tickers, period="5d", interval="1d", progress=False)

        # Handle both single-ticker and multi-ticker cases
        if isinstance(data.columns, pd.MultiIndex):
            # Multi-ticker case → extract Adj Close level
            if 'Adj Close' in data.columns.get_level_values(0):
                data = data['Adj Close']
            elif 'Close' in data.columns.get_level_values(0):
                data = data['Close']
            else:
                return pd.DataFrame()
        else:
            # Single ticker → just use Close or Adj Close directly
            if 'Adj Close' in data.columns:
                data = data['Adj Close']
            elif 'Close' in data.columns:
                data = data['Close']
            else:
                return pd.DataFrame()

        # Clean and compute % changes
        data = data.ffill().tail(2)
        if data.empty or len(data) < 2:
            return pd.DataFrame()

        changes = ((data.iloc[-1] / data.iloc[-2]) - 1) * 100
        latest_prices = data.iloc[-1]

        summary = pd.DataFrame({
            "Ticker": tickers,
            "Latest Price": [f"${latest_prices[t]:.2f}" for t in tickers],
            "Change (%)": [f"{'⬆️' if changes[t] > 0 else '⬇️'} {abs(changes[t]):.2f}%" for t in tickers]
        })

        return summary

    except Exception as e:
        print("Error fetching latest market data:", e)
        return pd.DataFrame()