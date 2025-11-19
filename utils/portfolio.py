# utils/portfolio.py
import pandas as pd
import numpy as np

def compute_portfolio_value(data, weights=None, initial_value=100000):
    """
    Compute the portfolio value over time based on stock prices and weights.
    
    Args:
        data (pd.DataFrame): DataFrame of stock prices (Adj Close), index=dates, columns=tickers
        weights (dict): Optional. Dictionary of ticker weights. If None, equal weights.
        initial_value (float): Starting portfolio value
    
    Returns:
        pd.Series: Portfolio value over time
    """
    if data.empty:
        return pd.Series(dtype=float)

    # Default: equal weights
    if weights is None:
        weights = {ticker: 1/len(data.columns) for ticker in data.columns}
    else:
        # Normalize weights if they don't sum to 1
        total_weight = sum(weights.values())
        weights = {k: v/total_weight for k, v in weights.items()}

    # Align weights with data columns
    weights_list = [weights[ticker] for ticker in data.columns]

    # Calculate daily portfolio value
    normalized_prices = data / data.iloc[0]  # start at 1
    weighted_prices = normalized_prices * weights_list
    portfolio_value = weighted_prices.sum(axis=1) * initial_value

    return portfolio_value

def compute_portfolio_metrics(portfolio_value):
    """
    Compute key portfolio metrics: cumulative return, annualized volatility, max drawdown.
    
    Args:
        portfolio_value (pd.Series): Portfolio value over time
    
    Returns:
        dict: metrics
    """
    daily_returns = portfolio_value.pct_change().dropna()
    cumulative_return = (portfolio_value[-1] / portfolio_value[0]) - 1
    annual_volatility = daily_returns.std() * (252 ** 0.5)
    running_max = portfolio_value.cummax()
    max_drawdown = (portfolio_value - running_max).min() / running_max.max()

    return {
        "Cumulative Return": cumulative_return,
        "Annual Volatility": annual_volatility,
        "Max Drawdown": max_drawdown
    }

def compute_sharpe_ratio(portfolio_values, risk_free_rate=0.02):
    """
    Compute annualized Sharpe Ratio assuming daily data.
    """
    daily_returns = portfolio_values.pct_change().dropna()
    excess_returns = daily_returns - risk_free_rate/252
    sharpe_ratio = (excess_returns.mean() / excess_returns.std()) * np.sqrt(252)
    return sharpe_ratio

def compute_sortino_ratio(portfolio_values, risk_free_rate=0.02):
    """
    Compute annualized Sortino Ratio assuming daily data.
    """
    daily_returns = portfolio_values.pct_change().dropna()
    excess_returns = daily_returns - risk_free_rate/252
    downside_std = daily_returns[daily_returns < 0].std()
    if downside_std == 0:
        return np.nan
    sortino_ratio = (excess_returns.mean() / downside_std) * np.sqrt(252)
    return sortino_ratio
