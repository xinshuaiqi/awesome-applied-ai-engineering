import unittest

from acl_rag import Chunk, SecureIndex, User

NOW = 1_000_000.0


def chunk(doc_id, text, tenant="acme", groups=(), users=(), synced=NOW, **kw):
    return Chunk(doc_id, text, tenant, frozenset(groups), frozenset(users), acl_synced_at=synced, **kw)


def build_index():
    idx = SecureIndex(max_acl_age_s=3600)
    idx.add(chunk("hr-policy", "parental leave policy twelve weeks", groups={"all-staff"}))
    idx.add(chunk("exec-comp", "executive compensation leave bonus plan", groups={"execs"}))
    idx.add(chunk("legal-memo", "settlement leave confidential memo", users={"gc"}))
    idx.add(chunk("globex-doc", "parental leave policy for globex", tenant="globex", groups={"all-staff"}))
    idx.add(chunk("orphan", "leave policy nobody may read"))  # empty ACL
    return idx


class PermissionAwareRagTests(unittest.TestCase):
    def setUp(self):
        self.idx = build_index()
        self.alice = User("alice", "acme", frozenset({"all-staff"}))

    def ids(self, query, user, now=NOW):
        return [c.doc_id for _, c in self.idx.search(query, user, now)]

    def test_user_sees_only_permitted_documents(self):
        self.assertEqual(self.ids("leave policy", self.alice), ["hr-policy"])

    def test_group_membership_grants_access(self):
        exec_user = User("erin", "acme", frozenset({"all-staff", "execs"}))
        self.assertIn("exec-comp", self.ids("leave bonus", exec_user))

    def test_direct_user_grant(self):
        gc = User("gc", "acme", frozenset())
        self.assertEqual(self.ids("settlement leave", gc), ["legal-memo"])

    def test_other_tenant_never_sees_documents_even_with_matching_group(self):
        outsider = User("bob", "globex", frozenset({"all-staff"}))
        self.assertEqual(self.ids("leave policy", outsider), ["globex-doc"])

    def test_empty_acl_means_nobody(self):
        everyone = User("root", "acme", frozenset({"all-staff", "execs", "admins"}))
        self.assertNotIn("orphan", self.ids("leave policy nobody", everyone))

    def test_hidden_documents_do_not_change_scores_or_order(self):
        before = self.idx.search("leave policy", self.alice, NOW)
        self.idx.add(chunk("exec-extra", "leave leave leave policy policy policy", groups={"execs"}))
        after = self.idx.search("leave policy", self.alice, NOW)
        self.assertEqual([(s, c.doc_id) for s, c in before], [(s, c.doc_id) for s, c in after])

    def test_revoked_access_takes_effect_after_resync(self):
        self.assertEqual(self.ids("parental leave", self.alice), ["hr-policy"])
        self.idx.resync_acl("hr-policy", allowed_groups=set(), allowed_users={"hr-admin"}, now=NOW)
        self.assertEqual(self.ids("parental leave", self.alice), [])

    def test_stale_acl_fails_closed(self):
        later = NOW + 7200  # ACL last synced two hours ago, limit is one hour
        self.assertEqual(self.ids("parental leave", self.alice, now=later), [])
        self.idx.resync_acl("hr-policy", {"all-staff"}, set(), now=later)
        self.assertEqual(self.ids("parental leave", self.alice, now=later), ["hr-policy"])

    def test_citations_and_audit_list_only_returned_documents(self):
        out = self.idx.answer_context("leave policy", self.alice, NOW)
        self.assertEqual([c["doc_id"] for c in out["citations"]], ["hr-policy"])
        self.assertEqual(out["audit"]["doc_ids"], ["hr-policy"])
        self.assertEqual(self.idx.audit_log[-1]["user_id"], "alice")

    def test_prompt_contains_no_hidden_text_and_marks_context_untrusted(self):
        out = self.idx.answer_context("leave", self.alice, NOW)
        self.assertNotIn("executive compensation", out["prompt"])
        self.assertNotIn("settlement", out["prompt"])
        self.assertIn("untrusted data", out["prompt"])

    def test_no_visible_documents_returns_empty_not_error(self):
        nobody = User("zed", "acme", frozenset())
        self.assertEqual(self.idx.search("leave", nobody, NOW), [])
        self.assertEqual(self.idx.answer_context("leave", nobody, NOW)["citations"], [])


if __name__ == "__main__":
    unittest.main()
