"""Syntax tree -> abstract data tree, then resolves RuleName references to Rule objects."""
import re
from dataclasses import dataclass

from lark import Token, Transformer, Tree

from .adt import (AnonRule, Element, Empty, LinguisticRules, Head, Lefts, Opt, Pattern,
                  Rule, StrPat, Symbol)
from .errors import DuplicateRuleError, UndefinedRuleError


@dataclass(frozen=True)
class _Ref:
    """A RuleName inside a Pattern, before it is resolved."""
    token: Token


class _ToADT(Transformer):
    def linguistic_rules(self, rules):
        return list(rules)

    def rule(self, children):
        name, patterns = children
        return name, Rule(str(name), patterns)

    def alternatives(self, patterns):
        return list(patterns)

    def pattern(self, elements):
        return Pattern(list(elements))

    def opt(self, children):
        return Opt(children[0])

    def lefts(self, _):
        return Lefts()

    def head(self, children):
        return Head(str(children[0]))

    def empty(self, _):
        return Empty()

    def strpat(self, children):
        # backslash escapes the next character: "a\"b" -> a"b
        return StrPat(re.sub(r"\\(.)", r"\1", children[0][1:-1]))

    def symbol(self, children):
        return Symbol(str(children[0]))

    def rule_ref(self, children):
        return _Ref(children[0])

    def anon_rule(self, children):
        return AnonRule(Rule("", children[0]))


def to_adt(tree: Tree) -> LinguisticRules:
    named = _ToADT().transform(tree)

    table: dict[str, Rule] = {}
    for token, rule in named:
        if rule.name in table:
            raise DuplicateRuleError(f"line {token.line}: rule {rule.name} is defined twice")
        table[rule.name] = rule

    def resolve(e: Element, owner: str) -> Element:
        if isinstance(e, _Ref):
            if str(e.token) not in table:
                raise UndefinedRuleError(f"line {e.token.line}, column {e.token.column}: "
                                         f"rule {e.token} (used in {owner}) is not defined")
            return table[str(e.token)]
        if isinstance(e, AnonRule):
            resolve_rule(e.rule, owner)
        elif isinstance(e, Opt):
            return Opt(resolve(e.element, owner))
        return e

    def resolve_rule(rule: Rule, owner: str):
        for p in rule.patterns:
            p.elements = [resolve(e, owner) for e in p.elements]

    for rule in table.values():
        resolve_rule(rule, rule.name)
    return LinguisticRules(list(table.values()))
