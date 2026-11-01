import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "skills", "attention-budget", "scripts"))
import unittest
from attention_budget.measure import measure, classify, fk_grade, unexpanded_terms, is_bare_reauth, is_requested
from attention_budget.budget import DEFAULT_BUDGET_TOML
import tomllib

B = tomllib.loads(DEFAULT_BUDGET_TOML)
V = {"api", "json", "cli"}


class Kinds(unittest.TestCase):
    def test_status(self):
        self.assertEqual(classify("Running the tests now."), "status")

    def test_decision(self):
        t = "Two options. A keeps the file, B deletes it and cannot be undone. Which do you want?"
        self.assertEqual(classify(t), "decision")

    def test_closure(self):
        t = ("I wrote the new parser to src/parser.py and updated the tests in tests/test_parser.py. "
             "Both pass. The old module is removed and nothing else changed in the tree today at all.")
        self.assertEqual(classify(t), "closure")

    def test_explanation(self):
        t = " ".join(["The reason this happens is that the scheduler holds a lease."] * 6)
        self.assertEqual(classify(t), "explanation")


class Terms(unittest.TestCase):
    def test_unexpanded_flags_unknown_acronym(self):
        self.assertEqual(unexpanded_terms("We use HNSW for search.", V), ["HNSW"])

    def test_expanded_first_use_passes(self):
        self.assertEqual(unexpanded_terms("We use HNSW (hierarchical navigable small world) for search.", V), [])

    def test_known_passes(self):
        self.assertEqual(unexpanded_terms("The API returns JSON.", V), [])

    def test_code_is_ignored(self):
        m = measure("Run it:\n```\nexport FOO_BAR=1; ./run --fast\n```\nDone.", V, B)
        self.assertEqual(m.unexpanded, [])
        self.assertEqual(m.kind, "status")


class Budget(unittest.TestCase):
    def test_over_budget_breach(self):
        t = " ".join(["This sentence is filler that explains nothing the reader needs to know today."] * 20)
        m = measure(t, V, B)
        self.assertEqual(m.kind, "explanation")
        self.assertTrue(any("budget 150" in b for b in m.breaches))

    def test_requested_raises_budget(self):
        t = " ".join(["This sentence is filler that explains nothing the reader needs to know today."] * 20)
        m = measure(t, V, B, requested=True)
        self.assertEqual(m.budget_words, 600)
        self.assertFalse(any("budget" in b for b in m.breaches))

    def test_grade_sane(self):
        self.assertLess(fk_grade("The cat sat on the mat. It was warm. The sun was out."), 4)
        self.assertGreater(fk_grade("Notwithstanding the aforementioned considerations, the implementation necessitates comprehensive reconsideration."), 14)


class Human(unittest.TestCase):
    def test_reauth(self):
        for s in ("continue", "Continue.", "yes", "go ahead", "ok"):
            self.assertTrue(is_bare_reauth(s), s)
        self.assertFalse(is_bare_reauth("continue with the second file only"))

    def test_requested(self):
        self.assertTrue(is_requested("explain why this fails"))
        self.assertTrue(is_requested("lets meditate on this problem"))
        self.assertFalse(is_requested("fix the typo in the readme"))


if __name__ == "__main__":
    unittest.main()


class Sentences(unittest.TestCase):
    def test_lines_are_sentences(self):
        from attention_budget.measure import sentences
        self.assertEqual(len(sentences("- first item\n- second item\nThird line here")), 3)

    def test_bullets_do_not_inflate_grade(self):
        t = "\n".join(["- the cache holds one day of bars"] * 12)
        self.assertLess(fk_grade(t), 8)
