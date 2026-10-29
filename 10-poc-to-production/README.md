# 10 · POC to Production

> The chapter that connects everything else. A technically good AI system is not yet an **operable enterprise system**: it must integrate with real workflows, respect data permissions, recover from failure, and prove that people use it and that it changes outcomes.

---

## Evals ≠ Production Readiness

| | Evals (chapter 04) | Production Readiness (this chapter) |
|---|---|---|
| Question | Is the output correct, grounded, and is the task completed? | Can the organization run, govern, and benefit from it? |
| Covers | Answer quality, faithfulness, tool trajectory, regression | Permissions, failure recovery, cost control, auditability, adoption, value |
| Fails as | Wrong or ungrounded answers | Duplicate actions, data leaks, outages, unused tools, no ROI |
| Owner | AI engineers | AI engineers + platform + business owner + security |

Passing evals is necessary, never sufficient.

---

## Stage-Gate Model

| Stage | Validate | Deliver | Stop If | Expand If |
|---|---|---|---|---|
| **1. Discovery** | Problem is real, measurable, owned; data exists and is accessible; AI is the right tool | Baseline metrics, business owner, data readiness assessment, risk list ranked by severity | No baseline, no owner, or data inaccessible | Riskiest assumption has a cheap test plan |
| **2. Prototype** | Riskiest assumption holds (extraction quality, retrieval hit rate, latency) | Working demo on real data, first golden set (50+ cases), cost/latency estimate | Quality cannot reach threshold on real data | Eval baseline meets target on golden set |
| **3. Pilot** | Real users, real workflow, bounded scope; humans in the loop | Integrated workflow, permission model, tracing, eval gate in CI, runbook draft, pilot success criteria | Adoption low, review burden exceeds time saved, or unresolved security finding | Adoption, quality, and cost beat baseline with a control comparison |
| **4. Production** | Reliability, security, and governance hold under real load | SLOs, failure handling, audit logs, on-call, rollback, cost attribution, user training | SLOs missed or incident without recovery path | Stable SLOs, audited, owner accepts operation |
| **5. Scale** | Reuse across teams without duplication; value sustained | Registry/catalog, platform services, chargeback, change management program | Value decays or platform cost exceeds benefit | Reusable pattern adopted by multiple teams |

Every gate needs a named decision-maker. "Stop" is a legitimate, successful outcome.

---

## 1. Workflow Integration: From "Answers" to "Completes the Task"

The common failure is not a wrong sentence. It is a mid-process failure: a duplicate action, a half-updated system, or a lost long-running task.

### Task Lifecycle Checklist

- [ ] **System of record identified** — where does the result land (CRM, ERP, ticketing)? Who owns that integration?
- [ ] **Read vs write separated** — read tools are broadly available; write tools are narrow, validated, and logged
- [ ] **Deterministic validation before every write** — schema, business rules, limits; never raw model output into a system of record
- [ ] **Idempotency keys** on every side-effecting call so retries do not duplicate actions
- [ ] **Retry policy** with backoff and a maximum; distinguish retryable from non-retryable errors
- [ ] **Compensation / rollback** defined for multi-step actions (what undoes step 2 if step 3 fails?)
- [ ] **Approval gates** for high-impact actions, with clear approver, timeout, and default-on-timeout
- [ ] **Human takeover** — a path to hand a half-finished task to a person with full context
- [ ] **Exception queue** — failed or ambiguous tasks land somewhere visible with an owner, not in logs
- [ ] **Long-running state** — checkpoint and resume after crash, deploy, or approval wait
- [ ] **End-to-end test** against a sandbox of the real systems, including failure injection

### Lifecycle Sketch
```
Trigger → context assembly → plan → validate plan
   → [read tools] → draft action
   → deterministic validation → approval (if required)
   → execute with idempotency key → verify result in system of record
   → success: log + notify | failure: retry → compensate → exception queue → human
```

---

## 2. Data Readiness & Permission-Aware Retrieval

### Data Readiness Assessment

Score each knowledge source before building on it:

| Dimension | Question | Red Flag |
|---|---|---|
| Ownership | Is there a named data owner? | "Nobody knows who maintains it" |
| Quality | Is content accurate, deduplicated, current? | Conflicting versions, stale policies |
| Freshness | How often does it change, and how fast must the index follow? | No refresh process |
| Provenance | Can each answer cite document, version, and location? | No stable identifiers |
| Access | Who is allowed to see which documents? | Permissions undocumented or only in the source UI |
| Format | Can it be parsed reliably (tables, scans, images)? | Scanned PDFs with no OCR plan |
| Sensitivity | Does it contain PII/PHI/confidential data? | Unclassified sources |

### Permission-Aware Retrieval

Retrieval must honor the source system's access controls. A user must never receive an answer derived from a document they cannot open.

```
Ingest:   document + ACL metadata (groups/users/tenant) → index with ACL fields
Query:    authenticate user → resolve their groups → filter retrieval by ACL
          → retrieve → answer with citations
Refresh:  ACL changes in the source propagate to the index on a defined schedule
```

Design rules:
- Filter **at retrieval time**, not after generation
- Tenant isolation enforced in the index (separate collections or mandatory tenant filter)
- Re-sync ACLs on a schedule; treat stale ACLs as a security defect
- Log which documents contributed to each answer for audit

---

## 3. Production Reliability

See chapter 05 for patterns (circuit breakers, fallback ladder, DLQ, checkpointing). Readiness requirements:

- [ ] SLOs defined for latency, error rate, and quality (checked by scheduled evals)
- [ ] Timeouts at every I/O boundary
- [ ] Rate limits and budget caps per user/team
- [ ] Degraded mode defined (what the user sees when the model or a tool is down)
- [ ] Failures classified: model quality vs infrastructure vs integration vs data
- [ ] Incident runbook tested, including disabling a tool and rolling back a prompt

---

## 4. Agent Runtime Security

See chapter 06. Readiness requirements:

- [ ] Agent has its own identity and short-lived scoped credentials
- [ ] Tool allowlist is deny-by-default
- [ ] Code-executing tools sandboxed
- [ ] Third-party/MCP tools reviewed and their outputs treated as untrusted
- [ ] Indirect prompt injection tested (red-team documents and tool results)
- [ ] Emergency revocation tested end to end

---

## 5. Platform Operations

When more than one team builds agents, add shared services (details in chapter 05):

- Agent and tool registry/catalog with owners and versions
- Shared gateway with per-team auth, budgets, and cost attribution
- Dev / test / prod separation with promotion via CI/CD and eval gates
- Canary release for prompt and model changes
- Clear split: platform team owns infrastructure and guardrails; application teams own business logic, prompts, evals, and domain data

---

## 6. Adoption & Value Realization

A technical metric improving does not guarantee business value. If users distrust the tool or the process was not redesigned, the gain disappears.

### Measure Against a Baseline

| Category | Metrics |
|---|---|
| Adoption | Active users / eligible users, repeat usage, task share handled by the system |
| Quality | Accepted-without-edit rate, error/rework rate, escalation rate |
| Efficiency | Cycle time, handle time, throughput per person |
| Human burden | Review time per output, override rate, time spent correcting |
| Cost | Model + infrastructure + review labor + maintenance (not model spend alone) |
| Outcome | Business KPI the use case exists to move (resolution rate, close time, loss rate) |

Use a control group or pre/post baseline with the same measurement method. Savings in "hours" count only when the time is redeployed or capacity is converted into outcomes.

### Change Management Checklist

- [ ] Named business owner accountable for the outcome (not just the AI team)
- [ ] Process redesigned around the tool, not the tool bolted onto the old process
- [ ] User training and guidance on when to trust, verify, or override
- [ ] Feedback channel inside the tool; feedback feeds the golden set (chapter 04)
- [ ] Review burden tracked; if it rises, scope or quality must change
- [ ] Regular value review with the business owner; stop or retarget if value is not appearing

---

## Anti-Patterns

| Anti-Pattern | Consequence |
|---|---|
| Declaring success from eval scores alone | Unused or untrusted tool, no business value |
| Piloting with no baseline | Impossible to prove or disprove value |
| Agent writes directly to systems of record | Duplicate or corrupt records, audit failures |
| Retrieval ignoring source ACLs | Data exposure to unauthorized users |
| No exception queue | Silent task failures |
| Each team builds its own gateway, registry, and guardrails | Fragmentation, inconsistent security, untracked cost |
| No owner after launch | Quality and relevance decay unnoticed |
