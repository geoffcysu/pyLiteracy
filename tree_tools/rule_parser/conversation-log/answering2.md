# answering notes2

This is answering the message logged in notes2.md

About those you didn't follow:
1. You're right, I changed spec.md, now a new Rule is lead with a newline (so this may change the lexer design)
2. I changed spec.md, now "?" is used exactly like regex, put after pattern.
3. I added "!" as a token in spec.md, but it seems you've added "!" already.

About the open questions:
1. Yes, _ ø _ count as consecutive _; please amend the current implementation.
2. 0?, ""? are allowed, _? is not allowed, for _ consumes in a greedy way.
