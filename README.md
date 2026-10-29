# Awesome Applied AI Engineering [![Awesome](https://awesome.re/badge.svg)](https://awesome.re)

> A curated, production-quality collection of frameworks, architectural patterns, evaluation toolkits, MCP servers, real-world integrations, and LLMOps strategies for building enterprise-grade AI systems.

**Applied AI Engineering** is the discipline of taking AI out of experimental sandboxes and embedding it into large-scale, mission-critical production systems. Unlike academic ML research or consumer wrapper apps, applied AI engineering demands high system availability, strict observability, deterministic guardrails, and measurable ROI.

This list enforces a **"Production Quality" filter** — no abandonware, no trivial API wrappers, no Hello World demos. Every entry must solve a real architectural problem at scale.

---

## Repository Map

Each chapter is a standalone guide. This README is the curated link index; the chapters hold the depth.

| # | Chapter | What You Get |
|---|---|---|
| 01 | [Problem Discovery & System Design](01-problem-discovery-and-system-design/) | Evidence-based progression (prompt → retrieval → tools → agents), riskiest-assumption-first, requirements, architecture patterns |
| 02 | [Context Engineering & RAG](02-context-engineering-and-rag/) | Long context vs RAG vs tools vs fine-tuning decision guide, hybrid retrieval, reranking, permission-aware retrieval |
| 03 | [Workflows, Agents & Tools](03-workflows-agents-and-tools/) | Workflow and agent pattern catalog, when NOT to use agents, MCP, workflow integration |
| 04 | [Evaluation & Testing](04-evaluation-and-testing/) | Offline-to-production eval loop, tool comparison, agent trajectory evals, CI gates |
| 05 | [Production Architecture & LLMOps](05-production-architecture-and-llmops/) | AI gateway, reliability patterns, platform operations, observability, cost |
| 06 | [Security, Safety & Governance](06-security-safety-and-governance/) | Content guardrails plus agent runtime security, compliance, governance checklist |
| 07 | [Use Cases & Reference Architectures](07-use-cases-and-reference-architectures/) | Business-bottleneck-to-KPI framework, platform integrations, domain architectures |
| 08 | [Code Examples & Starters](08-code-examples-and-starters/) | RAG API, HITL agent, MCP server, idempotent tools, eval gate, model router |
| 09 | [Reading List & Courses](09-reading-list-and-courses/) | Books, courses, papers, newsletters, people to follow |
| 10 | [POC to Production](10-poc-to-production/) | Stage gates, workflow integration, data readiness, adoption and value realization |

**Evals are not production readiness.** Evals ask whether outputs are correct; chapter 10 asks whether the organization can run, govern, and benefit from the system.

---

## Contents

- [Guideline & Purpose](#guideline--purpose)
- [Foundation Concepts](#foundation-concepts)
- [Related Awesome Collections](#related-awesome-collections)
- [Applied AI In Practice](#applied-ai-in-practice)
  - [Enterprise Integrations (SAP, Salesforce, Databricks)](#enterprise-integrations)
  - [Always-On Agents & Agentic Systems](#always-on-agents)
  - [Evaluation & Red-Teaming](#evaluation--red-teaming)
  - [Model Context Protocol (MCP)](#model-context-protocol-mcp)
  - [System Integration Patterns](#system-integration-patterns)
- [Orchestration & Agent Frameworks](#orchestration--agent-frameworks)
- [Context, RAG & Knowledge Retrieval](#context-rag--knowledge-retrieval)
- [LLMOps & Observability](#llmops--observability)
- [Tools & Software](#tools--software)
- [People to Follow](#people-to-follow)
- [Contributing](#contributing)

---

## Guideline & Purpose

### What Belongs Here

This list accepts entries that meet **all three** of the following criteria:

1. **Production-Grade**: Actively maintained, with real-world adoption evidence (stars, production deployments, blog posts with metrics).
2. **Architecturally Significant**: Solves a real engineering problem — not just wrapping an API endpoint.
3. **Enterprise-Applicable**: Applicable to teams with real compliance, security, latency, and cost constraints.

### What Does NOT Belong Here

- Simple one-file OpenAI wrapper scripts
- Unmaintained repos (last commit >12 months for a pre-v1 project)
- Pure research papers without a production-ready implementation
- Generic "Awesome" link dumps without architectural commentary

### Anti-Patterns We Explicitly Call Out

| Technique | When It Fails (Enterprise Anti-Pattern) |
|---|---|
| Agentic Loops | Simple lookup tasks — causes severe latency and token burn |
| GraphRAG | Flat QA on unstructured PDF manuals — over-engineered |
| Local SLMs | Complex open-ended reasoning without fallback routing |
| Single-Model Architectures | Any task requiring multi-modal, cost, or latency tradeoffs |

---

## Foundation Concepts

> Core mental models every applied AI engineer must internalize before building production systems.

- **[Attention Is All You Need](https://arxiv.org/abs/1706.03762)** — The foundational transformer paper. Read the intuition, not just the math.
- **[Chain-of-Thought Prompting](https://arxiv.org/abs/2201.11903)** — Why decomposing reasoning into steps improves reliability.
- **[ReAct: Synergizing Reasoning and Acting](https://arxiv.org/abs/2210.03629)** — The pattern behind most modern agent loops.
- **[RAG: Retrieval-Augmented Generation](https://arxiv.org/abs/2005.11401)** — Grounding LLM outputs in verifiable external knowledge.
- **[Tool Use & Function Calling](https://platform.openai.com/docs/guides/function-calling)** — How LLMs invoke deterministic code safely.
- **[The Bitter Lesson](http://www.incompleteideas.net/IncompleteIdeas.html/the-bitter-lesson.html)** — Richard Sutton on why scale beats hand-engineering — essential for calibrating architectural bets.

---

## Related Awesome Collections

> High-signal upstream lists. Use these to discover new tools; apply our filter before promoting entries here.

- **[awesome-mcp](https://github.com/korchasa/awesome-mcp)** — Meticulously maintained MCP servers, clients, and SDKs across Python, TypeScript, Go, and Rust.
- **[awesome-llm-apps](https://github.com/Shubhamsaboo/awesome-llm-apps)** — 100+ applied agents and RAG implementations with full code examples.
- **[dair-ai/Prompt-Engineering-Guide](https://github.com/dair-ai/Prompt-Engineering-Guide)** — Gold standard for prompt technique documentation, including security/injection defenses.
- **[awesome-evals (benchflow-ai)](https://github.com/benchflow-ai/awesome-evals)** — Modern evaluation patterns and harness design for LLM pipelines.
- **[openai/openai-cookbook](https://github.com/openai/openai-cookbook)** — Official production-ready code examples, structured output patterns, and classification setups.
- **[addyosmani/agent-skills](https://github.com/addyosmani/agent-skills)** — Modular, production-ready coding agent skills by Google engineer Addy Osmani.

---

## Applied AI In Practice

> Real-world implementations. Each entry must link to working code or a documented production case study.

### Enterprise Integrations

Systems that connect LLM reasoning to live enterprise data and workflows.

- **[Databricks Mosaic AI](https://docs.databricks.com/en/machine-learning/index.html)** — Training, fine-tuning, and inference directly on proprietary data lakes. Native Unity Catalog governance.
- **[Snowflake Cortex](https://docs.snowflake.com/en/user-guide/snowflake-cortex/overview)** — LLM functions (COMPLETE, SUMMARIZE, EXTRACT_ANSWER) directly in SQL against Snowflake tables.
- **[SAP AI Core](https://help.sap.com/docs/sap-ai-core)** — Enterprise AI lifecycle management integrated into the SAP Business Technology Platform.
- **[Salesforce Einstein Copilot](https://help.salesforce.com/s/articleView?id=sf.copilot_intro.htm)** — Grounded CRM reasoning with strict data permission enforcement.
- **[LangChain SAP HANA Vector Store](https://python.langchain.com/docs/integrations/vectorstores/sap_hanavs)** — Production RAG directly against SAP HANA Cloud vector index.

### Always-On Agents

Agents that run continuously, respond to events, or manage long-horizon tasks.

- **[LangGraph](https://github.com/langchain-ai/langgraph)** — State-machine-based orchestration for reliable, resumable, interruptible agent loops.
- **[AutoGen](https://github.com/microsoft/autogen)** — Multi-agent conversation framework; production-tested at Microsoft scale.
- **[Temporal](https://github.com/temporalio/temporal)** — Durable execution engine for long-running AI workflows with built-in retry, timeout, and visibility.
- **[Celery + Redis for Agent Task Queues](https://docs.celeryq.dev/en/stable/)** — Battle-tested pattern for always-on background agent workers.

### Evaluation & Red-Teaming

Treating LLM correctness like a first-class engineering discipline.

- **[Promptfoo](https://github.com/promptfoo/promptfoo)** — CLI-first prompt testing and red-teaming. Assert on exact outputs, semantic similarity, and cost. CI-native.
- **[DeepEval](https://github.com/confident-ai/deepeval)** — Unit testing for LLMs. G-Eval, hallucination, faithfulness, answer relevancy metrics with Pytest integration.
- **[RAGAS](https://github.com/explodinggradients/ragas)** — RAG-specific evaluation: faithfulness, answer relevancy, context recall, context precision.
- **[Langfuse](https://github.com/langfuse/langfuse)** — Open-source LLM observability. Trace trees, prompt versions, cost dashboards, eval pipelines.
- **[Giskard](https://github.com/Giskard-AI/giskard)** — AI quality & security testing. Detects hallucinations, biases, prompt injections in production models.
- **[PromptBench](https://github.com/microsoft/promptbench)** — Adversarial robustness evaluation for LLMs — essential for red-teaming.

### Model Context Protocol (MCP)

The open standard for connecting AI agents to enterprise tools and data sources.

- **[Anthropic MCP Specification](https://spec.modelcontextprotocol.io/)** — The protocol spec. Read this first before implementing any server.
- **[Official MCP Servers](https://github.com/modelcontextprotocol/servers)** — Reference implementations: filesystem, GitHub, GitLab, Google Drive, Slack, Postgres, SQLite, Sentry.
- **[awesome-mcp (korchasa)](https://github.com/korchasa/awesome-mcp)** — Comprehensive index of community MCP servers.
- **[MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)** — Official Python SDK for building MCP servers and clients.
- **[MCP TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk)** — Official TypeScript SDK.
- **Databricks MCP Server** *(community)* — Exposes Unity Catalog tables, SQL warehouses, and Jobs API to agents.
- **[mcp-server-github](https://github.com/modelcontextprotocol/servers/tree/main/src/github)** — Search repos, read files, create PRs via MCP.

### System Integration Patterns

Architectural blueprints for connecting AI to production infrastructure.

- **Hybrid RAG (BM25 + Vector Search)** — Combine sparse keyword retrieval with dense semantic search; re-rank with a cross-encoder. Beat pure vector RAG by 15–30% on enterprise QA benchmarks.
- **GraphRAG** — Knowledge graph + embedding retrieval for deeply interconnected domains (legal, medical, financial). See [Microsoft GraphRAG](https://github.com/microsoft/graphrag).
- **Semantic Caching** — Cache similar queries to identical responses using embedding similarity. Reduces latency 40–80% on repetitive enterprise workflows. See [GPTCache](https://github.com/zilliztech/GPTCache).
- **Fallback Routing** — Route complex tasks to frontier models (Claude Opus, GPT-4o), simple tasks to SLMs (Llama 3.1 8B). Implement with [LiteLLM](https://github.com/BerriAI/litellm).
- **Human-in-the-Loop Checkpoints** — LangGraph's interrupt pattern or Temporal's signal API for mandatory approval gates in financial or compliance workflows.

---

## Orchestration & Agent Frameworks

| Framework | Strength | Production Maturity |
|---|---|---|
| [LangGraph](https://github.com/langchain-ai/langgraph) | Stateful, resumable, human-in-the-loop | ⭐⭐⭐⭐⭐ |
| [PydanticAI](https://github.com/pydantic/pydantic-ai) | Structured output, type safety, testability | ⭐⭐⭐⭐ |
| [AutoGen](https://github.com/microsoft/autogen) | Multi-agent conversations at scale | ⭐⭐⭐⭐ |
| [CrewAI](https://github.com/crewAIInc/crewAI) | Role-based agent teams, rapid prototyping | ⭐⭐⭐ |
| [OpenAI Swarm](https://github.com/openai/swarm) | Lightweight handoff patterns, minimal abstraction | ⭐⭐⭐ |
| [Temporal](https://github.com/temporalio/temporal) | Durable long-running workflows with full replay | ⭐⭐⭐⭐⭐ |

---

## Context, RAG & Knowledge Retrieval

- **[LlamaIndex](https://github.com/run-llama/llama_index)** — End-to-end RAG framework. Advanced routers, query engines, sub-question decomposition.
- **[LangChain](https://github.com/langchain-ai/langchain)** — Mature chain and retrieval abstractions; widest ecosystem of integrations.
- **[Weaviate](https://github.com/weaviate/weaviate)** — Production vector DB with built-in BM25 hybrid search and multi-tenancy.
- **[Qdrant](https://github.com/qdrant/qdrant)** — Rust-core vector DB; fastest filtering at scale, native payload indexing.
- **[Microsoft GraphRAG](https://github.com/microsoft/graphrag)** — Knowledge graph augmented retrieval for complex multi-hop queries.
- **[Rerankers](https://github.com/AnswerDotAI/rerankers)** — Unified API for cross-encoder reranking (Cohere, BGE, FlashRank). Essential post-retrieval step.
- **[GPTCache](https://github.com/zilliztech/GPTCache)** — Semantic caching layer for LLM calls. Reduces cost and latency dramatically.

---

## LLMOps & Observability

- **[Langfuse](https://github.com/langfuse/langfuse)** — Open-source LLM observability: traces, sessions, prompt management, evals, cost tracking.
- **[Arize Phoenix](https://github.com/Arize-ai/phoenix)** — AI observability and evaluation for LLMs and CV models.
- **[MLflow](https://github.com/mlflow/mlflow)** — Model lifecycle management, experiment tracking, and LLM evaluation. Native Databricks integration.
- **[LiteLLM](https://github.com/BerriAI/litellm)** — Unified API across 100+ LLM providers. Load balancing, fallbacks, cost tracking, rate limiting.
- **[vLLM](https://github.com/vllm-project/vllm)** — High-throughput LLM inference with PagedAttention. For self-hosted models.
- **[Ollama](https://github.com/ollama/ollama)** — Run open-source LLMs locally with one command. macOS, Linux, Docker.

---

## Tools & Software

### Inference & Model Access
- **[Ollama](https://ollama.ai)** — Local LLM runtime. Supports Llama, Mistral, Gemma, DeepSeek, Phi. One-line setup.
- **[Open Router](https://openrouter.ai)** — Unified API gateway to 200+ models (Claude, GPT, Gemini, Mistral, Llama). Pay-per-token.
- **[LiteLLM](https://github.com/BerriAI/litellm)** — OpenAI-compatible proxy for any provider. Critical for vendor-agnostic enterprise stacks.
- **[vLLM](https://github.com/vllm-project/vllm)** — Production-grade self-hosted inference. PagedAttention for maximum GPU throughput.

### Developer Tooling
- **[Cursor](https://www.cursor.com)** — AI-native IDE. Real-time multi-file context, agent mode, and codebase indexing.
- **[Claude Code](https://claude.ai/code)** — Anthropic's agentic CLI. Skills, hooks, MCP servers, multi-agent orchestration.
- **[GitHub Copilot](https://github.com/features/copilot)** — Inline completions, chat, and workspace awareness in VS Code / JetBrains.
- **[Aider](https://github.com/paul-gauthier/aider)** — Terminal-based AI pair programmer. Git-aware, multi-file edits.

### Data & Pipelines
- **[Databricks](https://databricks.com)** — Unified lakehouse for data, ML, and AI. Mosaic AI, Delta Lake, Unity Catalog.
- **[dbt](https://github.com/dbt-labs/dbt-core)** — SQL-first data transformation with lineage, tests, and docs. Standard enterprise data layer.
- **[Airflow](https://github.com/apache/airflow)** — Battle-tested workflow orchestration for data pipelines feeding AI systems.
- **[Prefect](https://github.com/PrefectHQ/prefect)** — Modern dataflow orchestration with native AI task support.

### Security & Governance
- **[Guardrails AI](https://github.com/guardrails-ai/guardrails)** — Real-time output validation: PII detection, topic filters, schema enforcement.
- **[NeMo Guardrails](https://github.com/NVIDIA/NeMo-Guardrails)** — Conversation policy enforcement for LLM applications. NVIDIA-backed.
- **[LLM Guard](https://github.com/protectai/llm-guard)** — Input/output scanning: prompt injection, sensitive data, toxicity.

---

## People to Follow

Engineers and researchers who publish production-first, signal-dense content.

| Person | Why Follow | Where |
|---|---|---|
| **Andrej Karpathy** | Intuitive explanations of transformers, LLMs, and AI systems from first principles | [@karpathy](https://twitter.com/karpathy) · [YouTube](https://www.youtube.com/@AndrejKarpathy) |
| **Harrison Chase** | LangChain/LangGraph creator. Real agentic patterns from building production frameworks | [@hwchase17](https://twitter.com/hwchase17) |
| **Shreya Shankar** | ML engineering, data-centric AI, eval methodology from a practitioner lens | [@sh_reya](https://twitter.com/sh_reya) |
| **Eugene Yan** | Applied ML at Amazon. Writes about RAG, recs, and system design for ML in production | [@eugeneyan](https://twitter.com/eugeneyan) · [eugeneyan.com](https://eugeneyan.com) |
| **Chip Huyen** | ML systems design, inference engineering, AI engineering career paths | [@chipro](https://twitter.com/chipro) · [huyenchip.com](https://huyenchip.com) |
| **Simon Willison** | LLMs, prompt engineering, AI tools journalism. Relentlessly practical | [@simonw](https://twitter.com/simonw) · [simonwillison.net](https://simonwillison.net) |
| **Jason Liu** | Structured outputs, instructor library, applying LLMs to production data pipelines | [@jxnlco](https://twitter.com/jxnlco) |
| **Lilian Weng** (OpenAI) | Deep dives on agents, RAG, alignment — the most cited practitioner blog | [lilianweng.github.io](https://lilianweng.github.io) |
| **Swyx** (shawn wang) | AI engineer community builder, latent space podcast, AI engineering landscape maps | [@swyx](https://twitter.com/swyx) · [latent.space](https://www.latent.space) |
| **Jeremy Howard** | fast.ai, practical deep learning, pushing for applied over theoretical AI | [@jeremyphoward](https://twitter.com/jeremyphoward) |

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full submission criteria and PR template.

**Quick rules:**
1. Open a PR with your addition under the correct section.
2. Provide: name, one-line description, link, and a **why it's production-quality** note.
3. No pure wrappers, no abandoned projects, no self-promotion without evidence.
4. Maintainers may request a production case study link before merging.

---

*Maintained by the community. PRs welcome. Star if this saves you a week of research.*
