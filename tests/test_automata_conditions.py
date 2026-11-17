"""Regression tests for every custom language condition."""
import itertools
import unittest

from automata import CONDITIONS, build, build_custom


def words(alphabet, max_length=5):
    for length in range(max_length + 1):
        for chars in itertools.product(alphabet, repeat=length):
            yield "".join(chars)


RULES = [
    ("exact", "ab", lambda w: w == "ab", "ab"),
    ("starts", "ab", lambda w: w.startswith("ab"), "ab"),
    ("ends", "ab", lambda w: w.endswith("ab"), "ab"),
    ("contains", "aba", lambda w: "aba" in w, "ab"),
    ("not_starts", "ab", lambda w: not w.startswith("ab"), "ab"),
    ("not_ends", "ab", lambda w: not w.endswith("ab"), "ab"),
    ("not_contains", "aba", lambda w: "aba" not in w, "ab"),
    ("prefix", {"pattern": "01"}, lambda w: w.startswith("01"), "01"),
    ("at_least", {"symbols": "a", "count": 2}, lambda w: w.count("a") >= 2, "ab"),
    ("at_most", {"symbols": "a", "count": 1}, lambda w: w.count("a") <= 1, "ab"),
    ("exactly_count", {"symbols": "a", "count": 2}, lambda w: w.count("a") == 2, "ab"),
    ("even_count", {"symbols": "0,1"}, lambda w: w.count("0") % 2 == 0 and w.count("1") % 2 == 0, "01"),
    ("odd_count", {"symbols": "1"}, lambda w: w.count("1") % 2 == 1, "01"),
    ("no_adjacent", {"patterns": "00|11"}, lambda w: "00" not in w and "11" not in w, "01"),
    ("followed_by", {"before": "a", "after": "b"},
     lambda w: all(i + 1 < len(w) and w[i + 1] == "b" for i, c in enumerate(w) if c == "a"), "ab"),
    ("suffix_any", {"patterns": "00|11"}, lambda w: w.endswith("00") or w.endswith("11"), "01"),
    ("divisible", {"divisor": 3}, lambda w: int(w or "0", 2) % 3 == 0, "01"),
    ("position_end", {"symbol": "a", "position": 2}, lambda w: len(w) >= 2 and w[-2] == "a", "ab"),
]


class CustomLanguageTests(unittest.TestCase):
    def test_every_available_condition_for_each_automaton_type(self):
        self.assertEqual(set(CONDITIONS), {name for name, *_ in RULES})
        for kind in ("DFA", "NFA", "ENFA"):
            for name, value, expected, alphabet in RULES:
                auto = build_custom(list(alphabet), kind, {name: value})
                with self.subTest(kind=kind, condition=name):
                    for word in words(alphabet):
                        self.assertEqual(auto.simulate(word)[1], expected(word), word)

    def test_and_or_and_empty_string_options(self):
        for kind in ("DFA", "NFA", "ENFA"):
            with self.subTest(kind=kind):
                conjunction = build_custom(list("ab"), kind, {"starts": "a", "ends": "b"}, "AND")
                disjunction = build_custom(list("ab"), kind, {"starts": "a", "ends": "b"}, "OR")
                self.assertTrue(conjunction.simulate("abbaab")[1])
                self.assertFalse(conjunction.simulate("aa")[1])
                self.assertTrue(disjunction.simulate("aa")[1])
                self.assertTrue(disjunction.simulate("bb")[1])
                self.assertFalse(disjunction.simulate("ba")[1])

                accept_empty = build_custom(list("ab"), kind, {"starts": "a"}, "AND", "Accept")
                reject_empty = build_custom(list("ab"), kind, {"starts": "a"}, "AND", "Reject")
                self.assertTrue(accept_empty.simulate("")[1])
                self.assertTrue(accept_empty.simulate("ab")[1])
                self.assertFalse(reject_empty.simulate("")[1])
                self.assertTrue(reject_empty.simulate("ab")[1])

    def test_multiple_symbols_and_patterns_are_grouped_with_and(self):
        parity = build_custom(list("01"), "DFA", {"even_count": {"symbols": "0,1"}}, "OR")
        no_double = build_custom(list("01"), "DFA", {"no_adjacent": {"patterns": "00|11"}}, "OR")
        self.assertTrue(parity.simulate("0011")[1])
        self.assertFalse(parity.simulate("01")[1])
        self.assertTrue(no_double.simulate("0101")[1])
        self.assertFalse(no_double.simulate("001")[1])

    def test_legacy_modes_still_work(self):
        for kind in ("DFA", "NFA", "ENFA"):
            auto = build("abba", list("ab"), kind, "contains")
            self.assertTrue(auto.simulate("aabbaab")[1])
            self.assertFalse(auto.simulate("abab")[1])


if __name__ == "__main__":
    unittest.main()
