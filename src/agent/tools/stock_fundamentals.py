from typing import Any

import yfinance as yf
from langchain_core.tools import tool


@tool("fetch_stock_fundamentals", parse_docstring=True)
def fetch_stock_fundamentals(symbol: str) -> dict[str, Any]:
    """Fetch stock fundamentals for a given symbol.

    Args:
    symbol : str
        The stock symbol to fetch fundamentals for.

    Returns:
    dict[str, Any]
        A dictionary containing the stock fundamentals or an error message.
    """
    if not symbol:
        return {
            "query": symbol,
            "error": "Missing required argument: symbol"
        }
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        if not info or "shortName" not in info:
            return {"error": f"No data found for symbol: {symbol}"}
        report = _format_report(info)
        return {
            "query": symbol,
            "report": report
        }
    except Exception as e:
        return {
            "query": symbol,
            "error": str(e)
        }

def _format_report(info: dict) -> str:
    def safe(val, default="N/A"):
        return val if val is not None else default

    lines = []
    lines.append(f"# {safe(info.get('shortName'))} ({safe(info.get('symbol'))}) - Trading Fundamentals Report\n")

    # 1. Company Overview
    lines.append("## 1. Company Overview")
    lines.append(f"- Sector: {safe(info.get('sector'))}")
    lines.append(f"- Industry: {safe(info.get('industry'))}")
    lines.append(f"- Market Cap: {safe(info.get('marketCap')):,}" if info.get('marketCap') else "- Market Cap: N/A")
    lines.append(f"- Description: {safe(info.get('longBusinessSummary'))}\n")

    # 2. Valuation Metrics
    lines.append("## 2. Valuation Metrics")
    lines.append(f"- P/E Ratio: {safe(info.get('trailingPE'))}")
    lines.append(f"- P/B Ratio: {safe(info.get('priceToBook'))}")
    lines.append(f"- EV/EBITDA: {safe(info.get('enterpriseToEbitda'))}")
    lines.append(f"- Dividend Yield: {safe(info.get('dividendYield'))}\n")

    # 3. Growth & Profitability
    lines.append("## 3. Growth & Profitability")
    lines.append(f"- Revenue Growth (YoY): {safe(info.get('revenueGrowth'))}")
    lines.append(f"- EPS Growth (YoY): {safe(info.get('earningsQuarterlyGrowth'))}")
    lines.append(f"- ROE: {safe(info.get('returnOnEquity'))}")
    lines.append(f"- ROA: {safe(info.get('returnOnAssets'))}")
    lines.append(f"- Gross Margins: {safe(info.get('grossMargins'))}")
    lines.append(f"- Operating Margins: {safe(info.get('operatingMargins'))}\n")

    # 4. Financial Health
    lines.append("## 4. Financial Health")
    lines.append(f"- Debt/Equity: {safe(info.get('debtToEquity'))}")
    lines.append(f"- Current Ratio: {safe(info.get('currentRatio'))}")
    lines.append(f"- Free Cash Flow: {safe(info.get('freeCashflow'))}")
    lines.append(f"- Total Cash: {safe(info.get('totalCash'))}")
    lines.append(f"- Total Debt: {safe(info.get('totalDebt'))}\n")

    # 5. Recent Performance
    lines.append("## 5. Recent Performance")
    lines.append(f"- 52 Week High: {safe(info.get('fiftyTwoWeekHigh'))}")
    lines.append(f"- 52 Week Low: {safe(info.get('fiftyTwoWeekLow'))}")
    lines.append(f"- 50 Day Moving Avg: {safe(info.get('fiftyDayAverage'))}")
    lines.append(f"- 200 Day Moving Avg: {safe(info.get('twoHundredDayAverage'))}")
    lines.append(f"- Beta: {safe(info.get('beta'))}")
    lines.append(f"- Analyst Target Price: {safe(info.get('targetMeanPrice'))}\n")

    # 6. Trading Considerations
    lines.append("## 6. Trading Considerations")
    lines.append(f"- Key Risks: {safe(info.get('riskFactors', 'N/A'))}")
    lines.append(f"- Summary for Traders: {safe(info.get('longBusinessSummary'))}")

    return "\n".join(lines)
