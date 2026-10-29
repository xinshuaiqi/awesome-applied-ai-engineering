# Contributing to Awesome Applied AI Engineering

Thank you for helping maintain the signal-to-noise ratio in the AI engineering ecosystem. This is a **curation-first** project — quality and architectural relevance matter more than volume.

---

## The Production Quality Filter

Every submission must pass **all three** checks:

### ✅ Check 1: Is It Production-Grade?

The tool, framework, or resource must show evidence of real-world adoption:
- GitHub stars (>500 for libraries, >100 for niche enterprise tools)
- Documented production deployments (blog posts, case studies, conference talks)
- Active maintenance (commit within 6 months, responsive issue tracker)

**Instant rejection:** "I made this last week" without adoption evidence.

### ✅ Check 2: Does It Solve an Architectural Problem?

The entry must address a real engineering challenge — not just wrap an API:
- Handles non-determinism, retries, or failure modes
- Solves latency, cost, throughput, or accuracy tradeoffs
- Provides guardrails, observability, or governance hooks

**Instant rejection:** Single-file scripts that call `openai.ChatCompletion.create()`.

### ✅ Check 3: Is It Enterprise-Applicable?

The entry must be usable by teams with real constraints:
- Security/compliance considerations (SOC2, HIPAA, data residency)
- Multi-tenant or role-based access support
- Scalable beyond a single-server deployment
- Works with enterprise auth (SSO, SAML, RBAC)

---

## How to Submit

1. **Fork** this repository.
2. **Find the right section** in `README.md` or the appropriate section file.
3. **Add your entry** in this format:

```markdown
- **[Tool Name](https://link)** — One sentence on what it does and why it's production-worthy. Mention the specific problem it solves.
```

4. **Open a Pull Request** with:
   - Title: `Add: [Tool Name] to [Section Name]`
   - Body answering:
     - What does it do that existing listed tools do not?
     - Where is it deployed in production? (link to case study, blog, or usage stats)
     - What enterprise constraint does it address?

---

## Section Ownership

| Section | What Belongs |
|---|---|
| Foundation Concepts | Papers and mental models, not tools |
| Related Awesome Collections | Upstream curated lists only |
| Enterprise Integrations | SAP, Salesforce, Oracle, Databricks, Snowflake connectors |
| Always-On Agents | Persistent, event-driven, or long-horizon agent systems |
| Evaluation & Red-Teaming | Frameworks for measuring and attacking LLM outputs |
| MCP | Servers, clients, transports for Model Context Protocol |
| System Integration Patterns | Architecture blueprints with trade-off analysis |
| Orchestration | Agent and workflow frameworks |
| Context & RAG | Vector DBs, retrieval, reranking, caching |
| LLMOps | Observability, inference, cost management |
| Tools & Software | Developer tooling, runtime, data, security |
| People to Follow | Engineers who publish production-first content regularly |

---

## What We Will Reject

- Anything in the **anti-patterns** table in the README without a clear mitigation
- Submissions that duplicate existing entries without clear differentiation
- Self-promotion: you may submit your own work only if it has >1,000 GitHub stars or a documented enterprise customer case study
- Links to paywalled content without a free tier or open summary
- Anything from a company with known data privacy violations or CVEs left unpatched

---

## Maintaining the Anti-Patterns Section

If you discover that a listed tool has become abandonware, introduces a CVE, or has a better alternative, open an issue with:
- `[STALE]` — Last commit >12 months, consider removal
- `[REPLACED]` — Better alternative exists; link it
- `[SECURITY]` — Known CVE or data handling issue

---

## Licensing of Contributions

This repository is licensed under [CC BY-NC-SA 4.0](LICENSE): free to read, share, and adapt with attribution, for non-commercial purposes only, and adaptations must use the same license.

By submitting a pull request you confirm that:
- You wrote the contribution or have the right to submit it.
- You agree it is licensed under CC BY-NC-SA 4.0, the same as the rest of the repository.
- It contains no confidential, client-specific, or proprietary material.

Please do not copy text from other sources unless their license allows it; link to the source instead.

---

## Code of Conduct

Be helpful, be specific, and be honest about trade-offs. The goal is a list that saves a senior engineer 3 days of research — not a list that inflates contributor counts.
