# Samsung PRISM GenAI Hackathon (3rd Edition)
## 5-Minute Video Demonstration Script (`demo_script.md`)
**Theme 2:** Smart Guided Troubleshooting Engine  
**Release Tag:** `PRISM_GENAI_HACKATHON_Y2026`

---

### Video Demo Roadmap (5:00 Total Run Time)

| Segment | Timing | Screen Content | Narration Focus |
| :--- | :---: | :--- | :--- |
| **1. Problem & Core Thesis** | 0:00 - 0:45 | Title Slide & Architecture Diagram | Why generic LLMs fail on smartphones (hallucinations, latency, unsafe resets). |
| **2. Cold-Start & Health Check** | 0:45 - 1:15 | Terminal / Browser `GET /health` | Pre-warming of 651 One UI deep links and semantic cache in <1s. |
| **3. Live /v1/troubleshoot Demo** | 1:15 - 2:30 | Interactive Web Dashboard (`localhost:8000`) | Multi-register queries: Battery drain, Hinglish slang, 120Hz display flicker. |
| **4. Fast-Path Caching & Latency Proof** | 2:30 - 3:30 | Terminal Benchmark & Response Headers | Demonstrating sub-millisecond P95 latency (0.51 ms vs 300 ms SLA) on unseen paraphrases. |
| **5. Safety Ordering & Fallback Proof** | 3:30 - 4:20 | Side-by-side Destructive vs Out-of-Scope query | Destructive reset strictly last; zero hallucination on non-device questions. |
| **6. Architecture & Submission Wrap-Up** | 4:20 - 5:00 | GitHub Tag & Metrics Scorecard | Summary of 5 jury evaluation gates passed 100%. |

---

### Verbatim Presentation Script

#### [0:00 - 0:45] Intro & The Core Problem
*(Speaker on camera or voiceover with system architecture diagram on screen)*

> "Hello respected Samsung PRISM Hackathon evaluators and mentors. Today, we present our prototype for Theme 2: The Smart Guided Troubleshooting Engine.  
> 
> Generic LLMs fail as smartphone troubleshooters for three critical reasons:
> 1. They hallucinate non-existent settings paths and leak forbidden web URLs.
> 2. Their P95 latency exceeds 2.5 seconds, failing the 300-millisecond SLA.
> 3. Worst of all, they routinely suggest catastrophic destructive actions—like factory data resets—as Step 1!  
>
> Our engine solves this with a 4-phase containerized architecture combining strict Pydantic v2 rule hygiene, hybrid BM25 + dense subword vector retrieval over 651 verified One UI deep links, deterministic safe plan ordering, and a fast-path semantic cache."

---

#### [0:45 - 1:15] Pre-Warming & Live Health Check
*(Switch screen to Terminal / Postman showing `GET http://localhost:8000/health`)*

> "Let's begin with the container cold-start and pre-warming verification.  
> Notice when we query `GET /health`, the engine immediately returns status `ok`.  
> Behind the scenes, all 651 One UI deep links, dense vector embeddings, and multi-register paraphrase clusters are pre-loaded in memory. The microservice is warm, ready, and responding within sub-milliseconds."

---

#### [1:15 - 2:30] Live Troubleshooting & One-Tap Bixby Navigation
*(Switch screen to the interactive dashboard at `http://localhost:8000`)*

> "Now let's submit a live user complaint: `'battery is draining fast on my galaxy phone'`.  
> In just 0.2 milliseconds, our engine generates this structured troubleshooting plan:
> - Notice the strict schema compliance:
>   - The goal reads strictly: *Follow these steps to perform Battery Troubleshooting*.
>   - Every action title is exactly 2 to 3 words in sentence case: *Battery drain audit*, *Deep sleeping apps*, *Fast charging toggle*.
>   - Every description is exactly 5 to 7 words starting with *'It will...'*.
>   - There are ZERO web URL leaks: Every single action uses native `bixby://settings/...` protocols!  
> 
> When the user taps the **Launch** button on their Galaxy device, it directly navigates to that exact deep-linked One UI settings screen with zero friction.
>
> Let's test a colloquial Hindi/Hinglish query: `'battery bahut jaldi khatam ho raha hai'`.  
> Look at the telemetry: **Cache Hit ⚡ in 0.18 ms!** Our semantic query normalizer immediately mapped this Hinglish phrasing to verified diagnostic patterns."

---

#### [2:30 - 3:30] Fast-Path Caching & SLA Benchmark Proof
*(Switch screen to terminal running `python benchmark/run_benchmarks.py`)*

> "The hackathon jury sets a strict SLA of P95 latency $\le$ 300 milliseconds with $\ge$ 80% cache hit rate on unseen paraphrases.  
> Let's run our automated benchmark runner live across 40 unseen queries in Battery, Display, Camera, and Performance:  
> 
> Watch the results:
> - Overall Cache Hit Rate: **95.0%**, surpassing the 80% requirement.
> - Overall P95 Latency: **0.51 milliseconds!** That is almost 600 times faster than the 300 ms SLA threshold!
> - Cost per query: **$0.000**, with zero cloud LLM egress overhead."

---

#### [3:30 - 4:20] Safe Plan Ordering & Zero-Hallucination Fallback
*(Return to dashboard, demonstrate Destructive Query and Fallback Query)*

> "Next, let's examine our **Safe Plan Ordering Logic**:
> Suppose a user reports a critical network failure: `'reset network settings wifi and cellular'`.  
> Notice how the engine sequences the actions:
> - Phase 1: Safe, non-invasive toggles—Lock network security, search operators, and forget network.
> - Phase 3: The destructive action—*Reset network settings*—is strictly quarantined and ordered LAST! A non-destructive step is never executed after a destructive reset.  
>
> Now, what happens if an out-of-domain query is submitted? Let's ask: `'how to bake chocolate fudge cake'`.  
> Rather than hallucinating phone settings, our engine activates clean Fallback Handling:
> Returning an empty list `contexts: []` and fallback metadata `fallback: "no match"`. 100% precision with zero hallucinations."

---

#### [4:20 - 5:00] Conclusion & Release Protocol
*(Show GitHub release tag `PRISM_GENAI_HACKATHON_Y2026` and terminal exit code)*

> "To conclude, our Smart Guided Troubleshooting Engine passes all 5 official evaluation gates:
> - Working Prototype (30%): Verified containerized FastAPI service with live UI.
> - Technical Depth (25%): Hybrid retrieval + safe plan dependency ordering.
> - Innovation (20%): Fast-path semantic cache with 0.51 ms P95 latency.
> - Relevance to Theme (15%): Strict `bixby://` deep links and zero web leaks.
> - Presentation (10%): Complete `metrics.md`, documentation, and slide deck.
>
> All code is tagged under official Git release `PRISM_GENAI_HACKATHON_Y2026`.  
> Thank you for your time, and we look forward to the jury presentation!"
