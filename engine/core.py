import time
from typing import Dict, Any, Optional, List
from engine.schema import (
    ActionableDeepLink,
    ValidationDeepLink,
    StepGroup,
    ExecutionMetadata,
    TroubleshootRequest,
    TroubleshootResponse,
)
from engine.hybrid_retriever import HybridRetriever
from engine.safe_planner import SafePlanOrderer
from engine.semantic_cache import SemanticCache
from engine.sanitizer import PipelineSanitizer


class TroubleshootingEngine:
    """
    Samsung PRISM GenAI Hackathon Theme 2: Smart Guided Troubleshooting Engine
    Orchestrates:
    - Phase 1: Strict Schema & Rule Hygiene (Pydantic v2, sentence case, word count, zero web leaks)
    - Phase 2: Hybrid Retrieval (BM25 + Dense Vectors) & Safe Plan Ordering (non-destructive first)
    - Phase 3: Fast-Path Caching (< 300 ms response times, paraphrase enrichment)
    - Phase 4: Microservice Metadata & Telemetry
    """

    MODEL_ID = "prism-hybrid-v3"
    ESTIMATED_INFERENCE_COST_USD = 0.001

    def __init__(self, deeplinks_path: str = "data/deeplinks.json"):
        self.retriever = HybridRetriever(deeplinks_path=deeplinks_path)
        self.cache = SemanticCache(vectorizer=self.retriever.vectorizer, similarity_threshold=0.76)
        self.is_prewarmed = False

        # Automatically pre-warm standard diagnostic patterns
        self.prewarm()

    def prewarm(self):
        """Pre-warms vector indices and seeds semantic cache with core diagnostic domains."""
        seed_complaints = [
            # Battery
            ("battery", "Battery draining fast during idle standby", "Battery"),
            ("battery", "Super fast charging not working slow charge", "Battery"),
            ("battery", "Battery protection 85 percent limit setup", "Battery"),
            ("battery", "Restrict background app battery drain", "Battery"),
            ("battery", "Overheating and battery dying quickly", "Battery"),
            ("battery", "Battery health diagnostic test check", "Battery"),
            # Display
            ("display", "Screen flickering and auto brightness erratic", "Display"),
            ("display", "Motion smoothness refresh rate 120hz stutter", "Display"),
            ("display", "Touch screen unresponsive with screen protector", "Display"),
            ("display", "Eye comfort shield blue light filter setup", "Display"),
            ("display", "Dark mode schedule not turning on at night", "Display"),
            ("display", "Accidental touch protection triggering in pocket", "Display"),
            # Camera
            ("camera", "Camera app crashed and taking blurry photos", "Camera"),
            ("camera", "Camera failed error when opening viewfinder", "Camera"),
            ("camera", "Video recording shaky need optical stabilization", "Camera"),
            ("camera", "Clean camera lens and autofocus hunting", "Camera"),
            ("camera", "Scene optimizer not recognizing low light food", "Camera"),
            ("camera", "Shutter button delay and laggy picture capture", "Camera"),
            # Performance
            ("performance", "Phone lagging and stuttering after update", "Performance"),
            ("performance", "Device care ram plus virtual memory setup", "Performance"),
            ("performance", "Clear cache partition to stop phone freezing", "Performance"),
            ("performance", "System UI unresponsive during heavy multitasking", "Performance"),
            ("performance", "Background processes slowing down device speed", "Performance"),
            ("performance", "Device thermal throttling when playing games", "Performance"),
            # Connectivity & Sound
            ("connectivity", "Wifi disconnecting and network dropped", "Connectivity"),
            ("connectivity", "Bluetooth pairing failure wireless earbuds", "Connectivity"),
            ("connectivity", "Reset network settings wifi cellular bluetooth", "Connectivity"),
            ("sound", "Phone speaker crackling and audio volume low", "Sound"),
            ("sound", "Dolby atmos equalizer sound quality effects", "Sound"),
            ("sound", "Do not disturb notification silent mode", "Sound"),
        ]

        for topic, complaint, domain in seed_complaints:
            is_fb, docs, _ = self.retriever.retrieve(complaint, top_k=4)
            if not is_fb and docs:
                raw_steps = []
                for doc in docs:
                    raw_steps.append(
                        ActionableDeepLink(
                            id=doc["id"],
                            step_number=1,
                            title=PipelineSanitizer.format_title(doc["title"]),
                            description=PipelineSanitizer.format_description(doc["description"]),
                            uri=PipelineSanitizer.sanitize_uri(doc["uri"]),
                            is_destructive=doc.get("is_destructive", False),
                            invasive_level=doc.get("invasive_level", 1),
                            action_type=doc.get("action_type", "toggle")
                        )
                    )

                ordered_steps, groups = SafePlanOrderer.order_steps(raw_steps)
                goal = PipelineSanitizer.format_goal(domain)
                val_link = SafePlanOrderer.get_validation_link(domain)
                contexts = [f"{s.title}: {s.description}" for s in ordered_steps]

                plan_dict = {
                    "goal": goal,
                    "steps": [s.model_dump() for s in ordered_steps],
                    "step_groups": [g.model_dump() for g in groups],
                    "validation": val_link.model_dump(),
                    "contexts": contexts,
                    "fallback": None,
                }
                # Put in cache with generated paraphrases
                self.cache.put(complaint, plan_dict, domain=domain)

        self.is_prewarmed = True

    def troubleshoot(self, request: TroubleshootRequest) -> TroubleshootResponse:
        """
        Executes end-to-end troubleshooting pipeline:
        1. Fast-Path Semantic Cache Lookup
        2. Hybrid Retrieval (BM25 + Dense Vector Cosine)
        3. Safe Plan Ordering & Destructive Isolation
        4. Fallback Handling
        5. Schema Sanitization & Pure JSON Verification
        """
        start_time = time.perf_counter()
        query = request.query.strip()

        # Step 1: Check Fast-Path Semantic Cache
        is_hit, cached_plan, sim_score, lookup_lat = self.cache.get(query)
        if is_hit and cached_plan is not None:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            meta = ExecutionMetadata(
                latency_ms=elapsed_ms,
                cache_hit=True,
                model=f"{self.MODEL_ID} (Fast-Path Cache)",
                cost_usd=0.0
            )

            # Reconstruct and validate response
            return TroubleshootResponse(
                goal=cached_plan["goal"],
                steps=[ActionableDeepLink(**s) for s in cached_plan["steps"]],
                step_groups=[StepGroup(**g) for g in cached_plan["step_groups"]],
                validation=ValidationDeepLink(**cached_plan["validation"]) if cached_plan.get("validation") else None,
                contexts=cached_plan["contexts"],
                fallback=cached_plan.get("fallback"),
                meta=meta
            )

        # Step 2: Cache Miss -> Run Hybrid Retrieval
        is_fallback, retrieved_docs, max_score = self.retriever.retrieve(query, top_k=4)

        # Fallback Handling Rule:
        # "If no viable solution is present, cleanly return an empty list ('contexts': [])
        # with fallback metadata ('fallback': 'no match') rather than hallucinating steps"
        if is_fallback or not retrieved_docs:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            meta = ExecutionMetadata(
                latency_ms=elapsed_ms,
                cache_hit=False,
                model=self.MODEL_ID,
                cost_usd=self.ESTIMATED_INFERENCE_COST_USD
            )
            goal_text = PipelineSanitizer.format_goal("Out of Scope Query")
            return TroubleshootResponse(
                goal=goal_text,
                steps=[],
                step_groups=[],
                validation=None,
                contexts=[],
                fallback="no match",
                meta=meta
            )

        # Convert retrieved documents to validated ActionableDeepLink instances
        raw_steps: List[ActionableDeepLink] = []
        inferred_domain = retrieved_docs[0].get("category", "Device")

        for doc in retrieved_docs:
            step = ActionableDeepLink(
                id=doc["id"],
                step_number=1,
                title=PipelineSanitizer.format_title(doc["title"]),
                description=PipelineSanitizer.format_description(doc["description"]),
                uri=PipelineSanitizer.sanitize_uri(doc["uri"]),
                is_destructive=doc.get("is_destructive", False),
                invasive_level=doc.get("invasive_level", 1),
                action_type=doc.get("action_type", "toggle")
            )
            raw_steps.append(step)

        # Step 3: Safe Plan Ordering Logic
        # Non-invasive toggles first, destructive operations strictly last
        ordered_steps, step_groups = SafePlanOrderer.order_steps(raw_steps)

        # Validation Deep Link
        validation_link = SafePlanOrderer.get_validation_link(inferred_domain)

        # Goal formatting: strictly Follow these steps to perform <Topic> Troubleshooting or Configuration
        goal_text = PipelineSanitizer.format_goal(inferred_domain)

        # Contexts
        contexts = [f"{s.title}: {s.description} -> {s.uri}" for s in ordered_steps]

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        meta = ExecutionMetadata(
            latency_ms=elapsed_ms,
            cache_hit=False,
            model=f"{self.MODEL_ID} (Hybrid Retrieval + Safe Planner)",
            cost_usd=self.ESTIMATED_INFERENCE_COST_USD
        )

        response = TroubleshootResponse(
            goal=goal_text,
            steps=ordered_steps,
            step_groups=step_groups,
            validation=validation_link,
            contexts=contexts,
            fallback=None,
            meta=meta
        )

        # Store verified plan into Semantic Cache for future fast-path hits
        plan_to_cache = {
            "goal": response.goal,
            "steps": [s.model_dump() for s in response.steps],
            "step_groups": [g.model_dump() for g in response.step_groups],
            "validation": response.validation.model_dump() if response.validation else None,
            "contexts": response.contexts,
            "fallback": None,
        }
        self.cache.put(query, plan_to_cache, domain=inferred_domain)

        return response
