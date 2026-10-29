# 04 · Evaluation & Testing

> You cannot ship reliable AI systems without evaluating them systematically. Evals are the unit tests of AI engineering — build them before production, not after incidents.

---

## The Full Eval Pipeline: Offline to Production Feedback Loop

```
1. Define acceptance criteria & golden dataset
          ↓
2. Rule-based evals (exact match, regex, schema validation)
          ↓
3. LLM-as-judge evals (quality, faithfulness, relevancy)
          ↓
4. Human calibration (validate that automated evals correlate with human judgment)
          ↓
5. Agent trajectory & tool-call evaluation (for agentic systems)
          ↓
6. CI release gate (eval regression blocks deployment)
          ↓
7. Production tracing (Langfuse / Phoenix — log every call)
          ↓
8. Error case extraction → back to golden dataset
          ↑_______________________________________________↑
```

This is a closed loop. Production errors are your best source of new test cases. Every incident should generate at least 3 new golden dataset entries.

---

## The Eval Mindset Shift

Traditional software: deterministic inputs → deterministic outputs → assert equality.

AI systems: non-deterministic outputs → evaluate quality dimensions → track distributions over time.

**The fundamental challenge:** What is "correct" for an open-ended LLM response? You must define this explicitly before building — not after you see the first bad output.

---

## Eval Taxonomy

### By Output Type
| Output Type | Eval Approach |
|---|---|
| Factual QA | Exact match, semantic similarity, citation coverage |
| Summarization | Faithfulness, coverage, conciseness |
| Code generation | Execution pass rate, test suite pass rate |
| RAG answers | Faithfulness, answer relevancy, context recall, context precision |
| Agent trajectories | Task completion rate, step efficiency, cost per task |
| Classification | Precision, recall, F1 per class |

### By Method
| Method | Description | Best For |
|---|---|---|
| **Rule-based** | Exact match, regex, schema validation | High-confidence assertions, fast CI gates |
| **LLM-as-judge** | Use a capable model to score outputs | Open-ended quality, hard to rule-define |
| **Human eval** | Human raters score outputs | Ground truth, calibrating automated evals |
| **A/B testing** | Live traffic split, measure downstream metrics | Shipping decisions, real-world impact |
| **Red-teaming** | Adversarial probing for failures | Safety, prompt injection, jailbreaks |

---

## Tool Comparison

| Tool | Best For | Key Strengths | Notes |
|---|---|---|---|
| **[Promptfoo](https://github.com/promptfoo/promptfoo)** | Prompt A/B testing, CI gates | YAML config, multi-provider, red-teaming, CLI-native | Best for systematic prompt version comparison |
| **[DeepEval](https://github.com/confident-ai/deepeval)** | Unit testing for LLMs | Pytest integration, G-Eval, hallucination metric | Best for teams with existing test culture |
| **[RAGAS](https://github.com/explodinggradients/ragas)** | RAG pipeline evaluation | Faithfulness, answer relevancy, context recall/precision | Purpose-built for RAG; use this first for RAG systems |
| **[Langfuse](https://github.com/langfuse/langfuse)** | Production observability + evals | Trace trees, prompt versioning, cost dashboards, self-hostable | Best all-in-one for production LLM systems |
| **[Phoenix (Arize)](https://github.com/Arize-ai/phoenix)** | Trace-based observability | Strong LlamaIndex + LangChain integration, OSS | Good alternative to Langfuse |
| **[Opik (Comet)](https://github.com/comet-ml/opik)** | Experiment tracking + evals | Tight Comet integration, eval metrics, OSS | Best if already using Comet ML |
| **[Giskard](https://github.com/Giskard-AI/giskard)** | Automated quality & security testing | Detects hallucinations, bias, prompt injection automatically | Good for compliance-heavy orgs |
| **[Inspect AI](https://github.com/UKGovernmentBEIS/inspect_ai)** | Rigorous benchmark evaluation | Task-level evaluation framework, UK AISI | Best for structured capability benchmarking |

---

## Agent Trajectory & Tool-Call Evaluation

Standard output evals are not sufficient for agentic systems. You must also evaluate:

### What to Measure in Agents
- **Task completion rate** — Did the agent complete the goal? (binary)
- **Step efficiency** — Did it use the minimum steps necessary, or did it waste turns?
- **Tool call accuracy** — Were tool calls made with correct arguments?
- **Unnecessary tool calls** — Did the agent call tools it didn't need?
- **Error recovery** — Did the agent handle tool failures gracefully?
- **Cost per task** — Total token spend to complete the task

### Trajectory Eval Pattern
```python
# Record full agent trajectory
trajectory = {
    "task": "Summarize Q3 sales by region",
    "steps": [
        {"thought": "...", "action": "query_db", "args": {"query": "SELECT..."}, "result": "..."},
        {"thought": "...", "action": "format_output", "args": {...}, "result": "..."}
    ],
    "final_output": "...",
    "total_tokens": 1842,
    "completed": True
}

# Evaluate: was the tool use correct? Was it efficient?
# Compare against golden trajectory or use LLM judge
```

### Tool-Call Evaluation
For each tool call, evaluate:
1. **Was this tool the right choice?** (vs. alternatives available)
2. **Were the arguments correct?** (schema validation + semantic correctness)
3. **Was this call necessary?** (could it have been answered from context?)

---

## Core Frameworks

- **[Promptfoo](https://github.com/promptfoo/promptfoo)** — CLI-first prompt testing and red-teaming
  ```yaml
  prompts: [prompts/v1.txt, prompts/v2.txt]
  providers: [openai:gpt-4o, anthropic:claude-3-5-sonnet]
  tests:
    - vars: { query: "What is the refund policy?" }
      assert:
        - type: contains
          value: "30 days"
        - type: llm-rubric
          value: "Response is polite and clear"
  ```

- **[DeepEval](https://github.com/confident-ai/deepeval)** — Unit testing for LLMs with Pytest
  ```python
  from deepeval.metrics import HallucinationMetric, FaithfulnessMetric
  from deepeval.test_case import LLMTestCase

  def test_no_hallucination():
      test_case = LLMTestCase(input="...", actual_output="...", context=[...])
      assert_test(test_case, [HallucinationMetric(threshold=0.5)])
  ```

- **[RAGAS](https://github.com/explodinggradients/ragas)** — RAG-specific evaluation

- **[Giskard](https://github.com/Giskard-AI/giskard)** — Automated quality + security testing

---

## Building a Golden Dataset

1. **Minimum 50 examples** for meaningful signal (200+ for reliability)
2. **Cover failure modes** — include adversarial, edge-case, and ambiguous examples
3. **Sample from real traffic** — synthetic examples miss real distribution
4. **Include hard negatives** — "I don't know" and "out of scope" cases
5. **Version your dataset** — treat it like code; track changes in git
6. **Human-verify labels** — at least 2 raters per example

---

## LLM-as-Judge Design

```python
JUDGE_PROMPT = """
Score the response on FAITHFULNESS (1-5):
- 5: Every claim directly supported by provided context
- 4: Minor extrapolations, all grounded in context
- 3: Some claims go beyond context but are reasonable
- 2: Multiple unsupported claims
- 1: Response contradicts or ignores provided context

Query: {query}
Context: {context}
Response: {response}

Output JSON only: {"score": <int>, "reasoning": "<one sentence>"}
"""
```

Rules:
- Use a stronger model as judge than the model being evaluated
- Score on 1–5 scales, not binary
- Always output structured JSON
- Run each eval 3x and average — LLM judges have variance

---

## CI/CD Integration

Gate deployments on eval regressions:

```yaml
- name: Run eval suite
  run: promptfoo eval --config promptfoo.yaml --output results.json

- name: Check quality gate
  run: |
    python scripts/check_eval_gate.py \
      --results results.json \
      --min-faithfulness 0.85 \
      --max-hallucination-rate 0.05
```

---

## Anti-Patterns

| Anti-Pattern | Problem |
|---|---|
| No golden dataset before shipping | No baseline to detect regressions |
| Evaluating only on training examples | Overfitting to known cases |
| Binary pass/fail only | Loses gradient signal on quality degradation |
| No human baseline | Can't calibrate whether automated judge is accurate |
| Ignoring production traces | Best signal for new test cases is in your logs |
| Ignoring latency in evals | A 10x slower model that scores +2% is rarely a win |
