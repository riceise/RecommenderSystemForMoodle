import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from typing import Any
from urllib.parse import urlparse

from data.postgres_provider import PostgresDataProvider
from services.external_resource_ranker_service import ExternalResourceRankerService
from services.ollama_service import OllamaService
from services.search_service import SearchService
from services.url_validation_service import UrlValidationService
from utils.config import config

logger = logging.getLogger(__name__)
_discovery_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="external-discovery")


class ExternalCourseService:
    def __init__(self):
        self.postgres = PostgresDataProvider()
        self.ollama = OllamaService()
        self.search = SearchService()
        self.validator = UrlValidationService()
        self.ranker = ExternalResourceRankerService()

    def discover_courses(self, weak_topics: list[str], force_refresh: bool = False) -> dict[str, Any]:
        if not config.WEB_SEARCH_ENABLED:
            return {"saved": 0, "queries": [], "results": []}

        resources = self.discover_resources(weak_topics)
        selected = self._select_persistable_resources(resources)
        saved = self.postgres.upsert_external_courses([self._to_db_course(resource) for resource in selected])
        return {
            "saved": saved,
            "queries": list(dict.fromkeys([item.get("SearchQuery", "") for item in resources if item.get("SearchQuery")])),
            "results": selected,
        }

    def discover_and_load_relevant_resources(
        self,
        topics: list[str],
        course_name: str = "",
        weak_topics: list[str] | None = None,
        improvement_topics: list[str] | None = None,
        course_tags: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        clean_topics = list(dict.fromkeys([str(topic).strip() for topic in topics if str(topic).strip()]))
        if not clean_topics:
            return []

        cached_before = self._load_relevant_cached_resources(clean_topics)
        fresh_resources = self.discover_resources(clean_topics) if config.WEB_SEARCH_ENABLED else []
        if fresh_resources:
            saved = self.persist_resources(fresh_resources)
            logger.info("Synchronous external discovery saved %s resources for topics=%s", saved, clean_topics)

        cached_after = self._load_relevant_cached_resources(clean_topics)
        merged = self._merge_and_rank_resources(cached_after + fresh_resources + cached_before, clean_topics)
        return self.ranker.rank_resources(
            course_name=course_name,
            weak_topics=weak_topics or [],
            improvement_topics=improvement_topics or [],
            course_tags=course_tags or [],
            candidates=merged,
            max_results=5,
        )

    def discover_resources(self, weak_topics: list[str]) -> list[dict[str, Any]]:
        if not config.WEB_SEARCH_ENABLED:
            return []

        queries = self.ollama.generate_search_queries(weak_topics) if config.OLLAMA_EXTERNAL_SEARCH_ENABLED else []
        if not queries:
            queries = self._build_resource_queries(weak_topics)

        discovered: list[dict[str, Any]] = []
        seen_urls: set[str] = set()
        for query in queries:
            try:
                results = self.search.search(
                    query,
                    max_results=config.WEB_SEARCH_MAX_RESULTS,
                    allowed_domains=config.EXTERNAL_RESOURCE_DOMAINS,
                )
            except Exception as ex:
                logger.warning("Search failed for query '%s': %s", query, ex)
                continue

            for item in results:
                candidate = self._build_validated_candidate(query, item)
                if not candidate:
                    continue
                url = candidate.get("Url")
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                discovered.append(candidate)

        return discovered

    def discover_fresh_candidates(self, topics: list[str], timeout_seconds: int | None = None) -> list[dict[str, Any]]:
        clean_topics = [str(topic).strip() for topic in topics if str(topic).strip()]
        if not clean_topics:
            return []
        future = _discovery_executor.submit(self.discover_resources, clean_topics)
        try:
            return future.result(timeout=timeout_seconds or config.FRESH_DISCOVERY_TIMEOUT_SECONDS)
        except TimeoutError:
            logger.info("Fresh external discovery timed out after %s seconds", timeout_seconds or config.FRESH_DISCOVERY_TIMEOUT_SECONDS)
            return []
        except Exception as ex:
            logger.warning("Fresh external discovery failed: %s", ex)
            return []

    def persist_resources(self, resources: list[dict[str, Any]]) -> int:
        selected = self._select_persistable_resources(resources)
        return self.postgres.upsert_external_courses([self._to_db_course(resource) for resource in selected])

    def discover_courses_background(self, weak_topics: list[str], force_refresh: bool = False) -> None:
        if not config.WEB_SEARCH_ENABLED or not config.EXTERNAL_DISCOVERY_BACKGROUND_ENABLED:
            return
        topics = [str(topic).strip() for topic in weak_topics if str(topic).strip()]
        if not topics:
            return

        def _run() -> None:
            try:
                result = self.discover_courses(topics, force_refresh=force_refresh)
                logger.info(
                    "Background external discovery finished: topics=%s saved=%s queries=%s",
                    topics,
                    result.get("saved", 0),
                    result.get("queries", []),
                )
            except Exception as ex:
                logger.warning("Background external discovery failed for topics %s: %s", topics, ex)

        _discovery_executor.submit(_run)

    def _build_resource_queries(self, weak_topics: list[str], max_queries: int | None = None) -> list[str]:
        queries = []
        topics = weak_topics[:max_queries] if max_queries else weak_topics
        for topic in topics:
            topic_text = str(topic).strip()
            if not topic_text:
                continue
            queries.extend([
                f'site:coursera.org/learn "{topic_text}" course',
                f'site:edx.org/learn "{topic_text}" course',
                f'site:youtube.com/watch "{topic_text}" tutorial',
                f'site:learn.microsoft.com "{topic_text}" tutorial',
                f'site:developer.mozilla.org "{topic_text}" tutorial',
                f'site:geeksforgeeks.org "{topic_text}" tutorial',
                f'site:w3schools.com "{topic_text}" tutorial',
                f'site:coursera.org/specializations "{topic_text}" course',
            ])
        return queries

    def _build_validated_candidate(self, query: str, item: dict) -> dict[str, Any] | None:
        raw_url = item.get("url")
        resource_type = self.validator.detect_resource_type(raw_url)
        validation = self.validator.validate(raw_url, expected_type=resource_type)
        if not validation.is_valid:
            if resource_type != "video" and self._is_trusted_resource_domain(raw_url) and not self.validator.title_looks_like_error(item.get("title")):
                logger.info("Accept trusted search result without direct fetch validation: %s", raw_url)
                normalized_url = self.validator.normalize_url(raw_url)
                validation.normalized_url = normalized_url
            else:
                logger.info("Skip invalid external resource %s: %s", raw_url, validation.reason)
                try:
                    self.postgres.deactivate_external_course(validation.normalized_url or raw_url)
                except Exception:
                    pass
                return None

        url = validation.normalized_url or raw_url
        if self.validator.title_looks_like_error(item.get("title")):
            return None

        page: dict[str, Any] = {"url": url}
        if resource_type != "video":
            try:
                page = self.search.extract_course_page(url)
            except Exception as ex:
                logger.info("Page extraction skipped for %s: %s", url, ex)

        return self._normalize_without_ollama(query, item, page, resource_type)

    def _normalize_without_ollama(self, query: str, item: dict, page: dict, resource_type: str | None = None) -> dict:
        url = page.get("url") or item.get("url") or ""
        title = page.get("title") or item.get("title") or "External course"
        description = (
            page.get("description")
            or item.get("content")
            or item.get("description")
            or "External course found by NeuroTutor search."
        )
        resource_type = resource_type or self.validator.detect_resource_type(url)
        confidence = self._confidence_for_url(url, resource_type)
        return {
            "Title": str(title)[:300],
            "Description": str(description)[:1000],
            "Platform": self._detect_platform(url),
            "Difficulty": "Standard",
            "Topics": [str(topic) for topic in query.replace('"', "").split()[:8] if not topic.startswith("site:")],
            "Url": url,
            "ResourceType": resource_type,
            "RelevanceScore": confidence,
            "Language": "en",
            "ProviderCourseId": None,
            "ConfidenceScore": confidence,
            "Metadata": {"source": "searxng_sync", "search_result": item},
            "SearchQuery": query,
            "DiscoveryMethod": "searxng_sync",
        }

    def _select_persistable_resources(self, resources: list[dict[str, Any]]) -> list[dict[str, Any]]:
        courses = [
            item for item in resources
            if item.get("ResourceType") == "course" and self._is_course_domain(item.get("Url"))
        ]
        has_specific_by_query: set[str] = {
            item.get("SearchQuery", "")
            for item in courses
            if self.validator.is_specific_course_url(item.get("Url"))
        }
        selected = []
        for item in courses:
            if item.get("SearchQuery") in has_specific_by_query and not self.validator.is_specific_course_url(item.get("Url")):
                continue
            selected.append(item)

        for item in resources:
            if item.get("ResourceType") in {"article", "video"} and self._is_trusted_resource_domain(item.get("Url")):
                selected.append(item)

        deduped: dict[str, dict[str, Any]] = {}
        for item in selected:
            url = self.validator.normalize_url(item.get("Url"))
            if not url:
                continue
            if url not in deduped or item.get("ConfidenceScore", 0) > deduped[url].get("ConfidenceScore", 0):
                deduped[url] = item
        return list(deduped.values())

    def _to_db_course(self, item: dict[str, Any]) -> dict:
        return {
            "title": item.get("Title", ""),
            "description": item.get("Description", ""),
            "platform": item.get("Platform", "External"),
            "difficulty": item.get("Difficulty", "Standard"),
            "topics": item.get("Topics") or [],
            "url": item.get("Url"),
            "language": item.get("Language", "en"),
            "provider_course_id": item.get("ProviderCourseId"),
            "resource_type": item.get("ResourceType", "course"),
            "confidence_score": item.get("ConfidenceScore", 0.0),
            "metadata": item.get("Metadata", {}),
            "search_query": item.get("SearchQuery", ""),
            "discovery_method": item.get("DiscoveryMethod", "searxng_fallback"),
        }

    def _load_relevant_cached_resources(self, topics: list[str]) -> list[dict[str, Any]]:
        try:
            rows = self.postgres.get_external_courses_for_topics(topics, limit=80)
            if len(rows) < 20:
                seen_urls = {row.get("Url") for row in rows}
                rows.extend([row for row in self.postgres.get_external_courses(limit=120) if row.get("Url") not in seen_urls])
        except Exception as ex:
            logger.warning("Failed to load relevant cached external resources: %s", ex)
            return []
        return [self._from_db_course(row, topics) for row in rows]

    def _from_db_course(self, row: dict[str, Any], topics: list[str]) -> dict[str, Any]:
        score = self._resource_relevance_score(row, topics)
        return {
            "sourceKind": "external",
            "externalCourseId": str(row.get("Id")) if row.get("Id") else None,
            "Title": row.get("Title", ""),
            "Description": row.get("Description", ""),
            "Platform": row.get("Platform", "External"),
            "Difficulty": row.get("Difficulty", "Standard"),
            "Topics": row.get("Topics") or [],
            "Url": row.get("Url"),
            "ResourceType": row.get("ResourceType") or "course",
            "RelevanceScore": score,
            "ConfidenceScore": max(score, float(row.get("ConfidenceScore") or 0.0)),
            "SearchQuery": row.get("SearchQuery", ""),
        }

    def _merge_and_rank_resources(self, resources: list[dict[str, Any]], topics: list[str]) -> list[dict[str, Any]]:
        deduped: dict[str, dict[str, Any]] = {}
        for item in resources:
            normalized_url = self.validator.normalize_url(item.get("Url"))
            if not normalized_url:
                continue

            score = self._resource_relevance_score(item, topics)
            if score <= 0.0:
                continue

            normalized = {
                "sourceKind": "external",
                "externalCourseId": item.get("externalCourseId"),
                "Title": item.get("Title", ""),
                "Description": item.get("Description", ""),
                "Platform": item.get("Platform", "External"),
                "Difficulty": item.get("Difficulty", "Standard"),
                "Topics": item.get("Topics") or [],
                "Url": normalized_url,
                "ResourceType": item.get("ResourceType") or "article",
                "RelevanceScore": score,
                "ConfidenceScore": max(score, float(item.get("ConfidenceScore") or 0.0)),
                "SearchQuery": item.get("SearchQuery", ""),
            }

            existing = deduped.get(normalized_url)
            if not existing or normalized["RelevanceScore"] > existing.get("RelevanceScore", 0):
                deduped[normalized_url] = normalized

        ranked = list(deduped.values())
        ranked.sort(key=lambda item: (item.get("RelevanceScore", 0), self._url_priority(item.get("Url"))), reverse=True)
        return ranked

    def _select_recommendation_mix(self, resources: list[dict[str, Any]]) -> list[dict[str, Any]]:
        selected: list[dict[str, Any]] = []
        used_urls: set[str] = set()
        targets = [("article", 2), ("course", 2), ("video", 1)]

        for resource_type, count in targets:
            for item in [x for x in resources if x.get("ResourceType") == resource_type]:
                if len([x for x in selected if x.get("ResourceType") == resource_type]) >= count:
                    break
                url = item.get("Url")
                if not url or url in used_urls:
                    continue
                selected.append(item)
                used_urls.add(url)

        if len(selected) < 4:
            for item in resources:
                url = item.get("Url")
                if not url or url in used_urls:
                    continue
                selected.append(item)
                used_urls.add(url)
                if len(selected) >= 5:
                    break

        return selected[:5]

    def _is_allowed_course_candidate(self, item: dict[str, Any], url: str, score: float, has_specific_course: bool, topics: list[str]) -> bool:
        return True

    def _requires_stack_match(self, topics: list[str]) -> bool:
        return False

    def _has_learning_topic_match(self, text: str, topics: list[str]) -> bool:
        return False

    @staticmethod
    def _is_catalog_course_url(url: str | None) -> bool:
        parsed = urlparse(url or "")
        host = parsed.netloc.lower()
        path = parsed.path.lower()
        return any(domain in host for domain in ("coursera.org", "edx.org")) and (
            path in {"", "/"}
            or path.startswith("/courses")
            or path.startswith("/search")
            or path.startswith("/browse")
        )

    @staticmethod
    def _url_priority(url: str | None) -> float:
        parsed = urlparse(url or "")
        path = parsed.path.lower()
        if any(path.startswith(prefix) for prefix in ("/learn/", "/specializations/", "/professional-certificates/", "/xseries/", "/certificates/")):
            return 0.3
        if path.startswith(("/courses", "/search", "/browse")):
            return 0.15
        return 0.0

    def _resource_relevance_score(self, item: dict[str, Any], topics: list[str]) -> float:
        text = self._resource_text(item)
        score = float(item.get("ConfidenceScore") or item.get("RelevanceScore") or 0.25)
        for topic in topics:
            normalized_topic = str(topic).strip().lower()
            if normalized_topic and normalized_topic in text:
                score += 0.3
                continue
            tokens = [token for token in normalized_topic.split() if len(token) >= 4]
            token_matches = sum(1 for token in tokens if token in text)
            if tokens and token_matches >= max(1, len(tokens) // 2):
                score += min(0.25, 0.08 * token_matches)
        return min(score, 0.99)

    @staticmethod
    def _resource_text(item: dict[str, Any]) -> str:
        fields = [
            item.get("Title", ""),
            item.get("Description", ""),
            item.get("SearchQuery", ""),
            " ".join(item.get("Topics") or []) if isinstance(item.get("Topics"), list) else str(item.get("Topics") or ""),
        ]
        return " ".join(str(field).lower() for field in fields)

    @staticmethod
    def _resource_visible_text(item: dict[str, Any]) -> str:
        fields = [
            item.get("Title", ""),
            item.get("Description", ""),
            item.get("Url", ""),
        ]
        return " ".join(str(field).lower() for field in fields)

    def _confidence_for_url(self, url: str, resource_type: str) -> float:
        if resource_type == "video":
            return 0.72
        if self.validator.is_specific_course_url(url):
            return 0.85
        if "/courses" in urlparse(url).path.lower():
            return 0.42
        if resource_type == "article":
            return 0.65
        return 0.5

    @staticmethod
    def _is_course_domain(url: str | None) -> bool:
        host = urlparse(url or "").netloc.lower()
        return any(domain in host for domain in config.TRUSTED_COURSE_DOMAINS)

    @staticmethod
    def _is_trusted_resource_domain(url: str | None) -> bool:
        host = urlparse(url or "").netloc.lower()
        return any(domain in host for domain in config.EXTERNAL_RESOURCE_DOMAINS)

    @staticmethod
    def _detect_platform(url: str) -> str:
        lower = url.lower()
        if "coursera" in lower:
            return "Coursera"
        if "edx" in lower:
            return "edX"
        if "youtube" in lower or "youtu.be" in lower:
            return "YouTube"
        if "learn.microsoft.com" in lower:
            return "Microsoft Learn"
        if "developer.mozilla.org" in lower:
            return "MDN"
        return "External"
