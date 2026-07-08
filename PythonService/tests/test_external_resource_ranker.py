import json
import unittest

from services.external_resource_ranker_service import ExternalResourceRankerService
from services.url_validation_service import UrlValidationService


class _RaisingCompletions:
    def create(self, **_kwargs):
        raise RuntimeError("413 payload too large")


class _RaisingChat:
    completions = _RaisingCompletions()


class _RaisingClient:
    chat = _RaisingChat()


def _ranker() -> ExternalResourceRankerService:
    service = object.__new__(ExternalResourceRankerService)
    service.client = _RaisingClient()
    service.url_validator = UrlValidationService()
    return service


def _candidate(title, url, resource_type="article", description="", score=0.85):
    return {
        "Title": title,
        "Description": description,
        "Platform": "External",
        "Difficulty": "Standard",
        "Topics": [],
        "Url": url,
        "ResourceType": resource_type,
        "RelevanceScore": score,
        "ConfidenceScore": score,
        "SearchQuery": 'site:example.com "C#" "arrays" tutorial',
    }


class ExternalResourceRankerTests(unittest.TestCase):
    def setUp(self):
        self.service = _ranker()
        self.mixed_candidates = [
            _candidate(
                "Массивы - C# language specification | Microsoft Learn",
                "https://learn.microsoft.com/ru-ru/dotnet/csharp/language-reference/language-specification/arrays",
                "article",
                "C# language specification for arrays.",
            ),
            _candidate(
                "If and switch statements - C# reference | Microsoft Learn",
                "https://learn.microsoft.com/ru-ru/dotnet/csharp/language-reference/statements/selection-statements",
                "article",
                "C# selection statements.",
            ),
            _candidate(
                "Introduction to .NET Core | Coursera",
                "https://www.coursera.org/learn/intro-to-dotnet-core",
                "course",
                ".NET course for application development.",
            ),
            _candidate(
                "Типизированные массивы JavaScript - JavaScript | MDN",
                "https://developer.mozilla.org/ru/docs/Web/JavaScript/Guide/Typed_arrays",
                "article",
                "JavaScript typed arrays for web development.",
            ),
            _candidate(
                "Операции: присваивание - Знакомство с искусством C++ | Coursera",
                "https://www.coursera.org/learn/cplusplus-art-assignment",
                "course",
                "C++ course.",
            ),
            _candidate(
                "Как делать игры | Godot Engine | Условные операторы | GDScript",
                "https://www.youtube.com/watch?v=fpxCfqtzdHQ",
                "video",
                "Godot GDScript conditional operators.",
                0.72,
            ),
            _candidate(
                "Уроки Python с нуля - Условные операторы",
                "https://www.youtube.com/watch?v=SUDNfS_0X-Q",
                "video",
                "Python if else tutorial.",
                0.72,
            ),
        ]

    def test_csharp_course_filters_mixed_stack_candidates(self):
        selected = self.service._fallback_rank(
            self.mixed_candidates,
            max_results=5,
            course_name="Адаптивная оценка навыков: C# + Веб-разработка",
            weak_topics=["Массивы"],
            improvement_topics=["Условные операторы"],
            course_tags=[],
        )

        titles = [item["Title"] for item in selected]
        self.assertEqual(3, len(titles))
        self.assertTrue(all("C#" in title or ".NET" in title for title in titles))

    def test_no_explicit_stack_keeps_trusted_mixed_resources(self):
        selected = self.service._fallback_rank(
            self.mixed_candidates,
            max_results=5,
            course_name="Основы программирования",
            weak_topics=["Условные операторы"],
            improvement_topics=[],
            course_tags=[],
        )

        titles = [item["Title"] for item in selected]
        self.assertGreater(len(titles), 2)
        self.assertTrue(any(any(marker in title for marker in ("Python", "C++", "Godot", "JavaScript")) for title in titles))

    def test_ranker_payload_is_compact(self):
        candidates = [
            _candidate(
                f"C# Arrays Resource {index}",
                f"https://learn.microsoft.com/dotnet/csharp/resource-{index}",
                "article",
                "C# " + ("long description " * 80),
            )
            for index in range(40)
        ]
        context_terms = self.service._context_terms(
            "C# + Веб-разработка",
            ["Массивы"],
            ["Условные операторы"],
            [],
        )
        ranker_candidates = self.service._prefilter_candidates(candidates, context_terms, self.service.RANKER_CANDIDATE_LIMIT)
        payload = self.service._build_ranker_payload(
            course_name="C# + Веб-разработка",
            weak_topics=["Массивы"],
            improvement_topics=["Условные операторы"],
            course_tags=[],
            candidates=ranker_candidates,
            max_results=5,
            explicit_stacks=["csharp"],
        )
        payload_text = json.dumps(payload, ensure_ascii=False)

        self.assertLessEqual(len(payload["candidates"]), self.service.RANKER_CANDIDATE_LIMIT)
        self.assertLess(len(payload_text), 9000)
        self.assertTrue(
            all(len(candidate["description"]) <= self.service.MAX_DESCRIPTION_CHARS for candidate in payload["candidates"])
        )

    def test_rank_resources_413_fallback_stays_stack_relevant_and_stable(self):
        first = self.service.rank_resources(
            course_name="Адаптивная оценка навыков: C# + Веб-разработка",
            weak_topics=["Массивы"],
            improvement_topics=["Условные операторы"],
            course_tags=[],
            candidates=self.mixed_candidates,
            max_results=5,
        )
        second = self.service.rank_resources(
            course_name="Адаптивная оценка навыков: C# + Веб-разработка",
            weak_topics=["Массивы"],
            improvement_topics=["Условные операторы"],
            course_tags=[],
            candidates=self.mixed_candidates,
            max_results=5,
        )

        self.assertEqual([item["Url"] for item in first], [item["Url"] for item in second])
        self.assertEqual(3, len(first))
        self.assertTrue(all("csharp" in item["Url"] or "dotnet" in item["Url"] for item in first))


if __name__ == "__main__":
    unittest.main()
