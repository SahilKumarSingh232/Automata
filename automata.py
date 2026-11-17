"""Automaton construction and simulation (pure Python, no UI code)."""
from dataclasses import dataclass
from typing import Optional

EPS = "ε"
KINDS = {"DFA": "DFA", "NFA": "NFA", "ENFA": "ε-NFA"}
MODES = {
    "exact": "Exactly this string",
    "starts": "Starts with it",
    "ends": "Ends with it",
    "contains": "Contains it",
    "custom": "Custom rules (AND/OR)",
}
CONDITIONS = {
    "exact": "Is exactly",
    "starts": "Starts with",
    "ends": "Ends with",
    "contains": "Contains",
    "not_starts": "Does not start with",
    "not_ends": "Does not end with",
    "not_contains": "Does not contain",
    "at_least": "At least N occurrences of symbol(s)",
    "at_most": "At most N occurrences of symbol(s)",
    "exactly_count": "Exactly N occurrences of symbol(s)",
    "even_count": "An even number of each symbol",
    "odd_count": "An odd number of each symbol",
    "no_adjacent": "Does not contain adjacent pattern(s)",
    "followed_by": "Every occurrence of one symbol is followed by another",
    "prefix": "Has this exact prefix",
    "suffix_any": "Ends with one of these patterns",
    "divisible": "Binary value is divisible by N",
    "position_end": "Kth symbol from the end is",
}


@dataclass(frozen=True)
class Step:
    states: frozenset
    used: frozenset          # (from, to) pairs taken during this step
    symbol: Optional[str]
    text: str


class Automaton:
    def __init__(self, kind, n, accept, trans, labels, alphabet, start=0):
        self.kind, self.n, self.start = kind, n, start
        self.accept, self.trans = set(accept), list(trans)
        self.labels, self.alphabet = list(labels), list(alphabet)

    # ---- helpers ---------------------------------------------------------
    def _closure(self, states):
        seen, used, stack = set(states), set(), list(states)
        while stack:
            x = stack.pop()
            for a, c, b in self.trans:
                if a == x and c == EPS:
                    used.add((a, b))
                    if b not in seen:
                        seen.add(b)
                        stack.append(b)
        return seen, used

    def _fmt(self, states):
        return "{" + ", ".join(self.labels[i] for i in sorted(states)) + "}"

    # ---- simulation ------------------------------------------------------
    def simulate(self, word):
        """Return (steps, accepted). steps[0] is the start; steps[i] follows symbol i."""
        cur, used = self._closure({self.start})
        note = " (after ε-closure)" if self.kind == "ENFA" else ""
        steps = [Step(frozenset(cur), frozenset(used), None, f"Start in {self._fmt(cur)}{note}")]
        for ch in word:
            if ch not in self.alphabet:
                steps.append(Step(frozenset(), frozenset(), ch,
                                  f"Read '{ch}': not in the alphabet, so no transition exists. Reject."))
                return steps, False
            moved, used = set(), set()
            for a, c, b in self.trans:
                if c == ch and a in cur:
                    moved.add(b)
                    used.add((a, b))
            closed, eps_used = self._closure(moved)
            used |= eps_used
            text = f"Read '{ch}': {self._fmt(cur)} → {self._fmt(moved)}"
            if self.kind == "ENFA":
                text += f" → ε-closure {self._fmt(closed)}"
            dead = not closed or all(self.labels[s] == "dead" for s in closed)
            if dead:
                text += " (dead end)"
            steps.append(Step(frozenset(closed), frozenset(used), ch, text))
            cur = closed
            if not cur:
                return steps, False
        return steps, any(s in self.accept for s in cur)

    # ---- presentation ----------------------------------------------------
    def table(self, active=frozenset()):
        cols = list(self.alphabet) + ([EPS] if self.kind == "ENFA" else [])
        rows = []
        for i in range(self.n):
            row = {"": ("▶ " if i in active else "") + ("→ " if i == self.start else "")
                       + ("* " if i in self.accept else "") + self.labels[i]}
            for c in cols:
                tgt = [self.labels[b] for a, s, b in self.trans if a == i and s == c]
                row[c] = "∅" if not tgt else (tgt[0] if self.kind == "DFA" else "{" + ", ".join(tgt) + "}")
            rows.append(row)
        return rows

    def to_dot(self, active=frozenset(), used=frozenset()):
        q = lambda s: '"' + s.replace('"', '\\"') + '"'
        out = [
            "digraph G {", 'rankdir=LR; bgcolor="transparent"; pad=0.3;',
            'node [style=filled,fontname="Helvetica",fontsize=13,fillcolor="#1a0f38",'
            'color="#a9c9ff",fontcolor="#eaf2ff",penwidth=1.6,width=0.55];',
            'edge [color="#9a8bdc",fontcolor="#9fb0e0",fontname="Helvetica",fontsize=12,arrowsize=0.8];',
            '__s [shape=point,width=0.1,color="#a9c9ff"];',
        ]
        for i, lab in enumerate(self.labels):
            attrs = [f"label={q(lab)}", "shape=" + ("doublecircle" if i in self.accept else "circle")]
            if i in active:
                attrs += ['fillcolor="#7fd9ff"', 'fontcolor="#04101f"', 'color="#f5c451"', "penwidth=3"]
            elif i in self.accept:
                attrs.append('color="#f5c451"')
            out.append(f"n{i} [{','.join(attrs)}];")
        out.append(f"__s -> n{self.start};")
        groups = {}
        for a, c, b in self.trans:
            groups.setdefault((a, b), []).append(c)
        for (a, b), syms in groups.items():
            attrs = [f"label={q(','.join(sorted(syms)))}"]
            if (a, b) in used:
                attrs += ['color="#f5c451"', 'fontcolor="#ffe08a"', "penwidth=3"]
            out.append(f"n{a} -> n{b} [{','.join(attrs)}];")
        out.append("}")
        return "\n".join(out)


# ---- construction -------------------------------------------------------
def _build_nfa(word, alphabet, mode):
    n, trans = len(word), set()
    for i, ch in enumerate(word):
        trans.add((i, ch, i + 1))
    if mode in ("starts", "contains"):
        trans |= {(n, c, n) for c in alphabet}
    if mode in ("ends", "contains"):
        trans |= {(0, c, 0) for c in alphabet}
    return Automaton("NFA", n + 1, {n}, sorted(trans, key=lambda t: (t[0], t[1], t[2])),
                     [f"q{i}" for i in range(n + 1)], alphabet)


def _to_eps(nfa):
    # Each symbol step becomes: a --c--> m --ε--> b. Number each middle state right
    # after its source state so the diagram stays compact and readable.
    items = []
    for i in range(nfa.n):
        items.append(("s", i))
        outs = sorted((t for t in nfa.trans if t[0] == i), key=lambda t: (t[2] != i, t[1], t[2]))
        items += [("m", t) for t in outs]
    idx = {it: k for k, it in enumerate(items)}
    trans = []
    for t in nfa.trans:
        a, c, b = t
        m = idx[("m", t)]
        trans += [(idx[("s", a)], c, m), (m, EPS, idx[("s", b)])]
    return Automaton("ENFA", len(items), {idx[("s", s)] for s in nfa.accept}, trans,
                     [f"q{k}" for k in range(len(items))], nfa.alphabet)


def _to_dfa(nfa):
    key = lambda s: tuple(sorted(s))
    index, sets, trans = {(0,): 0}, [{0}], []
    i = 0
    while i < len(sets):
        for c in nfa.alphabet:
            nxt = {b for a, s, b in nfa.trans if s == c and a in sets[i]}
            if key(nxt) not in index:
                index[key(nxt)] = len(sets)
                sets.append(nxt)
            trans.append((i, c, index[key(nxt)]))
        i += 1
    accept = {k for k, s in enumerate(sets) if s & nfa.accept}
    labels = [f"q{k}" if s else "dead" for k, s in enumerate(sets)]
    return _minimize_dfa(Automaton("DFA", len(sets), accept, trans, labels, nfa.alphabet))


def _minimize_dfa(dfa):
    """Return an equivalent complete DFA with only reachable, distinct states."""
    transitions = {(a, symbol): b for a, symbol, b in dfa.trans}
    reachable, queue = {dfa.start}, [dfa.start]
    for state in queue:
        for symbol in dfa.alphabet:
            target = transitions[(state, symbol)]
            if target not in reachable:
                reachable.add(target)
                queue.append(target)

    partitions = [group for group in (reachable & dfa.accept, reachable - dfa.accept) if group]
    while True:
        block_of = {state: i for i, group in enumerate(partitions) for state in group}
        groups = {}
        for state in reachable:
            signature = (state in dfa.accept,
                         tuple(block_of[transitions[(state, symbol)]] for symbol in dfa.alphabet))
            groups.setdefault(signature, set()).add(state)
        refined = list(groups.values())
        if {frozenset(group) for group in refined} == {frozenset(group) for group in partitions}:
            partitions = refined
            break
        partitions = refined

    block_of = {state: i for i, group in enumerate(partitions) for state in group}
    start_block = block_of[dfa.start]
    order, seen, queue = [], {start_block}, [start_block]
    representatives = [min(group) for group in partitions]
    while queue:
        block = queue.pop(0)
        order.append(block)
        state = representatives[block]
        for symbol in dfa.alphabet:
            target = block_of[transitions[(state, symbol)]]
            if target not in seen:
                seen.add(target)
                queue.append(target)

    new_index = {block: i for i, block in enumerate(order)}
    minimized_trans = []
    minimized_accept = set()
    for block in order:
        source = new_index[block]
        state = representatives[block]
        if state in dfa.accept:
            minimized_accept.add(source)
        for symbol in dfa.alphabet:
            target = block_of[transitions[(state, symbol)]]
            minimized_trans.append((source, symbol, new_index[target]))
    labels = [f"q{i}" for i in range(len(order))]
    return Automaton("DFA", len(order), minimized_accept, minimized_trans, labels,
                     dfa.alphabet, start=0)


def build(word, alphabet, kind, mode):
    if EPS in alphabet:
        raise ValueError("ε is reserved for empty transitions. Use a different symbol.")
    missing = sorted({c for c in word if c not in alphabet})
    if missing:
        raise ValueError("The target string uses symbols outside the alphabet: " + ", ".join(missing))
    if not alphabet:
        raise ValueError("Enter a string or an alphabet to build an automaton.")
    nfa = _build_nfa(word, alphabet, mode)
    return {"DFA": _to_dfa, "ENFA": _to_eps}.get(kind, lambda x: x)(nfa)


def _dfa_for_condition(word, alphabet, condition):
    """Build a complete DFA for one literal-string condition."""
    if condition == "not_starts":
        return _complement(_dfa_for_condition(word, alphabet, "starts"))
    if condition == "not_ends":
        return _complement(_dfa_for_condition(word, alphabet, "ends"))
    if condition == "not_contains":
        return _complement(_dfa_for_condition(word, alphabet, "contains"))

    n, sink = len(word), len(word) + 1
    trans = []

    if condition in ("exact", "starts"):
        for q in range(n + 1):
            for c in alphabet:
                if condition == "starts" and q == n:
                    target = n
                elif q < n and c == word[q]:
                    target = q + 1
                else:
                    target = sink
                trans.append((q, c, target))
        for c in alphabet:
            trans.append((sink, c, sink))
        accept = {n}
        labels = [f"q{i}" for i in range(n + 1)] + ["dead"]
    else:
        # KMP prefix table lets the machine track the longest suffix of the
        # input that is also a prefix of the target, including overlapping hits.
        pi = [0] * n
        for i in range(1, n):
            j = pi[i - 1]
            while j and word[i] != word[j]:
                j = pi[j - 1]
            if word[i] == word[j]:
                j += 1
            pi[i] = j
        for q in range(n + 1):
            for c in alphabet:
                if n == 0:
                    target = 0
                elif condition == "contains" and q == n:
                    target = n
                else:
                    j = pi[n - 1] if q == n else q
                    while j and word[j] != c:
                        j = pi[j - 1]
                    if word[j] == c:
                        j += 1
                    target = j
                trans.append((q, c, target))
        accept = {n} if n else {0}
        labels = [f"q{i}" for i in range(n + 1)]

    if condition == "exact":
        accept = {n}
    elif condition == "starts":
        accept = {n}
    elif condition not in ("ends", "contains"):
        raise ValueError(f"Unsupported language condition: {condition}")

    return Automaton("DFA", len(labels), accept, trans, labels, alphabet)


def _complement(dfa):
    return Automaton("DFA", dfa.n, set(range(dfa.n)) - dfa.accept,
                     dfa.trans, dfa.labels, dfa.alphabet, dfa.start)


def _combine_dfas(dfas, alphabet, logic="AND"):
    """Return the DFA accepting strings accepted by all or any input DFAs."""
    if not dfas:
        return Automaton("DFA", 1, {0}, [(0, c, 0) for c in alphabet],
                         ["q0"], alphabet)
    start = tuple(d.start for d in dfas)
    states, index, trans = [start], {start: 0}, []
    for state in states:
        src = index[state]
        for c in alphabet:
            nxt = tuple(next(b for a, sym, b in d.trans if a == q and sym == c)
                        for d, q in zip(dfas, state))
            if nxt not in index:
                index[nxt] = len(states)
                states.append(nxt)
            trans.append((src, c, index[nxt]))
    accepts = [[q in d.accept for d, q in zip(dfas, state)]
               for state in states]
    accept = {i for i, values in enumerate(accepts)
              if (all(values) if logic == "AND" else any(values))}
    labels = [f"q{i}" for i in range(len(states))]
    return Automaton("DFA", len(states), accept, trans, labels, alphabet)


def _symbol_list(raw):
    if isinstance(raw, (list, tuple, set)):
        return [str(x) for x in raw if str(x)]
    return [x.strip() for x in str(raw).split(",") if x.strip()]


def _count_machine(alphabet, symbol, count, rule):
    if len(symbol) != 1:
        raise ValueError("Count conditions need a single-character symbol.")
    if symbol not in alphabet:
        raise ValueError(f"The symbol '{symbol}' is outside the alphabet.")
    if count < 0:
        raise ValueError("The count cannot be negative.")
    if count > 500:
        raise ValueError("Use a count limit of 500 or less to keep the automaton manageable.")
    cap = count + 1 if rule in ("at_most", "exactly_count") else count
    n = cap + 1 if rule in ("at_most", "exactly_count") else cap + 1
    trans = []
    for q in range(n):
        for c in alphabet:
            target = min(q + 1, cap) if c == symbol else q
            trans.append((q, c, target))
    if rule == "at_least":
        accept = {cap}
    elif rule == "at_most":
        accept = set(range(count + 1))
    else:
        accept = {count}
    return Automaton("DFA", n, accept, trans, [f"q{i}" for i in range(n)], alphabet)


def _parity_machine(alphabet, symbol, parity):
    if len(symbol) != 1 or symbol not in alphabet:
        raise ValueError("Each parity condition needs one symbol from the alphabet.")
    trans = [(q, c, q ^ int(c == symbol)) for q in range(2) for c in alphabet]
    accept = {0 if parity == "even" else 1}
    return Automaton("DFA", 2, accept, trans, ["even", "odd"], alphabet)


def _followed_by_machine(alphabet, before, after):
    if len(before) != 1 or len(after) != 1 or before not in alphabet or after not in alphabet:
        raise ValueError("Enter two single-character symbols from the alphabet.")
    # 0 = no pending requirement, 1 = previous symbol requires `after`, 2 = dead.
    trans = []
    for q in range(3):
        for c in alphabet:
            if q == 2 or (q == 1 and c != after):
                target = 2
            elif c == before:
                target = 1
            else:
                target = 0
            trans.append((q, c, target))
    return Automaton("DFA", 3, {0}, trans, ["q0", "need-next", "dead"], alphabet)


def _suffix_union_machine(alphabet, patterns):
    if not patterns:
        raise ValueError("Enter at least one suffix pattern.")
    return _combine_dfas([_dfa_for_condition(p, alphabet, "ends") for p in patterns],
                         alphabet, "OR")


def _position_machine(alphabet, symbol, position):
    if len(symbol) != 1 or symbol not in alphabet:
        raise ValueError("Enter one symbol from the alphabet.")
    if position < 1 or position > 8:
        raise ValueError("The position from the end must be between 1 and 8.")
    states = [()]
    index = {(): 0}
    trans = []
    for state in states:
        src = index[state]
        for c in alphabet:
            nxt = (state + (c,))[-position:]
            if nxt not in index:
                if len(states) >= 5000:
                    raise ValueError("This position and alphabet create too many states. Use a smaller position.")
                index[nxt] = len(states)
                states.append(nxt)
            trans.append((src, c, index[nxt]))
    accept = {i for i, state in enumerate(states)
              if len(state) == position and state[0] == symbol}
    return Automaton("DFA", len(states), accept, trans,
                     [f"q{i}" for i in range(len(states))], alphabet)


def _empty_string_machine(alphabet, accept_empty):
    trans = [(0, c, 1) for c in alphabet] + [(1, c, 1) for c in alphabet]
    accept = {0} if accept_empty else {1}
    return Automaton("DFA", 2, accept, trans, ["start", "nonempty"], alphabet)


def build_custom(alphabet, kind, conditions, logic="AND", empty_string="Either"):
    """Build an automaton from selected string and finite-state conditions."""
    if EPS in alphabet:
        raise ValueError("ε is reserved for empty transitions. Use a different symbol.")
    if not alphabet:
        raise ValueError("Enter an alphabet for the language conditions.")
    if not conditions:
        raise ValueError("Choose at least one language condition.")
    if logic not in ("AND", "OR"):
        raise ValueError("Combine conditions using AND or OR.")

    dfas = []
    for condition, value in conditions.items():
        if condition not in CONDITIONS:
            raise ValueError(f"Unsupported language condition: {condition}")
        if condition in ("exact", "starts", "ends", "contains", "not_starts", "not_ends", "not_contains"):
            word = str(value)
            missing = sorted(set(word) - set(alphabet))
            if missing:
                raise ValueError(f"The string for '{CONDITIONS[condition]}' uses symbols outside the alphabet: "
                                 + ", ".join(missing))
            dfas.append(_dfa_for_condition(word, alphabet, condition))
        elif condition in ("at_least", "at_most", "exactly_count"):
            symbols = _symbol_list(value.get("symbols", ""))
            if not symbols:
                raise ValueError("Enter at least one symbol for the count condition.")
            for symbol in symbols:
                dfas.append(_count_machine(alphabet, symbol, int(value["count"]), condition))
            dfas[-len(symbols):] = [_combine_dfas(dfas[-len(symbols):], alphabet, "AND")]
        elif condition in ("even_count", "odd_count"):
            symbols = _symbol_list(value.get("symbols", ""))
            if not symbols:
                raise ValueError("Enter at least one symbol for the parity condition.")
            parity = "even" if condition == "even_count" else "odd"
            rule_dfas = [_parity_machine(alphabet, symbol, parity) for symbol in symbols]
            dfas.append(_combine_dfas(rule_dfas, alphabet, "AND"))
        elif condition == "no_adjacent":
            patterns = [p for p in str(value.get("patterns", "")).split("|") if p]
            if not patterns:
                raise ValueError("Enter at least one forbidden pattern.")
            rule_dfas = []
            for pattern in patterns:
                missing = sorted(set(pattern) - set(alphabet))
                if missing:
                    raise ValueError("A forbidden pattern uses symbols outside the alphabet: " + ", ".join(missing))
                rule_dfas.append(_complement(_dfa_for_condition(pattern, alphabet, "contains")))
            dfas.append(_combine_dfas(rule_dfas, alphabet, "AND"))
        elif condition == "followed_by":
            dfas.append(_followed_by_machine(alphabet, str(value.get("before", "")),
                                              str(value.get("after", ""))))
        elif condition == "prefix":
            pattern = str(value.get("pattern", ""))
            missing = sorted(set(pattern) - set(alphabet))
            if missing:
                raise ValueError("The prefix uses symbols outside the alphabet: " + ", ".join(missing))
            dfas.append(_dfa_for_condition(pattern, alphabet, "starts"))
        elif condition == "suffix_any":
            patterns = str(value.get("patterns", "")).split("|")
            for pattern in patterns:
                missing = sorted(set(pattern) - set(alphabet))
                if missing:
                    raise ValueError("A suffix uses symbols outside the alphabet: " + ", ".join(missing))
            dfas.append(_suffix_union_machine(alphabet, patterns))
        elif condition == "divisible":
            divisor = int(value["divisor"])
            if divisor < 1:
                raise ValueError("The divisor must be at least 1.")
            if divisor > 500:
                raise ValueError("Use a divisor of 500 or less to keep the automaton manageable.")
            if "0" not in alphabet or "1" not in alphabet or any(c not in "01" for c in alphabet):
                raise ValueError("Binary divisibility needs an alphabet containing only 0 and 1.")
            trans = [(r, bit, (r * 2 + int(bit)) % divisor)
                     for r in range(divisor) for bit in alphabet]
            dfas.append(Automaton("DFA", divisor, {0}, trans,
                                  [f"remainder {r}" for r in range(divisor)], alphabet))
        elif condition == "position_end":
            dfas.append(_position_machine(alphabet, str(value.get("symbol", "")),
                                          int(value["position"])))

    dfa = _combine_dfas(dfas, alphabet, logic)
    if empty_string == "Accept":
        dfa = _combine_dfas([dfa, _empty_string_machine(alphabet, True)], alphabet, "OR")
    elif empty_string == "Reject":
        dfa = _combine_dfas([dfa, _empty_string_machine(alphabet, False)], alphabet, "AND")
    dfa = _minimize_dfa(dfa)
    if kind == "DFA":
        return dfa
    # A DFA is also a valid NFA/ε-NFA. Keep the minimized state graph for all
    # selected types instead of expanding every edge into extra ε-states.
    return Automaton(kind, dfa.n, dfa.accept, dfa.trans, dfa.labels, alphabet, dfa.start)


def suggestions(word, alphabet):
    a = alphabet[0] if alphabet else ""
    items = [word, word[:-1], word[1:], word[::-1], word + a, a + word, ""]
    return list(dict.fromkeys(items))[:7]
