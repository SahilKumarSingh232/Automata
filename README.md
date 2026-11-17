# Automata

Automaton Workshop builds and simulates finite automata. The original exact,
starts-with, ends-with, and contains modes are available. Choose **Custom rules
(AND/OR)** to combine rules. Available rules
include exact/prefix/suffix/contains patterns and their negations, count limits,
even/odd counts, forbidden adjacent patterns, required followers, binary
divisibility, and a symbol at a position from the end. You can also set whether
the empty string is accepted.

For example, select **Starts with** and enter `a`, then select **Ends with** and
enter `b` to recognize strings that start with `a` and end with `b`. Set the
combiner to OR for alternatives such as “contains `ab` or ends in `ba`.” For
“an even number of 0s and 1s,” select **An even number of each symbol** and enter
`0,1`. For suffix alternatives or forbidden patterns, separate patterns with
`|`, such as `00|11`.

The alphabet is inferred from the symbols in the rules unless you enter one
explicitly. Test strings containing other symbols are rejected. Count and
divisor limits are capped at 500, and positions from the end at 8 to keep the
generated machines manageable.

Generated deterministic machines are minimized before drawing, so equivalent
states are merged and the diagram stays as small as possible. NFA and ε-NFA
selections also keep this compact graph rather than adding extra ε-only states.
