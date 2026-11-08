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
    return Automaton("DFA", len(sets), accept, trans, labels, nfa.alphabet)


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


def suggestions(word, alphabet):
    a = alphabet[0] if alphabet else ""
    items = [word, word[:-1], word[1:], word[::-1], word + a, a + word, ""]
    return list(dict.fromkeys(items))[:7]
