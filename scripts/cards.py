#!/usr/bin/env python3
"""Quantum-themed animated profile cards (SVG) from the GitHub API. Standard library only.
Usage: GH_TOKEN=... GH_USER=Athleity python3 scripts/cards.py   (add --demo for sample data)"""
import datetime, html, json, math, os, sys, urllib.request

USER = os.environ.get("GH_USER", "Athleity")
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
DEMO = "--demo" in sys.argv
OUT, MONTHS = "cards", "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
CSS = f"""
:root{{--bg:#0d1117;--bd:#30363d;--fg:#e6edf3;--mu:#8b949e;--ac:#39d353;--ac2:#26a641}}
text{{font-family:{FONT}}}
.mono{{font-family:{MONO}}}
.bg{{fill:var(--bg);stroke:var(--bd)}}
.trk{{fill:var(--bd)}}
.t{{font-family:{MONO};font-size:11px;font-weight:600;letter-spacing:.06em;fill:var(--fg)}}
.k2{{font-size:11px;fill:var(--mu)}}
.v2{{font-size:11px;font-weight:600;fill:var(--fg);text-anchor:end}}
.k{{font-size:12px;fill:var(--mu)}}
.v{{font-size:12px;font-weight:600;fill:var(--fg);text-anchor:end}}
.s{{font-size:10px;fill:var(--mu)}}
.sub{{font-size:13px;fill:var(--mu)}}
.big{{font-family:{MONO};font-size:26px;font-weight:700;fill:var(--ac)}}
.acc{{fill:var(--ac)}}
.l0{{fill:#161b22}}.l1{{fill:#0e4429}}.l2{{fill:#006d32}}.l3{{fill:#26a641}}.l4{{fill:#39d353}}
.line{{opacity:0;animation:cycle 16s infinite}}
@keyframes cycle{{0%{{opacity:0}}4%,22%{{opacity:1}}26%,100%{{opacity:0}}}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}.line{{opacity:0}}.line.f{{opacity:1}}}}
"""
DEFS = ('<defs><radialGradient id="sph" cx=".38" cy=".32" r=".8"><stop offset="0" style="stop-color:var(--ac);stop-opacity:.18"/>'
        '<stop offset="1" style="stop-color:var(--ac);stop-opacity:.02"/></radialGradient>'
        '<linearGradient id="scan" x1="0" y1="0" x2="1" y2="0"><stop offset="0" style="stop-color:var(--ac);stop-opacity:0"/>'
        '<stop offset="1" style="stop-color:var(--ac);stop-opacity:.35"/></linearGradient></defs>')

QUERY = """
query($login:String!){user(login:$login){
 contributionsCollection{
  totalCommitContributions totalPullRequestContributions totalIssueContributions totalPullRequestReviewContributions
  contributionCalendar{totalContributions weeks{contributionDays{contributionCount date weekday}}}}
}}"""


def demo_data():
    start, weeks = datetime.date(2025, 10, 12), []
    for w in range(53):
        days = []
        for wd in range(7):
            d = start + datetime.timedelta(days=w * 7 + wd)
            if d <= datetime.date(2026, 10, 7):
                days.append({"date": d.isoformat(), "weekday": wd, "contributionCount": ((w * 7 + wd) * 37 % 11) * (wd % 3 != 0)})
        weeks.append({"contributionDays": days})
    return {"contributionsCollection": {"totalCommitContributions": 320, "totalPullRequestContributions": 12,
            "totalIssueContributions": 3, "totalPullRequestReviewContributions": 1,
            "contributionCalendar": {"totalContributions": 336, "weeks": weeks}}}


esc = lambda s: html.escape(str(s))
num = lambda n: f"{n:,}"


def fetch():
    if DEMO:
        return demo_data()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json", "User-Agent": "profile-cards"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if "errors" in data:
        sys.exit(json.dumps(data["errors"]))
    return data["data"]["user"]


def empty_data():
    today = datetime.date.today()
    start = today - datetime.timedelta(days=today.weekday() + 1 + 52 * 7)
    weeks = [{"contributionDays": [{"date": (start + datetime.timedelta(days=w * 7 + d)).isoformat(), "weekday": d,
                                    "contributionCount": 0}
                                   for d in range(7) if start + datetime.timedelta(days=w * 7 + d) <= today]} for w in range(53)]
    return {"contributionsCollection": {"totalCommitContributions": 0, "totalPullRequestContributions": 0,
            "totalIssueContributions": 0, "totalPullRequestReviewContributions": 0,
            "contributionCalendar": {"totalContributions": 0, "weeks": weeks}}}


def safe_fetch():
    try:
        return fetch()
    except BaseException as e:
        print(f"::warning::GitHub API call failed ({e}). Check that the GH_TOKEN secret is set in the workflow. "
              "Writing cards with an empty heatmap.", file=sys.stderr)
        return empty_data()


def repo_rows(name):
    """Real facts from the repo (language, stars, last push). Nothing invented."""
    try:
        if DEMO:
            raise RuntimeError
        req = urllib.request.Request(f"https://api.github.com/repos/{USER}/{name}",
                                     headers={"Authorization": f"bearer {TOKEN}", "User-Agent": "profile-cards"})
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.load(r)
        p = d["pushed_at"]
        return [("Language", d.get("language") or "n/a"), ("Stars", str(d["stargazers_count"])),
                ("Updated", f"{MONTHS[int(p[5:7])-1]} {p[:4]}")]
    except Exception:
        return [("Language", "–"), ("Stars", "–"), ("Updated", "–")]


def card(title, body, w, h, i=0, m=18, ket=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><style>{CSS}</style>{DEFS}'
            f'<rect class="bg" x=".5" y=".5" width="{w-1}" height="{h-1}" rx="10"/>'
            f'<rect class="acc" x="{m}" y="16" width="7" height="7" rx="1.5"/>'
            f'<text class="t" x="{m+13}" y="24">{esc(title.upper())}</text>{body}</svg>')


def rows(pairs, y, dy, w, m=18, k="k", v="v"):
    return "".join(f'<text class="{k}" x="{m}" y="{y+i*dy}">{esc(a)}</text>'
                   f'<text class="{v}" x="{w-m}" y="{y+i*dy}">{esc(b)}</text>' for i, (a, b) in enumerate(pairs))


def project(title, big, sub, pairs, i, bar=None, w=200, h=150, ket=""):
    pairs = [(x, y if len(x) + len(y) <= 29 else y[:max(1, 28 - len(x))] + "…") for x, y in pairs]  # never crash on long repo data
    sub = sub if len(sub) <= 34 else sub[:33] + "…"
    b = ""
    if bar:
        b = (f'<rect class="trk" x="14" y="68" width="{w-28}" height="3" rx="1.5"/>'
             f'<rect class="acc" x="14" y="68" width="{(w-28)*bar:.1f}" height="3" rx="1.5"/>')
    body = (f'<text class="big" x="14" y="60">{esc(big)}</text>{b}'
            f'<text class="s" x="14" y="86">{esc(sub)}</text>' + rows(pairs, 108, 16, w, 14, "k2", "v2"))
    return card(title, body, w, h, i, 14, ket)


def days_of(u):
    return [d for wk in u["contributionsCollection"]["contributionCalendar"]["weeks"] for d in wk["contributionDays"]]


def streaks(days):
    best = run = cur = 0
    for d in days:
        run = run + 1 if d["contributionCount"] else 0
        best = max(best, run)
    i = len(days) - 1
    if i >= 0 and days[i]["contributionCount"] == 0:
        i -= 1
    while i >= 0 and days[i]["contributionCount"] > 0:
        cur += 1
        i -= 1
    return cur, best


def c_heatmap(u, WW=540, h=152):
    cal = u["contributionsCollection"]["contributionCalendar"]
    weeks, n = cal["weeks"], max(1, len(cal["weeks"]))
    pitch = (WW - 36) / n
    cs = pitch - 2
    mx = max((d["contributionCount"] for d in days_of(u)), default=0) or 1
    cells, labels, last_m, last_x = [], "", None, -99
    for i, wk in enumerate(weeks):
        x = 18 + i * pitch
        for d in wk["contributionDays"]:
            c = d["contributionCount"]
            cells.append([f"l{0 if c == 0 else 1 + min(3, int(4 * c / (mx + 1)))}", x, 38 + d["weekday"] * pitch, i])
        if wk["contributionDays"]:
            m = wk["contributionDays"][0]["date"][5:7]
            if m != last_m and x - last_x >= 28:
                labels += f'<text class="s" x="{x:.1f}" y="116">{MONTHS[int(m)-1]}</text>'
                last_x = x
            last_m = m
    grid = "".join(f'<rect class="{c}" x="{x:.1f}" y="{y:.1f}" width="{cs:.1f}" height="{cs:.1f}" rx="2" '
                   f'/>' for c, x, y, i in cells)
    ph = 7 * pitch + 4
    scan = (f'<rect x="14" y="34" width="34" height="{ph:.0f}" fill="url(#scan)">'
            f'<animate attributeName="x" values="14;{WW-48}" dur="7s" repeatCount="indefinite"/></rect>')
    x0 = WW - 120
    legend = (f'<text class="s" x="{x0-6}" y="145" text-anchor="end">Less</text>'
              + "".join(f'<rect class="l{k}" x="{x0+k*13}" y="137" width="10" height="10" rx="2"/>' for k in range(5))
              + f'<text class="s" x="{x0+69}" y="145">More</text>')
    foot = f'<text class="s" x="18" y="145" style="font-size:11px">{num(cal["totalContributions"])} contributions in the last year</text>'
    return card("Contributions", grid + scan + labels + foot + legend, WW, h, 0)


def c_streaks(u, w=270, h=152):
    c, cal = u["contributionsCollection"], u["contributionsCollection"]["contributionCalendar"]
    cur, best = streaks(days_of(u))
    d = lambda n: f"{n} day{'s' * (n != 1)}"
    return card("Activity · 12 months", rows([
        ("Contributions", num(cal["totalContributions"])), ("Commits", num(c["totalCommitContributions"])),
        ("Pull requests", num(c["totalPullRequestContributions"])), ("Current streak", d(cur)), ("Longest streak", d(best))],
        58, 18, w), w, h, 1)


CYCLE = 17.2  # seconds; the sea, the cat and the Bloch sphere all share this one loop
# timeline as fractions of the loop: wave starts, bump fully up, cat reaches box, measurement starts, measurement ends
W0, W1, ARR, MEAS, MEND = .09, .16, .50, .56, .92

# Surfboard in cat-local coordinates (the cat stands on y=0). Side view of a shortboard:
# rounded tail, rocker that lifts the nose, pointed nose tip, stringer, wax patch and a thruster fin set.
BOARD = (
    '<path d="M-6 3 C-7 5.5 -10 7.6 -13.5 8 C-12.2 6 -11.6 4.5 -11.4 2.8 Z" class="acc" stroke="var(--bg)" stroke-width=".6" stroke-linejoin="round"/>'   # rear fin
    '<path d="M-14.5 2.9 C-15 4.8 -16.6 6.2 -19 6.8 C-18.4 5.4 -18.2 4.2 -18.4 2.8 Z" class="acc" stroke="var(--bg)" stroke-width=".6" stroke-linejoin="round"/>'  # tail fin
    '<path class="acc" stroke="var(--bg)" stroke-width=".9" stroke-linejoin="round" '
    'd="M-25 -.6 C-24.6 -2 -22 -2.7 -16 -2.8 C-6 -3.1 10 -3.1 20 -3.6 C25 -3.9 28.5 -5 30.5 -7.4 '
    'C29.6 -2.6 25 1.6 17 2.6 C6 3.7 -10 3.5 -20 2.6 C-23.6 2.2 -25.4 1.2 -25 -.6 Z"/>'                                   # hull
    '<path d="M-23 -.6 C-8 -1.4 12 -1.6 27.5 -6" fill="none" stroke="var(--bg)" stroke-width=".7" stroke-opacity=".75" stroke-linecap="round"/>'  # stringer
    '<path d="M-6 -2.2 C-3 -2.5 3 -2.5 6 -2.2" fill="none" stroke="var(--bg)" stroke-width=".7" stroke-opacity=".6" stroke-linecap="round"/>'    # wax mark under the cat
)


def cat_shape(sc, board_anim=''):
    return (f'<g transform="scale({sc})">'
            '<path d="M-6 -9 C-15 -9 -15 -21 -9 -23" fill="none" stroke="var(--ac)" stroke-width="2.2" stroke-linecap="round">'
            '<animateTransform attributeName="transform" type="rotate" values="-8 -6 -9;10 -6 -9;-8 -6 -9" dur="1.6s" repeatCount="indefinite"/></path>'
            '<ellipse class="acc" cx="0" cy="-10" rx="6" ry="7.5"/>'
            '<polygon class="acc" points="2,-24 3,-31 7,-25"/><polygon class="acc" points="6,-25 10,-30 11,-22"/>'
            '<circle class="acc" cx="6" cy="-20" r="5.4"/><circle cx="7.6" cy="-20.6" r="1" fill="var(--bg)"/>'
            '<g stroke="var(--ac)" stroke-width="2" stroke-linecap="round"><line x1="-3" y1="-13" x2="-11" y2="-17"/>'
            '<line x1="4" y1="-12" x2="12" y2="-9"/></g>'
            f'<g>{board_anim}{BOARD}</g></g>')


def surf_hero(x0=2, x1=602, base=131, amp=12, hw=44, hf=50, sc=.80, dur=CYCLE, M=360, step=8, bw=38, bh=38, LEAN=1.0):
    """Schroedinger's cat. One green line; ONE curved bump, kicked up by the cat's landing, carries the cat to a square open box next to the Bloch
    sphere. The cat steps in (ears and head stay visible) and a '?' appears. At MEAS (same moment as the Bloch
    sphere) the '?' goes, the box glows (measurement) and the cat slowly sinks and vanishes. Then a short rest, and
    the cat steps out of a portal before the wave, lands on its start, the portal closes, and the bump rises under it."""
    sm = lambda e: (lambda q: q * q * (3 - 2 * q))(min(1, max(0, e)))
    bx, top, o = x1, 95, 6                                                     # box front-left corner, wall top, 3D offset
    mid = bx + bw / 2 + o / 2
    E0, PX, LX = .04, 20, 52                                              # cat leaves the portal at x=PX, lands so the board tail sits at the wave's start (x0)
    u_in = lambda t: min(1, max(0, (t - E0) / (W0 - E0)))
    catx = lambda t: (PX - 12 + (LX - PX + 12) * sm(u_in(t))) if t < W0 else LX + (mid - LX) * sm((t - W0) / (ARR - W0))
    CO = 6                                                                     # crest sits only just behind the cat, so it rides near the middle of the wave
    EXT = x1 + hw + 2 - (mid - CO)                                             # extra travel so the whole wave runs into the box
    crest = lambda t: catx(t) - CO + EXT * sm((t - ARR + .10) / .28)          # rides behind the surfer, then carries on into the box
    env = lambda t: sm((t - W0) / (W1 - W0))                                   # bump rises once and keeps its shape until it is gone
    xs = list(range(x0, x1 + 1, step))
    if xs[-1] != x1:
        xs.append(x1)
    frames, cat_xy, cat_op, brd_op, kts = [], [], [], [], []
    for k in range(M + 1):
        t = k / M
        pk, e, p = crest(t), env(t), catx(t)
        hit = 5.5 * math.sin(math.pi * min(1, max(0, (t - W0 + .01) / .07)))   # the landing presses the line down, then it springs up
        def bump(x):
            return (amp * e * (1 + math.cos(math.pi * (pk - x) / hw)) / 2 if pk - hw < x <= pk       # back slope
                    else amp * e * (1 + math.cos(math.pi * (x - pk) / hf)) / 2 if pk < x < pk + hf else 0)  # front slope
        h = lambda x: bump(x) - hit * math.exp(-((x - LX) / 20) ** 2)
        # lean: the higher a point of the wave, the further it is pushed toward the surfer, so the crest curls forward
        frames.append("M" + " L".join(f"{min(x1, x + LEAN * bump(x)):.1f} {base - h(x):.1f}" for x in xs))
        xc = p
        for _ in range(8):                                                     # find the point of the wave that sits under the cat
            xc = p - LEAN * bump(xc)
        g = sm((p - (bx - 14)) / (mid - (bx - 14)))                            # 0 on the wave -> 1 inside the box
        y_in = top + 11 + 14 * sm((t - MEAS) / .16)                            # head and ears above the wall; sinks after measurement
        cat_xy.append(f"{p:.1f} {(base - h(xc) - 1 - (32 * u_in(t) * (1 - u_in(t)) if t < W0 else 0)) * (1 - g) + y_in * g:.2f}")
        brd_op.append(f"{1 - sm(g / .6):.3f}")                                 # board fades before the nose could poke out of the box
        cat_op.append(f"{sm((t - E0 + .005) / .01) * (1 - sm((t - MEAS) / .16)):.3f}")
        kts.append(f"{t:.4f}")
    kt, rep = ";".join(kts), f'dur="{dur}s" repeatCount="indefinite"'
    line = (f'<path d="{frames[0]}" shape-rendering="geometricPrecision" fill="none" stroke="var(--ac)" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
            f'<animate attributeName="d" values="{";".join(frames)}" {rep}/></path>')
    board_anim = f'<animate attributeName="opacity" values="{";".join(brd_op)}" {rep}/>'
    cat = (f'<g clip-path="url(#emerge)"><g opacity="0"><animateTransform attributeName="transform" type="translate" values="{";".join(cat_xy)}" {rep}/>'
           f'<animate attributeName="opacity" values="{";".join(cat_op)}" {rep}/>'
           f'<g filter="url(#unc)"><animate attributeName="filter" values="url(#unc);none" keyTimes="0;{W0+.002:.3f}" calcMode="discrete" {rep}/><animateTransform attributeName="transform" type="translate" values="0 0;0 -1.2;0 0" dur="1.4s" repeatCount="indefinite"/>'
           f'{cat_shape(sc, board_anim)}</g></g></g>')
    cy, ra, rb = base - 13, 8, 17
    defs = (f'<defs><clipPath id="emerge"><rect x="{PX}" y="70" width="800" height="70"/></clipPath>'
            f'<filter id="unc" x="-40%" y="-40%" width="180%" height="180%"><feGaussianBlur stdDeviation="0">'
            f'<animate attributeName="stdDeviation" values="3;3;0;0" keyTimes="0;{E0};{W0};1" {rep}/></feGaussianBlur></filter>'
            f'<filter id="glow" x="-100%" y="-50%" width="300%" height="200%"><feGaussianBlur stdDeviation="2.6"/></filter>'
            f'<radialGradient id="pg"><stop offset="0" style="stop-color:var(--ac);stop-opacity:.35"/>'
            f'<stop offset=".6" style="stop-color:var(--ac);stop-opacity:.12"/><stop offset="1" style="stop-color:var(--ac);stop-opacity:.03"/></radialGradient></defs>')
    # the portal sits before the wave: it snaps open with a small overshoot, glows and swirls while the cat steps out, then collapses
    swirl = "".join(f'<ellipse rx="{ra*k:.1f}" ry="{rb*k:.1f}" fill="none" stroke="var(--ac)" stroke-width="1.2" stroke-opacity="{o_}" stroke-dasharray="{d}">'
                     f'<animate attributeName="stroke-dashoffset" values="0;{v}" dur="{t_}s" repeatCount="indefinite"/></ellipse>'
                     for k, o_, d, v, t_ in ((.6, .55, "4 4", -18, 1.1),))
    portal = (f'<g transform="translate({PX} {cy})" opacity="0"><animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;.01;.03;.14;.17;1" {rep}/>'
              f'<g><animateTransform attributeName="transform" type="scale" values=".05;.05;1.06;1;1;.05;.05" keyTimes="0;.01;.04;.05;.14;.17;1" {rep}/>'
              f'<ellipse rx="{ra}" ry="{rb}" fill="none" stroke="var(--ac)" stroke-width="3" stroke-opacity=".25" filter="url(#glow)"/>'
              f'<ellipse rx="{ra}" ry="{rb}" fill="url(#pg)"/>{swirl}'
              f'<ellipse rx="{ra}" ry="{rb}" fill="none" stroke="var(--ac)" stroke-width="1.8"/>'
              f'<ellipse rx="2" ry="6" fill="var(--ac)"><animate attributeName="fill-opacity" values=".25;.6;.25" dur=".7s" repeatCount="indefinite"/></ellipse>'
              f'</g></g>')
    st = 'stroke="var(--ac)" stroke-width="1.5" stroke-linejoin="round" stroke-opacity=".9"'
    back = (f'<rect x="{bx+o}" y="{top-o}" width="{bw}" height="{bh}" rx="3" fill="#161b22" {st}>'
            f'<animate attributeName="fill" values="#161b22;#161b22;#0e4429;#0e4429;#161b22;#161b22" '
            f'keyTimes="0;{MEAS:.3f};{MEAS+.04:.3f};{MEND-.06:.3f};{MEND:.3f};1" {rep}/></rect>'
            f'<line x1="{bx}" y1="{top}" x2="{bx+o}" y2="{top-o}" {st}/>'
            f'<polygon points="{bx+bw},{top} {bx+bw+o},{top-o} {bx+bw+o},{top+bh-o} {bx+bw},{top+bh}" fill="var(--bg)" {st}/>')
    front = f'<rect x="{bx}" y="{top}" width="{bw}" height="{bh}" rx="3" fill="var(--bg)" {st}/>'
    mark = (f'<text class="mono" x="{bx+bw/2:.1f}" y="{top+31}" text-anchor="middle" style="font-size:32px;font-weight:700;fill:var(--ac)">?'
            f'<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;{ARR-.03:.3f};{ARR+.01:.3f};{MEAS-.005:.3f};{MEAS+.005:.3f};1" {rep}/></text>')
    ring = lambda s: (f'<circle cx="{bx+bw/2+o/2:.1f}" cy="{top+bh/2-o/2:.1f}" fill="none" stroke="var(--ac)">'
                      f'<animate attributeName="r" values="6;6;6;34;34" keyTimes="0;{s-.001:.3f};{s:.3f};{s+.10:.3f};1" {rep}/>'
                      f'<animate attributeName="stroke-opacity" values="0;0;.8;0;0" keyTimes="0;{s-.001:.3f};{s:.3f};{s+.10:.3f};1" {rep}/></circle>')
    return defs + line + back + cat + portal + front + mark + ring(MEAS) + ring(MEAS + .12) + ring(MEAS + .24)


def bloch(cx=705, cy=72, r=42, dur=CYCLE):
    """Precessing state vector. At T=.62 it is measured: snaps to |0>, rests there, then is re-prepared."""
    th0, M = math.radians(55), 360
    ease = lambda e: e * e * (3 - 2 * e)
    pts = []
    for k in range(M + 1):
        t = k / M
        if t < .03:
            th, ph = 0, 0
        elif t < .09:
            th, ph = th0 * ease((t - .03) / .06), 0
        elif t < MEAS:
            th, ph = th0, 2 * math.pi * 1.1 * (t - .09) / (MEAS - .09)
        elif t < MEAS + .10:
            th, ph = th0 * (1 - ease((t - MEAS) / .10)), 2 * math.pi * 1.1
        else:
            th, ph = 0, 0
        pts.append((cx + r * math.sin(th) * math.cos(ph), cy - r * math.cos(th) + r * .3 * math.sin(th) * math.sin(ph)))
    keys = ";".join(f"{k/M:.4f}" for k in range(M + 1))
    anim = lambda attr, a: (f'<animate attributeName="{attr}" values="{";".join(f"{p[a]:.2f}" for p in pts)}" '
                            f'dur="{dur}s" repeatCount="indefinite"/>')
    rx, oy = r * math.sin(th0), -r * math.cos(th0)
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#sph)" stroke="var(--ac)" stroke-opacity=".55"/>'
            f'<ellipse cx="{cx}" cy="{cy}" rx="{r}" ry="{r*.3:.1f}" fill="none" stroke="var(--bd)"/>'
            f'<ellipse cx="{cx}" cy="{cy}" rx="{r*.3:.1f}" ry="{r}" fill="none" stroke="var(--bd)"/>'
            f'<line x1="{cx}" y1="{cy-r-7}" x2="{cx}" y2="{cy+r+7}" stroke="var(--bd)"/>'
            f'<line x1="{cx-r-7}" y1="{cy}" x2="{cx+r+7}" y2="{cy}" stroke="var(--bd)"/>'
            f'<ellipse cx="{cx}" cy="{cy+oy:.1f}" rx="{rx:.1f}" ry="{rx*.3:.1f}" fill="none" stroke="var(--ac)" stroke-opacity=".4" stroke-dasharray="2 3"/>'
            f'<text class="s mono" x="{cx+5}" y="{cy-r-9}">|0⟩</text><text class="s mono" x="{cx+5}" y="{cy+r+16}">|1⟩</text>'
            f'<circle cx="{cx}" cy="{cy}" fill="none" stroke="var(--ac)">'
            f'<animate attributeName="r" values="{r};{r};{r};{r+14};{r+14}" keyTimes="0;{MEAS-.001:.3f};{MEAS:.3f};{MEAS+.14:.3f};1" dur="{dur}s" repeatCount="indefinite"/>'
            f'<animate attributeName="stroke-opacity" values="0;0;.7;0;0" keyTimes="0;{MEAS-.001:.3f};{MEAS:.3f};{MEAS+.14:.3f};1" dur="{dur}s" repeatCount="indefinite"/></circle>'
            f'<circle cx="{cx}" cy="{cy-r}" r="4.5" fill="none" stroke="var(--ac)">'
            f'<animate attributeName="stroke-opacity" values="1;1;0;0;1;1" keyTimes="0;.02;.05;{MEAS+.08:.3f};{MEAS+.12:.3f};1" dur="{dur}s" repeatCount="indefinite"/></circle>'
            f'<line x1="{cx}" y1="{cy}" x2="{pts[0][0]:.1f}" y2="{pts[0][1]:.1f}" stroke="var(--ac)" stroke-width="1.8" stroke-linecap="round">'
            f'{anim("x2", 0)}{anim("y2", 1)}</line>'
            f'<circle r="3.4" cx="{pts[0][0]:.1f}" cy="{pts[0][1]:.1f}" fill="var(--ac)">{anim("cx", 0)}{anim("cy", 1)}</circle>'
            f'<circle class="acc" cx="{cx}" cy="{cy}" r="2"/>')


def hero():
    w, h = 830, 140
    lines = ["QAOA on Rigetti Ankaa-3 · Best Overall, Q-volution 2026",
             "Lightning-Lite: C++20 statevector simulator, 3.5x vs Qiskit Aer",
             "Now: surface-code quantum error correction",
             "Translating papers into working code"]
    tl = "".join(f'<text class="mono line{" f" if i == 0 else ""}" x="30" y="85" font-size="13" fill="var(--fg)" '
                 f'style="animation-delay:{i*4}s"><tspan class="acc">›</tspan> {esc(t)}</text>'
                 for i, t in enumerate(lines))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><style>{CSS}</style>{DEFS}'
            f'<rect class="bg" x=".5" y=".5" width="{w-1}" height="{h-1}" rx="12"/>'
            f'<rect class="acc" x="0.5" y="24" width="4" height="44" rx="2"/>{bloch()}{surf_hero()}<g>'
            '<text x="30" y="48" font-size="30" font-weight="800" letter-spacing=".01em" fill="var(--fg)">Priyansh Bhavsar</text>'
            '<text class="sub" x="30" y="69">BS Physics · Quantum Technologies, IIT Jodhpur</text>'
            f'{tl}</g></svg>')


def stack():
    items = ["Python", "C++20", "Qiskit", "PennyLane", "pyQuil", "Cirq", "QuTiP", "Stim", "NumPy", "SciPy",
             "OpenMP", "CUDA", "pybind11", "PyTorch"]
    while sum(len(n) * 6.7 + 20 for n in items) + 6 * (len(items) - 1) > 790:
        items.pop()
    total = sum(len(n) * 6.7 + 20 for n in items) + 6 * (len(items) - 1)
    x, out = (830 - total) / 2, ""
    for name in items:
        gw = len(name) * 6.7 + 20
        out += (f'<rect x="{x:.1f}" y="7" width="{gw:.1f}" height="20" rx="4" fill="none" stroke="var(--ac)" stroke-opacity=".55"/>'
                f'<text class="mono" x="{x+gw/2:.1f}" y="21" text-anchor="middle" style="font-size:11px;fill:var(--fg)">{esc(name)}</text>')
        x += gw + 6
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="830" height="34" viewBox="0 0 830 34">'
            f'<style>{CSS}</style><rect class="bg" x=".5" y=".5" width="829" height="33" rx="8"/>{out}</svg>')


def main():
    u = safe_fetch()
    os.makedirs(OUT, exist_ok=True)
    cards = {
        "hero": hero(), "stack": stack(), "heatmap": c_heatmap(u), "streaks": c_streaks(u),
        "gridiq": project("GridIQ", "96.03%", "approx. ratio · Rigetti Ankaa-3", [
            ("Q-volution 2026", "Best Overall"), ("Best simulated", "97.31%"), ("vs vanilla SA", "+3.8%")], 2, bar=0.9603),
        "lightning": project("Lightning-Lite", "3.5×", "faster than Qiskit Aer", [
            ("Memory bandwidth", "94%"), ("Validation", "gate-by-gate"), ("Stack", "C++20 · SIMD")], 3),
        # Add a real result later: change "Hybrid" and the sub line, e.g. "0.82" / "mean ROC-AUC"
        "tox21": project("Tox21 Hybrid", "Hybrid", "quantum-classical toxicity model",
                         repo_rows("tox21-hybrid-quantum-model"), 4),
        "entangle": project("Entanglement", "Qubits", "quantum entanglement project",
                            repo_rows("Quantum-entanglement-project"), 5),
    }
    for name, svg in cards.items():
        with open(f"{OUT}/{name}.svg", "w", encoding="utf-8") as f:
            f.write(svg)
    print("wrote", ", ".join(f"{OUT}/{n}.svg" for n in cards))


if __name__ == "__main__":
    main()
