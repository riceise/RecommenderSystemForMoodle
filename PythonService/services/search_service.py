import logging
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from utils.config import config

logger = logging.getLogger(__name__)


class SearchService:
    def __init__(self):
        self.base_url = config.SEARXNG_BASE_URL.rstrip('/')

    def search(self, query: str, max_results: int | None = None) -> list[dict]:
        max_results = max_results or config.WEB_SEARCH_MAX_RESULTS
        response = requests.get(
            f"{self.base_url}/search",
            params={
                "q": query,
                "format": "json",
                "language": "ru-RU",
            },
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        results = payload.get("results", []) if isinstance(payload, dict) else []
        filtered = []
        for item in results:
            url = item.get("url")
            if not url:
                continue
            domain = urlparse(url).netloc.lower()
            if any(allowed in domain for allowed in config.EXTERNAL_SEARCH_DOMAINS):
                filtered.append(item)
        return filtered[:max_results]

    def extract_course_page(self, url: str) -> dict:
        response = requests.get(
            url,
            timeout=30,
            headers={"User-Agent": "NeuroTutorBot/1.0 (+educational research)"},
        )
        response.raise_for_status()
        html = response.text
        soup = BeautifulSoup(html, "lxml")

        title = (soup.title.text.strip() if soup.title and soup.title.text else "")
        meta_description = ""
        meta = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
        if meta:
            meta_description = (meta.get("content") or "").strip()

        headings = [h.get_text(" ", strip=True) for h in soup.find_all(["h1", "h2", "h3"])[:10]]
        text_blocks = [p.get_text(" ", strip=True) for p in soup.find_all(["p", "li"])[:40]]

        return {
            "url": url,
            "title": title,
            "description": meta_description,
            "headings": headings,
            "text_blocks": text_blocks,
            "raw_html_excerpt": html[:12000],
        }