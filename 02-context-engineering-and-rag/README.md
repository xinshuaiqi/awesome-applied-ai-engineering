# 02 · Context Engineering & RAG

> "Context engineering" is the discipline of building the right information into every LLM call. RAG is the most important production technique for grounding AI in real enterprise data.

---

## Decision Framework: What Kind of Context Do You Need?

Before picking a retrieval strategy, answer this first:

```
Is the information stable (documents, policies, knowledge base)?
    YES → Use RAG / retrieval
    NO  → Is it real-time system state (inventory, user account, live data)?
              YES → Use tool calls / function calling
              NO  → Is it a short, well-bounded reference (few pages)?
                        YES → Long context window (stuff it in)
                        NO  → Is it a learned skill or style (not facts)?
                                  YES → Fine-tuning
                                  NO  → Hybrid: RAG + tools
```

**The key boundary:**
- **Retrieval** = access to relatively stable knowledge (documents, FAQs, policies, past tickets)
- **Tool calls** = access to real-time state owned by other systems (CRM records, live inventory, user accounts, current prices)

Mixing these up is one of the most common architecture mistakes in enterprise AI.

### When to Use Each Approach

| Approach | Use When | Cost | Maintenance |
|---|---|---|---|
| **Long context** | Short, stable reference docs; few-shot examples; conversation history | Low latency cost, high token cost | None |
| **RAG** | Large knowledge base (>100 docs), frequently updated content | Medium | Embedding pipeline + index upkeep |
| **Tool calls** | Real-time data, system state, write operations | Low | API contract maintenance |
| **Fine-tuning** | Consistent style/format/domain vocabulary, not new facts | High (training cost) | Retraining on data drift |
| **Hybrid RAG + tools** | Enterprise workflows needing both knowledge and live data | Medium-High | Both pipelines |

---

## Why Context Engineering, Not Just Prompt Engineering

A prompt is a static string. Context engineering is the full pipeline that decides *what information* reaches the model *at inference time*: retrieval, re-ranking, chunking strategy, token budgets, conversation history management, and structured injection.

**The quality of your context determines 80% of your output quality.** Model choice is secondary.

---

## RAG Architecture Tiers

### Tier 1: Basic RAG (Prototype)
```
Query → Embed → Vector Search → Top-K Chunks → LLM → Answer
```
Fails in production due to: chunk boundary mismatches, embedding quality gaps, no re-ranking.

### Tier 2: Advanced RAG (Production Minimum)
```
Query → Query Rewriting → Hybrid Search (BM25 + Vector) → Re-ranking → Context Window Management → LLM
```

### Tier 3: Agentic RAG (Complex Domains)
```
Query → Router → [Multi-hop Retrieval | Sub-question Decomposition | GraphRAG | Tool Calls] → Synthesis → LLM
```

### Quality–Latency–Maintenance Cost Tradeoffs

| Approach | Quality | Latency | Maintenance Cost |
|---|---|---|---|
| Basic vector search | Medium | Fast (50–100ms) | Low |
| Hybrid BM25 + vector | High | Fast (80–150ms) | Low–Medium |
| Hybrid + cross-encoder rerank | Very High | Medium (300–600ms) | Medium |
| GraphRAG | Very High (multi-hop) | Slow (1–3s) | High |
| Agentic RAG | Highest | Variable (1–10s) | High |

Choose the minimum tier that meets your quality requirement. Don't default to the most complex.

---

## Core Components

### Embedding Models
| Model | Best For | Notes |
|---|---|---|
| `text-embedding-3-large` (OpenAI) | General enterprise text | Strong baseline, 3072 dims |
| `nomic-embed-text` | Local/private deployment | Via Ollama, competitive quality |
| `bge-large-en-v1.5` | Open source production | HuggingFace, great for fine-tuning |
| `cohere-embed-v3` | Multilingual enterprise | Best for non-English corpora |

### Chunking Strategies
- **Fixed-size** — Simple, fast. Fails at semantic boundaries. Use only for prototypes.
- **Recursive character splitting** — LangChain default. Better boundary handling.
- **Semantic chunking** — Split on embedding similarity drops. Best quality, slowest.
- **Document-aware** — Respect headers, sections, tables. Essential for enterprise docs.
- **Proposition chunking** — Convert paragraphs to atomic fact statements before embedding. Best recall for QA.

### Hybrid Search
Always combine sparse (BM25) and dense (vector) retrieval:
- BM25 wins on exact keyword matches (product codes, names, IDs)
- Vector wins on semantic similarity (synonyms, paraphrases, concepts)
- **Reciprocal Rank Fusion (RRF)** — standard merging strategy, no weight tuning required

### Re-ranking
Always re-rank top-K (50–100) results to final top-N (5–10) before passing to LLM:
- **Cross-encoders** — highest quality (BGE Reranker, Cohere Rerank). ~200ms latency.
- **LLM-as-judge re-ranking** — slower, higher cost, useful for complex queries
- **ColBERT** — token-level late interaction, fast and accurate

---

## Production Frameworks

### RAG Orchestration
- **[LlamaIndex](https://github.com/run-llama/llama_index)** — Most complete RAG framework. Routers, sub-question engines, knowledge graphs, multi-modal.
- **[LangChain](https://github.com/langchain-ai/langchain)** — Widest integration ecosystem. LCEL for composable retrieval chains.
- **[Haystack](https://github.com/deepset-ai/haystack)** — Pipeline-first design, strong enterprise document processing.

### Vector Databases
| DB | Strength | Self-Hosted | Managed |
|---|---|---|---|
| [Qdrant](https://github.com/qdrant/qdrant) | Fastest filtering, Rust core | ✅ | ✅ |
| [Weaviate](https://github.com/weaviate/weaviate) | Built-in BM25, multi-tenancy | ✅ | ✅ |
| [Pinecone](https://pinecone.io) | Easiest managed, serverless | ❌ | ✅ |
| [pgvector](https://github.com/pgvector/pgvector) | Already have Postgres? Use this | ✅ | ✅ |
| [Chroma](https://github.com/chroma-core/chroma) | Local dev, prototyping | ✅ | ❌ |
| [FAISS](https://github.com/facebookresearch/faiss) | Research, maximum performance | ✅ | ❌ |

### Re-ranking
- **[Rerankers](https://github.com/AnswerDotAI/rerankers)** — Unified API for cross-encoder reranking
- **[Cohere Rerank](https://cohere.com/rerank)** — Best managed re-ranking API
- **[FlashRank](https://github.com/PrithivirajDamodaran/FlashRank)** — Fastest local cross-encoder reranker

### Knowledge Graphs & GraphRAG
- **[Microsoft GraphRAG](https://github.com/microsoft/graphrag)** — Community detection + graph traversal for complex multi-hop queries. High setup cost; worth it for legal/medical/financial domains.
- **[LlamaIndex Property Graph](https://docs.llamaindex.ai/en/stable/module_guides/indexing/lpg_index_guide/)** — Lighter-weight graph RAG within LlamaIndex.

### Caching
- **[GPTCache](https://github.com/zilliztech/GPTCache)** — Semantic caching. Reduces cost 40–80% on repetitive enterprise queries.
- **[Redis](https://redis.io)** — Exact-match cache for frequent identical queries.

---

## Context Window Management

- **Lost in the Middle** — LLMs perform worst on information in the middle of long contexts. Put critical facts first and last.
- **Token Budget Enforcement** — Always count tokens before injection.
- **Dynamic Context Compression** — Summarize conversation history beyond a threshold.
- **[LLMLingua](https://github.com/microsoft/LLMLingua)** — Token compression. Up to 20x compression with <5% quality loss.

---

## Enterprise Document Processing

- **[Unstructured](https://github.com/Unstructured-IO/unstructured)** — Best open-source document parsing. Handles tables, figures, mixed layouts.
- **[LlamaParse](https://github.com/run-llama/llama_parse)** — Best for complex financial/legal PDFs.
- **[Azure Document Intelligence](https://azure.microsoft.com/en-us/products/ai-services/ai-document-intelligence)** — Enterprise OCR + structure extraction with HIPAA/SOC2 compliance.
- **[Docling](https://github.com/DS4SD/docling)** — IBM open-source, excellent table extraction.

---

## Data Readiness & Permission-Aware Retrieval

Retrieval technique is only half the problem. Before indexing a source, confirm: a named **data owner**, acceptable **quality**, a **refresh** process, stable **provenance** (document ID, version, location for citations), parseable **format**, and a known **sensitivity** class.

Retrieval must also honor the **source system's ACLs**: a user must never receive an answer derived from a document they cannot open.

```
Ingest:  document + ACL metadata (groups/users/tenant) → index with ACL fields
Query:   authenticate user → resolve groups → filter retrieval by ACL → retrieve → cited answer
Refresh: source ACL changes propagate to the index on a defined schedule
```

- Filter **at retrieval time**, not after generation
- Enforce tenant isolation in the index (separate collections or a mandatory tenant filter)
- Treat stale ACLs as a security defect; log which documents contributed to each answer

Full assessment checklist: [10 · POC to Production](../10-poc-to-production/README.md#2-data-readiness--permission-aware-retrieval).

---

## Anti-Patterns

| Anti-Pattern | What Goes Wrong | Fix |
|---|---|---|
| Using RAG for real-time state | Stale data, wrong answers on live inventory/accounts | Use tool calls instead |
| Using tool calls for stable docs | Unnecessary latency and API cost per query | Use RAG + caching |
| Chunk size = 512 everywhere | Cuts through sentences, breaks semantic units | Test multiple sizes; use semantic chunking |
| Pure vector search | Misses exact-match queries (IDs, codes, names) | Hybrid BM25 + vector always |
| No re-ranking | Top-K by similarity ≠ top-K by relevance | Add cross-encoder re-ranker |
| Stuffing all retrieved chunks in | Lost-in-the-middle, exceeds token budget | Select, compress, and order deliberately |
| Fine-tuning to inject new facts | Facts become stale; hallucination risk | Use RAG for facts, fine-tune for style only |
