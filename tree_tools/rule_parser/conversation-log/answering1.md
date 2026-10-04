# answering the request(1)

## These issues are mentioned in a session:

1. The circular check doesn't say what "consuming" means. In your example, CP reaches itself again through this chain:
   CP -> _ !c_pat TP → TP -> ø ModP → ModP -> "" "" NegP → NegP -> "" "" LightVP → LightVP -> ø ø (VP | …) → VP -> _ v_pat (CP | ClsP)
   Whether the example passes depends on which elements consume input. My guess is that ø and "" consume nothing and !head consumes something. But what about _ (could the left material be empty?) and bare words like v_pat? If neither of those consumes, your own example fails the check. I also need to know whether recursion counts anywhere in a pattern or only before the first element that consumes something, which is the usual definition of left recursion.
2. Bare wordNames are still not in the ADT. neg_pat, lightV_pat, v_pat, deg_pat, cls_pat, rc_pat, n_pat and pred_on_neg appear in the example, but Pattern has no element type for them. Last time you chose a new ADT type, but the spec doesn't include it. I'd add data Word = Word {name :: String}.
3. StrPat has no field. The " token is "used to express string", but StrPat can't hold the text. Either only "" is allowed, or StrPat needs a value :: String field so that "abc" keeps its text.

Gaps I can fill myself unless you object

4. No rule for the left-hand side. Rule -> Pattern [spaces] Patterns has no RuleName -> part, so nothing describes a whole definition or a file. I'd add Definition -> RuleName '->' Rule and File -> Definition+.
5. One-pattern rules don't match the grammar. Patterns is required, so a rule must have at least two alternatives, yet TP -> ø ModP and VP -> … have one. I'd make Patterns optional.
6. Rule has no name. A pattern element Rule (like TP inside CP) needs to say which rule it means. I'd add a name field to Rule, make references point to the actual Rule object, and treat an undefined RuleName as an error.
7. Where one rule ends and the next begins. After an element like TP, the parser can't tell from the next name alone whether it's another element or the start of the next definition (ModP -> …). It has to look one more token ahead for ->. Lark's Earley parser handles that, so [spaces] and newlines don't need to carry meaning, and I'd ignore them.
8. Leftovers and edge cases. ? is still listed as a token but is no longer used, so I'd drop it. For "no consecutive Lefts", I'd check only within a single pattern. For example, (… _) _ would be allowed.

If you answer 1–3, or tell me to use my suggested defaults, I'll write the parser and its test module under tree_tools/rule_parser/.

## And the answers to it:

1. ø,0,"" consume nothing; !head, wordName consume something; _ consume the rest left by !head and other patterns, so it cannot appear before non-consuming recursion; if there's a rule before _, expand the rule first. We don't consider recursion count.

2. Apply your suggestion, but use "symbol" instead of "wordName"

3. I edited StrPat so it contains the String.

4. I amended the rules, now the entry point is File, a File contains non or at least one Rule.

5. I amended the rule so one Pattern Rule is acceptable now.

6. I amended the rules and abstract data definitions.

7. I alter the need to express [spaces], I assume spaces would disappear after tokenizing the input.

8. Alter the syntax and abstract data so ? carries the function like regex's "optional".