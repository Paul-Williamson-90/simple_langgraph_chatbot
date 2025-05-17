import re
from datetime import datetime
from typing import Any

import requests
from bs4 import BeautifulSoup
from langchain_core.tools import tool

from src.tools.utils import RateLimitCounter
from src.tools.constants import HEADERS


def _create_url() -> str:
    today = datetime.now()
    year = today.year
    week = today.isocalendar()[1]
    suffix = f"{year}-W{week}"
    url = f"https://huggingface.co/papers/week/{suffix}"
    return url

def _get_papers_this_week_soup() -> BeautifulSoup:
    url = _create_url()
    response = requests.get(url)

    if not response.status_code == 200:
        raise Exception(f"Failed to fetch data from {url}. Status code: {response.status_code}")

    soup = BeautifulSoup(response.content, "html.parser")
    return soup

def _get_paper_links() -> list[str]:
    soup = _get_papers_this_week_soup()
    prefix = "https://huggingface.co"
    links = soup.find_all("a", href=True)
    pattern = re.compile(r"^/papers/\d+(\.\d+)?$")
    links = [link for link in links if pattern.match(link["href"])]
    paper_links = list(set([f"{prefix}{link["href"]}" for link in links]))
    return paper_links

def _get_paper_title(soup: BeautifulSoup) -> str:
    headers_1 = soup.find_all("h1")
    title = headers_1[0].text
    return title

def _get_paper_abstract(soup: BeautifulSoup) -> str:
    abstract_heading = soup.find("h2", string="Abstract")
    if not abstract_heading:
        return ""
    abstract_div = abstract_heading.find_next_sibling("div")
    if not abstract_div:
        return ""
    abstract_text = " ".join(p.get_text(strip=True) for p in abstract_div.find_all("p"))
    return abstract_text

def _get_publish_date(soup: BeautifulSoup) -> datetime:
    div = soup.select_one("div.mb-6.flex.gap-2.text-sm")
    pattern = re.compile(r"Published on (.+?)\n")
    date = pattern.findall(div.text)
    if not date:
        raise ValueError("Date not found in the text.")
    year = datetime.now().year
    date_str = f"{year} {date[0]}"
    publish_date = datetime.strptime(date_str, "%Y %b %d")
    return publish_date

def _get_authors(soup: BeautifulSoup) -> list[str]:
    authors = []
    author_spans = soup.find_all("span", class_="author flex items-center")
    for span in author_spans:
        author_name = span.get_text(strip=True)
        authors.append(author_name)
    return authors

def _get_upvotes(soup: BeautifulSoup) -> int:
    label = soup.find("div", class_=[
        "font-semibold", "text-orange-500"
    ])
    if not label:
        return 0
    try:
        return int(label.text)
    except Exception as _:
        return 0
    
def _get_paper_link(soup: BeautifulSoup) -> str:
    links = soup.select('a[href^="https://arxiv.org/pdf/"]')
    if not links:
        raise ValueError("No PDF link found.")
    link = links[0]["href"]
    return link

@tool("fetch_hf_papers")
def fetch_hf_papers() -> list[dict[str, Any]]:
    """
    Fetches the latest highlighted papers from Hugging Face and returns a list of dictionaries containing paper details.
    
    Returns:
    list[dict[str, Any]]
        A list of dictionaries, each containing the title, abstract, publish date, authors, upvotes, and paper link.
    """
    paper_links = _get_paper_links()
    hf_papers: list[dict[str, Any]] = []
    for url in RateLimitCounter(paper_links):
        response = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(response.content, "html.parser")
        title = _get_paper_title(soup)
        abstract = _get_paper_abstract(soup)
        publish_date = _get_publish_date(soup)
        authors = _get_authors(soup)
        upvotes = _get_upvotes(soup)
        paper_link = _get_paper_link(soup)
        hf_papers.append(
            {
                "title": title,
                "abstract": abstract,
                "publish_date": publish_date.strftime("%Y-%m-%d"),
                "authors": authors,
                "upvotes": upvotes,
                "paper_url": paper_link,
            }
        )
    hf_papers.sort(key=lambda x: x["upvotes"], reverse=True)
    return hf_papers