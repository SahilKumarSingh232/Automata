
def fireworks_html():

    bursts = [
        (22, 37, "#ff416c", 1.25, 1.00),
        (48, 28, "#ffd166", 1.65, 1.25),
        (76, 39, "#00e5ff", 2.00, 1.10),
        (35, 55, "#bd65ff", 2.35, 0.85),
        (68, 53, "#ff9f43", 2.70, 1.15),
    ]

    rockets = [
        (20, 2, -55, "#ff416c", 0.0),
        (48, 0, -65, "#ffd166", 0.35),
        (78, -4, -55, "#00e5ff", 0.65),
        (35, 3, -48, "#bd65ff", 1.0),
        (68, -3, -48, "#ff9f43", 1.3),
    ]

    rocket_html = ""

    for start, dx, up, color, delay in rockets:
        rocket_html += f"""
        <div class="rocket"
             style="
                --start:{start}%;
                --dx:{dx}vw;
                --up:{up}vh;
                --color:{color};
                --delay:{delay}s;
             ">
        </div>
        """

    burst_html = ""

    for x, y, color, delay, size in bursts:

        particles = ""

        # Main outer ring: long colourful streaks.
        for i in range(48):
            angle = i * 360 / 48
            distance = (105 + (i % 5) * 15) * size
            duration = 1.35 + (i % 4) * 0.18

            particle_color = (
                color if i % 4 != 0 else "#ffffff"
            )

            particles += f"""
            <span class="main-spark"
                  style="
                    --angle:{angle}deg;
                    --distance:{distance}px;
                    --spark-color:{particle_color};
                    --duration:{duration}s;
                  ">
            </span>
            """

        # Inner ring: shorter, brighter sparks.
        for i in range(24):
            angle = i * 360 / 24 + 7
            distance = (45 + (i % 4) * 12) * size

            particles += f"""
            <span class="inner-spark"
                  style="
                    --angle:{angle}deg;
                    --distance:{distance}px;
                    --spark-color:{'#ffffff' if i % 3 == 0 else color};
                  ">
            </span>
            """

        # Tiny twinkling points around the explosion.
        for i in range(18):
            angle = i * 360 / 18 + 12
            distance = (75 + (i % 3) * 20) * size

            particles += f"""
            <span class="twinkle"
                  style="
                    --angle:{angle}deg;
                    --distance:{distance}px;
                    --spark-color:{color};
                  ">
            </span>
            """

        burst_html += f"""
        <div class="burst"
             style="
                --x:{x}%;
                --y:{y}%;
                --color:{color};
                --delay:{delay}s;
             ">

            <div class="flash"></div>
            <div class="glow"></div>
            <div class="core"></div>

            {particles}

        </div>
        """

    return f"""
    <style>

    .fireworks-overlay {{
        position: fixed;
        inset: 0;
        width: 100vw;
        height: 100vh;
        overflow: hidden;
        pointer-events: none;
        z-index: 999999;
    }}

    /* ROCKET LAUNCH */

    .rocket {{
        position: absolute;
        bottom: -5%;
        left: var(--start);
        width: 4px;
        height: 16px;
        border-radius: 50%;
        background: white;

        box-shadow:
            0 0 8px 3px var(--color),
            0 0 20px var(--color);

        opacity: 0;

        animation: rocket-flight 1.35s
            cubic-bezier(.2,.7,.3,1) forwards;

        animation-delay: var(--delay);
    }}

    .rocket::after {{
        content: "";
        position: absolute;
        top: 12px;
        left: 1px;
        width: 3px;
        height: 75px;

        background: linear-gradient(
            to bottom,
            var(--color),
            rgba(255,255,255,.5),
            transparent
        );

        filter: blur(2px);
    }}

    @keyframes rocket-flight {{
        0% {{
            opacity: 0;
            transform: translate(0,0) scale(.5);
        }}

        15% {{ opacity: 1; }}
        85% {{ opacity: 1; }}

        100% {{
            opacity: 0;
            transform: translate(var(--dx),var(--up)) scale(1.2);
        }}
    }}

    /* BURST POSITION */

    .burst {{
        position: absolute;
        left: var(--x);
        top: var(--y);
        width: 1px;
        height: 1px;
        opacity: 0;

        animation: burst-show .05s forwards;
        animation-delay: var(--delay);
    }}

    @keyframes burst-show {{
        to {{ opacity: 1; }}
    }}

    /* LARGE OUTER SPARKS */

    .main-spark {{
        position: absolute;
        left: 0;
        top: 0;

        width: 3px;
        height: 13px;

        border-radius: 50%;

        background: linear-gradient(
            to bottom,
            #ffffff,
            var(--spark-color) 35%,
            transparent
        );

        box-shadow:
            0 0 5px 1px var(--spark-color),
            0 0 12px var(--spark-color);

        opacity: 0;

        animation: main-explode var(--duration)
            cubic-bezier(.15,.65,.3,1) forwards;

        animation-delay: var(--delay);
    }}

    @keyframes main-explode {{
        0% {{
            opacity: 0;
            transform:
                rotate(var(--angle))
                translateY(0)
                scaleY(.2);
        }}

        12% {{ opacity: 1; }}
        55% {{ opacity: .95; }}

        100% {{
            opacity: 0;
            transform:
                rotate(var(--angle))
                translateY(calc(-1 * var(--distance)))
                scaleY(.5);
        }}
    }}

    /* INNER SPARKS */

    .inner-spark {{
        position: absolute;
        left: 0;
        top: 0;

        width: 3px;
        height: 8px;
        border-radius: 50%;

        background: var(--spark-color);

        box-shadow:
            0 0 7px 2px var(--spark-color);

        opacity: 0;

        animation: inner-explode 1.2s ease-out forwards;
        animation-delay: var(--delay);
    }}

    @keyframes inner-explode {{
        0% {{
            opacity: 1;
            transform:
                rotate(var(--angle))
                translateY(0)
                scale(1);
        }}

        100% {{
            opacity: 0;
            transform:
                rotate(var(--angle))
                translateY(calc(-1 * var(--distance)))
                scale(.15);
        }}
    }}

    /* TINY TWINKLING SPARKS */

    .twinkle {{
        position: absolute;
        left: 0;
        top: 0;

        width: 4px;
        height: 4px;
        border-radius: 50%;

        background: white;

        box-shadow:
            0 0 7px 2px var(--spark-color),
            0 0 15px var(--spark-color);

        opacity: 0;

        animation: twinkle-out 1.5s ease-out forwards;
        animation-delay: var(--delay);
    }}

    @keyframes twinkle-out {{
        0% {{
            opacity: 0;
            transform:
                rotate(var(--angle))
                translateY(0)
                scale(.2);
        }}

        25% {{
            opacity: 1;
            transform:
                rotate(var(--angle))
                translateY(calc(-1 * var(--distance) * .5))
                scale(1.2);
        }}

        100% {{
            opacity: 0;
            transform:
                rotate(var(--angle))
                translateY(calc(-1 * var(--distance)))
                scale(.1);
        }}
    }}

    /* CENTRAL WHITE FLASH */

    .flash {{
        position: absolute;
        left: -9px;
        top: -9px;

        width: 18px;
        height: 18px;
        border-radius: 50%;

        background: white;

        box-shadow:
            0 0 20px 10px var(--color),
            0 0 45px 20px var(--color);

        opacity: 0;

        animation: flash-effect .65s ease-out forwards;
        animation-delay: var(--delay);
    }}

    @keyframes flash-effect {{
        0% {{
            opacity: 1;
            transform: scale(.2);
        }}

        35% {{
            opacity: 1;
            transform: scale(2.2);
        }}

        100% {{
            opacity: 0;
            transform: scale(.1);
        }}
    }}

    /* SOFT COLOURED GLOW */

    .glow {{
        position: absolute;
        left: -25px;
        top: -25px;

        width: 50px;
        height: 50px;
        border-radius: 50%;

        background: radial-gradient(
            circle,
            rgba(255,255,255,.8) 0%,
            var(--color) 15%,
            transparent 70%
        );

        filter: blur(7px);
        opacity: 0;

        animation: glow-fade 1.1s ease-out forwards;
        animation-delay: var(--delay);
    }}

    @keyframes glow-fade {{
        0% {{ opacity: .9; transform: scale(.3); }}
        35% {{ opacity: .5; transform: scale(2); }}
        100% {{ opacity: 0; transform: scale(3); }}
    }}

    /* BRIGHT CORE */

    .core {{
        position: absolute;
        left: -3px;
        top: -3px;

        width: 6px;
        height: 6px;
        border-radius: 50%;

        background: white;

        box-shadow:
            0 0 10px 4px white,
            0 0 25px 10px var(--color);

        opacity: 0;

        animation: core-fade .9s ease-out forwards;
        animation-delay: var(--delay);
    }}

    @keyframes core-fade {{
        0% {{ opacity: 1; transform: scale(.5); }}
        40% {{ opacity: 1; transform: scale(1.5); }}
        100% {{ opacity: 0; transform: scale(.1); }}
    }}

    </style>

    <div class="fireworks-overlay">
        {rocket_html}
        {burst_html}
    </div>
    """
