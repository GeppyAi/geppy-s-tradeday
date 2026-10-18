"""
Sentiment Analysis Module for Geppy's TradeDay
Analyzes recent market news titles and summaries for bullish/bearish sentiment.
"""

import re

# Comprehensive Financial Keyword Sentiment Dictionary
BULLISH_KEYWORDS = [
    "beat", "surpassed", "outperform", "surge", "soar", "gain", "bullish", "profit", "record",
    "rally", "upgrade", "growth", "expanding", "breakout", "strong", "higher", "positive",
    "dividend", "buyback", "boost", "climb", "revenue up", "eps beat", "jump", "skyrocket"
]

BEARISH_KEYWORDS = [
    "missed", "downgrade", "decline", "fall", "drop", "bearish", "loss", "plunge", "slump",
    "lawsuit", "investigation", "cut", "warning", "weak", "lower", "negative", "recession",
    "debt", "layoffs", "default", "risk", "concern", "plummet", "tumble", "bankrupt"
]

def analyze_article_sentiment(text: str) -> float:
    """
    Score a text snippet from -1.0 (extremely negative) to +1.0 (extremely positive).
    """
    if not text:
        return 0.0
    
    text_lower = text.lower()
    pos_count = sum(1 for kw in BULLISH_KEYWORDS if kw in text_lower)
    neg_count = sum(1 for kw in BEARISH_KEYWORDS if kw in text_lower)
    
    total = pos_count + neg_count
    if total == 0:
        return 0.0
    return (pos_count - neg_count) / total

def analyze_news_sentiment(articles: list) -> dict:
    """
    Analyze a collection of news articles for a stock ticker.
    """
    if not articles:
        return {
            "score": 50,
            "sentiment": "Neutral",
            "bullish_articles": 0,
            "bearish_articles": 0,
            "neutral_articles": 0,
            "analyzed_articles": []
        }

    scores = []
    analyzed = []
    bullish_cnt = 0
    bearish_cnt = 0
    neutral_cnt = 0

    for item in articles:
        title = item.get("title", "")
        sc = analyze_article_sentiment(title)
        scores.append(sc)
        
        if sc > 0.15:
            sentiment_tag = "Bullish"
            bullish_cnt += 1
        elif sc < -0.15:
            sentiment_tag = "Bearish"
            bearish_cnt += 1
        else:
            sentiment_tag = "Neutral"
            neutral_cnt += 1

        item_copy = item.copy()
        item_copy["sentiment"] = sentiment_tag
        item_copy["score"] = sc
        analyzed.append(item_copy)

    avg_score = sum(scores) / len(scores) if scores else 0.0
    # Map avg_score (-1.0 to 1.0) to 0-100 scale
    normalized_score = round((avg_score + 1) * 50)

    if normalized_score >= 60:
        overall = "Bullish"
    elif normalized_score <= 40:
        overall = "Bearish"
    else:
        overall = "Neutral"

    return {
        "score": normalized_score,
        "sentiment": overall,
        "bullish_articles": bullish_cnt,
        "bearish_articles": bearish_cnt,
        "neutral_articles": neutral_cnt,
        "analyzed_articles": analyzed
    }
