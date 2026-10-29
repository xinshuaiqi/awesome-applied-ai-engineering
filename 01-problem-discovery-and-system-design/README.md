# 01 · Problem Discovery & System Design

> Before writing a single line of AI code, understand the problem space and design the system architecture. Most AI project failures are scoping failures, not model failures.

---

## Evidence-Based Progression ← Start Here

**The single most important rule in applied AI engineering:**

```
Start simple. Add complexity only when evidence demands it.

Step 1: Prompt only          → Can an improved prompt solve 80% of cases?
Step 2: Add retrieval        → Does grounding in external knowledge fix the gap?
Step 3: Add tools            → Does the model need to take actions or query live state?
Step 4: Add agents           → Only when the task path cannot be enumerated in advance.
```

Each step should be **driven by eval data**, not intuition. If you can't measure improvement, you can't justify the added complexity — and agents at step 4 carry real costs: non-determinism, latency, error compounding, and debugging difficulty.

---

## Validate the Riskiest Assumption First

Every AI project rests on assumptions. List them, rank them by risk, and **test the most dangerous one first** — before building infrastructure around it.

Common high-risk assumptions:
- "The model can reliably extract X from unstructured text" → test with 50 real examples
- "Users will phrase queries in a way that matches our retrieval" → test with real user sessions
- "Latency of <3s is acceptable for this workflow" → validate with stakeholders before building
- "We can get access to the data we need" → confirm data contracts before committing to architecture

**Do not build a retrieval pipeline to test a retrieval hypothesis. Build the eval first.**

---

## Framing the Problem

The first question is never "which model?" — it's "should this be AI at all?"

| Signal | Use AI | Don't Use AI |
|---|---|---|
| Output space | Open-ended, natural language, ambiguous | Deterministic, rule-based, structured |
| Data availability | Large corpus of relevant examples | Sparse, no ground truth |
| Failure tolerance | Soft failures acceptable | Zero-tolerance (safety-critical) |
| Latency budget | >200ms acceptable | Hard real-time requirements |
| Cost structure | Per-query cost OK | High-volume, fixed compute preferred |

### The "Simpler First" Check
Before adding a complex AI layer, ask: can a simpler retrieval, search, or rule-based system solve 80% of this with 5% of the effort? Often yes.

---

## Requirements: Functional vs Non-Functional

Document both before designing. AI systems routinely fail non-functional requirements even when functional requirements are met.

### Functional Requirements
- What inputs does the system accept? (text, documents, structured data, images)
- What outputs does it produce? (answers, structured JSON, actions, summaries)
- What business process does it replace or augment?
- What are the acceptance criteria for a "correct" output?

### Non-Functional Requirements (often ignored, always critical)
| Dimension | Questions to Answer |
|---|---|
| Latency | P50/P95 targets? Streaming acceptable? Async OK? |
| Throughput | Peak queries per second? Burst patterns? |
| Cost | Per-query budget? Monthly ceiling? |
| Accuracy | Minimum quality threshold? How measured? |
| Privacy | PII handling? Data residency? Vendor restrictions? |
| Compliance | SOC2? HIPAA? GDPR? Audit trail required? |
| Availability | SLA? Fallback behavior during outage? |
| Explainability | Must decisions be auditable? Citation required? |

---

## System Design Principles

### 1. Design for Non-Determinism First
LLMs are stochastic. Every design decision must account for variable outputs:
- Define "good enough" outputs before building (acceptance criteria)
- Plan fallback paths for every AI call
- Store inputs + outputs for every production call (observability from day one)

### 2. Separate Concerns
```
[User Request]
     ↓
[Input Validation & Routing]        ← deterministic
     ↓
[Context Assembly / RAG]            ← semi-deterministic
     ↓
[LLM Inference]                     ← non-deterministic
     ↓
[Output Validation & Formatting]    ← deterministic
     ↓
[Response + Side Effects]
```
Each layer is independently testable. The deterministic layers wrap the non-deterministic core.

### 3. Latency & Cost Budget Design
Map your P50/P95 latency budget before choosing a model:

| Tier | Model Examples | Typical Latency | Cost/1M tokens |
|---|---|---|---|
| Frontier | Claude Opus, GPT-4o | 3–8s | $15–$30 |
| Balanced | Claude Sonnet, GPT-4o-mini | 1–3s | $1–$5 |
| Fast/Cheap | Claude Haiku, Llama 3.1 8B | 0.3–1s | $0.10–$0.50 |
| Local | Ollama + Phi-3, Gemma 2B | 0.1–0.5s | $0 (compute) |

---

## Architecture Patterns

### Pattern 1: Gateway + Router
A single entry point that classifies intent and routes to specialized sub-agents or retrieval paths.
```
User → Intent Classifier → [Simple RAG | Complex Agent | Direct Answer | Handoff]
```
**When to use:** Diverse query types, mixed latency requirements, cost optimization critical.

### Pattern 2: Agentic Loop with Human Checkpoints
```
Task → Plan → [Execute → Observe → Decide] loop → Checkpoint → Output
```
**When to use:** Multi-step tasks, operations with side effects, compliance requirements.

### Pattern 3: Ensemble + Judge
Run 2–3 model calls in parallel, use a judge LLM (or deterministic rules) to select the best output.
**When to use:** High-stakes outputs (legal, medical, financial), accuracy > latency.

### Pattern 4: Retrieval-First, Generation-Second
Never generate facts from model weights alone. Always retrieve first.
**When to use:** Enterprise knowledge bases, compliance-sensitive domains, any domain with recent data.

### Pattern 5: Offline + Online Split
```
Offline: Embed all docs → store in vector DB → pre-compute summaries
Online:  User query → embed → retrieve → generate
```
Keep expensive preprocessing offline. Online path must be fast.

---

## Tools for System Design

- **[Excalidraw](https://excalidraw.com)** — Collaborative whiteboarding for AI architecture diagrams
- **[C4 Model](https://c4model.com)** — Structured approach to communicating software architecture at 4 levels of abstraction
- **[Mermaid](https://mermaid.js.org)** — Code-first diagrams in Markdown; excellent for documenting agent flows in-repo
- **[draw.io / diagrams.net](https://diagrams.net)** — Free diagramming with AWS/Azure/GCP shape libraries

---

## Reading

- [Designing ML Systems — Chip Huyen](https://www.oreilly.com/library/view/designing-machine-learning/9781098107956/) — essential for production ML/AI architecture
- [AI Engineering — Chip Huyen](https://www.oreilly.com/library/view/ai-engineering/9781098166298/) — covers LLM-specific engineering challenges
- [The Bitter Lesson — Richard Sutton](http://www.incompleteideas.net/IncompleteIdeas.html/the-bitter-lesson.html) — calibrate your architectural bets against scale
