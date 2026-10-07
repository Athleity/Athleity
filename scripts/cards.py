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
.in{{animation:rise .6s ease-out both}}
.grow{{transform-box:fill-box;transform-origin:left;animation:sweep 1.2s .4s ease-out both}}
.cell{{animation:pop .5s ease-out both}}
.now,.dot{{animation:pulse 1.6s ease-in-out infinite}}
.line{{opacity:0;animation:cycle 16s infinite}}
.caret{{fill:var(--ac);animation:caret 1s steps(1) infinite}}
@keyframes rise{{from{{opacity:0;transform:translateY(6px)}}to{{opacity:1;transform:none}}}}
@keyframes sweep{{from{{transform:scaleX(0)}}to{{transform:scaleX(1)}}}}
@keyframes pop{{from{{opacity:0}}to{{opacity:1}}}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.3}}}}
@keyframes caret{{0%,49%{{opacity:1}}50%,100%{{opacity:0}}}}
@keyframes cycle{{0%{{opacity:0}}4%,22%{{opacity:1}}26%,100%{{opacity:0}}}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}.line{{opacity:0}}.line.f{{opacity:1}}}}
"""
DEFS = ('<defs><pattern id="dots" width="12" height="12" patternUnits="userSpaceOnUse">'
        '<circle cx="1" cy="1" r=".7" fill="#30363d" opacity=".55"/></pattern>'
        '<radialGradient id="glow"><stop offset="0" style="stop-color:var(--ac);stop-opacity:.22"/>'
        '<stop offset="1" style="stop-color:var(--ac);stop-opacity:0"/></radialGradient>'
        '<radialGradient id="sph" cx=".38" cy=".32" r=".8"><stop offset="0" style="stop-color:var(--ac);stop-opacity:.20"/>'
        '<stop offset="1" style="stop-color:var(--ac);stop-opacity:.02"/></radialGradient>'
        '<linearGradient id="scan" x1="0" y1="0" x2="1" y2="0"><stop offset="0" style="stop-color:var(--ac);stop-opacity:0"/>'
        '<stop offset="1" style="stop-color:var(--ac);stop-opacity:.35"/></linearGradient>'
        '<filter id="gl" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="2.2" result="b"/>'
        '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>')

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
        return [("Language", "Python"), ("Stars", "0"), ("Updated", "recently")]


def card(title, body, w, h, i=0, m=18, ket="|ψ⟩"):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><style>{CSS}</style>{DEFS}'
            f'<rect class="bg" x=".5" y=".5" width="{w-1}" height="{h-1}" rx="10"/>'
            f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="9" fill="url(#dots)"/>'
            f'<g class="in" style="animation-delay:{i*0.1:.2f}s">'
            f'<rect class="acc" x="{m}" y="16" width="7" height="7" rx="1.5"/>'
            f'<text class="t" x="{m+13}" y="24">{esc(title.upper())}</text>'
            f'<text class="s mono" x="{w-m}" y="24" text-anchor="end" style="fill:var(--ac);opacity:.7">{esc(ket)}</text>{body}</g></svg>')


def rows(pairs, y, dy, w, m=18, k="k", v="v"):
    return "".join(f'<text class="{k}" x="{m}" y="{y+i*dy}">{esc(a)}</text>'
                   f'<text class="{v}" x="{w-m}" y="{y+i*dy}">{esc(b)}</text>' for i, (a, b) in enumerate(pairs))


def mini_circuit(w, y, i):
    """Tiny animated circuit along the card bottom: wire, H gate, CNOT, meter, travelling pulse."""
    gate = lambda x, t: (f'<rect x="{x}" y="{y-7}" width="14" height="14" rx="3" fill="var(--bg)" stroke="var(--ac)" stroke-opacity=".7"/>'
                         f'<text class="mono" x="{x+7}" y="{y+3.5}" text-anchor="middle" style="font-size:9px;fill:var(--ac)">{t}</text>')
    mx = w - 38
    return (f'<line x1="14" y1="{y}" x2="{w-14}" y2="{y}" stroke="var(--bd)"/>'
            + gate(40, "H")
            + f'<circle class="acc" cx="86" cy="{y}" r="2.5"/><circle cx="108" cy="{y}" r="6" fill="var(--bg)" stroke="var(--ac)" stroke-opacity=".7"/>'
              f'<line x1="102" y1="{y}" x2="114" y2="{y}" stroke="var(--ac)" stroke-opacity=".7"/>'
              f'<line x1="108" y1="{y-6}" x2="108" y2="{y+6}" stroke="var(--ac)" stroke-opacity=".7"/>'
            + f'<rect x="{mx}" y="{y-7}" width="20" height="14" rx="3" fill="var(--bg)" stroke="var(--ac)" stroke-opacity=".7"/>'
              f'<path d="M{mx+4} {y+4} A6 6 0 0 1 {mx+16} {y+4}" fill="none" stroke="var(--ac)" stroke-opacity=".7"/>'
              f'<line x1="{mx+10}" y1="{y+4}" x2="{mx+14}" y2="{y-3}" stroke="var(--ac)" stroke-opacity=".7"/>'
            + f'<circle r="2.4" cy="{y}" fill="var(--ac)" filter="url(#gl)"><animate attributeName="cx" values="14;{w-14}" '
              f'dur="3.2s" begin="{i*0.5:.1f}s" repeatCount="indefinite"/>'
              f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.08;.92;1" dur="3.2s" begin="{i*0.5:.1f}s" repeatCount="indefinite"/></circle>')


def project(title, big, sub, pairs, i, bar=None, w=200, h=164, ket="|ψ⟩"):
    for a, b in pairs:
        assert len(a) + len(b) <= 29, (a, b)
    assert len(sub) <= 34, sub
    b = ""
    if bar:
        b = (f'<rect class="trk" x="14" y="68" width="{w-28}" height="3" rx="1.5"/>'
             f'<rect class="grow acc" x="14" y="68" width="{(w-28)*bar:.1f}" height="3" rx="1.5"/>')
    body = (f'<text class="big" x="14" y="60">{esc(big)}</text>{b}'
            f'<text class="s" x="14" y="86">{esc(sub)}</text>' + rows(pairs, 107, 15, w, 14, "k2", "v2")
            + mini_circuit(w, 149, i))
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


def c_heatmap(u, WW=540, h=140):
    cal = u["contributionsCollection"]["contributionCalendar"]
    weeks, n = cal["weeks"], len(cal["weeks"])
    pitch = (WW - 36) / n
    cs = pitch - 2
    mx = max((d["contributionCount"] for d in days_of(u)), default=0) or 1
    cells, labels, last_m, last_x = [], "", None, -99
    for i, wk in enumerate(weeks):
        x = 18 + i * pitch
        for d in wk["contributionDays"]:
            c = d["contributionCount"]
            cells.append([f"cell l{0 if c == 0 else 1 + min(3, int(4 * c / (mx + 1)))}", x, 38 + d["weekday"] * pitch, i])
        if wk["contributionDays"]:
            m = wk["contributionDays"][0]["date"][5:7]
            if m != last_m and x - last_x >= 28:
                labels += f'<text class="s" x="{x:.1f}" y="116">{MONTHS[int(m)-1]}</text>'
                last_x = x
            last_m = m
    if cells:
        cells[-1][0] = cells[-1][0].replace("cell", "now")
    grid = "".join(f'<rect class="{c}" x="{x:.1f}" y="{y:.1f}" width="{cs:.1f}" height="{cs:.1f}" rx="2" '
                   f'style="animation-delay:{i*18}ms"/>' for c, x, y, i in cells)
    ph = 7 * pitch + 4
    scan = (f'<rect x="14" y="34" width="34" height="{ph:.0f}" fill="url(#scan)">'
            f'<animate attributeName="x" values="14;{WW-48}" dur="7s" repeatCount="indefinite"/></rect>')
    x0 = WW - 120
    legend = (f'<text class="s" x="{x0-6}" y="133" text-anchor="end">Less</text>'
              + "".join(f'<rect class="l{k}" x="{x0+k*13}" y="125" width="10" height="10" rx="2"/>' for k in range(5))
              + f'<text class="s" x="{x0+69}" y="133">More</text>')
    foot = f'<text class="s" x="18" y="133" style="font-size:11px">{num(cal["totalContributions"])} contributions in the last year</text>'
    return card("Contributions", grid + scan + labels + foot + legend, WW, h, 0, ket="measured")


def c_streaks(u, w=270, h=140):
    c, cal = u["contributionsCollection"], u["contributionsCollection"]["contributionCalendar"]
    cur, best = streaks(days_of(u))
    d = lambda n: f"{n} day{'s' * (n != 1)}"
    return card("Activity · 12 months", rows([
        ("Contributions", num(cal["totalContributions"])), ("Commits", num(c["totalCommitContributions"])),
        ("Pull requests", num(c["totalPullRequestContributions"])), ("Current streak", d(cur)), ("Longest streak", d(best))],
        54, 17, w), w, h, 1, ket="|1⟩")


def wavepacket():
    """Two superposed wave packets that drift in phase: loops seamlessly."""
    x0, x1, yc, K, N = 30, 545, 122, 16, 86
    def frame(k, off):
        ph = 2 * math.pi * k / K + off
        pts = []
        for j in range(N + 1):
            x = x0 + (x1 - x0) * j / N
            env = math.exp(-(((x - 287) / 120) ** 2))
            pts.append(f"{x:.1f} {yc - 9 * env * math.sin(2 * math.pi * (x - x0) / 64 - ph):.1f}")
        return "M" + " L".join(pts)
    def path(off, op, sw):
        vals = ";".join(frame(k, off) for k in range(K + 1))
        return (f'<path d="{frame(0, off)}" fill="none" stroke="var(--ac)" stroke-opacity="{op}" stroke-width="{sw}" stroke-linecap="round">'
                f'<animate attributeName="d" values="{vals}" dur="3.2s" repeatCount="indefinite"/></path>')
    return path(0, ".9", 1.5) + path(math.pi / 2, ".3", 1)


def bloch(cx=690, cy=75, r=41):
    th = math.radians(55)
    rx, ry, oy = r * math.sin(th), r * math.sin(th) * .3, -r * math.cos(th)
    N = 48
    pts = [(cx + rx * math.cos(2 * math.pi * k / N), cy + oy + ry * math.sin(2 * math.pi * k / N)) for k in range(N + 1)]
    f = lambda a: ";".join(f"{p[a]:.1f}" for p in pts)
    anim = lambda attr, a: f'<animate attributeName="{attr}" values="{f(a)}" dur="7s" repeatCount="indefinite"/>'
    bars = ""
    for idx, (x, vals) in enumerate(((770, "46;49;44;47;45;46"), (794, "14;12;17;13;16;14"))):
        hs = vals.split(";")
        ys = ";".join(str(116 - int(v)) for v in hs)
        bars += (f'<rect class="acc" x="{x}" y="{116-int(hs[0])}" width="16" height="{hs[0]}" rx="2" fill-opacity="{.9 if idx == 0 else .55}">'
                 f'<animate attributeName="height" values="{vals}" dur="2.4s" repeatCount="indefinite"/>'
                 f'<animate attributeName="y" values="{ys}" dur="2.4s" repeatCount="indefinite"/></rect>'
                 f'<text class="s mono" x="{x+8}" y="128" text-anchor="middle">|{idx}⟩</text>')
    return (f'<circle cx="{cx}" cy="{cy}" r="96" fill="url(#glow)"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#sph)" stroke="var(--ac)" stroke-opacity=".55"/>'
            f'<ellipse cx="{cx}" cy="{cy}" rx="{r}" ry="{r*.3:.1f}" fill="none" stroke="var(--bd)"/>'
            f'<ellipse cx="{cx}" cy="{cy}" rx="{r*.3:.1f}" ry="{r}" fill="none" stroke="var(--bd)"/>'
            f'<line x1="{cx}" y1="{cy-r-7}" x2="{cx}" y2="{cy+r+7}" stroke="var(--bd)"/>'
            f'<line x1="{cx-r-7}" y1="{cy}" x2="{cx+r+7}" y2="{cy}" stroke="var(--bd)"/>'
            f'<ellipse cx="{cx}" cy="{cy+oy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="none" stroke="var(--ac)" stroke-opacity=".4" stroke-dasharray="2 3"/>'
            f'<text class="s mono" x="{cx+5}" y="{cy-r-9}">|0⟩</text><text class="s mono" x="{cx+5}" y="{cy+r+16}">|1⟩</text>'
            f'<line x1="{cx}" y1="{cy}" x2="{pts[0][0]:.1f}" y2="{pts[0][1]:.1f}" stroke="var(--ac)" stroke-width="1.8" stroke-linecap="round">'
            f'{anim("x2", 0)}{anim("y2", 1)}</line>'
            f'<circle r="3.4" cx="{pts[0][0]:.1f}" cy="{pts[0][1]:.1f}" fill="var(--ac)" filter="url(#gl)">{anim("cx", 0)}{anim("cy", 1)}</circle>'
            f'<circle class="acc" cx="{cx}" cy="{cy}" r="2"/>'
            f'<text class="s mono" x="814" y="38" text-anchor="end" style="fill:var(--ac);opacity:.8">1024 shots</text>'
            f'<line x1="766" y1="116.5" x2="814" y2="116.5" stroke="var(--bd)"/>{bars}')


def hero():
    w, h = 830, 140
    lines = ["QAOA on Rigetti Ankaa-3 · Best Overall, Q-volution 2026",
             "Lightning-Lite: C++20 statevector simulator, 3.5x vs Qiskit Aer",
             "Now: surface-code quantum error correction",
             "Translating papers into working code"]
    tl = "".join(f'<text class="mono line{" f" if i == 0 else ""}" x="30" y="90" font-size="13" fill="var(--fg)" '
                 f'style="animation-delay:{i*4}s"><tspan class="acc">›</tspan> {esc(t)}<tspan class="caret"> ▍</tspan></text>'
                 for i, t in enumerate(lines))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><style>{CSS}</style>{DEFS}'
            f'<rect class="bg" x=".5" y=".5" width="{w-1}" height="{h-1}" rx="12"/>'
            f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="11" fill="url(#dots)"/>'
            f'<rect class="acc" x="0.5" y="24" width="4" height="44" rx="2"/>{bloch()}{wavepacket()}<g class="in">'
            '<text x="30" y="48" font-size="30" font-weight="800" letter-spacing=".01em" fill="var(--fg)">Priyansh Bhavsar</text>'
            '<text class="sub" x="30" y="69">BS Physics · Quantum Technologies, IIT Jodhpur</text>'
            f'{tl}</g></svg>')


def stack():
    items = ["Python", "C++20", "Qiskit", "PennyLane", "pyQuil", "Cirq", "QuTiP", "Stim", "NumPy", "SciPy",
             "OpenMP", "CUDA", "SIMD", "pybind11", "PostgreSQL", "PyTorch"]
    x, parts = 0, []
    for k, name in enumerate(items):
        gw = len(name) * 6.8 + 18
        parts.append(f'<rect x="{x:.1f}" y="7" width="{gw:.1f}" height="20" rx="4" fill="var(--bg)" stroke="var(--ac)" stroke-opacity=".6"/>'
                     f'<text class="mono" x="{x+gw/2:.1f}" y="21" text-anchor="middle" style="font-size:11px;fill:var(--fg)">{esc(name)}</text>')
        x += gw
        if k % 3 == 2:
            parts.append(f'<circle class="acc" cx="{x+12:.1f}" cy="17" r="2.6"/>')
        x += 24
    L = round(x, 1)
    grp = "".join(parts)
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="830" height="34" viewBox="0 0 830 34">'
            f'<style>{CSS}</style><defs><linearGradient id="f"><stop offset="0" stop-color="#000"/>'
            '<stop offset=".07" stop-color="#fff"/><stop offset=".93" stop-color="#fff"/><stop offset="1" stop-color="#000"/>'
            '</linearGradient><mask id="m"><rect width="830" height="34" fill="url(#f)"/></mask></defs>'
            '<rect class="bg" x=".5" y=".5" width="829" height="33" rx="8"/>'
            f'<g mask="url(#m)"><g><animateTransform attributeName="transform" type="translate" from="0 0" to="-{L} 0" '
            f'dur="40s" repeatCount="indefinite"/><line x1="0" y1="17" x2="{L*3}" y2="17" stroke="var(--bd)"/>'
            f'{grp}<g transform="translate({L} 0)">{grp}</g><g transform="translate({2*L} 0)">{grp}</g></g></g></svg>')


def main():
    u = fetch()
    os.makedirs(OUT, exist_ok=True)
    cards = {
        "hero": hero(), "stack": stack(), "heatmap": c_heatmap(u), "streaks": c_streaks(u),
        "gridiq": project("GridIQ", "96.03%", "approx. ratio · Rigetti Ankaa-3", [
            ("Q-volution 2026", "Best Overall"), ("Best simulated", "97.31%"), ("vs vanilla SA", "+3.8%")], 2, bar=0.9603, ket="|QAOA⟩"),
        "lightning": project("Lightning-Lite", "3.5×", "faster than Qiskit Aer", [
            ("Memory bandwidth", "94%"), ("Validation", "gate-by-gate"), ("Stack", "C++20 · SIMD")], 3, ket="|sim⟩"),
        # Add a real result later: change "Hybrid" and the sub line, e.g. "0.82" / "mean ROC-AUC"
        "tox21": project("Tox21 Hybrid", "Hybrid", "quantum-classical toxicity model",
                         repo_rows("tox21-hybrid-quantum-model"), 4, ket="|QML⟩"),
        "entangle": project("Entanglement", "Qubits", "quantum entanglement project",
                            repo_rows("Quantum-entanglement-project"), 5, ket="|Φ⁺⟩"),
    }
    for name, svg in cards.items():
        with open(f"{OUT}/{name}.svg", "w", encoding="utf-8") as f:
            f.write(svg)
    print("wrote", ", ".join(cards))


if __name__ == "__main__":
    main()
