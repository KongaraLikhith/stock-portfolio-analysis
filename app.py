import streamlit as st
import pandas as pd
from utils.data_loader import fetch_stock_data
from utils.visualization import *
from utils.portfolio import compute_portfolio_value, compute_portfolio_metrics,compute_sharpe_ratio,compute_sortino_ratio
from utils.alerts import check_portfolio_drop, check_stock_drops, get_latest_market_changes


# Streamlit Page Config ------------------------ 

st.set_page_config(page_title="Portfolio Dashboard", layout="wide")
st.title("📊 Portfolio Performance Monitoring Dashboard")


# Sidebar Inputs  ---------------------------

st.sidebar.header("Portfolio Input")

tickers_input = st.sidebar.text_area(
    "Enter ticker symbols separated by commas", "AAPL,MSFT,TSLA"
)
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2020-01-01"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("2025-01-01"))

tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]
tickers = list(dict.fromkeys(tickers))  # removes duplicates while keeping order

# Portfolio Weights ------------------------------

weights = {}
if len(tickers) > 1:
    st.sidebar.header("Portfolio Weights (%)")
    raw_weights = []
    for ticker in tickers:
        weight = st.sidebar.number_input(
            f"Weight for {ticker}", min_value=0, max_value=100, value=int(100 / len(tickers))
        )
        raw_weights.append(weight)

    total = sum(raw_weights)
    if total == 0:
        st.sidebar.warning("Total weight cannot be 0. Using equal weights.")
        normalized_weights = {t: 1 / len(tickers) for t in tickers}
    else:
        normalized_weights = {t: w / total for t, w in zip(tickers, raw_weights)}

    st.sidebar.markdown("**Normalized Weights:**")
    for t, w in normalized_weights.items():
        st.sidebar.write(f"{t}: {w*100:.2f}%")
    weights = normalized_weights
elif len(tickers) == 1:
    weights = {tickers[0]: 1.0}

# Alerts Settings --------------------------------

st.sidebar.header("Alerts Settings")
stock_threshold = st.sidebar.number_input(
    "Stock Alert Threshold (%)", value=2.0, min_value=0.0, max_value=100.0, step=0.1
)
portfolio_threshold = st.sidebar.number_input(
    "Portfolio Alert Threshold (%)", value=2.0, min_value=0.0, max_value=100.0, step=0.1
)


# Load Data Button ----------------------------------

data = pd.DataFrame()  # default empty

load_data_clicked = st.sidebar.button("Load Data")

if load_data_clicked:
    if len(tickers) == 0:
        st.sidebar.error("Please enter at least one ticker symbol.")
    else:
        with st.spinner("Fetching data..."):
            data = fetch_stock_data(tickers, start_date, end_date)
            available_tickers = list(data.columns)
            invalid_tickers = [t for t in tickers if t not in available_tickers]
            tickers = available_tickers  # overwrite ticker list with valid ones
            if invalid_tickers:
                st.warning(f"Removed invalid tickers: {', '.join(invalid_tickers)}")
            if data.empty:
                st.error("No data returned. Check your ticker symbols or date range.")
            else:
                st.subheader(f"📄 Price Data from {start_date} to {end_date}")
                st.dataframe(data.tail())

                # Latest Market Changes
                st.markdown("### 📅 Latest Market Changes (Today vs Yesterday)")
                latest_changes = get_latest_market_changes(tickers)
                if latest_changes.empty:
                    st.info("No recent market data available (maybe market closed today).")
                else:
                    def color_change(val):
                        if '⬆️' in val:
                            return 'background-color: #d4edda; color: #155724;'
                        elif '⬇️' in val:
                            return 'background-color: #f8d7da; color: #721c24;'
                        return ''
                    styled_df = latest_changes.style.applymap(color_change, subset=['Change (%)'])
                    st.dataframe(styled_df, use_container_width=True, hide_index=True)

                # Stock Line Chart
                st.subheader("📈 Stock Price Trends")
                plot_stock_trends(data, title="Stock Price Trend")


# Portfolio Metrics & Charts -----------------------------
if not data.empty:
    # Portfolio value & metrics
    if len(tickers) == 1:
        ticker = tickers[0]
        portfolio_value = data[ticker]
        cumulative_return = (portfolio_value.iloc[-1] / portfolio_value.iloc[0] - 1) * 100
    else:
        portfolio_value = compute_portfolio_value(data, weights=weights)
        cumulative_return = (portfolio_value.iloc[-1] / portfolio_value.iloc[0] - 1) * 100

    main_col, alert_col = st.columns([3, 1])

   
    # Main Column ------------------------
  
    with main_col:
        if len(tickers) > 1:
            st.subheader("📋 Portfolio Composition")
            latest_prices = data.iloc[-1]
            composition_numeric = []
            total_portfolio_value = sum(weights[t] * latest_prices[t] for t in tickers)
            for t in tickers:
                pct_of_portfolio = (weights[t] * latest_prices[t] / total_portfolio_value) * 100
                composition_numeric.append({
                    "Ticker": t,
                    "Weight (%)": weights[t] * 100,
                    "Current Value ($)": weights[t] * latest_prices[t],
                    "% of Portfolio": pct_of_portfolio
                })
            composition_df_numeric = pd.DataFrame(composition_numeric)
            composition_df_numeric.index+=1
            st.dataframe(composition_df_numeric, use_container_width=True)

        # Metrics ------------------------------
        st.subheader("📊 Portfolio Metrics")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Number of Stocks", len(tickers))
        col2.metric("Cumulative Return", f"{cumulative_return:.2f}%")
        metrics = compute_portfolio_metrics(portfolio_value)
        col3.metric("Annual Volatility", f"{metrics['Annual Volatility']*100:.2f}%")
        col4.metric("Max Drawdown", f"{metrics['Max Drawdown']*100:.2f}%")
       
        sharpe = compute_sharpe_ratio(portfolio_value)
        sortino = compute_sortino_ratio(portfolio_value)
        col5, col6 = st.columns([1, 1], gap="small")
        col5.metric("Sharpe Ratio", f"{sharpe:.2f}")
        col6.metric("Sortino Ratio", f"{sortino:.2f}")
       
        # Performance Summary Cards -------------------------------
       
        if len(tickers) > 1:
            # Compute stock returns
            stock_returns = (data.iloc[-1] / data.iloc[0] - 1) * 100
            best_stock = stock_returns.idxmax()
            best_return = stock_returns.max()
            worst_stock = stock_returns.idxmin()
            worst_return = stock_returns.min()

            # Portfolio daily returns
            daily_portfolio_return = portfolio_value.pct_change().dropna()
            avg_daily_return = daily_portfolio_return.mean() * 100
            total_gain_loss = (portfolio_value.iloc[-1] / portfolio_value.iloc[0] - 1) * 100

            # Display in two columns (row 1)
            col7, col8 = st.columns([1, 1], gap="small")
            col7.metric("Best Performing Stock", f"{best_stock} ({best_return:.2f}%)")
            col8.metric("Worst Performing Stock", f"{worst_stock} ({worst_return:.2f}%)")

            # Display in two columns (row 2)
            col9, col10 = st.columns([1, 1], gap="small")
            col9.metric("Average Daily Return", f"{avg_daily_return:.2f}%")
            col10.metric("Total Gain/Loss", f"{total_gain_loss:.2f}%")


        if len(tickers) > 1:
            st.subheader("Portfolio Overview")

            tabs = st.tabs([
                "Portfolio Value",
                "Portfolio Contributions",
                "Daily Returns Distribution",
                "Portfolio Allocation"
            ])
            with tabs[0]:
                with st.spinner("Loading chart..."):
                    st.subheader("📈 Portfolio Value Over Time")
                    plot_portfolio_value(portfolio_value)
            with tabs[1]:
                st.subheader("📊 Portfolio Contributions Over Time")
                plot_portfolio_contributions(data, weights)
            with tabs[2]:
                st.subheader("📊 Daily Returns Distribution")
                plot_daily_returns_distribution(portfolio_value)
            with tabs[3]:
                st.subheader("🥧 Portfolio Allocation (Latest Prices)")
                plot_portfolio_allocation(composition_df_numeric)
        else:
            ticker = tickers[0]
            st.subheader(f"Analysis for {ticker}")
            tabs = st.tabs(["Candlestick", "Moving Averages", "Drawdown",'MACD'])
            with tabs[0]:
                with st.spinner("Loading chart..."):
                    st.subheader(f"📊 {ticker} Candlestick Chart")
                    plot_candlestick(data, ticker)
            with tabs[1]:
                st.subheader(f"📈 {ticker} Price with Moving Averages")
                plot_moving_averages(data, ticker)
            with tabs[2]:
                st.subheader(f"📉 {ticker} Drawdown (%)")
                plot_drawdown(data, ticker)
            with tabs[3]:
                st.subheader(f" {ticker} Price with Moving Averages")
                plot_macd(data,ticker)

    
    # Alerts Column ----------------------------
    
    with alert_col:
        st.subheader("⚠️Alerts")

        # Compute changes
        daily_change = data.pct_change() * 100
        portfolio_pct_change = (portfolio_value / portfolio_value.iloc[0] - 1) * 100
        latest_portfolio_change = portfolio_pct_change.iloc[-1]

        # Cumulative Alerts
        portfolio_alert = check_portfolio_drop(portfolio_value, threshold_pct=portfolio_threshold)
        stock_alerts = check_stock_drops(data, tickers, threshold_pct=stock_threshold)

        # Cumulative Alerts
        st.subheader("⚠️ Cumulative Alerts")
        if portfolio_alert:
            st.markdown(f"<p style='color: orange; font-size:16px;'>{portfolio_alert}</p>", unsafe_allow_html=True)

        for msg in stock_alerts:
            st.markdown(f"<p style='color: red; font-size:14px;'>{msg}</p>", unsafe_allow_html=True)

        if not portfolio_alert and not stock_alerts:
            st.success("✅ No cumulative alerts triggered.")
        st.markdown("---")
        # Latest Day Changes
        st.subheader("📅 Latest Day Changes")

        # Portfolio
        if abs(latest_portfolio_change) >= portfolio_threshold:
            color = "green" if latest_portfolio_change > 0 else "red"
            sign = "⬆️" if latest_portfolio_change > 0 else "⬇️"
            st.markdown(f"<span style='color:{color}; font-size:16px'>{sign} Portfolio {latest_portfolio_change:.2f}%</span>", unsafe_allow_html=True)

        # Stocks
        stock_alerted = False
        for t in tickers:
            latest_stock_change = daily_change[t].iloc[-1]
            if abs(latest_stock_change) >= stock_threshold:
                stock_alerted = True
                color = "green" if latest_stock_change > 0 else "red"
                sign = "⬆️" if latest_stock_change > 0 else "⬇️"
                st.markdown(f"<span style='color:{color}; font-size:14px'>{sign} {t} {latest_stock_change:.2f}%</span>", unsafe_allow_html=True)

        # No alerts today
        if abs(latest_portfolio_change) < portfolio_threshold and not stock_alerted:
            st.success("✅ No significant changes today.")

