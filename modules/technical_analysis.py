"""
Technical Analysis Module for Geppy's TradeDay
Computes technical indicators, support/resistance, and technical signal scores.
"""

import pandas as pd
import numpy as np

def add_technical_indicators(df: pd.DataFrame, params: dict = None) -> pd.DataFrame:
    """
    Calculate and append SMA, EMA, RSI, MACD, Bollinger Bands, and ATR to price dataframe.
    """
    if df.empty or 'Close' not in df.columns:
        return df

    df = df.copy()
    close = df['Close']
    
    # Fast parameters fallback
    sma_fast = params.get("sma_fast", 20) if params else 20
    sma_slow = params.get("sma_slow", 50) if params else 50
    sma_long = params.get("sma_long", 200) if params else 200
    ema_short = params.get("ema_short", 12) if params else 12
    ema_long = params.get("ema_long", 26) if params else 26
    rsi_period = params.get("rsi_period", 14) if params else 14
    macd_signal_p = params.get("macd_signal", 9) if params else 9
    bb_period = params.get("bb_period", 20) if params else 20
    bb_std = params.get("bb_std", 2.0) if params else 2.0

    # Moving Averages
    df['SMA_Fast'] = close.rolling(window=sma_fast).mean()
    df['SMA_Slow'] = close.rolling(window=sma_slow).mean()
    df['SMA_Long'] = close.rolling(window=sma_long).mean()
    
    df['EMA_Short'] = close.ewm(span=ema_short, adjust=False).mean()
    df['EMA_Long'] = close.ewm(span=ema_long, adjust=False).mean()

    # RSI (Relative Strength Index)
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
    rs = gain / loss.replace(0, np.nan)
    df['RSI'] = 100 - (100 / (1 + rs))
    df['RSI'] = df['RSI'].fillna(50)

    # MACD (Moving Average Convergence Divergence)
    df['MACD'] = df['EMA_Short'] - df['EMA_Long']
    df['MACD_Signal'] = df['MACD'].ewm(span=macd_signal_p, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']

    # Bollinger Bands
    df['BB_Middle'] = close.rolling(window=bb_period).mean()
    bb_std_val = close.rolling(window=bb_period).std()
    df['BB_Upper'] = df['BB_Middle'] + (bb_std_val * bb_std)
    df['BB_Lower'] = df['BB_Middle'] - (bb_std_val * bb_std)
    df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle']

    # Average True Range (ATR)
    if 'High' in df.columns and 'Low' in df.columns:
        high_low = df['High'] - df['Low']
        high_close = (df['High'] - close.shift()).abs()
        low_close = (df['Low'] - close.shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['ATR'] = tr.rolling(window=14).mean()

    return df

def find_support_resistance(df: pd.DataFrame, window: int = 15) -> dict:
    """
    Identify key support and resistance price levels based on recent local minima and maxima.
    """
    if df.empty or len(df) < window * 2:
        return {"support": [], "resistance": []}

    highs = df['High'].values
    lows = df['Low'].values
    
    supports = []
    resistances = []
    
    for i in range(window, len(df) - window):
        if lows[i] == min(lows[i - window:i + window + 1]):
            supports.append(round(lows[i], 2))
        if highs[i] == max(highs[i - window:i + window + 1]):
            resistances.append(round(highs[i], 2))
            
    # Group nearby levels
    def cluster_levels(levels):
        if not levels:
            return []
        levels = sorted(levels)
        clustered = [levels[0]]
        for l in levels[1:]:
            if abs(l - clustered[-1]) / clustered[-1] > 0.015:  # 1.5% distance
                clustered.append(l)
        return clustered[-5:]  # return top 5 closest levels

    current_price = df['Close'].iloc[-1]
    supp_clustered = [s for s in cluster_levels(supports) if s < current_price]
    res_clustered = [r for r in cluster_levels(resistances) if r > current_price]
    
    return {
        "support": supp_clustered,
        "resistance": res_clustered,
        "current_price": round(current_price, 2)
    }

def analyze_technical_signals(df: pd.DataFrame) -> dict:
    """
    Generate comprehensive technical signals and composite technical score (0 to 100).
    """
    if df.empty or len(df) < 50:
        return {"score": 50, "signals": ["Insufficient price history for complete analysis"], "bias": "Neutral"}

    last = df.iloc[-1]
    prev = df.iloc[-2]
    
    score = 50
    signals = []

    # 1. Moving Average Trend Alignment
    close = last['Close']
    sma_fast = last.get('SMA_Fast')
    sma_slow = last.get('SMA_Slow')
    sma_long = last.get('SMA_Long')
    
    if pd.notnull(sma_fast) and pd.notnull(sma_slow):
        if sma_fast > sma_slow:
            score += 10
            signals.append("Short-term Uptrend (20 SMA > 50 SMA)")
        else:
            score -= 10
            signals.append("Short-term Downtrend (20 SMA < 50 SMA)")

    if pd.notnull(sma_long):
        if close > sma_long:
            score += 15
            signals.append("Bullish Long-term Regime (Price > 200 SMA)")
        else:
            score -= 15
            signals.append("Bearish Long-term Regime (Price < 200 SMA)")

    # Golden / Death Cross Check
    if pd.notnull(sma_fast) and pd.notnull(sma_slow) and pd.notnull(prev.get('SMA_Fast')):
        if prev['SMA_Fast'] <= prev['SMA_Slow'] and sma_fast > sma_slow:
            score += 15
            signals.append("🌟 Golden Cross Alert! (Fast SMA crossed above Slow SMA)")
        elif prev['SMA_Fast'] >= prev['SMA_Slow'] and sma_fast < sma_slow:
            score -= 15
            signals.append("⚠️ Death Cross Alert! (Fast SMA crossed below Slow SMA)")

    # 2. RSI Signals
    rsi = last.get('RSI', 50)
    if rsi > 70:
        score -= 10
        signals.append(f"RSI Overbought ({rsi:.1f}) - Potential pullback or strong momentum")
    elif rsi < 30:
        score += 15
        signals.append(f"RSI Oversold ({rsi:.1f}) - Potential reversal/buy zone")
    elif 50 <= rsi <= 65:
        score += 10
        signals.append(f"RSI Bullish Expansion ({rsi:.1f})")
    elif 35 <= rsi < 50:
        score -= 5
        signals.append(f"RSI Weakness ({rsi:.1f})")

    # 3. MACD Crossover Signals
    macd = last.get('MACD')
    macd_sig = last.get('MACD_Signal')
    prev_macd = prev.get('MACD')
    prev_sig = prev.get('MACD_Signal')
    
    if pd.notnull(macd) and pd.notnull(macd_sig) and pd.notnull(prev_macd):
        if prev_macd <= prev_sig and macd > macd_sig:
            score += 15
            signals.append("Bullish MACD Crossover (MACD crossed above signal line)")
        elif prev_macd >= prev_sig and macd < macd_sig:
            score -= 15
            signals.append("Bearish MACD Crossover (MACD crossed below signal line)")
        elif macd > macd_sig:
            score += 5
            signals.append("Positive MACD Momentum")
        else:
            score -= 5
            signals.append("Negative MACD Momentum")

    # 4. Bollinger Bands Positioning
    bb_up = last.get('BB_Upper')
    bb_low = last.get('BB_Lower')
    if pd.notnull(bb_up) and pd.notnull(bb_low):
        if close >= bb_up:
            signals.append("Trading near Upper Bollinger Band (High Volatility/Breakout)")
        elif close <= bb_low:
            score += 10
            signals.append("Trading near Lower Bollinger Band (Potential Support Bounce)")

    score = max(0, min(100, score))
    
    if score >= 65:
        bias = "Strong Bullish"
    elif score >= 55:
        bias = "Bullish"
    elif score <= 35:
        bias = "Strong Bearish"
    elif score <= 45:
        bias = "Bearish"
    else:
        bias = "Neutral"

    return {
        "score": score,
        "signals": signals,
        "bias": bias,
        "rsi": round(rsi, 2) if pd.notnull(rsi) else None,
        "macd_hist": round(last.get('MACD_Hist', 0), 3) if pd.notnull(last.get('MACD_Hist')) else None
    }
