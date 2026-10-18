"""
Backtesting Engine for Geppy's TradeDay
Simulates trading strategies on historical price data and evaluates performance.
"""

import pandas as pd
import numpy as np
from modules.technical_analysis import add_technical_indicators

def run_backtest(df: pd.DataFrame, strategy: str = "MA_Crossover", initial_capital: float = 10000.0, params: dict = None) -> dict:
    """
    Run backtest on a ticker's historical dataframe.
    """
    if df.empty or len(df) < 60:
        return {"error": "Insufficient data for backtesting"}

    df = add_technical_indicators(df, params)
    
    cash = initial_capital
    position = 0.0  # shares held
    entry_price = 0.0
    entry_date = None

    equity_curve = []
    trades = []

    for i in range(len(df)):
        row = df.iloc[i]
        date = row['Date']
        close = row['Close']
        
        # Determine Signal based on selected strategy
        buy_signal = False
        sell_signal = False

        if strategy == "MA_Crossover":
            sma_f = row.get('SMA_Fast')
            sma_s = row.get('SMA_Slow')
            if pd.notnull(sma_f) and pd.notnull(sma_s):
                if sma_f > sma_s:
                    buy_signal = True
                else:
                    sell_signal = True

        elif strategy == "RSI_Reversal":
            rsi = row.get('RSI', 50)
            if rsi < 35:
                buy_signal = True
            elif rsi > 65:
                sell_signal = True

        elif strategy == "Bollinger_Breakout":
            bb_low = row.get('BB_Lower')
            bb_up = row.get('BB_Upper')
            if pd.notnull(bb_low) and close <= bb_low * 1.01:
                buy_signal = True
            elif pd.notnull(bb_up) and close >= bb_up * 0.99:
                sell_signal = True

        # Execution logic (simple market on close)
        if buy_signal and position == 0:
            position = cash / close
            cash = 0.0
            entry_price = close
            entry_date = date
        elif sell_signal and position > 0:
            exit_price = close
            cash = position * exit_price
            pnl = (exit_price - entry_price) / entry_price * 100
            trades.append({
                "entry_date": entry_date.strftime("%Y-%m-%d") if hasattr(entry_date, "strftime") else str(entry_date),
                "exit_date": date.strftime("%Y-%m-%d") if hasattr(date, "strftime") else str(date),
                "entry_price": round(entry_price, 2),
                "exit_price": round(exit_price, 2),
                "return_pct": round(pnl, 2),
                "win": pnl > 0
            })
            position = 0.0
            entry_price = 0.0
            entry_date = None

        current_value = cash if position == 0 else position * close
        equity_curve.append({
            "Date": date,
            "Strategy_Value": current_value,
            "BuyHold_Value": (initial_capital / df['Close'].iloc[0]) * close
        })

    # Close open position at end of period for metric calculation
    if position > 0:
        last_row = df.iloc[-1]
        exit_price = last_row['Close']
        cash = position * exit_price
        pnl = (exit_price - entry_price) / entry_price * 100
        trades.append({
            "entry_date": entry_date.strftime("%Y-%m-%d") if hasattr(entry_date, "strftime") else str(entry_date),
            "exit_date": last_row['Date'].strftime("%Y-%m-%d") if hasattr(last_row['Date'], "strftime") else str(last_row['Date']),
            "entry_price": round(entry_price, 2),
            "exit_price": round(exit_price, 2),
            "return_pct": round(pnl, 2),
            "win": pnl > 0
        })

    equity_df = pd.DataFrame(equity_curve)

    # Compute key stats
    final_val = equity_df['Strategy_Value'].iloc[-1]
    bh_final_val = equity_df['BuyHold_Value'].iloc[-1]

    strat_return = ((final_val - initial_capital) / initial_capital) * 100
    bh_return = ((bh_final_val - initial_capital) / initial_capital) * 100

    total_trades = len(trades)
    winning_trades = sum(1 for t in trades if t['win'])
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0

    # Max Drawdown calculation
    equity_df['Peak'] = equity_df['Strategy_Value'].cummax()
    equity_df['Drawdown'] = (equity_df['Strategy_Value'] - equity_df['Peak']) / equity_df['Peak'] * 100
    max_drawdown = equity_df['Drawdown'].min()

    # Sharpe ratio estimate (daily returns)
    daily_returns = equity_df['Strategy_Value'].pct_change().dropna()
    sharpe_ratio = (daily_returns.mean() / daily_returns.std() * np.sqrt(252)) if not daily_returns.empty and daily_returns.std() != 0 else 0.0

    return {
        "initial_capital": initial_capital,
        "final_value": round(final_val, 2),
        "strategy_return_pct": round(strat_return, 2),
        "buy_hold_return_pct": round(bh_return, 2),
        "total_trades": total_trades,
        "win_rate_pct": round(win_rate, 1),
        "max_drawdown_pct": round(max_drawdown, 2),
        "sharpe_ratio": round(sharpe_ratio, 2),
        "trades": trades,
        "equity_df": equity_df
    }
