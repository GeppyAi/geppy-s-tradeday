"""
Visualization Module for Geppy's TradeDay
Generates interactive Plotly charts for prices, technical indicators, backtest results, and score radar graphs.
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

def create_candlestick_chart(df: pd.DataFrame, ticker: str, supp_res: dict = None) -> go.Figure:
    """
    Create a comprehensive main candlestick chart with SMA overlays, Bollinger Bands, Volume, RSI, and MACD subplots.
    """
    if df.empty:
        return go.Figure()

    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        subplot_titles=(f"{ticker} - Price & Moving Averages", "RSI (Relative Strength Index)", "MACD"),
        row_heights=[0.60, 0.20, 0.20]
    )

    # 1. Candlesticks
    fig.add_trace(
        go.Candlestick(
            x=df['Date'],
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name="Price"
        ),
        row=1, col=1
    )

    # 2. Moving Averages
    if 'SMA_Fast' in df.columns:
        fig.add_trace(go.Scatter(x=df['Date'], y=df['SMA_Fast'], line=dict(color='orange', width=1.5), name="20 SMA"), row=1, col=1)
    if 'SMA_Slow' in df.columns:
        fig.add_trace(go.Scatter(x=df['Date'], y=df['SMA_Slow'], line=dict(color='blue', width=1.5), name="50 SMA"), row=1, col=1)
    if 'SMA_Long' in df.columns:
        fig.add_trace(go.Scatter(x=df['Date'], y=df['SMA_Long'], line=dict(color='purple', width=1.5), name="200 SMA"), row=1, col=1)

    # 3. Bollinger Bands
    if 'BB_Upper' in df.columns and 'BB_Lower' in df.columns:
        fig.add_trace(go.Scatter(x=df['Date'], y=df['BB_Upper'], line=dict(color='gray', dash='dash', width=1), name="Upper BB"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df['Date'], y=df['BB_Lower'], line=dict(color='gray', dash='dash', width=1), fill='tonexty', fillcolor='rgba(200,200,200,0.1)', name="Lower BB"), row=1, col=1)

    # Support / Resistance Horizontal Lines
    if supp_res:
        for s in supp_res.get("support", []):
            fig.add_hline(y=s, line_color="green", line_dash="dot", opacity=0.7, annotation_text=f"Support ${s:.2f}", row=1, col=1)
        for r in supp_res.get("resistance", []):
            fig.add_hline(y=r, line_color="red", line_dash="dot", opacity=0.7, annotation_text=f"Resistance ${r:.2f}", row=1, col=1)

    # 4. RSI Subplot
    if 'RSI' in df.columns:
        fig.add_trace(go.Scatter(x=df['Date'], y=df['RSI'], line=dict(color='purple', width=1.5), name="RSI"), row=2, col=1)
        fig.add_hline(y=70, line_color="red", line_dash="dash", row=2, col=1)
        fig.add_hline(y=30, line_color="green", line_dash="dash", row=2, col=1)

    # 5. MACD Subplot
    if 'MACD' in df.columns and 'MACD_Signal' in df.columns:
        fig.add_trace(go.Scatter(x=df['Date'], y=df['MACD'], line=dict(color='blue', width=1.5), name="MACD"), row=3, col=1)
        fig.add_trace(go.Scatter(x=df['Date'], y=df['MACD_Signal'], line=dict(color='orange', width=1.5), name="Signal"), row=3, col=1)
        colors = ['green' if val >= 0 else 'red' for val in df['MACD_Hist']]
        fig.add_trace(go.Bar(x=df['Date'], y=df['MACD_Hist'], marker_color=colors, name="Hist"), row=3, col=1)

    fig.update_layout(
        template="plotly_white",
        height=800,
        margin=dict(l=40, r=40, t=60, b=40),
        xaxis_rangeslider_visible=False,
        hovermode="x unified"
    )

    return fig

def create_score_gauge(tech: float, fund: float, sent: float, composite: float) -> go.Figure:
    """
    Create a multi-metric horizontal bar / score overview figure.
    """
    categories = ['Technical', 'Fundamental', 'Sentiment', 'Overall Pick']
    scores = [tech, fund, sent, composite]
    colors = ['#1f77b4', '#2ca02c', '#ff7f0e', '#9467bd']

    fig = go.Figure(go.Bar(
        x=scores,
        y=categories,
        orientation='h',
        marker=dict(color=colors),
        text=[f"{s}/100" for s in scores],
        textposition='auto'
    ))

    fig.update_layout(
        title="Stock Pick Score Breakdown",
        xaxis=dict(range=[0, 100]),
        template="plotly_white",
        height=300,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    return fig

def create_backtest_chart(equity_df: pd.DataFrame) -> go.Figure:
    """
    Create equity curve comparison chart for Backtest results.
    """
    if equity_df.empty:
        return go.Figure()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=equity_df['Date'], y=equity_df['Strategy_Value'], line=dict(color='green', width=2), name="Strategy Portfolio ($)"))
    fig.add_trace(go.Scatter(x=equity_df['Date'], y=equity_df['BuyHold_Value'], line=dict(color='gray', dash='dash', width=1.5), name="Buy & Hold Benchmark ($)"))

    fig.update_layout(
        title="Portfolio Growth ($10,000 Initial Investment)",
        template="plotly_white",
        height=450,
        xaxis_title="Date",
        yaxis_title="Portfolio Value ($)",
        hovermode="x unified"
    )
    return fig
