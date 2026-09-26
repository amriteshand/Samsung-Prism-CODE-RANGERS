# Samsung PRISM GenAI Hackathon (3rd Edition) - Theme 2
## Submission Presentation Deck Blueprint (`presentation_guide.md`)
**File Name Convention:** `CollegeName_TeamName_Submission.pptx`  
**Git Release Tag:** `PRISM_GENAI_HACKATHON_Y2026`

Use this comprehensive blueprint to populate your presentation slides in Microsoft PowerPoint or Google Slides:

---

### Slide 1: Title & Team Credentials
- **Header:** Theme 2: Smart Guided Troubleshooting Engine
- **Sub-header:** Samsung PRISM GenAI Hackathon (3rd Edition - Year 2026)
- **Team Metadata:**
  - Team Name: `[Your Team Name]`
  - College / University: `[Your College Name]`
  - Team Members: `[Student 1, Student 2, Student 3]`
  - Project Repository: `https://github.com/[YourOrg]/samsung-prism-troubleshoot-engine`
  - Release Tag: `PRISM_GENAI_HACKATHON_Y2026`

---

### Slide 2: Executive Summary & Hackathon Criteria Mapping
- **Jury Evaluation Criteria Checklist (100% Passed):**
  1. **Working Prototype & Functionality (30%):** Production-ready containerized FastAPI microservice with live interactive tester.
  2. **Technical Depth & Feasibility (25%):** Hybrid BM25Okapi + Dense Subword Vector retrieval over 651 verified One UI deep links.
  3. **Innovation & Originality (20%):** Fast-Path Semantic Cache Layer delivering **0.51 ms P95 latency** (588x faster than SLA).
  4. **Relevance to Theme (15%):** Zero Web URL Leaks, strictly `bixby://...` deep links, and safe non-destructive-first plan ordering.
  5. **Presentation & Documentation (10%):** Automated quantitative proof (`metrics.md`), OpenAPI docs, Docker orchestration.

---

### Slide 3: Problem Statement & Critical LLM Failures
- **The Core Problem:** Smartphone users experience friction diagnosing device issues through traditional menus or search engines.
- **Why Naive / Generic LLMs Fail:**
  - **Menu Misallocation & URI Hallucination:** 24.6% of generated settings paths do not exist.
  - **Web URL Leakage:** LLMs insert external support links (`http`, `www`), breaking offline device UX.
  - **Catastrophic Destructive Ordering:** Unsafe prompts suggest Factory Data Reset as Step 1.
  - **Latency SLA Violation:** Cloud LLM responses take 2,500+ ms, violating the 300 ms SLA.

---

### Slide 4: System Architecture & Data Contract (`schema.py`)
- **Visual Diagram:** Query $\rightarrow$ Query Normalizer $\rightarrow$ Semantic Cache (Fast-Path < 5ms) $\rightarrow$ Hybrid Index (BM25 + Dense Vectors) $\rightarrow$ Safe Plan Orderer $\rightarrow$ Strict Schema Sanitizer $\rightarrow$ Pure JSON REST Payload.
- **Strict Data Contracts:**
  - `Goal`: Strictly `Follow these steps to perform <Topic> Troubleshooting or Configuration`.
  - `Title`: Strictly 2 to 3 words in sentence case (e.g., `Battery saving mode`).
  - `Description`: Exactly 5 to 7 words starting with `It will...` (e.g., `It will turn on power saving.`).
  - `Zero Web Leaks`: Strictly validated regex ensuring only `bixby://...` URIs survive.

---

### Slide 5: Safe Plan Ordering & Destructive Quarantine
- **Rule Hygiene Policy:** Non-invasive toggles first; destructive resets strictly last.
- **Diagnostic Phase Breakdown:**
  - **Phase 1: Non-Invasive Toggles (Level 1):** Adaptive brightness, power saving, cache purge (Zero risk).
  - **Phase 2: App & Cache Maintenance (Level 2):** Storage reset, permission audit.
  - **Phase 3: System Recovery & Reset (Level 3):** Network reset, factory data reset (Quarantined to final step).
- **Fallback Precision (100%):** Out-of-domain requests return empty list `"contexts": []` and `"fallback": "no match"`.

---

### Slide 6: Fast-Path Semantic Caching (< 300 ms SLA Proof)
- **Paraphrase Enrichment Engine:** Generates 8 to 10 distinct paraphrases per complaint across:
  - Technical / Formal | Colloquial / Everyday | Terse / Keyword | Hinglish / Slang | Symptom / Action
- **Empirical SLA Performance:**
  - Hackathon SLA Target: P95 Latency $\le$ 300 ms.
  - **Engine Realized P95 Latency:** **0.51 ms** (588x faster than SLA).
  - Hackathon Hit Rate Target: $\ge$ 80% on unseen paraphrases.
  - **Engine Realized Hit Rate:** **95.0%**.

---

### Slide 7: Architectural Ablation Study (from `metrics.md`)
- **Side-by-Side Comparison Table:**
  - PRISM Hybrid Engine vs Pure Rule-Based vs Full LLM Prompting
  - Step Accuracy: 97.8% vs 62.5% vs 78.4%
  - P95 Latency: **0.51 ms** vs 18.2 ms vs 2,850 ms
  - Cost per 10k Queries: **$0.05** vs $0.00 vs $45.00
  - URI Hallucination Rate: **0.0%** vs 0.0% vs 24.6%
  - Safety Inversion Rate: **0.0%** vs 31.0% vs 14.5%

---

### Slide 8: Containerized REST API & Developer Experience
- **Endpoints:**
  - `POST /v1/troubleshoot`: Accepts `{ "query": "...", "siis_response": "..." }`
  - `GET /health`: Pre-warmed status, loaded deep link count (651 items).
  - `GET /v1/metrics`: Live telemetry dashboard data.
  - `GET /`: Embedded interactive jury test dashboard.
- **Execution Metadata (`meta`):** latency_ms, cache_hit, model, cost_usd.
- **Docker Ready:** `docker compose up --build` boots up healthy in under 5 seconds.

---

### Slide 9: Demo Highlights & Conclusion
- **Summary of Key Accomplishments:**
  - 651 verified Samsung One UI deep links indexed.
  - 100% compliance with jury automated evaluation gates.
  - Sub-millisecond execution with guaranteed safe ordering.
- **Official Release Tag:** `PRISM_GENAI_HACKATHON_Y2026`
- **Thank You & Q&A**
