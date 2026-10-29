import os
import tempfile
import unittest

from ticket_agent import ExceptionQueue, FakeCRM, TaskStore, TriageAgent, idem_key


def make_agent(crm=None, store=None, propose=None):
    crm = crm or FakeCRM()
    exceptions = ExceptionQueue()
    kwargs = {"propose": propose} if propose else {}
    agent = TriageAgent(crm, store or TaskStore(), exceptions, sleep=lambda s: None, **kwargs)
    return agent, crm, exceptions


class TicketAgentTests(unittest.TestCase):
    def test_happy_path_creates_ticket_and_notifies(self):
        agent, crm, _ = make_agent()
        task = agent.run("t1", "Checkout is down")
        self.assertEqual(task["status"], "done")
        self.assertEqual(len(crm.tickets), 1)
        self.assertEqual(len(crm.notifications), 1)
        self.assertEqual(next(iter(crm.tickets.values()))["priority"], "high")

    def test_lost_response_retry_does_not_duplicate(self):
        agent, crm, _ = make_agent()
        crm.inject_fault("create_ticket", times=2, after_apply=True)
        task = agent.run("t1", "Printer broken")
        self.assertEqual(task["status"], "done")
        self.assertEqual(len(crm.tickets), 1)

    def test_replaying_a_finished_task_is_a_noop(self):
        agent, crm, _ = make_agent()
        agent.run("t1", "Printer broken")
        agent.run("t1", "Printer broken")
        self.assertEqual((len(crm.tickets), len(crm.notifications)), (1, 1))

    def test_refund_waits_for_approval_and_executes_once(self):
        agent, crm, _ = make_agent()
        task = agent.run("t1", "Refund $40 for order 8812")
        self.assertEqual(task["status"], "pending_approval")
        self.assertEqual(len(crm.refunds), 0)
        task = agent.approve("t1", "supervisor")
        self.assertEqual(task["status"], "done")
        self.assertEqual(len(crm.refunds), 1)
        agent.run("t1", "Refund $40 for order 8812")
        self.assertEqual(len(crm.refunds), 1)

    def test_rejected_refund_never_executes(self):
        agent, crm, _ = make_agent()
        agent.run("t1", "Refund $40 for order 8812")
        task = agent.approve("t1", "supervisor", approved=False)
        self.assertEqual(task["status"], "rejected")
        self.assertEqual(len(crm.refunds), 0)
        self.assertEqual(agent.run("t1", "Refund $40 for order 8812")["status"], "rejected")
        self.assertEqual(len(crm.refunds), 0)

    def test_approve_requires_pending_state(self):
        agent, _, _ = make_agent()
        agent.run("t1", "Printer broken")
        with self.assertRaises(ValueError):
            agent.approve("t1", "supervisor")

    def test_invalid_model_output_never_reaches_the_crm(self):
        agent, crm, exceptions = make_agent()
        task = agent.run("t1", "Refund $99999 for order 1")
        self.assertEqual(task["status"], "invalid")
        self.assertEqual((len(crm.tickets), len(crm.refunds)), (0, 0))
        self.assertEqual(len(exceptions.items), 1)

    def test_unknown_action_type_is_rejected(self):
        agent, crm, exceptions = make_agent(propose=lambda text: {"type": "delete_all_tickets"})
        self.assertEqual(agent.run("t1", "anything")["status"], "invalid")
        self.assertEqual(len(exceptions.items), 1)

    def test_permanent_failure_compensates_and_queues_exception(self):
        agent, crm, exceptions = make_agent()
        crm.inject_fault("notify", times=1, exc=__import__("ticket_agent").PermanentError)
        task = agent.run("t1", "Printer broken")
        self.assertEqual(task["status"], "failed")
        self.assertEqual(task["compensated"], ["create_ticket"])
        self.assertEqual(next(iter(crm.tickets.values()))["status"], "cancelled")
        self.assertEqual(len(exceptions.items), 1)

    def test_exhausted_retries_compensate_a_refund(self):
        agent, crm, exceptions = make_agent()
        agent.run("t1", "Refund $40 for order 8812")
        crm.inject_fault("notify", times=10)  # always fails transiently
        task = agent.approve("t1", "supervisor")
        self.assertEqual(task["status"], "failed")
        self.assertEqual(next(iter(crm.refunds.values()))["status"], "reversed")
        self.assertEqual(len(exceptions.items), 1)

    def test_failed_compensation_is_flagged_for_manual_cleanup(self):
        agent, crm, exceptions = make_agent()
        crm.inject_fault("notify", times=1, exc=__import__("ticket_agent").PermanentError)
        crm.inject_fault("cancel_ticket", times=10)
        task = agent.run("t1", "Printer broken")
        self.assertEqual(task["status"], "failed_needs_manual_cleanup")
        self.assertEqual(task["manual_cleanup"], ["create_ticket"])

    def test_resume_after_crash_does_not_redo_finished_steps(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "tasks.json")
            crm = FakeCRM()
            agent, _, _ = make_agent(crm=crm, store=TaskStore(path))
            crm.inject_fault("notify", times=1, exc=RuntimeError)  # not retryable: simulates a crashed worker
            with self.assertRaises(RuntimeError):
                agent.run("t1", "Printer broken")
            self.assertEqual(len(crm.tickets), 1)
            self.assertEqual(len(crm.notifications), 0)

            restarted, _, _ = make_agent(crm=crm, store=TaskStore(path))  # new process, same durable state
            task = restarted.run("t1", "Printer broken")
            self.assertEqual(task["status"], "done")
            self.assertEqual((len(crm.tickets), len(crm.notifications)), (1, 1))

    def test_resume_does_not_ask_the_model_again(self):
        calls = []

        def counting_propose(text):
            calls.append(text)
            return {"type": "create_ticket", "summary": text, "priority": "low"}

        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "tasks.json")
            crm = FakeCRM()
            agent, _, _ = make_agent(crm=crm, store=TaskStore(path), propose=counting_propose)
            crm.inject_fault("notify", times=1, exc=RuntimeError)
            with self.assertRaises(RuntimeError):
                agent.run("t1", "Printer broken")
            restarted, _, _ = make_agent(crm=crm, store=TaskStore(path), propose=counting_propose)
            restarted.run("t1", "Printer broken")
            self.assertEqual(len(calls), 1)

    def test_idempotency_keys_are_stable_and_distinct(self):
        self.assertEqual(idem_key("t1", "notify"), idem_key("t1", "notify"))
        self.assertNotEqual(idem_key("t1", "notify"), idem_key("t2", "notify"))
        self.assertNotEqual(idem_key("t1", "notify"), idem_key("t1", "create_ticket"))


if __name__ == "__main__":
    unittest.main()
