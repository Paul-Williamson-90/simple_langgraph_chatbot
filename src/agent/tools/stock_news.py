from datetime import datetime
from typing import Any
import requests

from bs4 import BeautifulSoup
import yfinance as yf
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential_jitter


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

REMOVALS = [
    "Oops, something went wrong"
]


class YFNewsArticle(BaseModel):
    id: str = Field(description="Unique identifier for the news article.")
    title: str = Field(description="Title of the news article.")
    summary: str = Field(description="Summary of the news article.")
    published_date: datetime = Field(description="Publication date of the news article.")
    url: str = Field(description="URL of the news article.")
    content: str = Field(description="Content of the news article.")
    
    @classmethod
    def from_ticker_news(cls, data: dict) -> "YFNewsArticle":
        content = data["content"]
        return cls(
            id=data["id"],
            title=content["title"],
            summary=content["summary"],
            published_date=datetime.fromisoformat(content["pubDate"]),
            url=content["canonicalUrl"]["url"],
            content=cls.get_content(content["canonicalUrl"]["url"]),
        )
        
    @staticmethod
    @retry(reraise=True, stop=stop_after_attempt(5), wait=wait_exponential_jitter(exp_base=2, initial=1, max=20, jitter=1))
    def get_content(url: str) -> str:
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            paras = soup.find_all("p")
            content = "\n".join([d.get_text() for d in paras])
            for removal in REMOVALS:
                content = content.replace(removal, "")
            return content.strip()
        else:
            raise Exception(f"Failed to fetch content from {url}. Status code: {response.status_code}")
        
    def to_dict(self) -> dict[str, str]:
        return {
            "Title": self.title,
            "Summary": self.summary,
            "Published Date": self.published_date.isoformat(),
            "URL": self.url,
            "Content": self.content,
        }
        
    
@tool("fetch_stock_related_news", parse_docstring=True)
def fetch_stock_related_news(symbol: str) -> dict[str, Any]:
    """Fetch latest news regarding a stock (from Yahoo!).
    Retrieves up to 10 news articles related to the stock symbol provided.

    Args:
    symbol : str
        The stock symbol to fetch related news for.

    Returns:
    dict[str, Any]
        A dictionary containing the stock symbol and a list of news articles or an error message.
    """
    if not symbol:
        return {
            "query": symbol,
            "error": "Missing required argument: symbol"
        }
    try:
        ticker = yf.Ticker(symbol)
        news = ticker.get_news(count=10)
        if len(news) == 0:
            return {
                "query": symbol,
                "error": f"No news found for symbol: {symbol}"
            }
        news_report = _format_report(news)
        return {
            "query": symbol,
            "news_report": news_report
        }
    except Exception as e:
        return {
            "query": symbol,
            "error": str(e)
        }

def _format_report(news: list[dict]) -> list[dict[str, str]]:
    articles: list[dict[str, str]] = []
    for n in news:
        try:
            article = YFNewsArticle.from_ticker_news(n)
            articles.append(article.to_dict())
        except Exception as _:
            continue
    return articles