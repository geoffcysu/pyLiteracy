"""
The grammar rules of spec.md that the parser itself can't express:

1. A Pattern can contain at most one Head.
2. No consecutive Lefts (`_`). Two `_` are consecutive when everything between them
   may consume nothing (e.g. `_ ø _`). A Rule next to a `_` is expanded first, so in
   `A -> B _` with `B -> x _`, the two `_` are consecutive.
3. Circular check: a rule shouldn't be recursed without consuming.
   ø, 0, "" consume nothing; !head, symbol and non-empty strings consume something;
   `_` only takes what the others leave, so it may consume nothing; `x?` may be absent.
   So `A -> _ A` or `A -> ø B`, `B -> "" A` are errors.
"""
from typing import Callable, Optional

from .adt import (AnonRule, Element, Empty, LinguisticRules, Head, Lefts, Opt, Pattern,
                  Rule, StrPat, Symbol, all_rules, to_source)
from .adt import _elem_source as elem_source
from .errors import ConsecutiveLeftsError, LeftRecursionError, MultipleHeadsError


def check(linguistic_rules: LinguisticRules) -> None:
    """Raises the first violation found."""
    rules = list(all_rules(linguistic_rules))
    _check_heads(rules)
    # before the Lefts check: `_` followed by a non-consuming recursion also expands
    # into consecutive `_`, but the recursion is the clearer explanation.
    _check_left_recursion(linguistic_rules, rules)
    _check_consecutive_lefts(rules)


def _where(rule: Rule, owner: Rule, i: int) -> str:
    inside = "" if rule is owner else " of a (...) group"
    return f"rule {owner.name}, pattern {i + 1}{inside}"


# ---- 1. at most one Head --------------------------------------------------

def _check_heads(rules: list[tuple[Rule, Rule]]):
    def is_head(e: Element) -> bool:
        return isinstance(e, Head) or (isinstance(e, Opt) and is_head(e.element))

    for rule, owner in rules:
        for i, p in enumerate(rule.patterns):
            heads = [e for e in p.elements if is_head(e)]
            if len(heads) > 1:
                raise MultipleHeadsError(f"{_where(rule, owner, i)}: more than one Head "
                                         f"in `{to_source(p)}`")


# ---- helpers: properties of rules, computed as fixpoints ------------------

def _fixpoint(rules: list[Rule],
              pattern_has: Callable[[Pattern, Callable[[Element], bool]], bool],
              base: Callable[[Element, Callable[[Element], bool]], bool]
              ) -> Callable[[Element], bool]:
    """The least fixpoint of a boolean property over all rules (rules can be cyclic).
    base(e, prop) gives the property of a non-rule element; prop is used for nested elements."""
    table = {rule: False for rule in rules}

    def prop(e: Element) -> bool:
        if isinstance(e, Rule):
            return table[e]
        if isinstance(e, AnonRule):
            return table[e.rule]
        return base(e, prop)

    changed = True
    while changed:
        changed = False
        for rule in rules:
            if not table[rule] and any(pattern_has(p, prop) for p in rule.patterns):
                table[rule] = changed = True
    return prop


def _nullable(rules: list[Rule]) -> Callable[[Element], bool]:
    """Whether an element may consume nothing."""
    def base(e, prop):
        if isinstance(e, (Lefts, Empty, Opt)):
            return True
        if isinstance(e, StrPat):
            return e.value == ""
        return False  # Head, Symbol
    return _fixpoint(rules, lambda p, prop: all(prop(e) for e in p.elements), base)


def _lefts_at(rules: list[Rule], nullable: Callable[[Element], bool],
              from_end: bool) -> Callable[[Element], bool]:
    """Whether an element may start / end (from_end) with a `_` after expansion,
    skipping elements that may consume nothing (`x _ ø` ends with `_`)."""
    def base(e, prop):
        if isinstance(e, Lefts):
            return True
        if isinstance(e, Opt):
            return prop(e.element)
        return False

    def pattern_has(p: Pattern, prop) -> bool:
        for e in (reversed(p.elements) if from_end else p.elements):
            if prop(e):
                return True
            if not nullable(e):
                return False
        return False
    return _fixpoint(rules, pattern_has, base)


# ---- 2. no consecutive Lefts ----------------------------------------------

def _check_consecutive_lefts(rules: list[tuple[Rule, Rule]]):
    plain = [rule for rule, _ in rules]
    nullable = _nullable(plain)
    starts = _lefts_at(plain, nullable, from_end=False)
    ends = _lefts_at(plain, nullable, from_end=True)
    for rule, owner in rules:
        for i, p in enumerate(rule.patterns):
            for a_i, a in enumerate(p.elements):
                if not ends(a):
                    continue
                # look right, through elements that may consume nothing
                for b_i in range(a_i + 1, len(p.elements)):
                    b = p.elements[b_i]
                    if starts(b):
                        between = " ".join(elem_source(e) for e in p.elements[a_i:b_i + 1])
                        raise ConsecutiveLeftsError(
                            f"{_where(rule, owner, i)}: `{between}` "
                            f"gives consecutive `_` in `{to_source(p)}`")
                    if not nullable(b):
                        break


# ---- 3. circular check -----------------------------------------------------

def _check_left_recursion(linguistic_rules: LinguisticRules, rules: list[tuple[Rule, Rule]]):
    plain = [rule for rule, _ in rules]
    nullable = _nullable(plain)

    def targets(e: Element) -> list[Rule]:
        if isinstance(e, Rule):
            return [e]
        if isinstance(e, AnonRule):
            return [e.rule]
        if isinstance(e, Opt):
            return targets(e.element)
        return []

    # rule -> the rules it can reach before anything is consumed
    edges: dict[Rule, list[Rule]] = {}
    for rule in plain:
        edges[rule] = []
        for p in rule.patterns:
            for e in p.elements:
                edges[rule] += targets(e)
                if not nullable(e):
                    break

    # depth first search for a cycle
    WHITE, GREY, BLACK = 0, 1, 2
    color = {rule: WHITE for rule in plain}
    path: list[Rule] = []

    def dfs(rule: Rule) -> Optional[list[Rule]]:
        color[rule] = GREY
        path.append(rule)
        for nxt in edges[rule]:
            if color[nxt] == GREY:
                return path[path.index(nxt):] + [nxt]
            if color[nxt] == WHITE and (cycle := dfs(nxt)):
                return cycle
        path.pop()
        color[rule] = BLACK
        return None

    def show(rule: Rule) -> str:
        return rule.name or "(" + " | ".join(to_source(p) for p in rule.patterns) + ")"

    for rule in linguistic_rules.rules:
        if color[rule] == WHITE and (cycle := dfs(rule)):
            raise LeftRecursionError("recursion without consuming anything: "
                                     + " -> ".join(show(r) for r in cycle))
