# Notes from agent(2)

Usage:
import rule_parser as rp
f = rp.parse(text)            # returns a File; raises a RuleGrammarError subclass on problems
f["CP"].patterns              # [Pattern([Lefts(), Head('c_pat'), Rule('TP')]), ...]
rp.to_source(f)               # prints the rules back in the same notation
Run the tests with .venv/bin/python tree_tools/rule_parser/test_rule_parser.py.

Files:

┌─────────────────────┬────────────────────────────────────────────────────────────────────────────────────────────┐
│        File         │                                        What it does                                        │
├─────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────┤
│ grammar.lark        │ tokens and syntax rules                                                                    │
├─────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────┤
│ syntax.py           │ lexer (tokenize) and Lark parse tree (parse_tree)                                          │
├─────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────┤
│ adt.py              │ the dataclasses (Lark tree → ADT conversion is in transform.py), and to_source             │
├─────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────┤
│ transform.py        │ converts the parse tree into the dataclasses and replaces each RuleName with the actual    │
│                     │ Rule object                                                                                │
├─────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────┤
│ checks.py           │ at most one Head, no consecutive _, circular check                                         │
├─────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────┤
│ errors.py           │ one exception class per kind of problem                                                    │
├─────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────┤
│ test_rule_parser.py │ 35 tests: lexer, the spec example, syntax, references, all three checks                    │
└─────────────────────┴────────────────────────────────────────────────────────────────────────────────────────────┘

How I read your answers:
- Consuming: ø, 0, "" and _ can consume nothing. !head, a bare symbol and a non-empty string always consume something. An optional element can consume nothing, since it may be absent. A rule that reaches itself through only non-consuming elements is an error, so A -> _ B with B -> ø A fails. That covers "_ cannot appear before non-consuming recursion".
- "Expand the rule first": I applied this to the consecutive-_ check. A -> B _ with B -> x _ is an error. I also check the mirror case, _ B where B starts with _.
- ADT additions:
  - Symbol(name) for bare symbols.
  - Opt(element) for ?x. I called it Opt so it doesn't clash with typing.Optional.
  - File(rules) as the entry point.
  - An anonymous group's inner Rule has name="".
- Rule references: a RuleName inside a pattern becomes the actual Rule object, so the rules form a cyclic graph. Two consequences:
  - Rule compares by identity.
  - Its printed form shows referenced rules by name only, as Rule('TP'), so printing doesn't loop forever.
- Strings: a backslash escapes the next character, so "a\"b" is the text a"b.

Places where I didn't follow spec.md literally:
1. Rules -> Rule ?('|' Rules) would put | between rules. Your example doesn't do that, and it would clash with | between patterns. Rules are simply written one after another, and a new rule starts wherever RuleName -> appears.
2. ? goes before its element (?x), matching how spec.md writes optional parts. Regexes put it after (x?).
3. spec.md doesn't list ! as a token, but Head -> '!' wordName needs it. Bare symbols aren't in its ADT yet either, and the docs still say wordName. I haven't edited spec.md.

Open questions:
- Does _ ø _ count as consecutive _? I treated it as allowed, because only directly adjacent elements are checked.
- Should ? be allowed on things where it means nothing, like ?_, ?ø and ?""? Right now they're accepted.