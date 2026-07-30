import streamlit as st
import yfinance as df
import pandas as pd
import plotly.graph_objects as go
from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator

# ----------------------------------------------------
# 1. Page Configurations
# ----------------------------------------------------
st.set_page_config(page_title="Trade Analysis Dashboard", layout="wide")
st.title("📈 Real-Time Trade Analysis Dashboard")
st.markdown("Analyze stock trends, moving averages, and RSI indicators instantly.")

# ----------------------------------------------------
# 2. Sidebar Controls (User Input)
# ----------------------------------------------------
st.sidebar.header("Navigation & Settings")
ticker = st.sidebar.text_input("Enter Stock Ticker", value="AAPL").upper()

time_period = st.sidebar.selectbox(
    "Select Time Period",
    options=["1mo", "3mo", "6mo", "1y", "2y", "5y"],
    index=2
)

interval = st.sidebar.selectbox(
    "Select Interval",
    options=["1d", "1wk", "1mo"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Technical Indicator Settings**")
sma_window = st.sidebar.slider("SMA Window Length", min_value=5, max_value=50, value=20)
rsi_window = st.sidebar.slider("RSI Window Length", min_value=5, max_value=30, value=14)

# ----------------------------------------------------
# 3. Data Fetching & Processing Logic
# ----------------------------------------------------
@st.cache_data(ttl=3600)  # Cache data for 1 hour to prevent redundant API hits
def load_data(symbol, period, data_interval):
    try:
        stock = df.Ticker(symbol)
        history = stock.history(period=period, interval=data_interval)
        if history.empty:
            return None, None
        return history, stock.info
    except Exception:
        return None, None

data, info = load_data(ticker, time_period, interval)

# ----------------------------------------------------
# 4. App UI Layout & Visualization
# ----------------------------------------------------
if data is not None and len(data) > 0:
    
    # Summary Cards
    company_name = info.get('longName', ticker)
    current_price = data['Close'].iloc[-1]
    price_change = current_price - data['Close'].iloc[-2]
    pct_change = (price_change / data['Close'].iloc[-2]) * 100
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Company Name", company_name)
    col2.metric("Latest Close Price", f"${current_price:.2f}")
    col3.metric("Daily Change", f"${price_change:.2f}", f"{pct_change:.2f}%")
    
    st.markdown("---")
    
    # Calculate Indicators using 'ta' library
    sma = SMAIndicator(close=data['Close'], window=sma_window)
    data['SMA'] = sma.sma_indicator()
    
    rsi = RSIIndicator(close=data['Close'], window=rsi_window)
    data['RSI'] = rsi.rsi()

    # Layout for Charts
    chart_col, data_col = st.columns([2, 1])
    
    with chart_col:
        st.subheader("Price & Technical Indicator Charts")
        
        # Main Price Chart (Candlestick + SMA)
        fig_price = go.Figure()
        fig_price.add_trace(go.Candlestick(
            x=data.index,
            open=data['Open'], high=data['High'],
            low=data['Low'], close=data['Close'],
            name="Price Actions"
        ))
        fig_price.add_trace(go.Scatter(
            x=data.index, y=data['SMA'], 
            line=dict(color='orange', width=2), 
            name=f"SMA ({sma_window})"
        ))
        fig_price.update_layout(
            title=f"{ticker} Price Chart",
            xaxis_rangeslider_visible=False,
            height=400,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_price, use_container_width=True)
        
        # RSI Chart
        fig_rsi = go.Figure()
        fig_rsi.add_trace(go.Scatter(
            x=data.index, y=data['RSI'], 
            line=dict(color='purple', width=2), 
            name="RSI"
        ))
        # RSI overbought/oversold baseline thresholds
        fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought (70)")
        fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold (30)")
        fig_rsi.update_layout(
            title="Relative Strength Index (RSI)",
            yaxis=dict(range=[0, 100]),
            height=200,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_rsi, use_container_width=True)

    with data_col:
        st.subheader("Raw Data & Metrics")
        # Display the data table
        display_df = data[['Open', 'High', 'Low', 'Close', 'Volume']].tail(10)
        st.dataframe(display_df.style.format("{:.2f}"), use_container_width=True)
        
        # Simple Rule-Based Analytical Insights
        st.subheader("Automated Technical Signal")
        latest_rsi = data['RSI'].iloc[-1]
        latest_close = data['Close'].iloc[-1]
        latest_sma = data['SMA'].iloc[-1]
        
        if latest_rsi > 70:
            st.error("⚠️ Overbought Condition: RSI is above 70. Asset might be overvalued.")
        elif latest_rsi < 30:
            st.success("✅ Oversold Condition: RSI is below 30. Asset might be undervalued.")
        else:
            st.info("Neutral Condition: RSI is currently stable between 30 and 70.")
            
        if latest_close > latest_sma:
            st.success("📈 Bullish Trend: Asset price is tracking above the Simple Moving Average.")
        else:
            st.error("📉 Bearish Trend: Asset price is falling below the Simple Moving Average.")

else:
    st.error("Invalid Ticker symbol or no data available. Please check the stock symbol and try again.")
