"""
Geppy's TradeDay - Interactive Stock Trend Analysis & AI Stock Picker
Main Streamlit Application
"""

import streamlit as st
import pandas as pd
import numpy as np
import datetime

from config import APP_TITLE, APP_ICON, PRESET_WATCHLISTS, DEFAULT_STRATEGY_WEIGHTS
from modules.data_loader import fetch_stock_data, fetch_ticker_info, fetch_ticker_news
from modules.technical_analysis import add_technical_indicators, find_support_resistance, analyze_technical_signals
from modules.fundamental_analysis import evaluate_fundamentals
from modules.sentiment_analysis import analyze_news_sentiment
from modules.stock_screener import screen_and_rank_stocks
from modules.backtester import run_backtest
from modules.visualization import create_candlestick_chart, create_score_gauge, create_backtest_chart

# Page Configuration
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border-radius: 8px;
        padding: 12px;
        border: 1px solid #E2E8F0;
    }
    .badge-buy {
        background-color: #DEF7EC;
        color: #03543F;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
    }
    .badge-avoid {
        background-color: #FDE8E8;
        color: #9B1C1C;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar Navigation & Settings
st.sidebar.image("https://img.icons8.com/color/96/000000/line-chart.png", width=70)
st.sidebar.title("TradeDay Controls")

app_mode = st.sidebar.radio(
    "Select Feature",
    ["🔥 AI Stock Picker", "📊 Ticker Deep-Dive", "🧪 Strategy Backtester", "ℹ️ Strategy Guide"]
)

st.sidebar.markdown("---")

# Main Header
st.markdown(f"<div class='main-header'>{APP_ICON} {APP_TITLE}</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-header'>Automated Trend Analysis, Fundamental Scoring, News Sentiment & Backtesting</div>", unsafe_allow_html=True)


# ==========================================
# PAGE 1: AI STOCK PICKER & SCREENER
# ==========================================
if app_mode == "🔥 AI Stock Picker":
    st.header("🔥 AI Stock Picker & Screener")
    st.write("Scan a stock universe or custom watchlist to rank top buy candidates based on combined Technical, Fundamental, and Sentiment scoring.")

    col1, col2 = st.columns([1, 2])
    with col1:
        watchlist_choice = st.selectbox("Select Watchlist Universe", list(PRESET_WATCHLISTS.keys()))
        custom_input = ""
        if watchlist_choice == "Custom Watchlist":
            custom_input = st.text_input("Enter Tickers (comma-separated)", "AAPL, NVDA, MSFT, GOOGL, AMZN, TSLA")
            tickers_to_scan = [t.strip().upper() for t in custom_input.split(",") if t.strip()]
        else:
            tickers_to_scan = PRESET_WATCHLISTS[watchlist_choice]

        scan_period = st.selectbox("Historical Lookback Period", ["3m", "6m", "1y"], index=1)

    with col2:
        st.subheader("Weighting Strategy")
        w_tech = st.slider("Technical Indicators Weight (%)", 0, 100, 40, step=5)
        w_fund = st.slider("Fundamental Health Weight (%)", 0, 100, 40, step=5)
        w_sent = st.slider("News Sentiment Weight (%)", 0, 100, 20, step=5)

        total_weight = w_tech + w_fund + w_sent
        if total_weight != 100:
            st.caption(f"⚠️ Total weight is {total_weight}%. Normalizing automatically.")

    if st.button("🚀 Run Stock Screener & Generate Picks", use_container_width=True, type="primary"):
        progress_bar = st.progress(0.0)
        status_text = st.empty()

        def update_prog(ratio, msg):
            progress_bar.progress(ratio)
            status_text.text(msg)

        norm_weights = {
            "technical": w_tech / (total_weight or 1),
            "fundamental": w_fund / (total_weight or 1),
            "sentiment": w_sent / (total_weight or 1)
        }

        results_df = screen_and_rank_stocks(tickers_to_scan, weights=norm_weights, period=scan_period, progress_callback=update_prog)
        progress_bar.empty()
        status_text.empty()

        if not results_df.empty:
            st.subheader(f"🏆 Ranked Stock Picks ({len(results_df)} Stocks Analyzed)")

            # Top Pick Cards
            top_picks = results_df.head(3)
            st.markdown("### 🌟 Top 3 Ranked Stock Picks")
            card_cols = st.columns(min(3, len(top_picks)))
            for idx, (_, row) in enumerate(top_picks.iterrows()):
                with card_cols[idx]:
                    st.metric(
                        label=f"#{idx+1} {row['Ticker']} ({row['Company']})",
                        value=f"${row['Price']}",
                        delta=f"{row['Return (%)']}% (Period)"
                    )
                    st.markdown(f"**Score:** `{row['Composite Score']}/100` | **Rating:** `{row['Pick Rating']}`")
                    st.caption(f"Rationale: {row['Key Rationale']}")

            st.markdown("---")
            st.subheader("📋 Full Watchlist Rankings")
            
            # Formatted Dataframe Display
            try:
                styled_df = results_df.style.background_gradient(subset=["Composite Score"], cmap="Greens")
            except Exception:
                styled_df = results_df

            st.dataframe(
                styled_df,
                column_config={
                    "Composite Score": st.column_config.NumberColumn("Composite Score", format="%.1f"),
                    "Return (%)": st.column_config.NumberColumn("Return (%)", format="%.1f%%"),
                    "Price": st.column_config.NumberColumn("Price ($)", format="$%.2f")
                },
                use_container_width=True
            )
        else:
            st.error("No valid stock data could be retrieved for the specified tickers.")


# ==========================================
# PAGE 2: TICKER DEEP-DIVE
# ==========================================
elif app_mode == "📊 Ticker Deep-Dive":
    st.header("📊 Ticker Deep-Dive Analysis")

    search_col1, search_col2 = st.columns([1, 3])
    with search_col1:
        ticker = st.text_input("Enter Ticker Symbol", "NVDA").upper().strip()
    with search_col2:
        period = st.selectbox("Chart Timeframe", ["1m", "3m", "6m", "1y", "2y", "5y"], index=3)

    if ticker:
        with st.spinner(f"Fetching market data for {ticker}..."):
            df = fetch_stock_data(ticker, period=period)
            info = fetch_ticker_info(ticker)
            news = fetch_ticker_news(ticker)

        if not df.empty:
            df = add_technical_indicators(df)
            tech_res = analyze_technical_signals(df)
            fund_res = evaluate_fundamentals(info)
            sent_res = analyze_news_sentiment(news)
            supp_res = find_support_resistance(df)

            # Header Overview
            cur_price = df['Close'].iloc[-1]
            prev_close = df['Close'].iloc[-2] if len(df) > 1 else cur_price
            price_chg = cur_price - prev_close
            pct_chg = (price_chg / prev_close) * 100

            st.title(f"{info.get('longName', ticker)} ({ticker})")
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Current Price", f"${cur_price:.2f}", f"{price_chg:+.2f} ({pct_chg:+.2f}%)")
            m2.metric("Market Cap", f"${info.get('marketCap', 0)/1e9:.2f}B" if info.get('marketCap') else "N/A")
            m3.metric("P/E Ratio", f"{info.get('trailingPE'):.1f}" if info.get('trailingPE') else "N/A")
            m4.metric("Technical Score", f"{tech_res['score']}/100", tech_res['bias'])
            m5.metric("Fundamental Grade", fund_res['rating'], f"Score: {fund_res['score']}")

            st.markdown("---")

            # Main Chart & Score Breakdown
            c_chart, c_score = st.columns([3, 1])
            with c_chart:
                fig_candlestick = create_candlestick_chart(df, ticker, supp_res)
                st.plotly_chart(fig_candlestick, use_container_width=True)

            with c_score:
                st.subheader("Composite Score")
                comp_score = round(tech_res['score']*0.4 + fund_res['score']*0.4 + sent_res['score']*0.2, 1)
                fig_gauge = create_score_gauge(tech_res['score'], fund_res['score'], sent_res['score'], comp_score)
                st.plotly_chart(fig_gauge, use_container_width=True)

                st.subheader("Key Support / Resistance")
                st.write("**Support Levels:**", ", ".join([f"${s}" for s in supp_res['support']]) or "None detected")
                st.write("**Resistance Levels:**", ", ".join([f"${r}" for r in supp_res['resistance']]) or "None detected")

                st.subheader("Technical Signal Digest")
                for sig in tech_res['signals']:
                    st.markdown(f"• {sig}")

            st.markdown("---")

            # Detailed Metrics Tabs
            t_fund, t_news, t_raw = st.tabs(["🏛️ Fundamental Details", "📰 News & Sentiment", "📋 Raw Data"])

            with t_fund:
                f_col1, f_col2 = st.columns(2)
                with f_col1:
                    st.markdown("#### Key Valuation & Health Ratios")
                    st.write(f"**Trailing P/E:** {info.get('trailingPE', 'N/A')}")
                    st.write(f"**Forward P/E:** {info.get('forwardPE', 'N/A')}")
                    st.write(f"**PEG Ratio:** {info.get('pegRatio', 'N/A')}")
                    st.write(f"**Price to Book:** {info.get('priceToBook', 'N/A')}")
                    st.write(f"**Debt to Equity:** {info.get('debtToEquity', 'N/A')}")
                with f_col2:
                    st.markdown("#### Growth & Profitability")
                    st.write(f"**Profit Margin:** {info.get('profitMargins', 0)*100:.1f}%" if info.get('profitMargins') else "N/A")
                    st.write(f"**Return on Equity (ROE):** {info.get('returnOnEquity', 0)*100:.1f}%" if info.get('returnOnEquity') else "N/A")
                    st.write(f"**YoY Revenue Growth:** {info.get('revenueGrowth', 0)*100:.1f}%" if info.get('revenueGrowth') else "N/A")
                    st.write(f"**YoY Earnings Growth:** {info.get('earningsGrowth', 0)*100:.1f}%" if info.get('earningsGrowth') else "N/A")

                st.markdown("#### Fundamental Analysis Summary")
                for h in fund_res['highlights']:
                    st.markdown(f"✓ {h}")

            with t_news:
                st.markdown(f"### News Sentiment Analysis ({sent_res['sentiment']})")
                s_col1, s_col2, s_col3 = st.columns(3)
                s_col1.metric("Bullish News Count", sent_res['bullish_articles'])
                s_col2.metric("Neutral News Count", sent_res['neutral_articles'])
                s_col3.metric("Bearish News Count", sent_res['bearish_articles'])

                for article in sent_res['analyzed_articles']:
                    st.write(f"[{article['title']}]({article['link']}) — *{article['publisher']}* (`{article['sentiment']}`)")

            with t_raw:
                st.dataframe(df.tail(50), use_container_width=True)

        else:
            st.error(f"Could not load market data for ticker '{ticker}'. Please check the symbol.")


# ==========================================
# PAGE 3: STRATEGY BACKTESTER
# ==========================================
elif app_mode == "🧪 Strategy Backtester":
    st.header("🧪 Historical Strategy Backtester")
    st.write("Test rule-based trading strategies against past stock market performance to verify win rate, returns, and drawdown.")

    bt_col1, bt_col2, bt_col3 = st.columns(3)
    with bt_col1:
        bt_ticker = st.text_input("Backtest Ticker", "NVDA").upper().strip()
        bt_period = st.selectbox("Backtest History Length", ["6m", "1y", "2y", "5y"], index=2)
    with bt_col2:
        bt_strategy = st.selectbox("Trading Strategy", ["MA_Crossover", "RSI_Reversal", "Bollinger_Breakout"])
        bt_capital = st.number_input("Initial Capital ($)", value=10000.0, step=1000.0)
    with bt_col3:
        st.subheader("Strategy Description")
        if bt_strategy == "MA_Crossover":
            st.caption("Buy when Fast Moving Average (20) crosses above Slow Moving Average (50). Sell on cross below.")
        elif bt_strategy == "RSI_Reversal":
            st.caption("Buy when RSI drops below 35 (Oversold). Sell when RSI crosses above 65 (Overbought).")
        elif bt_strategy == "Bollinger_Breakout":
            st.caption("Buy when price touches/crosses Lower Bollinger Band. Sell when price touches Upper Band.")

    if st.button("▶️ Run Strategy Backtest", type="primary", use_container_width=True):
        with st.spinner(f"Running backtest for {bt_ticker}..."):
            df = fetch_stock_data(bt_ticker, period=bt_period)
            if not df.empty:
                results = run_backtest(df, strategy=bt_strategy, initial_capital=bt_capital)
                
                if "error" in results:
                    st.error(results["error"])
                else:
                    st.success(f"Backtest Complete for {bt_ticker} ({bt_period})")

                    m1, m2, m3, m4, m5 = st.columns(5)
                    m1.metric("Strategy Return", f"{results['strategy_return_pct']}%", f"${results['final_value']:,.2f}")
                    m2.metric("Buy & Hold Return", f"{results['buy_hold_return_pct']}%")
                    m3.metric("Win Rate", f"{results['win_rate_pct']}%", f"{results['total_trades']} Trades")
                    m4.metric("Max Drawdown", f"{results['max_drawdown_pct']}%")
                    m5.metric("Sharpe Ratio", f"{results['sharpe_ratio']}")

                    st.plotly_chart(create_backtest_chart(results['equity_df']), use_container_width=True)

                    if results['trades']:
                        st.subheader("📜 Detailed Trade Log")
                        st.dataframe(pd.DataFrame(results['trades']), use_container_width=True)
            else:
                st.error(f"Could not load historical data for {bt_ticker}.")


# ==========================================
# PAGE 4: STRATEGY GUIDE
# ==========================================
elif app_mode == "ℹ️ Strategy Guide":
    st.header("ℹ️ TradeDay Strategy & Technical Guide")
    st.markdown("""
    ### How Geppy's TradeDay Stock Picks Work
    TradeDay evaluates stocks across **3 Core Pillars**:

    1. **Technical Indicators (40% default weight)**
       - **Moving Averages (SMA 20, 50, 200)**: Golden Cross (20 SMA crossing 50 SMA upward) signals bullish momentum.
       - **RSI (14)**: Measures velocity of price movements. Values below 30 indicate oversold buy conditions, while values above 70 indicate overbought conditions.
       - **MACD**: Identifies changes in the strength, direction, momentum, and duration of a trend.
       - **Bollinger Bands**: Highlights price volatility and support/resistance boundaries.

    2. **Fundamental Scoring (40% default weight)**
       - **Valuation**: Trailing P/E, Forward P/E, PEG Ratio, and Price/Book.
       - **Growth**: YoY Revenue Growth and Earnings (EPS) Growth.
       - **Health**: Profit Margins, Return on Equity (ROE), and Debt-to-Equity ratio.

    3. **News Sentiment (20% default weight)**
       - Scrapes latest news headlines for the stock.
       - Runs natural language sentiment keyword scoring to detect market sentiment (Bullish vs Bearish).

    ---
    *Disclaimer: Geppy's TradeDay is for educational and research purposes only. Always consult a financial advisor before investing.*
    """)
