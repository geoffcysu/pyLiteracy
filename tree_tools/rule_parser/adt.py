"""
Abstract data types of the rule language (spec.md, "abstract data type").

    data LinguisticRules = LinguisticRules {rules :: List Rule}
    data Rule    = Rule {name :: String, patterns :: List Pattern}
    data AnonRule = AnonRule Rule
    data Pattern = Pattern (List (Lefts|Head|Rule|Empty|StrPat|Symbol|AnonRule|Opt))
    data Lefts   = Lefts
    data Head    = Head {pattern :: String}
    data Empty   = Empty
    data StrPat  = StrPat String
    data Symbol  = Symbol {name :: String}
    data Opt     = Opt Element            -- `x?`, x is optional

A `Rule` inside a Pattern is the very same object as the named Rule it refers to,
so rules form a (possibly cyclic) graph. `Rule` therefore compares by identity,
and its repr shows referenced rules by name only.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterator, Union


@dataclass(frozen=True)
class Lefts:
    """`_`: consumes whatever is left by the Head and the other elements."""


@dataclass(frozen=True)
class Head:
    """`!symbol`"""
    pattern: str


@dataclass(frozen=True)
class Empty:
    """`ø` or `0`: consumes nothing."""


@dataclass(frozen=True)
class StrPat:
    """`"..."`: a literal string. `""` consumes nothing."""
    value: str


@dataclass(frozen=True)
class Symbol:
    """a bare `symbol` (python variable name), e.g. `neg_pat`."""
    name: str


@dataclass(eq=False)
class Rule:
    name: str  # "" for the Rule inside an AnonRule
    patterns: list[Pattern] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"Rule(name={self.name!r}, patterns={self.patterns!r})"


@dataclass(eq=False)
class AnonRule:
    """`( Pattern | Pattern ... )`"""
    rule: Rule

    def __repr__(self) -> str:
        return f"AnonRule({self.rule.patterns!r})"


@dataclass(frozen=True)
class Opt:
    """`element?`"""
    element: Element

    def __repr__(self) -> str:
        return f"Opt({_elem_repr(self.element)})"


Element = Union[Lefts, Head, Rule, Empty, StrPat, Symbol, AnonRule, Opt]


@dataclass
class Pattern:
    elements: list[Element]

    def __repr__(self) -> str:
        return f"Pattern([{', '.join(_elem_repr(e) for e in self.elements)}])"


@dataclass(eq=False)
class LinguisticRules:
    rules: list[Rule] = field(default_factory=list)

    def __getitem__(self, name: str) -> Rule:
        for rule in self.rules:
            if rule.name == name:
                return rule
        raise KeyError(name)

    def __contains__(self, name: str) -> bool:
        return any(rule.name == name for rule in self.rules)

    def names(self) -> list[str]:
        return [rule.name for rule in self.rules]


def _elem_repr(e: Element) -> str:
    # A referenced Rule is shown by name, otherwise cyclic rules would print forever.
    return f"Rule({e.name!r})" if isinstance(e, Rule) else repr(e)


def all_rules(linguistic_rules: LinguisticRules) -> Iterator[tuple[Rule, Rule]]:
    """Yields (rule, owner) for every named Rule and every Rule inside an AnonRule.
    owner is the named Rule the rule is written in."""
    def nested(e: Element) -> Iterator[Rule]:
        if isinstance(e, AnonRule):
            yield e.rule
            for p in e.rule.patterns:
                for x in p.elements:
                    yield from nested(x)
        elif isinstance(e, Opt):
            yield from nested(e.element)

    for rule in linguistic_rules.rules:
        yield rule, rule
        for p in rule.patterns:
            for e in p.elements:
                for anon in nested(e):
                    yield anon, rule


def to_source(x: Union[LinguisticRules, Rule, Pattern, Element]) -> str:
    """Prints back the rule language. parse(to_source(f)) gives the same structure as f."""
    if isinstance(x, LinguisticRules):
        return "\n".join(to_source(r) for r in x.rules)
    if isinstance(x, Pattern):
        return " ".join(_elem_source(e) for e in x.elements)
    if isinstance(x, Rule):
        # a top level definition; Rules inside Patterns are handled by _elem_source
        sep = "\n" + " " * (len(x.name) + 1) + "| "
        return f"{x.name} -> " + sep.join(to_source(p) for p in x.patterns)
    return _elem_source(x)


def _elem_source(e: Element) -> str:
    if isinstance(e, Lefts):
        return "_"
    if isinstance(e, Head):
        return "!" + e.pattern
    if isinstance(e, Empty):
        return "ø"
    if isinstance(e, StrPat):
        return '"' + re.sub(r'(["\\])', r"\\\1", e.value) + '"'
    if isinstance(e, Symbol):
        return e.name
    if isinstance(e, Rule):
        return e.name
    if isinstance(e, AnonRule):
        return "(" + " | ".join(to_source(p) for p in e.rule.patterns) + ")"
    if isinstance(e, Opt):
        return _elem_source(e.element) + "?"
    raise TypeError(f"not an element: {e!r}")
