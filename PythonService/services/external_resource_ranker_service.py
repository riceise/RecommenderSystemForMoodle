import json
import logging
import os
import re
from typing import Any

from dotenv import load_dotenv
from groq import Groq

from services.url_validation_service import UrlValidationService

load_dotenv()
logger = logging.getLogger(__name__)


class ExternalResourceRankerService:
    MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3-32b")
    RANKER_CANDIDATE_LIMIT = 15
    MAX_DESCRIPTION_CHARS = 220
    MAX_SEARCH_QUERY_CHARS = 80
    RANKER_MAX_TOKENS = 1024
    GENERIC_CONTEXT_TERMS = {
        "web",
        "веб",
        "веб-разработка",
        "programming",
        "development",
        "разработка",
        "программирование",
        "course",
        "курс",
        "tutorial",
        "обучение",
    }
    STACK_ALIASES: dict[str, tuple[str, ...]] = {
        "csharp": (
            "c#",
            "c sharp",
            "c-sharp",
            "csharp",
            ".net",
            "dotnet",
            "asp.net",
            "asp net",
            "blazor",
            "entity framework",
        ),
        "javascript": (
            "javascript",
            "java script",
            "js",
            "typescript",
            "node.js",
            "nodejs",
            "react",
            "vue",
            "angular",
        ),
        "python": ("python", "django", "flask", "fastapi"),
        "java": ("java", "spring", "spring boot"),
        "cpp": ("c++", "cplusplus", "cpp"),
        "sql": ("sql", "postgresql", "postgres", "mysql", "sqlite", "database", "базы данных", "бд"),
    }
    STACK_DISPLAY_NAMES: dict[str, str] = {
        "csharp": "C#",
        "javascript": "JavaScript",
        "python": "Python",
        "java": "Java",
        "cpp": "C++",
        "sql": "SQL",
    }

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

        explicit_stacks = self.extract_stack_terms([course_name, *(course_tags or []), *(weak_topics or []), *(improvement_topics or [])])
        if explicit_stacks:
            normalized_candidates = self.filter_candidates_by_stack(normalized_candidates, explicit_stacks)
            if not normalized_candidates:
                return []

        context_terms = self._context_terms(course_name, weak_topics, improvement_topics, course_tags)
        ranker_candidates = self._prefilter_candidates(normalized_candidates, context_terms, self.RANKER_CANDIDATE_LIMIT)

        payload = self._build_ranker_payload(
            course_name=course_name,
            weak_topics=weak_topics,
            improvement_topics=improvement_topics,
            course_tags=course_tags,
            candidates=ranker_candidates,
            max_results=max_results,
            explicit_stacks=explicit_stacks,
        )

        try:
            response = self.client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {"role": "system", "content": self._system_prompt()},
                    {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
                ],
                temperature=0.1,
                max_tokens=self.RANKER_MAX_TOKENS,
                response_format={"type": "json_object"},
            )
            parsed = json.loads(response.choices[0].message.content.strip())
            course_terms = [] if explicit_stacks else self._context_terms(course_name, [], [], course_tags)
            return self._map_ranked_resources(parsed.get("resources", []), ranker_candidates, max_results, course_terms)
        except Exception as ex:
            logger.warning("Groq external ranker failed, using deterministic fallback: %s", ex)
            return self._fallback_rank(normalized_candidates, max_results, course_name, weak_topics, improvement_topics, course_tags)

    @staticmethod
    def _system_prompt() -> str:
        return """You are a strict educational resource ranker.
Return only a JSON object with key "resources".
Each resource must contain: url, isRelevant, score, reason, matchedTopics, resourceType.
Choose only from candidate URLs. Never create new URLs.
Reject resources that are off-topic, too generic, or for the wrong technology stack.
The courseName is a hard constraint: if it names a technology, selected resources must match that technology."""

    def _build_ranker_payload(
        self,
        course_name: str,
        weak_topics: list[str],
        improvement_topics: list[str],
        course_tags: list[str],
        candidates: list[dict[str, Any]],
        max_results: int,
        explicit_stacks: list[str] | None = None,
    ) -> dict[str, Any]:
        return {
            "courseName": course_name,
            "explicitStacks": [self.STACK_DISPLAY_NAMES.get(stack, stack) for stack in explicit_stacks or []],
            "weakTopics": weak_topics[:8],
            "improvementTopics": improvement_topics[:8],
            "courseTags": course_tags[:8],
            "resourceMix": "Prefer 1-2 articles, up to 2 courses, and optionally 1 video.",
            "rules": [
                "Treat explicitStacks as a hard relevance constraint.",
                "Select only resources that directly help the course topics.",
                "Do not select resources for a different programming language or unrelated technology stack.",
                "Use only URLs from candidates. Never invent or rewrite URLs.",
                "It is better to return fewer resources than irrelevant resources.",
            ],
            "candidates": [self._candidate_payload(item) for item in candidates[: self.RANKER_CANDIDATE_LIMIT]],
            "maxResults": max_results,
        }

    def _candidate_payload(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "url": item.get("Url"),
            "title": self._truncate(item.get("Title", ""), 180),
            "description": self._truncate(item.get("Description", ""), self.MAX_DESCRIPTION_CHARS),
            "resourceType": item.get("ResourceType", "course"),
            "platform": item.get("Platform", "External"),
            "topics": [self._truncate(topic, 40) for topic in (item.get("Topics") or [])[:6]],
            "searchQuery": self._truncate(item.get("SearchQuery", ""), self.MAX_SEARCH_QUERY_CHARS),
        }

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

    @staticmethod
    def _truncate(value: Any, max_chars: int) -> str:
        text = str(value or "").strip()
        return text[:max_chars]

    def _prefilter_candidates(
        self,
        candidates: list[dict[str, Any]],
        context_terms: list[str],
        limit: int,
    ) -> list[dict[str, Any]]:
        ranked = sorted(
            candidates,
            key=lambda item: (
                self._context_score(item, context_terms),
                float(item.get("ConfidenceScore") or item.get("RelevanceScore") or 0.0),
                self._url_priority(item.get("Url")),
            ),
            reverse=True,
        )
        return ranked[:limit]

    def _map_ranked_resources(
        self,
        ranked: list[dict[str, Any]],
        candidates: list[dict[str, Any]],
        max_results: int,
        course_terms: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        by_url = {self.url_validator.normalize_url(item.get("Url")): item for item in candidates}
        course_terms = course_terms or []
        has_course_context_matches = bool(course_terms) and any(self._context_score(candidate, course_terms) > 0 for candidate in candidates)
        selected: list[dict[str, Any]] = []
        used_urls: set[str] = set()

        for item in ranked:
            if not item.get("isRelevant", True):
                continue
            normalized_url = self.url_validator.normalize_url(item.get("url"))
            if not normalized_url or normalized_url in used_urls or normalized_url not in by_url:
                continue
            if has_course_context_matches and self._context_score(by_url[normalized_url], course_terms) <= 0:
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
        explicit_stacks = self.extract_stack_terms([course_name, *(course_tags or []), *(weak_topics or []), *(improvement_topics or [])])
        if explicit_stacks:
            candidates = self.filter_candidates_by_stack(candidates, explicit_stacks)
            if not candidates:
                return []

        context_terms = self._context_terms(course_name, weak_topics or [], improvement_topics or [], course_tags or [])
        course_terms = self._context_terms(course_name, [], [], course_tags or [])
        if not explicit_stacks and course_terms and any(self._context_score(item, course_terms) > 0 for item in candidates):
            candidates = [item for item in candidates if self._context_score(item, course_terms) > 0]
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
            [(course_name, 8)]
            + [(tag, 8) for tag in course_tags]
            + [(topic, 1) for topic in weak_topics]
            + [(topic, 1) for topic in improvement_topics]
        )
        for value, weight in weighted_values:
            lowered = str(value).strip().lower()
            if not lowered:
                continue
            high_precision = weight > 1
            expanded = [lowered]
            for token in lowered.replace("+", " ").replace("-", " ").replace(":", " ").split():
                if len(token) < 2:
                    continue
                if ExternalResourceRankerService._is_generic_context_term(token):
                    continue
                if high_precision and not ExternalResourceRankerService._is_precise_context_token(token):
                    continue
                expanded.append(token)
            for term in expanded:
                if ExternalResourceRankerService._is_generic_context_term(term):
                    continue
                terms.extend([term] * weight)
        return terms

    @staticmethod
    def _is_precise_context_token(token: str) -> bool:
        return len(token) <= 4 or any(char.isdigit() or char in "#+." for char in token) or any("a" <= char <= "z" for char in token)

    @staticmethod
    def _is_generic_context_term(term: str) -> bool:
        normalized = term.strip().lower()
        return normalized in ExternalResourceRankerService.GENERIC_CONTEXT_TERMS

    @staticmethod
    def _context_score(item: dict[str, Any], terms: list[str]) -> float:
        text = " ".join([
            str(item.get("Title", "")),
            str(item.get("Description", "")),
            str(item.get("Url", "")),
        ]).lower()
        return sum(1.0 for term in terms if term and term in text)

    @classmethod
    def extract_stack_terms(cls, values: list[Any] | tuple[Any, ...] | None) -> list[str]:
        text = " ".join(str(value or "") for value in values or []).lower()
        stacks: list[str] = []
        for stack, aliases in cls.STACK_ALIASES.items():
            if any(cls._contains_alias(text, alias) for alias in aliases):
                stacks.append(stack)
        return stacks

    @classmethod
    def stack_display_names(cls, stacks: list[str]) -> list[str]:
        return [cls.STACK_DISPLAY_NAMES.get(stack, stack) for stack in stacks]

    @classmethod
    def filter_candidates_by_stack(cls, candidates: list[dict[str, Any]], stacks: list[str]) -> list[dict[str, Any]]:
        if not stacks:
            return candidates
        return [candidate for candidate in candidates if cls.resource_matches_stack(candidate, stacks)]

    @classmethod
    def resource_matches_stack(cls, item: dict[str, Any], stacks: list[str]) -> bool:
        if not stacks:
            return True
        text = cls._resource_stack_text(item)
        return any(any(cls._contains_alias(text, alias) for alias in cls.STACK_ALIASES.get(stack, ())) for stack in stacks)

    @staticmethod
    def _resource_stack_text(item: dict[str, Any]) -> str:
        return " ".join([
            str(item.get("Title", "")),
            str(item.get("Description", "")),
            str(item.get("Url", "")),
            str(item.get("Platform", "")),
        ]).lower()

    @staticmethod
    def _contains_alias(text: str, alias: str) -> bool:
        normalized_text = text.lower()
        normalized_alias = alias.lower()

        if normalized_alias == "java":
            return re.search(r"(?<![a-z0-9])java(?![a-z0-9])", normalized_text) is not None
        if normalized_alias == "js":
            return re.search(r"(?<![a-z0-9])js(?![a-z0-9])", normalized_text) is not None
        if normalized_alias == "c#":
            return re.search(r"(?<![a-z0-9])c#(?![a-z0-9])", normalized_text) is not None
        if normalized_alias == "c++":
            return re.search(r"(?<![a-z0-9])c\+\+(?![a-z0-9])", normalized_text) is not None
        if normalized_alias == ".net":
            return re.search(r"(?<![a-z0-9])\.net(?![a-z0-9])", normalized_text) is not None

        escaped = re.escape(normalized_alias)
        return re.search(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", normalized_text) is not None

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
