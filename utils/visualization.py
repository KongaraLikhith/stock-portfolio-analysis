# utils/visualization.py
import plotly.express as px
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sb
import plotly.graph_objects as go

def plot_stock_trends(data, title="Stock Price Trend"):
    """
    Plots line charts for single or multiple stocks with hover dates in "Nov 05 2025" format.
    """
    if data.empty:
        st.warning("No data to plot.")
        return

    # Reset index to have 'Date' as a column
    plot_data = data.reset_index().rename(columns={'index':'Date'})

    # Multi-stock handling: melt to long format
    if len(data.columns) > 1:
        df_long = plot_data.melt(id_vars=['Date'], value_vars=data.columns,
                                 var_name='Ticker', value_name='Price')
        fig = px.line(df_long, x='Date', y='Price', color='Ticker', title=title,
                      hover_data={'Date': True, 'Price': ':.2f', 'Ticker': False})
    else:
        ticker = data.columns[0]
        fig = px.line(plot_data, x='Date', y=ticker, title=f"{ticker} Price Trend",
                      hover_data={'Date': True, ticker: ':.2f'})

    # Format hover and x-axis ticks
    fig.update_xaxes(tickformat="%b %d %Y", hoverformat="%b %d %Y")

    # Custom hover template for full date
    fig.update_traces(
        hovertemplate="<b>%{fullData.name}</b><br>Date: %{x|%b %d %Y}<br>Price: %{y:.2f}<extra></extra>"
    )

    st.plotly_chart(fig, use_container_width=True)

def plot_portfolio_value(portfolio_value, title="Portfolio Value Over Time"):
    # Ensure portfolio_value is a DataFrame
    if isinstance(portfolio_value, pd.Series):
        df = pd.DataFrame({
            'Date': portfolio_value.index,
            'Value': portfolio_value.values
        })
    else:
        df = portfolio_value.reset_index()
        df = df.rename(columns={df.columns[0]: 'Date', df.columns[1]: 'Value'})

    fig = px.area(df, x='Date', y='Value', title=title, hover_data={'Value':':.2f'})
    fig.update_layout(xaxis_title='Date', yaxis_title='Value')
    st.plotly_chart(fig, use_container_width=True)

    
def plot_portfolio_allocation(composition_df, title="Portfolio Allocation"):
    """
    Plots a pie chart showing portfolio allocation using precomputed numeric values.
    
    Args:
        composition_df (pd.DataFrame): DataFrame containing 'Ticker' and '% of Portfolio' columns.
    """
    if composition_df.empty:
        st.warning("No data to plot allocation.")
        return

    # Use numeric '% of Portfolio' values
    fig = px.pie(
        composition_df,
        names="Ticker",
        values="% of Portfolio",
        title=title,
        hole=0.4
    )
    st.plotly_chart(fig, use_container_width=True)
    
    
def plot_portfolio_contributions(data, weights):
    """
    Plot portfolio contributions as an interactive stacked area chart using Plotly.
    """
    # Compute weighted portfolio for each stock
    df = data.copy()
    for t in weights:
        df[t] = df[t] * weights[t]
    df['Date'] = df.index

    fig = px.area(df, x='Date', y=list(weights.keys()),
                  title="Portfolio Contributions Over Time",
                  labels={'value': 'Value ($)', 'variable': 'Stock'},
                  template='plotly_white')
    fig.update_layout(legend_title_text='Stocks')
    st.plotly_chart(fig, use_container_width=True)
    
def plot_daily_returns_distribution(portfolio_value):
    daily_returns = portfolio_value.pct_change().dropna() * 100

    fig = go.Figure()

    # Histogram
    fig.add_trace(go.Histogram(
        x=daily_returns,
        nbinsx=30,
        name="Histogram",
        marker_color='skyblue',
        opacity=0.75
    ))

    # Boxplot (overlay)
    fig.add_trace(go.Box(
        x=daily_returns,
        name="Boxplot",
        marker_color='green',
        boxpoints='outliers'
    ))

    fig.update_layout(
        title="Daily Returns Distribution",
        xaxis_title="Daily Return (%)",
        yaxis_title="Frequency",
        barmode='overlay',
        template='plotly_white'
    )

    st.plotly_chart(fig, use_container_width=True)


def plot_candlestick(df, ticker):
    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df[ticker].shift(1),  # approximate open from previous close
        high=df[ticker],
        low=df[ticker],
        close=df[ticker],
        increasing_line_color='green',
        decreasing_line_color='red',
        name=ticker
    )])
    fig.update_layout(title=f"{ticker} Candlestick Chart", xaxis_title="Date", yaxis_title="Price ($)", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
    
def plot_moving_averages(df, ticker):
    df_copy = df.copy()
    df_copy['SMA_20'] = df_copy[ticker].rolling(20).mean()
    df_copy['SMA_50'] = df_copy[ticker].rolling(50).mean()

    st.area_chart(df_copy[[ticker, 'SMA_20', 'SMA_50']])

def plot_drawdown(df, ticker):
    prices = df[ticker]
    cum_max = prices.cummax()
    drawdown = (prices - cum_max) / cum_max * 100  # % drawdown
    st.line_chart(drawdown, height=300)
    st.caption("Drawdown (%) from peak")
    
def plot_macd(data, ticker):
    """
    Plots MACD chart for a given stock.
    data: DataFrame with stock prices (Adj Close)
    ticker: str, stock symbol
    """
    if ticker not in data.columns or data[ticker].isnull().all():
        st.warning(f"No data available for {ticker}")
        return

    prices = data[ticker]

    # Compute EMAs
    ema12 = prices.ewm(span=12, adjust=False).mean()
    ema26 = prices.ewm(span=26, adjust=False).mean()

    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    hist = macd - signal

    # Plot
    fig = go.Figure()
    # fig.add_trace(go.Scatter(x=prices.index, y=prices, mode='lines', name='Price', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=prices.index, y=macd, mode='lines', name='MACD', line=dict(color='green')))
    fig.add_trace(go.Scatter(x=prices.index, y=signal, mode='lines', name='Signal', line=dict(color='red')))
    fig.add_trace(go.Bar(x=prices.index, y=hist, name='Histogram', marker_color='orange'))

    fig.update_layout(title=f"{ticker} MACD Chart", xaxis_title="Date", yaxis_title="Price / MACD")
    st.plotly_chart(fig, use_container_width=True)
