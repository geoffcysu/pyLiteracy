# The spec of the rule grammar (used in python projects)

using the package lark

## Goal
1. Program a parser, which includes the lexer, syntax tree, abstract data tree modules, according to the descriptions below. The syntax rules are only listed those special ones, you should finalize the whole syntax rules.
2. some rules in the grammar: (the capitalized term is defined below)
    - A Pattern can contain at most one Head.
    - No consecutive Lefts ('_')
    - _ consume the rest left by !head and other patterns, so it cannot appear before non-consuming recursion; if there's a rule before _, expand the rule first.
    - circular check: a rule shouldn't be recursed without consuming 
3. Generate a test module


### tokens (separated with ",", explanation in parentheses):
->, |, !, ?, RuleName(python class name), symbol(python variable name), "(used to express string), ø, 0, (, ), _

### specific syntax rule (left is the syntax data type, right is the tokens it consumes)

LinguisticRules -> Rules?
Rules -> Rule (\n Rules)?
Lefts -> '_'
Head -> '!' symbol
Empty -> 'ø' | '0'
Rule -> RuleName '->' Pattern Patterns?
Patterns -> '|' Pattern Patterns?

### abstract data type (written in haskell here, but should be implemented with python dataclass)

data LinguisticRules = LinguisticRules {rules :: List Rule}
data Rule = Rule {name :: String, patterns :: List Pattern}  -- name is "" for the Rule inside an AnonRule
data AnonRule = AnonRule Rule                                -- ( Pattern | Pattern ... )
data Pattern = Pattern (List Element)
type Element = Lefts|Head|Rule|Empty|StrPat|Symbol|AnonRule|Opt
data Lefts = Lefts                                           -- _
data Head = Head {pattern :: String}                         -- !symbol
data Empty = Empty                                           -- ø or 0
data StrPat = StrPat String                                  -- "..."
data Symbol = Symbol {name :: String}                        -- a bare symbol, e.g. neg_pat
data Opt = Opt Element                                       -- Element?

A Rule inside a Pattern (e.g. TP in `CP -> _ !c_pat TP`) is the same Rule object
as the definition of TP, so rules can refer to each other in cycles.


### an example:
```
CP -> _ !c_pat TP
    | ø ø TP
TP -> ø ModP
ModP -> _ !mod_pat NegP
    | "" "" NegP
NegP -> _ neg_pat LightVP
    | "" "" LightVP
LightVP -> _ lightV_pat (VP | DegP | pred_on_neg)
    | ø ø (VP | DegP | pred_on_neg)
VP -> _ v_pat (CP | ClsP)
DegP -> _ deg_pat ClsP
ClsP -> _ cls_pat NP
    | ø ø NP
NP -> (_ rc_pat) _
    | _ n_pat _
    | ø ø _

```