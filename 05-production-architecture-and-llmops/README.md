# 05 · Production Architecture & LLMOps

> Getting an AI system to work in a notebook is 10% of the work. Getting it to run reliably, cost-efficiently, and observably at enterprise scale is the other 90%.

---

## The LLMOps Stack

```
┌─────────────────────────────────────────────────────────────┐
│              AI Gateway Layer                               │
│   LiteLLM · Open Router · Azure APIM · Custom Gateway       │
├─────────────────────────────────────────────────────────────┤
│              Orchestration Layer                            │
│   LangGraph · Temporal · Prefect · Airflow                  │
├─────────────────────────────────────────────────────────────┤
│              Observability Layer                            │
│   Langfuse · Phoenix · MLflow · W&B Weave                   │
├─────────────────────────────────────────────────────────────┤
│              Caching & Cost Layer                           │
│   GPTCache · Redis · Prompt Caching · Model Routing         │
├─────────────────────────────────────────────────────────────┤
│              Data & Feature Layer                           │
│   Vector DBs · Feature Stores · Databricks · Snowflake      │
└─────────────────────────────────────────────────────────────┘
```

**Core principle: Probabilistic models must be wrapped in deterministic business and security boundaries.**
Never let a model directly execute unvalidated system writes. Every side effect should pass through a deterministic validation + approval layer.

---

## AI Gateway Design

An AI Gateway is the single entry point for all LLM traffic. It handles routing, security, cost, and observability in one layer — keeping application code clean.

```
Application → AI Gateway → [Model A / Model B / Local Model]
                  │
                  ├── Auth & rate limiting (per team / per user)
                  ├── Request validation & PII scrubbing
                  ├── Model routing (by cost, latency, task type)
                  ├── Semantic caching (skip LLM for similar queries)
                  ├── Fallback routing (provider outage handling)
                  ├── Cost tracking & budget enforcement
                  └── Full request/response logging
```

### Gateway Implementation Options
- **[LiteLLM Proxy](https://github.com/BerriAI/litellm)** — Most complete open-source AI gateway. OpenAI-compatible API, 100+ providers, team-level budgets, rate limiting, fallbacks. Best for most enterprises.
- **[Azure APIM + OpenAI](https://learn.microsoft.com/en-us/azure/api-management/azure-openai-enable-semantic-caching)** — Native Azure integration with semantic caching, token metering, and AD-based auth.
- **[Portkey](https://portkey.ai)** — Managed AI gateway with caching, routing, and observability.
- **[Kong AI Gateway](https://konghq.com/products/kong-ai-gateway)** — Extension of Kong API Gateway for LLM traffic.

---

## Production Reliability

### Distinguish Failure Types

| Failure Type | Examples | Response Strategy |
|---|---|---|
| **Model quality failure** | Hallucination, wrong format, refused to answer | Retry with different prompt, escalate to stronger model, flag for human review |
| **Infrastructure failure** | Provider 5xx, timeout, rate limit hit | Circuit breaker, fallback to different provider, queue and retry |
| **Integration failure** | Tool API down, DB connection lost, auth expired | Retry with backoff, return partial result, queue for later completion |
| **Data failure** | Stale index, missing document, wrong retrieval | Fallback to broader search, flag for index rebuild |

### Reliability Patterns

**SLO Design for AI Systems**
```
Define before building:
- P50 latency target: 2s
- P95 latency target: 8s
- P99 latency target: 20s (streaming acceptable)
- Error rate budget: <0.5%/month
- Hallucination rate: <2% on evals (checked weekly)
```

**Circuit Breaker**
```python
from litellm import completion

# LiteLLM handles circuit breaking natively
response = completion(
    model="anthropic/claude-3-5-sonnet",
    fallbacks=["openai/gpt-4o", "anthropic/claude-3-haiku"],
    num_retries=3,
    timeout=30,
    context_window_fallback_dict={"anthropic/claude-3-5-sonnet": "anthropic/claude-3-haiku"}
)
```

**Graceful Degradation Ladder**
```
Primary: Claude Opus (full quality)
    ↓ on timeout/rate limit
Fallback 1: Claude Sonnet (fast, good quality)
    ↓ on rate limit
Fallback 2: Claude Haiku (fast, acceptable quality)
    ↓ on full outage
Fallback 3: Cached response / deterministic rule-based answer
    ↓ if none available
Final: Return "service temporarily unavailable" with human escalation
```

**Timeouts at Every Layer**
```python
# Set timeouts at application level, not just network level
TIMEOUT_CONFIG = {
    "intent_classifier": 2,    # Fast, cheap model
    "retrieval": 5,            # Vector DB + reranking
    "generation": 30,          # Main LLM call
    "tool_execution": 10,      # External API calls
    "total_request": 45        # Hard wall for entire request
}
```

**Dead Letter Queue for Agent Tasks**
```
Agent Task → Task Queue
                  ↓
            Worker (attempt 1)
                  ↓ fails
            Retry Queue (wait 30s, attempt 2)
                  ↓ fails
            Retry Queue (wait 5m, attempt 3)
                  ↓ fails
            Dead Letter Queue → Alert on-call → Human review
```

**Checkpoint / Resume for Long-Running Agents**
Use Temporal or LangGraph persistence to checkpoint agent state. If the worker crashes mid-task, it resumes from the last checkpoint — not from the beginning.

**Incident Runbook Template**
Every AI service should have:
1. How to check model provider status (status page URLs)
2. How to switch to fallback provider manually
3. How to disable specific agent tools in production
4. How to roll back prompt version
5. How to trigger eval suite manually and interpret results
6. On-call escalation path for data/privacy incidents

---

## Inference Infrastructure

### Managed APIs
- **[LiteLLM](https://github.com/BerriAI/litellm)** — Unified API across 100+ providers. Load balancing, fallbacks, cost tracking.
  ```python
  from litellm import completion
  response = completion(model="anthropic/claude-3-5-sonnet-20241022", messages=[...])
  ```
- **[Open Router](https://openrouter.ai)** — 200+ models, pay-per-token. Good for model comparison.

### Self-Hosted Inference
- **[vLLM](https://github.com/vllm-project/vllm)** — Production-grade. PagedAttention for 2–4x GPU throughput.
- **[Ollama](https://github.com/ollama/ollama)** — Local LLM runtime. Air-gapped or privacy-first deployments.
- **[TGI](https://github.com/huggingface/text-generation-inference)** — HuggingFace's production server. Flash Attention, continuous batching.

### Model Routing Strategy
```
High-complexity task    → Claude Opus / GPT-4o       ($15–30/1M tokens)
Standard task           → Claude Sonnet / GPT-4o-mini ($1–5/1M tokens)
Simple classification   → Claude Haiku / Llama 3.1 8B ($0.10–0.50/1M tokens)
Private/offline task    → Ollama + local model        ($0)
```

---

## Platform Operations (Multi-Team Scale)

When multiple teams build AI features, platform chaos emerges: duplicate integrations, untracked costs, inconsistent security, no discoverability.

### What a Platform Team Provides

| Capability | What It Solves |
|---|---|
| **Agent/Tool Registry** | Teams can discover existing tools instead of rebuilding them |
| **Shared Gateway** | Centralized auth, cost attribution, rate limits per team |
| **Model Version Pinning** | Apps don't break silently when providers update models |
| **Dev/Test/Prod Environments** | Safe experimentation without hitting production data or costs |
| **Prompt Registry** | Version-controlled prompts with rollback, shared across teams |
| **Cost Chargeback** | Each team sees their actual LLM spend; prevents runaway usage |
| **Canary Deployment** | New model or prompt versions roll out gradually with monitoring |

### Team Responsibility Boundaries

| Platform Team | Application Teams |
|---|---|
| AI gateway, auth, rate limits | Business logic, prompts, evals |
| Shared vector DB infrastructure | Domain-specific indexes |
| Security guardrails (PII, toxicity) | Domain-specific output validation |
| Cost monitoring & budget alerts | Per-feature cost optimization |
| Model version policy | Model selection within policy |
| On-call for infra failures | On-call for model quality issues |

### Tools
- **[MLflow Model Registry](https://mlflow.org/docs/latest/model-registry.html)** — Stage-based model approval (Staging → Production)
- **[Langfuse](https://github.com/langfuse/langfuse)** — Prompt registry + versioning + team-level dashboards
- **[LiteLLM](https://github.com/BerriAI/litellm)** — Team-level budgets, cost attribution by tag

---

## Observability

Every LLM call must capture: input, output, latency (TTFT + total), token counts + cost, model + version, trace ID, user/session ID.

### Tools
- **[Langfuse](https://github.com/langfuse/langfuse)** — Best open-source. Trace trees, prompt versioning, cost dashboards, evals, self-hostable.
- **[Arize Phoenix](https://github.com/Arize-ai/phoenix)** — Trace-based, strong LlamaIndex + LangChain integration.
- **[MLflow](https://github.com/mlflow/mlflow)** — Experiment tracking + LLM traces. Native Databricks.
- **[OpenTelemetry](https://opentelemetry.io)** — Vendor-neutral instrumentation. Export to Datadog, Jaeger, Honeycomb.

---

## Cost Optimization

### Prompt Caching
- **Anthropic** — 90% discount on cached prefix tokens (>1024 tokens). Use `cache_control`.
- **OpenAI** — Automatic caching for prompts >1024 tokens, 50% discount.

### Semantic Caching
Cache similar queries to reuse responses. **[GPTCache](https://github.com/zilliztech/GPTCache)** reduces cost 40–80% on repetitive enterprise queries.

### Token Optimization
- Count before calling — reject oversized inputs at the gate
- Compress retrieved context — LLMLingua can reduce 20x with <5% quality loss
- Batch API — 50% cost discount for non-real-time workloads (both OpenAI and Anthropic)

---

## Anti-Patterns

| Anti-Pattern | Impact | Fix |
|---|---|---|
| Single model, no fallback | Provider outage = full outage | LiteLLM with fallback routing |
| No prompt versioning | Can't roll back bad prompt changes | Langfuse prompt management |
| Synchronous LLM in hot path | Cascading timeouts under load | Async + queue-based processing |
| Cost monitoring as afterthought | Surprise $10K bills | Instrument from day one |
| No timeout at every layer | Slow tool hangs the whole agent | Set timeouts at every I/O boundary |
| No dead letter queue for agents | Silent task failures | DLQ + alerting on all agent tasks |
