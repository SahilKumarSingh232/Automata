
"""Automaton Workshop: build an automaton for a string and watch it run (Streamlit)."""

import time

import streamlit as st
import streamlit.components.v1 as components

from automata import CONDITIONS, KINDS, MODES, build, build_custom, suggestions
from diagram import HEIGHT, diagram_html
from fireworks import fireworks_html

st.set_page_config(
    page_title="Automaton Workshop",
    page_icon="🌑",
    layout="wide"
)

st.markdown(
    """
<style>
.stApp {
    background:
        radial-gradient(ellipse 80% 45% at 50% -10%,#3a1478 0%,transparent 70%),
        radial-gradient(ellipse 60% 40% at 100% 100%,#0c2f6b 0%,transparent 70%),
        #07040f;
}

.stApp::before {
    content:"";
    position:fixed;
    top:0;
    left:0;
    right:0;
    height:3px;
    z-index:999;
    background:linear-gradient(
        90deg,#8b5cf6,#6fd3ff,#f5c451,#6fd3ff,#8b5cf6
    );
    background-size:300% 100%;
    animation:flow 7s linear infinite;
}

.hero {
    font:700 2.8rem/1.1 Georgia,serif;
    margin:0;
    background:linear-gradient(
        100deg,#8b5cf6,#c9f0ff,#f5c451,#c9f0ff,#8b5cf6
    );
    background-size:300% 100%;
    -webkit-background-clip:text;
    background-clip:text;
    color:transparent;
    animation:rise .7s both,flow 9s linear infinite;
}

.tape {
    display:flex;
    flex-wrap:wrap;
    gap:6px;
    margin:14px 0 6px;
}

.tape span {
    min-width:40px;
    text-align:center;
    padding:6px 8px;
    border:1px solid rgba(255,255,255,.25);
    border-radius:8px;
    font:700 20px monospace;
    transition:all .3s;
}

.tape .done {
    background:rgba(110,231,168,.16);
    border-color:#6ee7a8;
    color:#6ee7a8;
}

.tape .cur {
    background:#6fd3ff;
    border-color:#6fd3ff;
    color:#04101f;
    transform:translateY(-5px);
    animation:tick .4s;
}

.verdict {
    display:inline-block;
    padding:8px 20px;
    border-radius:12px;
    font-size:1.3rem;
    font-weight:700;
    animation:pop .5s;
}

.verdict.ok {
    background:linear-gradient(
        100deg,#6ee7a8,#e6fff0,#f5c451,#6ee7a8
    );
    background-size:300% 100%;
    color:#06301a;
    animation:pop .5s,flow 3s linear infinite;
}

.verdict.bad {
    background:#ff8fa3;
    color:#3a0a16;
}

.stButton>button {
    border-radius:10px;
    transition:transform .15s,box-shadow .2s,border-color .2s;
}

.stButton>button:hover {
    transform:translateY(-3px);
    box-shadow:0 8px 18px rgba(111,211,255,.35);
    border-color:#f5c451;
}

.stButton>button:active {
    transform:translateY(1px) scale(.96);
}

[data-testid="stProgress"] div[role="progressbar"]>div {
    background:linear-gradient(
        90deg,#8b5cf6,#6fd3ff,#f5c451
    )!important;
}

@keyframes flow {
    to {
        background-position:300% 0;
    }
}

@keyframes rise {
    from {
        opacity:0;
        transform:translateY(16px);
    }
}

@keyframes tick {
    0% {
        transform:translateY(4px) scale(.8);
    }
    60% {
        transform:translateY(-9px) scale(1.1);
    }
}

@keyframes pop {
    0% {
        transform:scale(.6);
        opacity:0;
    }
    70% {
        transform:scale(1.1);
    }
    100% {
        transform:scale(1);
        opacity:1;
    }
}

@media (prefers-reduced-motion:reduce) {
    * {
        animation:none!important;
        transition:none!important;
    }
}
</style>
""",
    unsafe_allow_html=True
)

st.markdown(
    '<h1 class="hero">Automaton Workshop</h1>',
    unsafe_allow_html=True
)

st.caption(
    "Describe a string or language. Summon a machine. "
    "Then watch it think, one symbol at a time."
)


# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------

with st.sidebar:

    st.header("Build the machine")

    mode = st.selectbox(
        "Language accepted",
        list(MODES),
        format_func=MODES.get
    )

    condition_inputs = {}
    if mode == "custom":
        selected_conditions = st.multiselect(
            "Conditions to combine",
            list(CONDITIONS),
            format_func=CONDITIONS.get,
            help="Choose conditions such as Starts with 'a' and Ends with 'b', then combine with AND or OR."
        )
        condition_logic = st.selectbox("How to combine the selected conditions", ["AND", "OR"])
        empty_string = st.selectbox("Empty string (ε)", ["Either", "Accept", "Reject"])
        for condition in selected_conditions:
            if condition in ("exact", "starts", "ends", "contains", "not_starts", "not_ends", "not_contains", "prefix"):
                field = "pattern" if condition == "prefix" else "string"
                condition_inputs[condition] = {
                    "pattern": st.text_input(
                        f"String: {CONDITIONS[condition]}", key=f"condition_{condition}"
                    )
                } if field == "pattern" else st.text_input(
                    f"String: {CONDITIONS[condition]}", key=f"condition_{condition}"
                )
            elif condition in ("at_least", "at_most", "exactly_count"):
                condition_inputs[condition] = {
                    "symbols": st.text_input(
                        "Symbol(s), comma separated", key=f"condition_{condition}_symbols",
                        help="For example: a,b applies the same count rule to both symbols."
                    ),
                    "count": st.number_input("N", min_value=0, max_value=500, step=1, key=f"condition_{condition}_count")
                }
            elif condition in ("even_count", "odd_count"):
                condition_inputs[condition] = {
                    "symbols": st.text_input(
                        "Symbol(s), comma separated", key=f"condition_{condition}_symbols"
                    )
                }
            elif condition in ("no_adjacent", "suffix_any"):
                condition_inputs[condition] = {
                    "patterns": st.text_input(
                        "Patterns separated by |", key=f"condition_{condition}_patterns",
                        help="Example: 00|11"
                    )
                }
            elif condition == "followed_by":
                before, after = st.columns(2)
                condition_inputs[condition] = {
                    "before": before.text_input("Symbol that needs a follower", key="condition_followed_before", max_chars=1),
                    "after": after.text_input("Required next symbol", key="condition_followed_after", max_chars=1)
                }
            elif condition == "divisible":
                condition_inputs[condition] = {
                    "divisor": st.number_input("Divisor", min_value=1, max_value=500, value=3, step=1, key="condition_divisor")
                }
            elif condition == "position_end":
                symbol, position = st.columns(2)
                condition_inputs[condition] = {
                    "symbol": symbol.text_input("Required symbol", key="condition_position_symbol", max_chars=1),
                    "position": position.number_input("Position from end (1 = last)", min_value=1, max_value=8, value=2, step=1, key="condition_position")
                }
        word = ""
    else:
        word = st.text_input(
            "Target string",
            value="abba"
        ).strip()
        condition_logic, empty_string = "AND", "Either"

    alpha_raw = st.text_input(
        "Alphabet (optional)",
        placeholder="auto from strings, e.g. a,b"
    )

    kind = st.selectbox(
        "Automaton type",
        list(KINDS),
        format_func=KINDS.get
    )

    streak_box = st.empty()


raw = "".join(
    ch for ch in alpha_raw
    if not ch.isspace() and ch != ","
)

language_symbols = word
for value in condition_inputs.values():
    if isinstance(value, dict):
        language_symbols += "".join(
            str(item).replace(",", "").replace("|", "")
            for key, item in value.items()
            if key in ("symbols", "patterns", "pattern", "before", "after", "symbol")
        )
    else:
        language_symbols += str(value).replace(",", "").replace("|", "")
alphabet = sorted(set(raw or language_symbols))


try:
    if mode == "custom" and not condition_inputs:
        st.info("Choose at least one condition to build a custom language.")
        st.stop()
    auto = (build_custom(alphabet, kind, condition_inputs, condition_logic, empty_string) if mode == "custom"
            else build(word, alphabet, kind, mode))

except ValueError as err:
    st.error(str(err))
    st.stop()


# ---------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------

S = st.session_state

for k, v in {
    "step": 0,
    "streak": 0,
    "best": 0,
    "fired": False,
    "playing": False
}.items():
    S.setdefault(k, v)


sig = (word, tuple(alphabet), kind, mode, repr(sorted(condition_inputs.items())), condition_logic, empty_string)

if S.get("sig") != sig:

    S.update(
        sig=sig,
        test=word,
        last_test=word,
        step=0,
        shown=-1,
        intro=True,
        guess="No guess",
        fired=False,
        playing=False
    )
if mode == "custom":
    rules = []
    for condition, value in condition_inputs.items():
        if isinstance(value, dict):
            if condition in ("at_least", "at_most", "exactly_count"):
                detail = f"{CONDITIONS[condition].replace('N', str(value['count']))} {value['symbols']}"
            elif condition in ("even_count", "odd_count"):
                detail = f"{CONDITIONS[condition]}: {value['symbols']}"
            elif condition == "followed_by":
                detail = f"Every {value['before']} is followed by {value['after']}"
            elif condition == "divisible":
                detail = f"Binary value divisible by {value['divisor']}"
            elif condition == "position_end":
                detail = f"{value['position']} from end is {value['symbol']}"
            else:
                detail = f"{CONDITIONS[condition]} {value.get('patterns', value.get('pattern', ''))}"
        else:
            detail = f"{CONDITIONS[condition]} “{value}”"
        rules.append(detail)
    connector = " and " if condition_logic == "AND" else " or "
    accepted_description = (
        f"all selected conditions: {connector.join(rules)}"
        if condition_logic == "AND"
        else f"any selected condition: {connector.join(rules)}"
    )
    if empty_string != "Either":
        accepted_description += f"; empty string: {empty_string.lower()}"
else:
    accepted_description = f"{MODES[mode].lower()} “{word}”"

st.success(
    f"{KINDS[kind]} with {auto.n} states over "
    f"{{{', '.join(alphabet)}}}; language: {accepted_description}. "
    "Double circle = accepting."
)


# ---------------------------------------------------------
# TEST CONTROLS
# ---------------------------------------------------------

test = st.text_input(
    "Test string",
    key="test"
)

if test != S.last_test:

    S.update(
        last_test=test,
        step=0,
        guess="No guess",
        fired=False,
        playing=False
    )


steps, accepted = auto.simulate(test)

last = len(steps) - 1

S.step = min(S.step, last)

if S.step < last:
    S.fired = False


def pick(x):
    S.test = x


suggestion_word = word
if not suggestion_word and condition_inputs:
    first_value = next(iter(condition_inputs.values()))
    suggestion_word = (next((str(v) for k, v in first_value.items()
                             if k in ("pattern", "patterns", "symbols") and v), "")
                       if isinstance(first_value, dict) else first_value)
chips = suggestions(suggestion_word, alphabet)

cols = st.columns([1] + [2] * len(chips))

cols[0].markdown("Try one:")

for col, c in zip(cols[1:], chips):

    col.button(
        c or "ε (empty)",
        key=f"chip_{c}",
        on_click=pick,
        args=(c,),
        use_container_width=True
    )


st.radio(
    "Your call before running it",
    ["No guess", "Accept", "Reject"],
    key="guess",
    horizontal=True,
    disabled=S.step > 0
)


# ---------------------------------------------------------
# NAVIGATION FUNCTIONS
# ---------------------------------------------------------

def jump(to):

    S.playing = False
    S.step = max(0, min(last, to))


def move(delta):

    jump(S.step + delta)


def toggle_play():

    if S.playing:

        S.playing = False

    else:

        if S.step >= last:
            S.step = 0

        S.playing = True


# ---------------------------------------------------------
# BUTTONS
# ---------------------------------------------------------

b1, b2, b3, b4, b5 = st.columns(5)

b1.button(
    "◀ Back",
    on_click=move,
    args=(-1,),
    use_container_width=True
)

b2.button(
    "Next ▶",
    on_click=move,
    args=(1,),
    type="primary",
    use_container_width=True
)

b3.button(
    "Pause" if S.playing else "Auto-play",
    on_click=toggle_play,
    use_container_width=True
)

b4.button(
    "Run to end",
    on_click=jump,
    args=(last,),
    use_container_width=True
)

b5.button(
    "Reset",
    on_click=jump,
    args=(0,),
    use_container_width=True
)


stage = st.empty()


# ---------------------------------------------------------
# RENDERING
# ---------------------------------------------------------

def render(idx):

    s = steps[idx]

    animate = (
        idx > 0 and S.get("shown") == idx - 1
    )

    prev = (
        steps[idx - 1].states
        if idx > 0
        else frozenset()
    )

    # Keep the fireworks outside the stage container so the fixed-position
    # overlay covers the full Streamlit page.
    launch_fireworks = False

    with stage.container():

        cells = "".join(
            f'<span class="{"done" if i < idx else "cur" if i == idx else ""}">{c}</span>'
            for i, c in enumerate(test)
        ) or '<span class="cur">ε (empty string)</span>'

        st.markdown(
            f'<div class="tape">{cells}</div>',
            unsafe_allow_html=True
        )

        st.progress(
            idx / last if last else 1.0
        )

        components.html(
            diagram_html(
                auto,
                s.states,
                s.used,
                prev,
                s.symbol,
                animate,
                S.pop("intro", False)
            ),
            height=HEIGHT
        )

        S.shown = idx

        # -------------------------------------------------
        # FINAL RESULT
        # -------------------------------------------------

        if idx == last:

            g = S.guess

            right = (
                None
                if g == "No guess"
                else (g == "Accept") == accepted
            )

            if not S.fired:

                # Mark this run as completed so the fireworks do not
                # restart on every Streamlit rerun.
                S.fired = True

                if right is not None:

                    S.streak = (
                        S.streak + 1
                        if right
                        else 0
                    )

                    S.best = max(
                        S.best,
                        S.streak
                    )

                # Launch fireworks only when the input is accepted.
                if accepted:
                    launch_fireworks = True

            consumed = (
                not any(
                    "not in the alphabet" in x.text
                    for x in steps
                )
                and idx == len(test)
            )

            why = (
                "Input consumed and an accepting state is active."
                if accepted
                else
                "The run ended before the whole input was consumed."
                if not consumed
                else
                "Input consumed, but no active state is accepting."
            )

            st.markdown(
                f'<span class="verdict {"ok" if accepted else "bad"}">'
                f'{"Accepted" if accepted else "Rejected"}'
                '</span>',
                unsafe_allow_html=True
            )

            st.caption(why)

            if right is not None:

                (st.success if right else st.error)(
                    f"{'You called it.' if right else 'Not this time, check the log to see why.'} "
                    f"Streak {S.streak}, best {S.best}."
                )

        # -------------------------------------------------
        # STEP LOG
        # -------------------------------------------------

        st.markdown(
            "\\n".join(
                f"{'**' if i == idx else ''}{i}. {x.text}{'**' if i == idx else ''}"
                for i, x in enumerate(steps[:idx + 1])
            )
        )

        # -------------------------------------------------
        # TRANSITION TABLE
        # -------------------------------------------------

        with st.expander(
            "Transition table",
            expanded=True
        ):

            st.table(
                auto.table(s.states)
            )

    # Render the animation at page level, not inside the stage container.
    if launch_fireworks:
        st.html(fireworks_html())


# ---------------------------------------------------------
# DISPLAY
# ---------------------------------------------------------

render(S.step)


streak_box.metric(
    "Streak",
    f"{S.streak} 🔥",
    f"best {S.best}",
    delta_color="off"
)


# ---------------------------------------------------------
# AUTO-PLAY
# ---------------------------------------------------------

if S.playing:

    if S.step < last:

        time.sleep(1.5)

        S.step += 1

        st.rerun()

    else:

        S.playing = False
