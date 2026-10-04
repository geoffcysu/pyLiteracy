"""
Tests of rule_parser.

Run from anywhere:
    .venv/bin/python tree_tools/rule_parser/test_rule_parser.py
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import rule_parser as rp
from rule_parser import (AnonRule, Empty, LinguisticRules, Head, Lefts, Opt, Pattern, Rule,
                         StrPat, Symbol)

# the example of spec.md
EXAMPLE = """
CP -> _ !c_pat TP
    | ø ø TP
TP -> ø ModP
ModP -> _ !mod_pat NegP
    | "" "" NegP
NegP -> _ neg_pat LightVP
    | "" "" LightVP
LightVP -> _ lightV_pat (VP | DegP | pred_on_neg)
    | ø ø (VP | DegP | pred_on_neg)
VP -> _ v_pat (CP | ClsP)
DegP -> _ deg_pat ClsP
ClsP -> _ cls_pat NP
    | ø ø NP
NP -> (_ rc_pat) _
    | _ n_pat _
    | ø ø _
"""


def tokens(text):
    return [(t.type, str(t)) for t in rp.tokenize(text)]


class TestLexer(unittest.TestCase):

    def test_token_kinds(self):
        self.assertEqual(
            [kind for kind, _ in tokens('A -> _ !h x "s" ø 0 B? (C | D)')],
            ["RULE_NAME", "__ANON_0", "UNDERSCORE", "BANG", "SYMBOL", "SYMBOL", "STRING",
             "EMPTY", "EMPTY", "RULE_NAME", "QMARK", "LPAR", "RULE_NAME", "VBAR",
             "RULE_NAME", "RPAR"])

    def test_underscore_vs_symbol(self):
        self.assertEqual(tokens("_ _foo __ x_1"),
                         [("UNDERSCORE", "_"), ("SYMBOL", "_foo"), ("SYMBOL", "__"), ("SYMBOL", "x_1")])

    def test_rule_name_vs_symbol(self):
        self.assertEqual(tokens("LightVP lightV_pat"),
                         [("RULE_NAME", "LightVP"), ("SYMBOL", "lightV_pat")])

    def test_spaces_ignored(self):
        self.assertEqual(tokens("A->x"), tokens("A  ->\t x"))

    def test_newline_is_a_token(self):
        self.assertEqual(tokens("A -> x\n\n  B -> y"),
                         [("RULE_NAME", "A"), ("__ANON_0", "->"), ("SYMBOL", "x"),
                          ("_NL", "\n\n  "),
                          ("RULE_NAME", "B"), ("__ANON_0", "->"), ("SYMBOL", "y")])

    def test_newline_before_bar_is_ignored(self):
        self.assertEqual(tokens("A -> x\n    | y"), tokens("A -> x | y"))
        self.assertEqual(tokens("A -> x\n\n    | y"), tokens("A -> x | y"))

    def test_bad_character(self):
        with self.assertRaises(rp.RuleSyntaxError):
            rp.tokenize("A -> x & y")


class TestExample(unittest.TestCase):

    def setUp(self):
        self.f = rp.parse(EXAMPLE)

    def test_rule_names(self):
        self.assertEqual(self.f.names(),
                         ["CP", "TP", "ModP", "NegP", "LightVP", "VP", "DegP", "ClsP", "NP"])

    def test_CP(self):
        cp, tp = self.f["CP"], self.f["TP"]
        self.assertEqual(cp.patterns, [Pattern([Lefts(), Head("c_pat"), tp]),
                                       Pattern([Empty(), Empty(), tp])])

    def test_references_are_the_rule_objects(self):
        self.assertIs(self.f["CP"].patterns[0].elements[2], self.f["TP"])
        # cyclic: VP -> (CP | ClsP), CP -> ... -> VP
        anon = self.f["VP"].patterns[0].elements[2]
        self.assertIs(anon.rule.patterns[0].elements[0], self.f["CP"])

    def test_strpat_and_symbol(self):
        self.assertEqual(self.f["ModP"].patterns[1],
                         Pattern([StrPat(""), StrPat(""), self.f["NegP"]]))
        self.assertEqual(self.f["NegP"].patterns[0].elements[1], Symbol("neg_pat"))

    def test_anon_rule(self):
        anon = self.f["LightVP"].patterns[0].elements[2]
        self.assertIsInstance(anon, AnonRule)
        self.assertEqual(anon.rule.name, "")
        self.assertEqual(anon.rule.patterns, [Pattern([self.f["VP"]]),
                                              Pattern([self.f["DegP"]]),
                                              Pattern([Symbol("pred_on_neg")])])

    def test_NP(self):
        np = self.f["NP"]
        first = np.patterns[0].elements[0]
        self.assertEqual(first.rule.patterns, [Pattern([Lefts(), Symbol("rc_pat")])])
        self.assertEqual(np.patterns[1], Pattern([Lefts(), Symbol("n_pat"), Lefts()]))
        self.assertEqual(np.patterns[2], Pattern([Empty(), Empty(), Lefts()]))

    def test_repr_does_not_loop(self):
        self.assertIn("Rule('TP')", repr(self.f["CP"]))

    def test_round_trip(self):
        src = rp.to_source(self.f)
        self.assertEqual(rp.to_source(rp.parse(src)), src)


class TestSyntax(unittest.TestCase):

    def test_empty_file(self):
        self.assertEqual(rp.parse("").rules, [])
        self.assertEqual(rp.parse("  \n ").rules, [])

    def test_one_pattern_rule(self):
        self.assertEqual(rp.parse("A -> x").rules[0].patterns, [Pattern([Symbol("x")])])

    def test_rules_are_separated_by_newlines(self):
        self.assertEqual(rp.parse("A -> x B\nB -> y").names(), ["A", "B"])
        self.assertEqual(rp.parse("\n\nA -> x B\n\n\nB -> y\n\n").names(), ["A", "B"])
        self.assertEqual(rp.parse("A -> x B\r\nB -> y\r\n").names(), ["A", "B"])

    def test_rules_on_one_line(self):
        with self.assertRaises(rp.RuleSyntaxError):
            rp.parse("A -> x B B -> y")

    def test_continuation_lines(self):
        f = rp.parse("A -> x\n  | y\n\n  | z\nB -> w")
        self.assertEqual(len(f["A"].patterns), 3)
        self.assertEqual(f["B"].patterns, [Pattern([Symbol("w")])])

    def test_pattern_cannot_continue_without_bar(self):
        with self.assertRaises(rp.RuleSyntaxError):
            rp.parse("A -> x\n     y")

    def test_empty_is_o_slash_or_zero(self):
        self.assertEqual(rp.parse("A -> ø 0 x").rules[0].patterns[0].elements[:2],
                         [Empty(), Empty()])

    def test_strings(self):
        p = rp.parse(r'A -> "" "abc" "a\"b" "a\\b"').rules[0].patterns[0]
        self.assertEqual(p.elements, [StrPat(""), StrPat("abc"), StrPat('a"b'), StrPat("a\\b")])

    def test_optional(self):
        f = rp.parse("A -> !h? x? B? (x | y?)\nB -> z")
        e = f["A"].patterns[0].elements
        self.assertEqual(e[:3], [Opt(Head("h")), Opt(Symbol("x")), Opt(f["B"])])
        self.assertEqual(e[3].rule.patterns[1], Pattern([Opt(Symbol("y"))]))

    def test_optional_group(self):
        e = rp.parse("A -> (x | y)? z").rules[0].patterns[0].elements[0]
        self.assertIsInstance(e, Opt)
        self.assertIsInstance(e.element, AnonRule)

    def test_optional_round_trip(self):
        src = "A -> !h? (x | y)? z"
        self.assertEqual(rp.to_source(rp.parse(src)), src)

    def test_nested_groups(self):
        f = rp.parse("A -> ((x | y) z)")
        inner = f["A"].patterns[0].elements[0].rule.patterns[0].elements[0]
        self.assertIsInstance(inner, AnonRule)

    def test_syntax_errors(self):
        for text in ["A ->", "A -> | x", "A -> x |", "a -> x", "A x", "A -> ()",
                     "A -> (x", "A -> !B", "A -> ?x", "A -> x??", "-> x"]:
            with self.subTest(text=text), self.assertRaises(rp.RuleSyntaxError):
                rp.parse(text)

    def test_syntax_error_has_position(self):
        with self.assertRaisesRegex(rp.RuleSyntaxError, "line 2"):
            rp.parse("A -> x\nB -> | y")


class TestReferences(unittest.TestCase):

    def test_undefined(self):
        with self.assertRaisesRegex(rp.UndefinedRuleError, "rule C .*used in A"):
            rp.parse("A -> x C")

    def test_undefined_inside_group(self):
        with self.assertRaises(rp.UndefinedRuleError):
            rp.parse("A -> x (y | C?)")

    def test_duplicate(self):
        with self.assertRaises(rp.DuplicateRuleError):
            rp.parse("A -> x\nA -> y")

    def test_forward_reference(self):
        f = rp.parse("A -> x B\nB -> y")
        self.assertIs(f["A"].patterns[0].elements[1], f["B"])


class TestChecks(unittest.TestCase):

    def assertValid(self, text):
        self.assertIsInstance(rp.parse(text), LinguisticRules)

    def assertInvalid(self, error, text):
        with self.subTest(text=text), self.assertRaises(error):
            rp.parse(text)

    def test_validate_flag(self):
        self.assertIsInstance(rp.parse("A -> !a !b", validate=False), LinguisticRules)

    # at most one Head
    def test_heads(self):
        self.assertValid("A -> _ !h x")
        self.assertValid("A -> x y")
        self.assertValid("A -> (!a | !b) !c")  # each group pattern is its own Pattern
        self.assertInvalid(rp.MultipleHeadsError, "A -> !a !b")
        self.assertInvalid(rp.MultipleHeadsError, "A -> !a !b?")
        self.assertInvalid(rp.MultipleHeadsError, "A -> x | _ !a x !b")
        self.assertInvalid(rp.MultipleHeadsError, "A -> (!a !b)")

    # no consecutive Lefts
    def test_consecutive_lefts(self):
        self.assertValid("A -> _ x _")
        self.assertValid("A -> _ !h _")
        self.assertValid('A -> _ "a" _')
        self.assertInvalid(rp.ConsecutiveLeftsError, "A -> _ _")
        self.assertInvalid(rp.ConsecutiveLeftsError, "A -> x _ _?")
        self.assertInvalid(rp.ConsecutiveLeftsError, "A -> (x | y _) _")

    def test_consecutive_lefts_through_non_consuming(self):
        # everything between the two `_` may consume nothing
        self.assertInvalid(rp.ConsecutiveLeftsError, "A -> _ ø _")
        self.assertInvalid(rp.ConsecutiveLeftsError, "A -> _ 0 ø _")
        self.assertInvalid(rp.ConsecutiveLeftsError, 'A -> _ "" _')
        self.assertInvalid(rp.ConsecutiveLeftsError, "A -> _ x? _")
        self.assertInvalid(rp.ConsecutiveLeftsError, "A -> _ E _\nE -> ø | x")
        self.assertValid("A -> _ E _\nE -> ø x")
        self.assertInvalid(rp.ConsecutiveLeftsError, "A -> B _\nB -> x _ ø")
        self.assertInvalid(rp.ConsecutiveLeftsError, "A -> _ B\nB -> \"\" _ x")

    def test_consecutive_lefts_after_expanding_rules(self):
        self.assertValid("A -> B _\nB -> _ x")
        self.assertInvalid(rp.ConsecutiveLeftsError, "A -> B _\nB -> x _")
        self.assertInvalid(rp.ConsecutiveLeftsError, "A -> B _\nB -> x | C\nC -> y _")  # through C
        self.assertInvalid(rp.ConsecutiveLeftsError, "A -> x _ B\nB -> _ y")

    # circular check
    def test_consuming_recursion_is_fine(self):
        self.assertValid("A -> !h A | x")
        self.assertValid("A -> x A | y")
        self.assertValid('A -> "a" A | y')
        self.assertValid("A -> ø x A | y")
        self.assertValid("A -> B\nB -> x A | y")

    def test_left_recursion(self):
        self.assertInvalid(rp.LeftRecursionError, "A -> A x")
        self.assertInvalid(rp.LeftRecursionError, "A -> ø A")
        self.assertInvalid(rp.LeftRecursionError, "A -> 0 A")
        self.assertInvalid(rp.LeftRecursionError, 'A -> "" A')
        self.assertInvalid(rp.LeftRecursionError, "A -> x? A")
        self.assertInvalid(rp.LeftRecursionError, "A -> ø B\nB -> \"\" A")

    def test_lefts_before_recursion(self):
        # `_` may consume nothing, so it can't come before a non-consuming recursion
        self.assertInvalid(rp.LeftRecursionError, "A -> _ B\nB -> ø A")

    def test_recursion_through_groups_and_nullable_rules(self):
        self.assertInvalid(rp.LeftRecursionError, "A -> (B | x) y\nB -> A")
        self.assertInvalid(rp.LeftRecursionError, "A -> E A\nE -> ø | x")
        self.assertValid("A -> E A | y\nE -> x")

    def test_error_shows_cycle(self):
        with self.assertRaisesRegex(rp.LeftRecursionError, "A -> B -> A"):
            rp.parse("A -> ø B\nB -> ø A")


if __name__ == "__main__":
    unittest.main(verbosity=2)
