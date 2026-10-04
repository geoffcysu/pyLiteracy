"""
Parser of the rule language described in spec.md.

    from rule_parser import parse
    f = parse(open("rules.txt").read())
    f["CP"].patterns

Modules:
    grammar.lark  tokens and syntax rules
    syntax.py     lexer (tokenize) and syntax tree (parse_tree)
    adt.py        abstract data types, to_source
    transform.py  syntax tree -> abstract data tree, resolves rule references
    checks.py     Head count, consecutive Lefts, circular check
"""
from .adt import (AnonRule, Element, Empty, LinguisticRules, Head, Lefts, Opt, Pattern,
                  Rule, StrPat, Symbol, to_source)
from .checks import check
from .errors import (ConsecutiveLeftsError, DuplicateRuleError, LeftRecursionError,
                     MultipleHeadsError, RuleGrammarError, RuleSyntaxError,
                     UndefinedRuleError)
from .syntax import parse_tree, tokenize
from .transform import to_adt


def parse(text: str, *, validate: bool = True) -> LinguisticRules:
    linguistic_rules = to_adt(parse_tree(text))
    if validate:
        check(linguistic_rules)
    return linguistic_rules
