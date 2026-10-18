"""
Fundamental Analysis Module for Geppy's TradeDay
Evaluates company valuation, financial health, growth, and fundamental score.
"""

def evaluate_fundamentals(info: dict) -> dict:
    """
    Score fundamental metrics on a scale of 0 to 100 based on valuation, profitability, growth, and balance sheet health.
    """
    if not info:
        return {
            "score": 50,
            "rating": "N/A",
            "valuation_score": 50,
            "growth_score": 50,
            "health_score": 50,
            "highlights": ["No fundamental data available"]
        }

    highlights = []
    
    # 1. Valuation Metrics (Max 35 pts)
    val_score = 15
    pe = info.get("trailingPE")
    fwd_pe = info.get("forwardPE")
    peg = info.get("pegRatio")
    pb = info.get("priceToBook")
    
    if pe is not None and pe > 0:
        if pe < 15:
            val_score += 10
            highlights.append(f"Low Valuation: Trailing P/E is attractive at {pe:.1f}")
        elif pe < 25:
            val_score += 6
            highlights.append(f"Moderate Valuation: Trailing P/E is {pe:.1f}")
        elif pe > 50:
            val_score -= 5
            highlights.append(f"High Valuation Warning: Trailing P/E is {pe:.1f}")

    if fwd_pe is not None and pe is not None and fwd_pe < pe:
        val_score += 5
        highlights.append(f"Forward P/E ({fwd_pe:.1f}) is lower than Trailing P/E ({pe:.1f}), indicating expected earnings growth")

    if peg is not None and 0 < peg < 1.5:
        val_score += 5
        highlights.append(f"Attractive Growth-at-Value: PEG ratio is {peg:.2f}")

    val_score = max(0, min(35, val_score))

    # 2. Profitability & Health Metrics (Max 35 pts)
    health_score = 15
    profit_margin = info.get("profitMargins")
    roe = info.get("returnOnEquity")
    debt_equity = info.get("debtToEquity")

    if profit_margin is not None:
        if profit_margin > 0.20:
            health_score += 10
            highlights.append(f"Strong Profitability: Profit margin of {profit_margin*100:.1f}%")
        elif profit_margin > 0.10:
            health_score += 5
        elif profit_margin < 0:
            health_score -= 8
            highlights.append(f"Unprofitable: Negative profit margin ({profit_margin*100:.1f}%)")

    if roe is not None:
        if roe > 0.15:
            health_score += 5
            highlights.append(f"High Return on Equity: ROE is {roe*100:.1f}%")

    if debt_equity is not None:
        if debt_equity < 80:
            health_score += 5
            highlights.append(f"Healthy Balance Sheet: Debt to Equity is low ({debt_equity:.1f}%)")
        elif debt_equity > 200:
            health_score -= 5
            highlights.append(f"High Financial Leverage: Debt to Equity is high ({debt_equity:.1f}%)")

    health_score = max(0, min(35, health_score))

    # 3. Growth Metrics (Max 30 pts)
    growth_score = 15
    rev_growth = info.get("revenueGrowth")
    eps_growth = info.get("earningsGrowth")

    if rev_growth is not None:
        if rev_growth > 0.20:
            growth_score += 8
            highlights.append(f"High Revenue Expansion: YoY Revenue growth is +{rev_growth*100:.1f}%")
        elif rev_growth > 0.05:
            growth_score += 4
        elif rev_growth < 0:
            growth_score -= 5
            highlights.append(f"Revenue Contraction: YoY Revenue growth is {rev_growth*100:.1f}%")

    if eps_growth is not None:
        if eps_growth > 0.15:
            growth_score += 7
            highlights.append(f"Strong Earnings Growth: YoY Earnings growth is +{eps_growth*100:.1f}%")
        elif eps_growth < 0:
            growth_score -= 5

    growth_score = max(0, min(30, growth_score))

    total_score = round(val_score + health_score + growth_score)
    
    if total_score >= 80:
        rating = "A (Excellent)"
    elif total_score >= 65:
        rating = "B (Good)"
    elif total_score >= 50:
        rating = "C (Average)"
    elif total_score >= 35:
        rating = "D (Below Average)"
    else:
        rating = "F (Weak)"

    return {
        "score": total_score,
        "rating": rating,
        "valuation_score": round(val_score * (100/35)),
        "growth_score": round(growth_score * (100/30)),
        "health_score": round(health_score * (100/35)),
        "highlights": highlights
    }
