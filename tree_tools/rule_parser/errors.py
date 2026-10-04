class RuleGrammarError(Exception):
    """Base class of every error raised by rule_parser."""


class RuleSyntaxError(RuleGrammarError):
    """The input can't be tokenized or doesn't follow the grammar."""


class DuplicateRuleError(RuleGrammarError):
    pass


class UndefinedRuleError(RuleGrammarError):
    pass


class MultipleHeadsError(RuleGrammarError):
    """A Pattern can contain at most one Head."""


class ConsecutiveLeftsError(RuleGrammarError):
    """No consecutive Lefts (`_`), also after expanding the Rules next to a `_`."""


class LeftRecursionError(RuleGrammarError):
    """A rule can recurse into itself without consuming anything."""
