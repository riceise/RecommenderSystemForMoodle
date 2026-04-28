import logging
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from utils.config import config

logger = logging.getLogger(__name__)


class SearchService:
    def __init__(self):
        self.base_url = config.SEARXNG_BASE_URL.rstrip('/')
        self.headers = {
            "User-Agent": "NeuroTutorBot/1.0 (+educational research)",
            "Accept": "application/json",
            "X-Forwarded-For": "127.0.0.1",
            "X-Real-IP": "127.0.0.1",
        }

    def health(self) -> dict:
        if not config.WEB_SEARCH_ENABLED:
            return {"status": "disabled", "baseUrl": self.base_url}
        try:
            response = requests.get(
                f"{self.base_url}/search",
                params={"q": "health", "format": "json"},
                headers=self.headers,
                timeout=min(config.WEB_SEARCH_TIMEOUT_SECONDS, 10),
            )
            if response.status_code == 403:
                return {
                    "status": "forbidden",
                    "baseUrl": self.base_url,
                    "statusCode": response.status_code,
                    "hint": "Enable json in SearXNG search.formats and check bot detection/proxy headers.",
                }
            response.raise_for_status()
            payload = response.json()
            return {
                "status": "ok",
                "baseUrl": self.base_url,
                "results": len(payload.get("results", [])) if isinstance(payload, dict) else 0,
            }
        except Exception as ex:
            return {"status": "down", "baseUrl": self.base_url, "error": str(ex)}

    def search(self, query: str, max_results: int | None = None, allowed_domains: list[str] | None = None) -> list[dict]:
        max_results = max_results or config.WEB_SEARCH_MAX_RESULTS
        response = requests.get(
            f"{self.base_url}/search",
            params={
                "q": query,
                "format": "json",
                "language": "ru-RU",
            },
            headers=self.headers,
            timeout=config.WEB_SEARCH_TIMEOUT_SECONDS,
        )
        if response.status_code == 403:
            logger.warning(
                "SearXNG returned 403 for query '%s'. Body: %s",
                query,
                response.text[:300],
            )
        response.raise_for_status()
        payload = response.json()
        results = payload.get("results", []) if isinstance(payload, dict) else []
        filtered = []
        for item in results:
            url = item.get("url")
            if not url:
                continue
            if allowed_domains is not None:
                domain = urlparse(url).netloc.lower()
                if not any(allowed in domain for allowed in allowed_domains):
                    continue
            filtered.append(item)
        return filtered[:max_results]

    def extract_course_page(self, url: str) -> dict:
        response = requests.get(
            url,
            timeout=config.COURSE_PAGE_TIMEOUT_SECONDS,
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
