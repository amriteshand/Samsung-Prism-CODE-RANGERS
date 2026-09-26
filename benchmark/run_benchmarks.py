import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time
import numpy as np
from typing import List, Dict, Any

from engine.core import TroubleshootingEngine
from engine.schema import TroubleshootRequest


BENCHMARK_DOMAINS = {
    "Battery": [
        "Battery draining fast on my galaxy phone",
        "phn btry draining super fast please help",
        "Battery percentage drops rapidly even on standby",
        "Phone battery bahut jaldi khatam ho raha hai",
        "How to turn on battery saving mode",
        "Device drops 30% battery overnight in idle",
        "Super fast charging not working properly",
        "Restrict background battery drain for social apps",
        "Battery health diagnostic check",
        "Overheating and battery dying quickly"
    ],
    "Display": [
        "Screen flickering and auto brightness erratic",
        "disp scrn flickering and brightness glitching",
        "Screen display blink kar rahi hai",
        "Motion smoothness dropping below 60fps stutter",
        "How to configure adaptive brightness and motion smoothness",
        "Display refresh rate 120hz fix",
        "Touch screen unresponsive with screen protector",
        "Eye comfort shield blue light filter setup",
        "Dark mode schedule not turning on at night",
        "Accidental touch protection triggering in pocket"
    ],
    "Camera": [
        "Camera app crashed and taking blurry photos",
        "cam crashed and taking blurry photos",
        "Camera open nahi ho raha crash kar raha hai",
        "Photos are out of focus and lens fails to calibrate",
        "How to clear camera app cache and reset settings",
        "Camera failed error when opening viewfinder",
        "Video recording shaky need optical stabilization",
        "Camera lens clean and autofocus hunting",
        "Scene optimizer not recognizing low light food",
        "Shutter button delay and laggy picture capture"
    ],
    "Performance": [
        "Phone lagging and stuttering after update",
        "phn laging and overheating after update",
        "Phone bahut garam aur lag ho raha hai",
        "Applications stuttering and delayed app launch latency",
        "How to optimize memory and enable auto restart",
        "Device care ram plus virtual memory setup",
        "Clear cache partition to stop phone freezing",
        "System UI unresponsive during heavy multitasking",
        "Background processes slowing down device speed",
        "Device thermal throttling when playing games"
    ]
}


def run_benchmark():
    print("=" * 70)
    print("SAMSUNG PRISM HACKATHON: AUTOMATED QUANTITATIVE BENCHMARK RUNNER")
    print("=" * 70)

    engine = TroubleshootingEngine(deeplinks_path="data/deeplinks.json")
    results_by_domain = {}

    overall_latencies = []
    cache_hits = 0
    total_queries = 0
    safety_violations = 0
    url_leaks = 0

    for domain, queries in BENCHMARK_DOMAINS.items():
        domain_lats = []
        domain_hits = 0

        for q in queries:
            total_queries += 1
            res = engine.troubleshoot(TroubleshootRequest(query=q))
            lat = res.meta.latency_ms
            domain_lats.append(lat)
            overall_latencies.append(lat)

            if res.meta.cache_hit:
                domain_hits += 1
                cache_hits += 1

            # Verify Safe Ordering Hygiene
            seen_destructive = False
            for step in res.steps:
                if step.is_destructive or step.invasive_level == 3:
                    seen_destructive = True
                elif seen_destructive:
                    safety_violations += 1

                # Verify Zero Web URL Leaks
                if not step.uri.startswith("bixby://"):
                    url_leaks += 1
                if any(x in step.uri for x in ["http", "https", "www.", ".com"]):
                    url_leaks += 1

        results_by_domain[domain] = {
            "queries_count": len(queries),
            "p50_ms": round(float(np.percentile(domain_lats, 50)), 2),
            "p90_ms": round(float(np.percentile(domain_lats, 90)), 2),
            "p95_ms": round(float(np.percentile(domain_lats, 95)), 2),
            "avg_ms": round(float(np.mean(domain_lats)), 2),
            "hit_rate_pct": round((domain_hits / len(queries)) * 100, 1)
        }

    # Fallback Benchmark Test
    fallback_queries = [
        "how to bake chocolate fudge cake",
        "weather in paris tomorrow morning",
        "best football players of all time",
        "who is the prime minister of australia",
        "recipe for chicken tikka masala"
    ]
    fb_success = 0
    for q in fallback_queries:
        res = engine.troubleshoot(TroubleshootRequest(query=q))
        if res.fallback == "no match" and res.contexts == [] and len(res.steps) == 0:
            fb_success += 1

    fallback_precision = round((fb_success / len(fallback_queries)) * 100, 1)

    print("\n--- BENCHMARK RESULTS ACROSS DOMAINS ---")
    for d, stats in results_by_domain.items():
        print(f"Domain: {d:12} | P50: {stats['p50_ms']:5.2f} ms | P90: {stats['p90_ms']:5.2f} ms | P95: {stats['p95_ms']:5.2f} ms | Hit Rate: {stats['hit_rate_pct']}%")

    overall_p50 = round(float(np.percentile(overall_latencies, 50)), 2)
    overall_p90 = round(float(np.percentile(overall_latencies, 90)), 2)
    overall_p95 = round(float(np.percentile(overall_latencies, 95)), 2)
    overall_hit_rate = round((cache_hits / total_queries) * 100, 1)

    print("\n--- OVERALL ENGINE TELEMETRY ---")
    print(f"Total Test Queries:        {total_queries}")
    print(f"Overall Cache Hit Rate:    {overall_hit_rate}% (Target: >= 80%)")
    print(f"Overall P95 Latency:       {overall_p95} ms (Target: <= 300 ms)")
    print(f"Safety Violations:         {safety_violations} (100% Non-destructive first)")
    print(f"Web URL Leaks:             {url_leaks} (100% Strict Bixby Protocol)")
    print(f"Fallback Precision:        {fallback_precision}% (Zero hallucination)")

    return {
        "domain_results": results_by_domain,
        "overall": {
            "total_queries": total_queries,
            "p50_ms": overall_p50,
            "p90_ms": overall_p90,
            "p95_ms": overall_p95,
            "cache_hit_rate_pct": overall_hit_rate,
            "safety_violations": safety_violations,
            "url_leaks": url_leaks,
            "fallback_precision_pct": fallback_precision
        }
    }


if __name__ == "__main__":
    run_benchmark()
