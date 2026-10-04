# notes from agent(3)

What changed:

1. A newline ends a rule.
   - A line break before a | continues the current rule (    | ø ø TP). Any other line break starts the next rule.
   - Blank lines, Windows line endings, and leading or trailing newlines are all fine.
   - Writing two rules on one line (A -> x B -> y) is now a syntax error. So is starting a line with an element instead of |.
   - With newlines meaningful, the parser switched from Earley to LALR, which is faster.
2. ? goes after the element, like in regex: x?, !h?, B?, (x | y)?. ?x is a syntax error now, and to_source prints the postfix form.
3. _ ø _ counts as consecutive _. I applied it the same way as the circular check: two _ are consecutive if everything between them can consume nothing. This also catches a few cases you didn't mention, so check they're what you want:
   - _ "" _
   - _ x? _, since x? may be absent
   - _ E _ where E -> ø | x, since E can be empty

   Expanding rules looks through these too: with B -> x _ ø, the pattern B _ is an error. If you meant only ø/0 to sit between _, I can narrow it.

Other changes:
- Check order: the circular check now runs before the consecutive-_ check. A _ followed by recursion that consumes nothing (A -> _ B, B -> ø A) also expands into consecutive _. Reporting it as recursion explains the problem more clearly.
- Tests: updated for the new syntax, with new tests for newline handling, continuation lines, optional groups, and the wider consecutive-_ rule. That brings the total from 35 to 43.

Still open: your answer to open question 2 is blank, so _?, ø? and ""? are still accepted even though ? changes nothing for them.

Not done: spec.md's ADT still doesn't list Symbol or Opt, and I haven't edited it.