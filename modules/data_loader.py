"""
Data Loader Module for Geppy's TradeDay
Handles fetching market data, ticker metrics, financial statements, and news via yfinance.
"""

import pandas as pd
import numpy as np
import yfinance as yf
import streamlit as st
import datetime

@st.cache_data(ttl=3600)
def fetch_stock_data(ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    """
    Fetch historical price and volume data for a given ticker.
    """
    period_map = {"1m": "1mo", "3m": "3mo", "6m": "6mo", "1y": "1y", "2y": "2y", "5y": "5y"}
    yf_period = period_map.get(period, period)
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=yf_period, interval=interval)
        if df.empty:
            return pd.DataFrame()
        df.reset_index(inplace=True)
        # Ensure Date or Datetime column is named 'Date'
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
        elif 'Datetime' in df.columns:
            df['Date'] = pd.to_datetime(df['Datetime'])
        return df
    except Exception as e:
        st.error(f"Error fetching historical data for {ticker}: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def fetch_ticker_info(ticker: str) -> dict:
    """
    Fetch fundamental key metrics and company profile for a ticker.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        if not info:
            return {}
        
        # Extract structured fundamentals with safe default handling
        return {
            "symbol": ticker.upper(),
            "shortName": info.get("shortName", ticker),
            "longName": info.get("longName", info.get("shortName", ticker)),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "marketCap": info.get("marketCap", None),
            "trailingPE": info.get("trailingPE", None),
            "forwardPE": info.get("forwardPE", None),
            "pegRatio": info.get("pegRatio", None),
            "priceToBook": info.get("priceToBook", None),
            "priceToSales": info.get("priceToSalesTrailing12Months", None),
            "profitMargins": info.get("profitMargins", None),
            "operatingMargins": info.get("operatingMargins", None),
            "revenueGrowth": info.get("revenueGrowth", None),
            "earningsGrowth": info.get("earningsGrowth", None),
            "debtToEquity": info.get("debtToEquity", None),
            "returnOnEquity": info.get("returnOnEquity", None),
            "freeCashflow": info.get("freeCashflow", None),
            "dividendYield": info.get("dividendYield", None),
            "fiftyTwoWeekHigh": info.get("fiftyTwoWeekHigh", None),
            "fiftyTwoWeekLow": info.get("fiftyTwoWeekLow", None),
            "fiftyDayAverage": info.get("fiftyDayAverage", None),
            "twoHundredDayAverage": info.get("twoHundredDayAverage", None),
            "targetMeanPrice": info.get("targetMeanPrice", None),
            "recommendationKey": info.get("recommendationKey", "N/A"),
            "summary": info.get("longBusinessSummary", "No summary available.")
        }
    except Exception as e:
        st.warning(f"Could not load fundamental info for {ticker}: {e}")
        return {}

@st.cache_data(ttl=1800)
def fetch_ticker_news(ticker: str) -> list:
    """
    Fetch latest news articles related to the ticker.
    """
    try:
        stock = yf.Ticker(ticker)
        news = stock.news
        articles = []
        if news:
            for item in news[:10]:
                # Handle varying yfinance news dictionary formats
                content = item.get("content", {})
                title = item.get("title") or content.get("title") or "No Title"
                link = item.get("link") or (content.get("canonicalUrl", {}).get("url") if isinstance(content, dict) else "")
                publisher = item.get("publisher") or (content.get("provider", {}).get("displayName") if isinstance(content, dict) else "Market News")
                pub_time = item.get("providerPublishTime") or content.get("pubDate") or ""
                
                articles.append({
                    "title": title,
                    "publisher": publisher,
                    "link": link,
                    "pubTime": pub_time
                })
        return articles
    except Exception as e:
        return []

@st.cache_data(ttl=3600)
def fetch_batch_history(tickers: list, period: str = "6m") -> dict:
    """
    Fetch history for multiple tickers for quick screening.
    """
    data_dict = {}
    for t in tickers:
        df = fetch_stock_data(t, period=period)
        if not df.empty:
            data_dict[t] = df
    return data_dict
