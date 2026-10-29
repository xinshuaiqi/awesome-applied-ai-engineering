# 03 · Workflows, Agents & Tools

> Agents are not magic — they are structured loops around LLM calls with tool access. Production agents require state management, error handling, observability, and human-in-the-loop design from day one.

---

## When NOT to Use Agents ← Read This First

Most production AI systems should **not** use autonomous agents. Use agents only when the task path cannot be enumerated in advance.

| Situation | Use Instead |
|---|---|
| Task has a fixed, known sequence of steps | Deterministic workflow / prompt chain |
| Task needs one LLM call + one tool call | Augmented LLM (not an agent loop) |
| Failure is expensive or hard to reverse | Human-in-the-loop workflow with approval gate |
| Latency must be <1s | Pre-defined pipeline; agents compound latency |
| You can write an if/else that covers 90% of cases | Write the if/else |

**The rule:** Start with augmented LLM → add deterministic workflow → only add agent loops when enumeration is genuinely impossible.

---

## Workflow vs Agent: Control Flow Comparison

| Dimension | Workflow | Agent |
|---|---|---|
| Control flow | Predefined by developer | Decided by LLM at runtime |
| Predictability | High — same input, same path | Low — path varies per run |
| Debuggability | Easy — trace the fixed steps | Hard — trace the LLM decisions |
| Latency | Predictable and bounded | Unbounded (agent decides step count) |
| Cost | Predictable | Unbounded token spend |
| When path is unknown | Cannot handle | Designed for this |
| Audit trail | Complete | Requires explicit logging |
| Best for | Data pipelines, document workflows, form processing | Open-ended research, multi-step planning, dynamic tool selection |

---

## Pattern Catalog

### Workflow Patterns (Deterministic Control)

**1. Prompt Chain**
Sequential LLM calls where each output feeds the next. Most reliable, easiest to debug.
```
Input → [Prompt A] → intermediate → [Prompt B] → intermediate → [Prompt C] → Output
```
Use for: multi-step document processing, staged extraction, progressive refinement.

**2. Routing**
A classifier directs input to the appropriate specialized prompt or pipeline.
```
Input → [Classifier] → Route A: simple QA
                     → Route B: complex analysis
                     → Route C: escalate to human
```
Use for: mixed query types, cost optimization by complexity, multi-domain systems.

**3. Parallelization**
Multiple LLM calls run simultaneously, results merged by aggregator.
```
Input → [Worker A] ↘
Input → [Worker B] → [Aggregator] → Output
Input → [Worker C] ↗
```
Use for: document section analysis, ensemble voting, multi-perspective evaluation.

**4. Orchestrator-Worker**
An orchestrator decomposes the task and dispatches to specialized workers.
```
Task → [Orchestrator: plans subtasks]
           → [Worker: web search]
           → [Worker: code execution]
           → [Worker: summarization]
       → [Orchestrator: synthesizes] → Output
```
Use for: complex research tasks, report generation, multi-source data collection.

**5. Evaluator-Optimizer**
Generator produces output, evaluator scores it, loop continues until quality gate is met.
```
Task → [Generator] → draft → [Evaluator] → score
                         ↑                      ↓ if below threshold
                         └──── [Refiner] ←──────┘
```
Use for: high-quality writing, code generation with test validation, structured output refinement.

### Agent Patterns (LLM-Controlled Flow)

**6. ReAct (Reason + Act)**
The foundational agent loop. LLM alternates between reasoning and tool calls.
```
Thought → Action → Observation → Thought → Action → ... → Final Answer
```
Risk: infinite loops, runaway token spend. Always set max iterations + budget limits.

**7. Planning**
LLM creates a full plan first, then executes step by step. More predictable than pure ReAct.
```
Plan: [Step 1, Step 2, Step 3] → Execute Step 1 → Replan if needed → ...
```

**8. Reflection**
Agent critiques its own output and iterates.
```
Draft → [Self-critique] → Identify gaps → [Revise] → [Self-critique] → ... → Final
```

**9. Multi-Agent**
Multiple specialized agents collaborate, with a coordinator managing the overall task.
```
Coordinator → [Research Agent] → findings
           → [Code Agent]     → implementation
           → [QA Agent]       → test results
           → Synthesis → Output
```

---

## Mental Model: Agents Are State Machines

A production agent is a **state machine** where:
- **States** = stages of task execution (planning, tool call, observation, decision, output)
- **Transitions** = LLM decisions + tool results
- **Guards** = validation, budget limits, human approval gates
- **Memory** = conversation history + external state store

If you can't draw the state machine, don't ship the agent.

---

## Orchestration Frameworks

| Framework | Pattern | Maturity | Best For |
|---|---|---|---|
| [LangGraph](https://github.com/langchain-ai/langgraph) | State machine | ⭐⭐⭐⭐⭐ | Resumable, stateful, HITL workflows |
| [AutoGen](https://github.com/microsoft/autogen) | Multi-agent conversation | ⭐⭐⭐⭐ | Agent-to-agent dialogue, code execution |
| [PydanticAI](https://github.com/pydantic/pydantic-ai) | Typed agents | ⭐⭐⭐⭐ | Structured output, testability, type safety |
| [CrewAI](https://github.com/crewAIInc/crewAI) | Role-based teams | ⭐⭐⭐ | Rapid prototyping, role-defined workflows |
| [OpenAI Swarm](https://github.com/openai/swarm) | Handoff patterns | ⭐⭐⭐ | Lightweight agent handoffs, minimal abstraction |
| [Temporal](https://github.com/temporalio/temporal) | Durable execution | ⭐⭐⭐⭐⭐ | Long-running workflows, retry/replay, compliance |
| [Prefect](https://github.com/PrefectHQ/prefect) | Dataflow | ⭐⭐⭐⭐ | Data pipeline + AI hybrid workflows |

---

## Model Context Protocol (MCP)

MCP is Anthropic's open standard for connecting AI agents to enterprise tools, replacing brittle custom integrations with a standardized protocol.

### How MCP Works
```
AI Agent (Client) ←→ MCP Protocol ←→ MCP Server ←→ Tool/Data Source
```

### Official MCP Servers
- **[modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers)** — Reference implementations:
  - `filesystem`, `github`, `postgres`, `sqlite`, `slack`, `google-drive`, `sentry`, `brave-search`

### MCP SDKs
- **[Python SDK](https://github.com/modelcontextprotocol/python-sdk)** — Official
- **[TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk)** — Official
- **[Go SDK](https://github.com/mark3labs/mcp-go)** — Community, production-grade

### Enterprise MCP Servers (Community)
- **Databricks MCP** — Unity Catalog tables, SQL warehouses, Jobs API
- **Snowflake MCP** — Query Snowflake via natural language
- **Salesforce MCP** — CRM data access for agents
- **[awesome-mcp (korchasa)](https://github.com/korchasa/awesome-mcp)** — Full community index

---

## Tool Design Principles

1. **Idempotent where possible** — Tool calls that can be retried safely
2. **Typed inputs and outputs** — Use JSON Schema strictly; validate before execution
3. **Fast, bounded scope** — Each tool does one thing
4. **Explicit error messages** — LLMs adjust behavior based on error text; be descriptive
5. **Cost/latency awareness** — Tag tools with expected cost and latency for router decisions
6. **Least privilege** — Tools should have the minimum permissions needed for the task

---

## Always-On Agents

### Patterns
- **Event-driven** — Trigger on webhook, cron, queue message. Process → respond → sleep.
- **Polling loop** — Check data source on interval. New data → process → act.
- **Streaming** — Consume live data stream (Kafka, Kinesis). Each message = agent invocation.

### Infrastructure Options
| Stack | Use When |
|---|---|
| LangGraph + LangGraph Platform | Stateful agents, built-in persistence, human-in-the-loop |
| Temporal + Python worker | Durable long-running tasks, retry/replay, compliance audit trail |
| Celery + Redis | Simple background task queues, existing Python stack |
| AWS Step Functions + Bedrock | Fully managed, AWS-native, compliance-heavy |

---

## Workflow Integration: Completing the Business Task

An agent that answers well but fails mid-process creates duplicate actions, half-updated systems, or lost tasks. Design the full task lifecycle:

```
Trigger → plan → validate plan → read tools → draft action
   → deterministic validation → approval (if required)
   → execute with idempotency key → verify in system of record
   → failure: retry → compensate → exception queue → human takeover
```

Key requirements: system-of-record writes go through deterministic validation (never raw model output), every side-effecting call carries an idempotency key, multi-step actions have compensation steps, and failed tasks land in a visible exception queue. See the full checklist in [10 · POC to Production](../10-poc-to-production/README.md#1-workflow-integration-from-answers-to-completes-the-task) and an idempotent tool-call example in [08 · Code Examples](../08-code-examples-and-starters/README.md#pattern-5-idempotent-tool-call-for-agent-actions).

---

## Memory Architecture

| Type | Storage | Lifetime | Use Case |
|---|---|---|---|
| In-context | Prompt window | Single session | Conversation history, current task state |
| External short-term | Redis, Postgres | Hours–days | Cross-session working memory |
| External long-term | Vector DB | Indefinite | User preferences, learned facts |
| Episodic | DB + embeddings | Indefinite | "Last time user asked X, they wanted Y" |

- **[mem0](https://github.com/mem0ai/mem0)** — Memory layer for AI agents. Automatic extraction + retrieval of long-term facts.
- **[Zep](https://github.com/getzep/zep)** — Enterprise memory store. Temporal knowledge graphs.
