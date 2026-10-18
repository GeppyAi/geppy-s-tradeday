"""
Test module execution for Geppy's TradeDay
"""
import sys
import os

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules.data_loader import fetch_stock_data, fetch_ticker_info, fetch_ticker_news
from modules.technical_analysis import add_technical_indicators, analyze_technical_signals, find_support_resistance
from modules.fundamental_analysis import evaluate_fundamentals
from modules.sentiment_analysis import analyze_news_sentiment
from modules.backtester import run_backtest
from modules.stock_screener import screen_and_rank_stocks

def run_tests():
    print("--- Testing Ticker Data Fetch ---")
    ticker = "AAPL"
    df = fetch_stock_data(ticker, period="3m")
    print(f"Fetched {len(df)} rows for {ticker}")
    assert not df.empty, "DataFrame should not be empty"

    print("--- Testing Technical Analysis ---")
    df_tech = add_technical_indicators(df)
    signals = analyze_technical_signals(df_tech)
    supp_res = find_support_resistance(df_tech)
    print("Technical Score:", signals["score"], "Bias:", signals["bias"])
    print("Support/Resistance:", supp_res)

    print("--- Testing Fundamental Evaluation ---")
    info = fetch_ticker_info(ticker)
    fund_res = evaluate_fundamentals(info)
    print("Fundamental Rating:", fund_res["rating"], "Score:", fund_res["score"])

    print("--- Testing News Sentiment ---")
    news = fetch_ticker_news(ticker)
    sent_res = analyze_news_sentiment(news)
    print("Sentiment Score:", sent_res["score"], "Overall:", sent_res["sentiment"])

    print("--- Testing Backtester ---")
    bt_res = run_backtest(df, strategy="MA_Crossover", initial_capital=10000.0)
    print("Backtest Return:", bt_res["strategy_return_pct"], "Win Rate:", bt_res["win_rate_pct"])

    print("--- Testing Screener ---")
    rankings = screen_and_rank_stocks(["AAPL", "NVDA", "MSFT"], period="3m")
    print("Rankings DataFrame:")
    for _, row in rankings.iterrows():
        print(f"Ticker: {row['Ticker']} | Score: {row['Composite Score']} | Rating: {row['Pick Rating'].encode('ascii', 'ignore').decode('ascii')}")

    print("\nALL MODULE TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
