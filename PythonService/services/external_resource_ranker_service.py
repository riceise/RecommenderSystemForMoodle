import json
import logging
import os
from typing import Any

from dotenv import load_dotenv
from groq import Groq

from services.url_validation_service import UrlValidationService

load_dotenv()
logger = logging.getLogger(__name__)


class ExternalResourceRankerService:
    MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY not set in environment")
        self.client = Groq(api_key=api_key)
        self.url_validator = UrlValidationService()

    def rank_resources(
        self,
        course_name: str,
        weak_topics: list[str],
        improvement_topics: list[str],
        course_tags: list[str],
        candidates: list[dict[str, Any]],
        max_results: int = 5,
    ) -> list[dict[str, Any]]:
        normalized_candidates = self._dedupe_candidates(candidates)
        if not normalized_candidates:
            return []

        payload = {
            "courseName": course_name,
            "weakTopics": weak_topics,
            "improvementTopics": improvement_topics,
            "courseTags": course_tags,
            "resourceMix": "Prefer 1-2 articles, up to 2 courses, and optionally 1 video.",
            "rules": [
                "Select only resources that directly help the course topics.",
                "Do not select resources for a different programming language or unrelated technology stack.",
                "Use only URLs from candidates. Never invent or rewrite URLs.",
                "It is better to return fewer resources than irrelevant resources.",
            ],
            "candidates": [
                {
                    "url": item.get("Url"),
                    "title": item.get("Title", ""),
                    "description": item.get("Description", ""),
                    "resourceType": item.get("ResourceType", "course"),
                    "platform": item.get("Platform", "External"),
                    "topics": item.get("Topics") or [],
                    "searchQuery": item.get("SearchQuery", ""),
                }
                for item in normalized_candidates[:40]
            ],
            "maxResults": max_results,
        }

        try:
            response = self.client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {"role": "system", "content": self._system_prompt()},
                    {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
                ],
                temperature=0.1,
                max_tokens=2048,
                response_format={"type": "json_object"},
            )
            parsed = json.loads(response.choices[0].message.content.strip())
            return self._map_ranked_resources(parsed.get("resources", []), normalized_candidates, max_results)
        except Exception as ex:
            logger.warning("Groq external ranker failed, using deterministic fallback: %s", ex)
            return self._fallback_rank(normalized_candidates, max_results, course_name, weak_topics, improvement_topics, course_tags)

    @staticmethod
    def _system_prompt() -> str:
        return """You are a strict educational resource ranker.
Return only a JSON object with key "resources".
Each resource must contain: url, isRelevant, score, reason, matchedTopics, resourceType.
Choose only from candidate URLs. Never create new URLs.
Reject resources that are off-topic, too generic, or for the wrong technology stack."""

    def _dedupe_candidates(self, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        deduped: dict[str, dict[str, Any]] = {}
        for item in candidates:
            normalized_url = self.url_validator.normalize_url(item.get("Url"))
            if not normalized_url:
                continue
            candidate = dict(item)
            candidate["Url"] = normalized_url
            existing = deduped.get(normalized_url)
            if not existing or float(candidate.get("ConfidenceScore") or candidate.get("RelevanceScore") or 0) > float(existing.get("ConfidenceScore") or existing.get("RelevanceScore") or 0):
                deduped[normalized_url] = candidate
        return list(deduped.values())

    def _map_ranked_resources(self, ranked: list[dict[str, Any]], candidates: list[dict[str, Any]], max_results: int) -> list[dict[str, Any]]:
        by_url = {self.url_validator.normalize_url(item.get("Url")): item for item in candidates}
        selected: list[dict[str, Any]] = []
        used_urls: set[str] = set()

        for item in ranked:
            if not item.get("isRelevant", True):
                continue
            normalized_url = self.url_validator.normalize_url(item.get("url"))
            if not normalized_url or normalized_url in used_urls or normalized_url not in by_url:
                continue
            score = max(0.0, min(1.0, float(item.get("score", by_url[normalized_url].get("RelevanceScore", 0.6)))))
            candidate = dict(by_url[normalized_url])
            candidate["RelevanceScore"] = score
            candidate["ResourceType"] = item.get("resourceType") or candidate.get("ResourceType", "course")
            candidate["Reason"] = str(item.get("reason", ""))[:500]
            candidate["MatchedTopics"] = [str(topic) for topic in item.get("matchedTopics", []) if topic][:10]
            selected.append(candidate)
            used_urls.add(normalized_url)
            if len(selected) >= max_results:
                break

        return selected or self._fallback_rank(candidates, max_results)

    def _fallback_rank(
        self,
        candidates: list[dict[str, Any]],
        max_results: int,
        course_name: str = "",
        weak_topics: list[str] | None = None,
        improvement_topics: list[str] | None = None,
        course_tags: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        context_terms = self._context_terms(course_name, weak_topics or [], improvement_topics or [], course_tags or [])
        ranked = sorted(
            candidates,
            key=lambda item: (
                self._context_score(item, context_terms),
                float(item.get("ConfidenceScore") or item.get("RelevanceScore") or 0.0),
                self._url_priority(item.get("Url")),
            ),
            reverse=True,
        )
        return self._apply_resource_mix(ranked, max_results)

    @staticmethod
    def _context_terms(course_name: str, weak_topics: list[str], improvement_topics: list[str], course_tags: list[str]) -> list[str]:
        terms: list[str] = []
        weighted_values = (
            [(course_name, 3)]
            + [(tag, 5) for tag in course_tags]
            + [(topic, 1) for topic in weak_topics]
            + [(topic, 1) for topic in improvement_topics]
        )
        for value, weight in weighted_values:
            lowered = str(value).strip().lower()
            if not lowered:
                continue
            expanded = [lowered]
            expanded.extend([token for token in lowered.replace("+", " ").replace("-", " ").split() if len(token) >= 2])
            for term in expanded:
                terms.extend([term] * weight)
        return terms

    @staticmethod
    def _context_score(item: dict[str, Any], terms: list[str]) -> float:
        text = " ".join([
            str(item.get("Title", "")),
            str(item.get("Description", "")),
            str(item.get("Url", "")),
        ]).lower()
        return sum(1.0 for term in terms if term and term in text)

    def _apply_resource_mix(self, candidates: list[dict[str, Any]], max_results: int) -> list[dict[str, Any]]:
        selected: list[dict[str, Any]] = []
        used_urls: set[str] = set()
        targets = [("article", 2), ("course", 2), ("video", 1)]
        for resource_type, count in targets:
            for item in [candidate for candidate in candidates if candidate.get("ResourceType") == resource_type]:
                if len([candidate for candidate in selected if candidate.get("ResourceType") == resource_type]) >= count:
                    break
                url = item.get("Url")
                if not url or url in used_urls:
                    continue
                selected.append(item)
                used_urls.add(url)
                if len(selected) >= max_results:
                    return selected

        for item in candidates:
            url = item.get("Url")
            if not url or url in used_urls:
                continue
            selected.append(item)
            used_urls.add(url)
            if len(selected) >= max_results:
                break
        return selected

    @staticmethod
    def _url_priority(url: str | None) -> float:
        lowered = (url or "").lower()
        if any(part in lowered for part in ("/learn/", "/specializations/", "/professional-certificates/", "/xseries/", "/certificates/")):
            return 0.3
        if any(part in lowered for part in ("/courses", "/search", "/browse")):
            return 0.15
        return 0.0
