import logging
import re
from dataclasses import dataclass
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import requests

from utils.config import config

logger = logging.getLogger(__name__)


@dataclass
class UrlValidationResult:
    is_valid: bool
    normalized_url: str | None = None
    status_code: int | None = None
    reason: str = ""
    resource_type: str = "article"


class UrlValidationService:
    TRACKING_PREFIXES = ("utm_",)
    TRACKING_KEYS = {"fbclid", "gclid", "msclkid", "mc_cid", "mc_eid", "igshid", "si", "feature"}
    ERROR_MARKERS = (
        "video unavailable",
        "this video is unavailable",
        "this video is no longer available",
        "это видео больше не доступно",
        "404 not found",
        "page not found",
    )

    def __init__(self):
        self.timeout = config.URL_VALIDATION_TIMEOUT_SECONDS
        self.headers = {
            "User-Agent": "Mozilla/5.0 NeuroTutorBot/1.0",
            "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
        }

    def normalize_url(self, url: str | None) -> str | None:
        if not url:
            return None
        parsed = urlparse(str(url).strip())
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return None

        host = parsed.netloc.lower()
        if host == "youtu.be":
            video_id = parsed.path.strip("/").split("/")[0]
            return f"https://www.youtube.com/watch?v={video_id}" if video_id else None

        if host.endswith("youtube.com"):
            query = dict(parse_qsl(parsed.query, keep_blank_values=False))
            video_id = query.get("v")
            if video_id:
                return f"https://www.youtube.com/watch?v={video_id}"

        kept_query = []
        for key, value in parse_qsl(parsed.query, keep_blank_values=False):
            key_lower = key.lower()
            if key_lower in self.TRACKING_KEYS or any(key_lower.startswith(prefix) for prefix in self.TRACKING_PREFIXES):
                continue
            kept_query.append((key, value))

        clean = parsed._replace(
            netloc=host,
            fragment="",
            query=urlencode(kept_query, doseq=True),
        )
        return urlunparse(clean)

    def validate(self, url: str | None, expected_type: str = "article") -> UrlValidationResult:
        normalized = self.normalize_url(url)
        if not normalized:
            return UrlValidationResult(False, reason="empty_or_invalid_url", resource_type=expected_type)

        if self.is_youtube_url(normalized):
            return self.validate_youtube(normalized)

        try:
            response = requests.get(
                normalized,
                headers=self.headers,
                timeout=self.timeout,
                allow_redirects=True,
            )
            if response.status_code in {403, 404, 410} or response.status_code >= 500:
                return UrlValidationResult(False, normalized, response.status_code, "bad_status", expected_type)
            if not (200 <= response.status_code < 400):
                return UrlValidationResult(False, normalized, response.status_code, "unexpected_status", expected_type)
            excerpt = response.text[:5000].lower()
            if any(marker in excerpt for marker in self.ERROR_MARKERS):
                return UrlValidationResult(False, normalized, response.status_code, "error_page", expected_type)
            return UrlValidationResult(True, response.url or normalized, response.status_code, "ok", expected_type)
        except Exception as ex:
            logger.info("URL validation failed for %s: %s", normalized, ex)
            return UrlValidationResult(False, normalized, reason=str(ex), resource_type=expected_type)

    def validate_youtube(self, url: str) -> UrlValidationResult:
        normalized = self.normalize_url(url)
        if not normalized:
            return UrlValidationResult(False, reason="invalid_youtube_url", resource_type="video")
        try:
            response = requests.get(
                "https://www.youtube.com/oembed",
                params={"url": normalized, "format": "json"},
                headers=self.headers,
                timeout=self.timeout,
            )
            if response.status_code == 200:
                return UrlValidationResult(True, normalized, response.status_code, "ok", "video")
            return UrlValidationResult(False, normalized, response.status_code, "youtube_oembed_rejected", "video")
        except Exception as ex:
            logger.info("YouTube validation failed for %s: %s", normalized, ex)
            return UrlValidationResult(False, normalized, reason=str(ex), resource_type="video")

    @staticmethod
    def is_youtube_url(url: str | None) -> bool:
        if not url:
            return False
        host = urlparse(url).netloc.lower()
        return host.endswith("youtube.com") or host == "youtu.be"

    @staticmethod
    def is_specific_course_url(url: str | None) -> bool:
        if not url:
            return False
        parsed = urlparse(url)
        path = parsed.path.lower()
        return any(
            path.startswith(prefix)
            for prefix in ("/learn/", "/specializations/", "/professional-certificates/", "/xseries/", "/certificates/")
        )

    @staticmethod
    def detect_resource_type(url: str | None) -> str:
        if UrlValidationService.is_youtube_url(url):
            return "video"
        parsed = urlparse(url or "")
        host = parsed.netloc.lower()
        if any(domain in host for domain in ("coursera.org", "edx.org")):
            return "course"
        if any(domain in host for domain in ("learn.microsoft.com", "developer.mozilla.org", "geeksforgeeks.org", "w3schools.com")):
            return "article"
        return "article"

    @staticmethod
    def title_looks_like_error(title: str | None) -> bool:
        if not title:
            return True
        lowered = re.sub(r"\s+", " ", title).strip().lower()
        return any(marker in lowered for marker in ("404", "not found", "unavailable", "недоступ"))
