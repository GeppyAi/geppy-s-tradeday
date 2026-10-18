"""
Geppy's TradeDay - App Configuration & Presets
"""

APP_TITLE = "Geppy's TradeDay - Stock Analysis & AI Stock Picker"
APP_ICON = "📈"

# Default Stock Watchlists / Preset Universe
PRESET_WATCHLISTS = {
    "Popular Tech & Growth": ["AAPL", "NVDA", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "AMD", "NFLX", "PLTR"],
    "Blue Chip Dividend & Value": ["JNJ", "PG", "KO", "PEP", "XOM", "CVX", "JPM", "BAC", "WMT", "COST"],
    "High Momentum & AI Stocks": ["NVDA", "AVGO", "SMCI", "ARM", "PLTR", "TSM", "ORCL", "PANW", "CRWD", "NOW"],
    "Major ETFs & Indices": ["SPY", "QQQ", "IWM", "DIA", "XLK", "XLF", "XLV", "XLE", "SMH"],
    "Custom Watchlist": ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA"]
}

# Technical Indicator Defaults
DEFAULT_INDICATOR_PARAMS = {
    "sma_fast": 20,
    "sma_slow": 50,
    "sma_long": 200,
    "ema_short": 12,
    "ema_long": 26,
    "rsi_period": 14,
    "rsi_overbought": 70,
    "rsi_oversold": 30,
    "macd_signal": 9,
    "bb_period": 20,
    "bb_std": 2.0
}

# Stock Picker Scoring Weights
DEFAULT_STRATEGY_WEIGHTS = {
    "trend_momentum": 35,
    "rsi_valuation": 25,
    "fundamental_health": 25,
    "sentiment_news": 15
}
