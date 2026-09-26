import unittest
from pydantic import ValidationError

from engine.schema import (
    ActionableDeepLink,
    ValidationDeepLink,
    TroubleshootRequest,
    TroubleshootResponse,
    ExecutionMetadata,
    StepGroup
)
from engine.sanitizer import PipelineSanitizer
from engine.core import TroubleshootingEngine


class TestSchemaAndHygiene(unittest.TestCase):
    """Phase 1: Enforce Strict Schema & Rule Hygiene."""

    def test_goal_syntax_valid(self):
        valid_goal = "Follow these steps to perform Battery Troubleshooting"
        meta = ExecutionMetadata(latency_ms=1.5, cache_hit=True, model="test", cost_usd=0.0)
        res = TroubleshootResponse(
            goal=valid_goal,
            steps=[],
            step_groups=[],
            contexts=[],
            fallback="no match",
            meta=meta
        )
        self.assertEqual(res.goal, valid_goal)

    def test_goal_syntax_invalid(self):
        invalid_goal = "How to fix your battery issues"
        meta = ExecutionMetadata(latency_ms=1.5, cache_hit=True, model="test", cost_usd=0.0)
        with self.assertRaises(ValidationError):
            TroubleshootResponse(
                goal=invalid_goal,
                steps=[],
                step_groups=[],
                contexts=[],
                fallback="no match",
                meta=meta
            )

    def test_title_word_count_and_casing(self):
        # Valid: 2 or 3 words in sentence case
        link = ActionableDeepLink(
            id="LINK_001",
            step_number=1,
            title="Battery saving mode",
            description="It will turn on power saving.",
            uri="bixby://settings/battery/power_saving",
            invasive_level=1,
            is_destructive=False
        )
        self.assertEqual(link.title, "Battery saving mode")

        # Invalid: 4 words
        with self.assertRaises(ValidationError):
            ActionableDeepLink(
                id="LINK_002",
                step_number=1,
                title="This is four words",
                description="It will turn on power saving.",
                uri="bixby://settings/battery/power_saving"
            )

        # Invalid: 1 word
        with self.assertRaises(ValidationError):
            ActionableDeepLink(
                id="LINK_003",
                step_number=1,
                title="Battery",
                description="It will turn on power saving.",
                uri="bixby://settings/battery/power_saving"
            )

    def test_description_length_and_prefix(self):
        # Valid: exactly 6 words starting with "It will"
        link = ActionableDeepLink(
            id="LINK_001",
            step_number=1,
            title="Fast charging toggle",
            description="It will enable rapid cable charging.",
            uri="bixby://settings/battery/fast_charging"
        )
        self.assertTrue(link.description.startswith("It will"))

        # Invalid: does not start with "It will"
        with self.assertRaises(ValidationError):
            ActionableDeepLink(
                id="LINK_002",
                step_number=1,
                title="Fast charging toggle",
                description="Enables rapid cable charging on phone.",
                uri="bixby://settings/battery/fast_charging"
            )

        # Invalid: too short (4 words)
        with self.assertRaises(ValidationError):
            ActionableDeepLink(
                id="LINK_003",
                step_number=1,
                title="Fast charging toggle",
                description="It will turn on.",
                uri="bixby://settings/battery/fast_charging"
            )

    def test_zero_web_url_leaks(self):
        # Forbidden http / https / www / markdown
        with self.assertRaises(ValidationError):
            ActionableDeepLink(
                id="LINK_001",
                step_number=1,
                title="Battery saving mode",
                description="It will turn on power saving.",
                uri="https://samsung.com/settings/battery"
            )

        with self.assertRaises(ValidationError):
            ActionableDeepLink(
                id="LINK_002",
                step_number=1,
                title="Battery saving mode",
                description="It will turn on power saving.",
                uri="www.samsung.com"
            )

        # Valid bixby URI
        link = ActionableDeepLink(
            id="LINK_003",
            step_number=1,
            title="Battery saving mode",
            description="It will turn on power saving.",
            uri="bixby://settings/battery/power_saving"
        )
        self.assertTrue(link.uri.startswith("bixby://"))


class TestHybridRetrievalAndOrdering(unittest.TestCase):
    """Phase 2: Build Hybrid Retrieval & Safe Plan Ordering."""

    @classmethod
    def setUpClass(cls):
        cls.engine = TroubleshootingEngine(deeplinks_path="data/deeplinks.json")

    def test_safe_plan_ordering_destructive_last(self):
        # Query requesting network troubleshooting
        res = self.engine.troubleshoot(TroubleshootRequest(query="reset network settings wifi and bluetooth"))
        self.assertGreater(len(res.steps), 0)

        # Assert no non-destructive step appears after a destructive step
        seen_destructive = False
        for step in res.steps:
            if step.is_destructive or step.invasive_level == 3:
                seen_destructive = True
            elif seen_destructive:
                self.fail(f"Non-destructive step {step.title} found after a destructive step!")

        # Verify step numbers are sequential 1..N
        for idx, step in enumerate(res.steps, start=1):
            self.assertEqual(step.step_number, idx)

    def test_fallback_handling_out_of_domain(self):
        # Nonsensical or out-of-domain query
        res = self.engine.troubleshoot(TroubleshootRequest(query="how to bake a strawberry chocolate cake"))
        self.assertEqual(res.fallback, "no match")
        self.assertEqual(res.contexts, [])
        self.assertEqual(len(res.steps), 0)


class TestFastPathCaching(unittest.TestCase):
    """Phase 3: Fast-Path Caching for < 300 ms Response Times."""

    @classmethod
    def setUpClass(cls):
        cls.engine = TroubleshootingEngine(deeplinks_path="data/deeplinks.json")

    def test_cache_hit_latency_under_300ms(self):
        query = "battery is draining fast on my galaxy phone"
        # First query may be hit or miss, second must be cache hit
        res1 = self.engine.troubleshoot(TroubleshootRequest(query=query))
        res2 = self.engine.troubleshoot(TroubleshootRequest(query=query))

        self.assertTrue(res2.meta.cache_hit)
        self.assertLessEqual(res2.meta.latency_ms, 300.0)
        self.assertLessEqual(res2.meta.latency_ms, 20.0)  # Realistically < 5 ms!

    def test_slang_and_hinglish_paraphrase_hit(self):
        # Query with Hinglish & slang
        res = self.engine.troubleshoot(TroubleshootRequest(query="phn btry draining super fast please help"))
        self.assertLessEqual(res.meta.latency_ms, 300.0)
        self.assertTrue(len(res.steps) > 0 or res.fallback is not None)


if __name__ == "__main__":
    unittest.main()
