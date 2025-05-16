from typing import Any, Literal
import requests

import bbc
from bs4 import BeautifulSoup
from langchain_core.tools import tool

from src.agent.tools.constants import HEADERS


NewsCategories = Literal[
    'Latest',
    'Only from the BBC',
    'Arts in Motion',
    'Listen',
    'Must watch',
    'The SpeciaList',
    'Culture',
    'US & Canada news',
    'More world news',
    'Sport',
    'Business',
    'Latest audio',
    'Tech',
    'Science & health',
    'Arts',
    'Watch',
    'Travel',
    "World's Table",
    'Earth',
    'Video',
    'Discover more from the BBC'
]


@tool("fetch_latest_news")
def fetch_latest_news(category: NewsCategories) -> dict[str, Any]:
    """Fetch latest news from the BBC by category.
    Retrieves the latest news articles from the BBC in the specified category.

    Args:
    category : Literal[
        'Latest',
        'Only from the BBC',
        'Arts in Motion',
        'Listen',
        'Must watch',
        'The SpeciaList',
        'Culture',
        'US & Canada news',
        'More world news',
        'Sport',
        'Business',
        'Latest audio',
        'Tech',
        'Science & health',
        'Arts',
        'Watch',
        'Travel',
        "World's Table",
        'Earth',
        'Video',
        'Discover more from the BBC'
    ]

    Returns:
    dict[str, Any]
        A dictionary containing the category and a list of news articles or an error message.
    """
    try:
        news = bbc.news.get_news(
            language=bbc.languages.Languages.English
        )
        section_news = news.news_category(category)
        news_results: list[dict[str, str]] = []
        for news_dict in section_news:
            url = news_dict.get("news_link", None)
            if isinstance(url, str) and url.startswith("https://bbc.com/news/articles/"):
                response = requests.get(url, headers=HEADERS)
                soup = BeautifulSoup(response.content, "html.parser")
                paras = soup.find_all("p")
                content = "\n".join([d.get_text() for d in paras])
                record = {
                    "Title": news_dict.get("title", "UNKNOWN"),
                    "url": url,
                    "content": content,
                }
                news_results.append(record)
        if len(news_results) == 0:
            return {
                "query": category,
                "error": f"No news found for category: {category}"
            }
        return {
            "query": category,
            "news_results": news_results
        }
        
    except Exception as e:
        return {
            "query": category,
            "error": str(e)
        }