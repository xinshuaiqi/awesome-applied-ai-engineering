# 07 · Use Cases & Reference Architectures

> Production-proven patterns for specific enterprise domains and integration targets. Each use case is framed as **business bottleneck → ML/LLM division of labor → what the agent can do → risks & KPIs** — not as a feature list.

---

## Use Case Framework

| Domain | Business Bottleneck | Traditional ML vs LLM Split | What the Agent Can Do | Key Risks | KPIs |
|---|---|---|---|---|---|
| **Customer Service** | High ticket volume, slow resolution, inconsistent answers | ML: intent classification, routing, churn prediction. LLM: answer drafting, summarization | Triage, retrieve policy, draft reply, update ticket, escalate with summary | Wrong policy cited, tone failures, PII leakage | First-contact resolution, handle time, CSAT, escalation rate |
| **Supply Chain** | Disruption response is manual; data spread across ERP/WMS/TMS | ML: demand forecasting, anomaly detection. LLM: exception explanation, supplier comms | Detect exception, gather context from systems, propose re-route, draft supplier notice | Acting on stale data, unvalidated order changes | OTIF, expedite cost, exception cycle time |
| **Finance** | Month-end close, reconciliation, variance explanation | ML: anomaly/fraud scoring, forecasting. LLM: variance narrative, document extraction | Match invoices, explain variances with citations, draft commentary | Hallucinated figures, audit trail gaps | Close cycle days, reconciliation exceptions, auditor rework |
| **HR** | Repetitive policy questions, slow onboarding, screening load | ML: attrition modeling, matching. LLM: policy Q&A, job-description drafting | Answer policy questions with citations, onboarding checklists, route cases to HRBP | Bias, sensitive data exposure, over-automation of decisions | Case deflection, time-to-resolution, employee satisfaction |
| **Legal & Compliance** | Contract review backlog, regulatory change tracking | ML: clause classification. LLM: clause extraction, redlining, summary | Extract clauses, compare to playbook, suggest redlines, flag deviations | Fabricated citations, privilege leakage | Review cycle time, deviation catch rate, attorney edit rate |
| **Security Operations** | Alert fatigue, slow triage | ML: detection, scoring. LLM: alert enrichment, incident summary | Enrich alert, correlate sources, draft incident report, propose containment | Agent with excessive privileges, injection via log content | MTTD/MTTR, false-positive triage time |
| **IT Service** | Repetitive tickets, access requests, knowledge sprawl | ML: ticket routing. LLM: troubleshooting guidance | Resolve known issues, reset/provision with approval, document fixes | Unapproved access changes | Auto-resolution rate, MTTR, approval turnaround |

**Selection rule:** pick use cases with a measurable baseline, a clear owner, accessible data, and bounded blast radius. Avoid starting with the most impressive demo.

---

## Enterprise Platform Integrations

### Databricks
- **Mosaic AI** — Model serving, AI Playground, MLflow evaluation
- **Unity Catalog** — Governance for data, models, features, AI assets
- **Genie** — Natural language to SQL over lakehouse data
- **Vector Search** — Managed vector index inside the workspace

```
Data Sources → Delta Lake (bronze/silver/gold) → Vector Search → Model Serving → Unity Catalog governance → App/API
```

### Snowflake
- **Cortex LLM Functions** — `COMPLETE()`, `SUMMARIZE()`, `EXTRACT_ANSWER()` in SQL
- **Cortex Search / Analyst** — Hybrid search and natural-language-to-SQL
- **Arctic Embed** — Open embedding model optimized for retrieval

### SAP
- **SAP AI Core** — LLM lifecycle within SAP BTP
- **HANA Cloud Vector Engine** — Native vector search; see [LangChain HANA Vector Store](https://python.langchain.com/docs/integrations/vectorstores/sap_hanavs)

```
SAP documents → HANA Vector Engine → RAG chain → LLM → Fiori UI / Teams bot
```
Writes back to SAP must go through deterministic validation and approval, never directly from model output.

### Salesforce
- **Agentforce** — Agents acting on Salesforce data (cases, records, flows)
- **Data Cloud** — Embeddings and unified customer data for RAG

---

## Domain Reference Architectures

### Financial Services — Earnings Analysis Agent
```
10-K/10-Q PDFs + transcripts → structured parsing → chunk + embed (Qdrant/pgvector)
→ hybrid RAG with citation tracking → analysis generation
→ citation verification pass → human review gate → report
```
Every numerical claim cites source + page. Run hallucination evals on every output. Store full trace for audit.

### Healthcare & Life Sciences — Clinical Documentation Assistant
```
EHR data (de-identified via Presidio) → on-prem or BAA-covered inference
→ clinical NER → structured FHIR-compatible output → clinician review (mandatory) → EHR write-back
```

### Legal — Contract Review Agent
```
Contract PDFs → layout-aware parsing → clause extraction/classification
→ risk scoring vs playbook (RAG over standard terms) → redline suggestions → attorney approval
```
Never cite cases that cannot be verified against a curated source.

### Customer Support — Tiered Agent
```
Query → intent classification
   FAQ       → RAG over knowledge base → answer
   Technical → agent with ticket/CRM/product tools
   Escalate  → summary + human handoff
→ response + CSAT logging → weekly eval on CSAT correlation and hallucination rate
```

---

## Case Study Template (Synthetic / De-identified)

Use this structure for community-contributed case studies. Replace all customer data with synthetic equivalents.

```
1. Business problem and baseline metrics
2. Why AI (and why not simpler automation)
3. Architecture diagram (data → retrieval → model → validation → system of record)
4. Evidence-based progression: what was tried first, what was added and why
5. Eval design: golden set size, metrics, release gate
6. Failure handling: what happens on tool/model/data failure
7. Security & permissions model
8. Pilot results: adoption rate, quality, cost, cycle time vs baseline
9. What failed and what we changed
```

### Example Sketch: Digital Farm Advisor (Synthetic)
- **Problem:** Agronomists spend hours correlating sensor, weather, and field-note data to advise growers.
- **Split:** ML for yield/anomaly prediction from sensor streams; LLM for explaining findings and drafting recommendations from field notes and agronomy documents.
- **Architecture:** Sensor/weather ingestion → lakehouse → feature tables + document index → agent with read-only data tools → recommendation draft → agronomist approval → grower-facing summary.
- **Boundary:** The agent never writes prescriptions or equipment commands; humans approve, deterministic systems execute.

### Example Sketch: Medical Information Request Assistant (Synthetic)
- **Problem:** Medical information teams answer repetitive inquiries from a large, versioned literature and label corpus.
- **Architecture:** Versioned document ingestion → permission-aware retrieval → cited answer drafting → medical reviewer approval → response library update.
- **Boundary:** Every claim cited to an approved source; unapproved or off-label content is routed to a human.

---

## Always-On Agent Architectures

### Event-Driven Agent (Slack/Email)
```
Webhook → queue (SQS/Redis) → agent worker (LangGraph/Temporal)
→ tools [CRM read, calendar, draft] → human approval for high-stakes actions → send/act
```

### Continuous Monitoring Agent
```
Cron → data source check → anomaly detection → if anomaly: root-cause agent
→ summary to Slack/email → ticket created with idempotency key
```
