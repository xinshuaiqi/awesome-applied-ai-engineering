"""Ticket-triage agent: an end-to-end workflow-integration pattern (stdlib only).

Lifecycle:  propose -> validate -> (human approval) -> execute as a saga -> verify -> done
            any failure -> compensate completed steps -> exception queue

propose_action() is a deterministic stand-in for an LLM call so the example runs
offline. Swap it for a real model call; every stage after it is model-independent.

Run the demo:   python3 ticket_agent.py
Run the tests:  python3 -m unittest -v
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time

ALLOWED_PRIORITIES = {"low", "medium", "high"}
MAX_REFUND = 500.0
NEEDS_APPROVAL = {"issue_refund"}
TERMINAL = {"done", "rejected", "invalid", "failed", "failed_needs_manual_cleanup", "failed_verification"}


class TransientError(Exception):
    """Retryable: timeout, 5xx, rate limit."""


class PermanentError(Exception):
    """Not retryable: target system rejected the request, auth failure."""


def idem_key(task_id: str, step: str) -> str:
    """Stable per (task, step): a retry or replay produces the same key."""
    return hashlib.sha256(f"{task_id}:{step}".encode()).hexdigest()[:16]


class FakeCRM:
    """In-memory system of record. Every write is idempotent on external_id."""

    def __init__(self):
        self.tickets, self.refunds, self.notifications = {}, {}, {}
        self._faults = {}

    def inject_fault(self, op, times=1, exc=TransientError, after_apply=False):
        """after_apply=True simulates a lost response: the write happened, the caller saw an error."""
        self._faults[op] = {"times": times, "exc": exc, "after_apply": after_apply}

    def _fault(self, op, phase):
        f = self._faults.get(op)
        if f and f["times"] > 0 and (phase == "after") == f["after_apply"]:
            f["times"] -= 1
            raise f["exc"](f"{op} failed ({phase})")

    def create_ticket(self, external_id, summary, priority):
        self._fault("create_ticket", "before")
        rec = self.tickets.setdefault(
            external_id, {"id": external_id, "summary": summary, "priority": priority, "status": "open"})
        self._fault("create_ticket", "after")
        return dict(rec)

    def cancel_ticket(self, external_id):
        self._fault("cancel_ticket", "before")
        if external_id in self.tickets:
            self.tickets[external_id]["status"] = "cancelled"
        return {"id": external_id, "status": "cancelled"}

    def issue_refund(self, external_id, order_id, amount):
        self._fault("issue_refund", "before")
        rec = self.refunds.setdefault(
            external_id, {"id": external_id, "order_id": order_id, "amount": amount, "status": "issued"})
        self._fault("issue_refund", "after")
        return dict(rec)

    def reverse_refund(self, external_id):
        self._fault("reverse_refund", "before")
        if external_id in self.refunds:
            self.refunds[external_id]["status"] = "reversed"
        return {"id": external_id, "status": "reversed"}

    def notify(self, external_id, message):
        self._fault("notify", "before")
        rec = self.notifications.setdefault(external_id, {"id": external_id, "message": message})
        self._fault("notify", "after")
        return dict(rec)


class TaskStore:
    """Durable task state so a crashed or redeployed worker resumes instead of restarting."""

    def __init__(self, path=None):
        self.path, self.tasks = path, {}
        if path and os.path.exists(path):
            with open(path) as f:
                self.tasks = json.load(f)

    def get(self, task_id):
        return self.tasks.get(task_id)

    def save(self, task_id, task):
        self.tasks[task_id] = task
        if self.path:
            tmp = f"{self.path}.tmp"
            with open(tmp, "w") as f:
                json.dump(self.tasks, f)
            os.replace(tmp, self.path)  # atomic: never a half-written state file


class ExceptionQueue:
    """Failed or ambiguous tasks land here with an owner to act on them, not only in logs."""

    def __init__(self):
        self.items = []

    def push(self, task_id, reason, detail=None):
        self.items.append({"task_id": task_id, "reason": reason, "detail": detail})


def with_retry(fn, attempts=3, base_delay=0.2, sleep=time.sleep):
    for i in range(attempts):
        try:
            return fn()
        except TransientError:
            if i == attempts - 1:
                raise
            sleep(base_delay * 2 ** i)


def propose_action(text: str) -> dict:
    """Stand-in for the LLM. Returns a *proposal*; nothing here touches a system."""
    t = text.lower()
    if "refund" in t:
        amount = re.search(r"\$(\d+(?:\.\d+)?)", text)
        order = re.search(r"order\s+#?(\w+)", t)
        return {"type": "issue_refund",
                "amount": float(amount.group(1)) if amount else None,
                "order_id": order.group(1) if order else None}
    priority = "high" if any(w in t for w in ("outage", "down", "urgent")) else "medium"
    return {"type": "create_ticket", "summary": text.strip()[:80], "priority": priority}


def validate(action: dict) -> list[str]:
    """Deterministic gate between model output and any system write."""
    errors, kind = [], action.get("type")
    if kind == "create_ticket":
        if action.get("priority") not in ALLOWED_PRIORITIES:
            errors.append("priority must be low, medium, or high")
        if not str(action.get("summary", "")).strip():
            errors.append("summary is required")
    elif kind == "issue_refund":
        amount = action.get("amount")
        if isinstance(amount, bool) or not isinstance(amount, (int, float)) or not 0 < amount <= MAX_REFUND:
            errors.append(f"refund amount must be between 0 and {MAX_REFUND}")
        if not action.get("order_id"):
            errors.append("order_id is required")
    else:
        errors.append(f"unknown action type: {kind!r}")
    return errors


class TriageAgent:
    def __init__(self, crm, store, exceptions, propose=propose_action, sleep=time.sleep):
        self.crm, self.store, self.exceptions = crm, store, exceptions
        self.propose, self.sleep = propose, sleep

    def run(self, task_id, text):
        task = self.store.get(task_id) or {"status": "new", "text": text, "steps": {}}
        if task["status"] in TERMINAL:
            return task  # replaying a finished task is a no-op
        if "action" not in task:  # the proposal is stored, so resume never re-asks the model
            action = self.propose(text)
            errors = validate(action)
            if errors:
                task.update(status="invalid", errors=errors, action=action)
                self.store.save(task_id, task)
                self.exceptions.push(task_id, "model output failed validation", errors)
                return task
            task["action"] = action
        if task["action"]["type"] in NEEDS_APPROVAL and task.get("approval") != "approved":
            task["status"] = "pending_approval"
            self.store.save(task_id, task)
            return task
        return self._execute(task_id, task)

    def approve(self, task_id, approver, approved=True):
        task = self.store.get(task_id)
        if not task or task["status"] != "pending_approval":
            raise ValueError(f"task {task_id} is not awaiting approval")
        task.update(approval="approved" if approved else "rejected", approver=approver)
        if not approved:
            task["status"] = "rejected"
            self.store.save(task_id, task)
            return task
        self.store.save(task_id, task)
        return self._execute(task_id, task)

    def _plan(self, task_id, action):
        """Ordered (name, do, undo) steps. undo=None means nothing to roll back."""
        crm = self.crm
        key = lambda step: idem_key(task_id, step)  # noqa: E731
        if action["type"] == "create_ticket":
            main = ("create_ticket",
                    lambda: crm.create_ticket(key("create_ticket"), action["summary"], action["priority"]),
                    lambda: crm.cancel_ticket(key("create_ticket")))
            message = f"Ticket opened: {action['summary']}"
        else:
            main = ("issue_refund",
                    lambda: crm.issue_refund(key("issue_refund"), action["order_id"], action["amount"]),
                    lambda: crm.reverse_refund(key("issue_refund")))
            message = f"Refund of {action['amount']} issued for order {action['order_id']}"
        return [main, ("notify", lambda: crm.notify(key("notify"), message), None)]

    def _execute(self, task_id, task):
        task["status"] = "in_progress"
        self.store.save(task_id, task)
        plan = self._plan(task_id, task["action"])
        for name, do, _ in plan:
            if name in task["steps"]:
                continue  # finished before a crash or restart
            try:
                task["steps"][name] = with_retry(do, sleep=self.sleep)
                self.store.save(task_id, task)  # checkpoint after every step
            except (TransientError, PermanentError) as exc:
                return self._compensate(task_id, task, plan, name, exc)
        return self._verify(task_id, task)

    def _compensate(self, task_id, task, plan, failed_step, exc):
        undone, manual = [], []
        for name, _, undo in reversed(plan):
            if name in task["steps"] and undo is not None:
                try:
                    with_retry(undo, sleep=self.sleep)
                    undone.append(name)
                except (TransientError, PermanentError):
                    manual.append(name)
        task.update(status="failed_needs_manual_cleanup" if manual else "failed",
                    error=f"{failed_step}: {exc}", compensated=undone, manual_cleanup=manual)
        self.store.save(task_id, task)
        self.exceptions.push(task_id, f"step {failed_step!r} failed", {"compensated": undone, "manual": manual})
        return task

    def _verify(self, task_id, task):
        """Read back from the system of record instead of trusting the write's return value."""
        step = "create_ticket" if task["action"]["type"] == "create_ticket" else "issue_refund"
        table = self.crm.tickets if step == "create_ticket" else self.crm.refunds
        expected = "open" if step == "create_ticket" else "issued"
        record = table.get(idem_key(task_id, step))
        if not record or record["status"] != expected:
            task["status"] = "failed_verification"
            self.exceptions.push(task_id, "system of record does not match expected state", record)
        else:
            task["status"] = "done"
        self.store.save(task_id, task)
        return task


def _demo():
    crm, exceptions = FakeCRM(), ExceptionQueue()
    agent = TriageAgent(crm, TaskStore(), exceptions, sleep=lambda s: None)

    crm.inject_fault("create_ticket", after_apply=True)  # write succeeds, response is lost
    print("1.", agent.run("t1", "Checkout is down for EU customers")["status"],
          "| tickets in CRM:", len(crm.tickets), "(retry did not duplicate)")

    task = agent.run("t2", "Please refund $40 for order 8812")
    print("2.", task["status"], "| refunds before approval:", len(crm.refunds))
    print("  ", agent.approve("t2", "supervisor@example.com")["status"], "| refunds after:", len(crm.refunds))

    print("3.", agent.run("t3", "Refund $99999 for order 1")["status"], "| exception queue:", len(exceptions.items))


if __name__ == "__main__":
    _demo()
