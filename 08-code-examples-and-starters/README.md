# 08 · Code Examples & Starters

> Patterns you can copy and adapt. Treat these as starting points: add auth, timeouts, logging, and evals before production use.

---

## Starter Repositories

- **[LangChain Templates](https://github.com/langchain-ai/langchain/tree/master/templates)** — RAG, agents, extraction, summarization templates
- **[LlamaIndex Examples](https://github.com/run-llama/llama_index/tree/main/docs/docs/examples)** — End-to-end RAG notebooks and scripts
- **[Promptfoo Examples](https://github.com/promptfoo/promptfoo/tree/main/examples)** — Ready-to-run eval configs
- **[awesome-llm-apps](https://github.com/Shubhamsaboo/awesome-llm-apps)** — 100+ applied agent and RAG implementations

---

## Runnable Examples (Tested)

Both examples use only the Python standard library, run offline, and ship with unit tests. The "LLM" and the retriever are deliberately simple stand-ins: swap in your real model and index, and keep the surrounding control logic.

### Runnable Example: Ticket-Triage Agent

[`ticket-triage-agent/`](ticket-triage-agent/) shows how an agent completes a business task safely, not just how it answers.

```
propose (model) → validate (deterministic) → approval gate → saga execute → read-back verify → done
                                     any failure → compensate finished steps → exception queue
```

| Concern | Where it shows up |
|---|---|
| Deterministic validation before any write | `validate()` rejects out-of-policy model output; the CRM is never touched |
| Human approval | Refunds stop at `pending_approval` until `approve()`; rejected refunds never execute |
| Idempotency | Keys derive from `(task_id, step)`, so a retry after a lost response does not duplicate the write |
| Retry with backoff | `with_retry()` retries only `TransientError`; `PermanentError` fails fast |
| Compensation | A failed later step reverses earlier steps (cancel ticket, reverse refund) |
| Exception queue | Invalid output and failed tasks are queued with a reason, including cleanup that itself failed |
| Resume after crash | Task state is checkpointed to disk; a restarted worker skips finished steps and does not re-ask the model |
| Verification | The agent reads back the system of record rather than trusting the write response |

```bash
cd ticket-triage-agent
python3 ticket_agent.py        # prints a 3-scenario demo
python3 -m unittest -v         # 14 tests
```

Not included (add for production): a real queue and database, authentication, tracing, and a replay command for failed tasks.

### Runnable Example: Permission-Aware RAG

[`permission-aware-rag/`](permission-aware-rag/) shows retrieval that respects the source system's access controls.

| Rule | How it is enforced |
|---|---|
| Filter before scoring | `search()` selects visible chunks first; unauthorized text never reaches ranking or the prompt |
| Tenant isolation | `can_read()` requires matching tenant before any group or user grant is considered |
| Deny by default | A chunk with an empty ACL is readable by nobody |
| No ranking side channel | IDF statistics are computed over visible chunks only, so hidden documents cannot change scores or order |
| ACL freshness | `resync_acl()` applies permission changes; ACLs older than `max_acl_age_s` fail closed |
| Untrusted context | `build_prompt()` delimits retrieved text and tells the model to ignore instructions inside it |
| Audit | Every answer returns citations and logs which documents were used, per user |

```bash
cd permission-aware-rag
python3 -m unittest -v         # 11 tests
```

In a real system, apply the same filter as a metadata filter in your vector store (Qdrant, pgvector, OpenSearch) and sync ACLs from the source system on a schedule or by change events.

---

## Pattern 1: RAG API (FastAPI + LlamaIndex + Qdrant)

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from llama_index.core import VectorStoreIndex, Settings
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.anthropic import Anthropic
import qdrant_client

app = FastAPI()

client = qdrant_client.QdrantClient(url="http://qdrant:6333")
vector_store = QdrantVectorStore(client=client, collection_name="enterprise_docs")
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-large")
Settings.llm = Anthropic(model="claude-sonnet-4-5")
index = VectorStoreIndex.from_vector_store(vector_store)
query_engine = index.as_query_engine(streaming=True, similarity_top_k=5)

@app.post("/query")
async def query(q: str):
    async def generate():
        response = query_engine.query(q)
        for chunk in response.response_gen:
            yield f"data: {chunk}\n\n"
    return StreamingResponse(generate(), media_type="text/event-stream")
```

Production additions: user auth, ACL-filtered retrieval (see chapter 02), timeouts, tracing.

---

## Pattern 2: LangGraph Agent with Human Approval Gate

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, Annotated
import operator

class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    pending_action: dict | None

def plan(state: AgentState) -> AgentState:
    # LLM proposes an action; nothing executes yet
    return {"pending_action": {"tool": "send_email", "args": {}}}

def execute(state: AgentState) -> AgentState:
    action = state["pending_action"]
    result = TOOLS[action["tool"]](**action["args"])
    return {"messages": [result], "pending_action": None}

graph = StateGraph(AgentState)
graph.add_node("plan", plan)
graph.add_node("execute", execute)
graph.set_entry_point("plan")
graph.add_edge("plan", "execute")
graph.add_edge("execute", END)

# Execution pauses before "execute" until a human approves and resumes the run
app = graph.compile(checkpointer=MemorySaver(), interrupt_before=["execute"])
```

Use a durable checkpointer (Postgres/Redis) in production, not `MemorySaver`.

---

## Pattern 3: Structured Extraction with Validation

```python
from anthropic import Anthropic
from pydantic import BaseModel, Field

client = Anthropic()

class ContractRisk(BaseModel):
    party_name: str
    contract_value: float
    termination_clause: bool
    risk_level: str = Field(description="low, medium, or high")
    risk_reasons: list[str]

def extract_contract_risks(text: str) -> ContractRisk:
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        tools=[{
            "name": "extract_contract_risk",
            "description": "Extract structured risk data from contract text",
            "input_schema": ContractRisk.model_json_schema(),
        }],
        tool_choice={"type": "tool", "name": "extract_contract_risk"},
        messages=[{"role": "user", "content": f"Extract risks from:\n\n{text}"}],
    )
    block = next(b for b in response.content if b.type == "tool_use")
    return ContractRisk.model_validate(block.input)  # deterministic validation of model output
```

---

## Pattern 4: MCP Server Template

```python
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

server = Server("enterprise-data-server")

@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [types.Tool(
        name="query_sales_data",
        description="Query sales data by region and date range (read-only)",
        inputSchema={
            "type": "object",
            "properties": {
                "region": {"type": "string", "enum": ["NA", "EMEA", "APAC"]},
                "start_date": {"type": "string", "format": "date"},
                "end_date": {"type": "string", "format": "date"},
            },
            "required": ["region", "start_date", "end_date"],
        },
    )]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "query_sales_data":
        rows = query_sales(**arguments)  # parameterized, read-only query
        return [types.TextContent(type="text", text=rows.to_json(orient="records"))]
    raise ValueError(f"Unknown tool: {name}")

async def main():
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Pattern 5: Idempotent Tool Call for Agent Actions

Minimal sketch. For a complete tested version with retries, compensation, and resume, see the [Ticket-Triage Agent](#runnable-example-ticket-triage-agent).

```python
import hashlib

def idempotency_key(task_id: str, action: str, args: dict) -> str:
    raw = f"{task_id}:{action}:{sorted(args.items())}"
    return hashlib.sha256(raw.encode()).hexdigest()

def create_ticket(task_id: str, args: dict, store, crm):
    key = idempotency_key(task_id, "create_ticket", args)
    if (existing := store.get(key)):
        return existing                      # retry returns the same result, no duplicate
    result = crm.create_ticket(**args, external_id=key)
    store.set(key, result)
    return result
```

---

## Pattern 6: Eval Gate in CI

```python
import json, sys
from deepeval import evaluate
from deepeval.metrics import FaithfulnessMetric, HallucinationMetric, AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase

def run(test_cases: list[dict]) -> bool:
    metrics = [
        FaithfulnessMetric(threshold=0.85),
        HallucinationMetric(threshold=0.10),
        AnswerRelevancyMetric(threshold=0.80),
    ]
    cases = [LLMTestCase(**tc) for tc in test_cases]
    results = evaluate(cases, metrics)
    return all(r.success for r in results.test_results)

if __name__ == "__main__":
    with open("test_cases.json") as f:
        ok = run(json.load(f))
    sys.exit(0 if ok else 1)
```

Check the DeepEval version you install; result object shapes change between releases.

---

## Pattern 7: Cost-Aware Model Router

```python
from litellm import completion

MODELS = {
    "simple":   "anthropic/claude-haiku-4-5",
    "standard": "anthropic/claude-sonnet-4-5",
    "complex":  "anthropic/claude-opus-4-1",
}

def classify(prompt: str) -> str:
    r = completion(
        model=MODELS["simple"],
        messages=[{"role": "user", "content":
                   f"Classify as simple, standard, or complex. One word only.\n{prompt}"}],
        max_tokens=5,
    )
    label = r.choices[0].message.content.strip().lower()
    return label if label in MODELS else "standard"

def smart_completion(prompt: str):
    return completion(
        model=MODELS[classify(prompt)],
        fallbacks=[MODELS["standard"]],
        messages=[{"role": "user", "content": prompt}],
    )
```

Verify current model IDs against your provider before use.

---

## Local AI Dev Stack (Docker Compose)

```yaml
services:
  qdrant:
    image: qdrant/qdrant:latest
    ports: ["6333:6333"]
    volumes: ["qdrant_data:/qdrant/storage"]
  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: langfuse
      POSTGRES_PASSWORD: change-me
      POSTGRES_DB: langfuse
    volumes: ["postgres_data:/var/lib/postgresql/data"]
  langfuse:
    image: langfuse/langfuse:2
    ports: ["3000:3000"]
    depends_on: [postgres]
    environment:
      DATABASE_URL: postgresql://langfuse:change-me@postgres:5432/langfuse
      NEXTAUTH_SECRET: change-me
      SALT: change-me
      NEXTAUTH_URL: http://localhost:3000
  ollama:
    image: ollama/ollama:latest
    ports: ["11434:11434"]
    volumes: ["ollama_data:/root/.ollama"]

volumes:
  qdrant_data:
  postgres_data:
  ollama_data:
```
