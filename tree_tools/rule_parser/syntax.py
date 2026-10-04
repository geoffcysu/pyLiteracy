"""Lexer and syntax tree (lark parse tree) of the rule language."""
from lark import Lark, Token, Tree
from lark.exceptions import UnexpectedInput

from .errors import RuleSyntaxError

# Rules are separated by line breaks, so LALR(1) is enough.
# The basic lexer (not the contextual one) makes tokenize() give the same tokens the parser sees.
_lark = Lark.open("grammar.lark", rel_to=__file__,
                  start="linguistic_rules", parser="lalr", lexer="basic",
                  propagate_positions=True)


def _syntax_error(text: str, e: UnexpectedInput) -> RuleSyntaxError:
    return RuleSyntaxError(f"line {e.line}, column {e.column}: {type(e).__name__}\n"
                           + e.get_context(text))


def tokenize(text: str) -> list[Token]:
    try:
        return list(_lark.lex(text))
    except UnexpectedInput as e:
        raise _syntax_error(text, e) from None


def parse_tree(text: str) -> Tree:
    try:
        return _lark.parse(text)
    except UnexpectedInput as e:
        raise _syntax_error(text, e) from None
