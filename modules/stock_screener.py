"""
Stock Screener & AI Picker Engine for Geppy's TradeDay
Ranks stocks across technical, fundamental, and sentiment factors to generate recommended stock picks.
"""

import pandas as pd
import numpy as np
from modules.data_loader import fetch_stock_data, fetch_ticker_info, fetch_ticker_news
from modules.technical_analysis import add_technical_indicators, analyze_technical_signals
from modules.fundamental_analysis import evaluate_fundamentals
from modules.sentiment_analysis import analyze_news_sentiment

def screen_and_rank_stocks(tickers: list, weights: dict = None, period: str = "6mo", progress_callback=None) -> pd.DataFrame:
    """
    Screen a list of tickers and compute composite ratings & recommendations.
    """
    if weights is None:
        weights = {"technical": 0.40, "fundamental": 0.40, "sentiment": 0.20}

    # Map friendly period format to yfinance period strings
    period_map = {"1m": "1mo", "3m": "3mo", "6m": "6mo", "1y": "1y", "2y": "2y", "5y": "5y"}
    yf_period = period_map.get(period, period)

    results = []
    total = len(tickers)

    for idx, ticker in enumerate(tickers):
        if progress_callback:
            progress_callback((idx + 1) / total, f"Analyzing {ticker} ({idx+1}/{total})...")

        ticker = ticker.strip().upper()
        
        # 1. Fetch History & Technicals
        df = fetch_stock_data(ticker, period=yf_period)
        if df.empty or len(df) < 20:
            continue
            
        df = add_technical_indicators(df)
        tech_res = analyze_technical_signals(df)
        tech_score = tech_res["score"]
        
        # Current price & 6-month price return
        current_price = df['Close'].iloc[-1]
        start_price = df['Close'].iloc[0]
        period_return = ((current_price - start_price) / start_price) * 100

        # 2. Fetch Fundamentals
        info = fetch_ticker_info(ticker)
        fund_res = evaluate_fundamentals(info)
        fund_score = fund_res["score"]

        # 3. Sentiment Analysis
        news = fetch_ticker_news(ticker)
        sent_res = analyze_news_sentiment(news)
        sent_score = sent_res["score"]

        # 4. Calculate Weighted Composite Score (0 - 100)
        w_tech = weights.get("technical", 0.40)
        w_fund = weights.get("fundamental", 0.40)
        w_sent = weights.get("sentiment", 0.20)

        composite_score = round(
            (tech_score * w_tech) + (fund_score * w_fund) + (sent_score * w_sent), 1
        )

        # 5. Recommendation Action
        if composite_score >= 72:
            action = "🔥 Strong Buy Pick"
        elif composite_score >= 60:
            action = "BUY Buy / Accumulate"
        elif composite_score >= 45:
            action = "HOLD Hold / Watch"
        elif composite_score >= 35:
            action = "SELL Weak / Trim"
        else:
            action = "⚠️ Strong Avoid"

        # Key Reason Bullet
        primary_reason = []
        if tech_res.get("bias") in ["Strong Bullish", "Bullish"]:
            primary_reason.append(f"Bullish Technicals ({tech_res['bias']})")
        if fund_res.get("rating") in ["A (Excellent)", "B (Good)"]:
            primary_reason.append(f"Solid Fundamentals ({fund_res['rating']})")
        if sent_res.get("sentiment") == "Bullish":
            primary_reason.append("Positive News Sentiment")
        
        reason_str = " | ".join(primary_reason) if primary_reason else "Balanced Market Metrics"

        results.append({
            "Ticker": ticker,
            "Company": info.get("shortName", ticker),
            "Sector": info.get("sector", "N/A"),
            "Price": round(current_price, 2),
            "Return (%)": round(period_return, 1),
            "Composite Score": composite_score,
            "Pick Rating": action,
            "Tech Score": tech_score,
            "Fund Score": fund_score,
            "Sent Score": sent_score,
            "Key Rationale": reason_str,
            "P/E": info.get("trailingPE"),
            "RSI": tech_res.get("rsi")
        })

    results_df = pd.DataFrame(results)
    if not results_df.empty:
        results_df = results_df.sort_values(by="Composite Score", ascending=False).reset_index(drop=True)
    return results_df
