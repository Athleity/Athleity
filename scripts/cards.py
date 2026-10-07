#!/usr/bin/env python3
"""Animated profile cards (SVG) from the GitHub API. Standard library only.
Usage: GH_TOKEN=... GH_USER=Athleity python3 scripts/cards.py   (add --demo for sample data)"""
import datetime, html, json, os, sys, urllib.request

USER = os.environ.get("GH_USER", "Athleity")
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
DEMO = "--demo" in sys.argv
OUT, MONTHS = "cards", "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
CSS = f"""
:root{{--bg:#fff;--bd:#d0d7de;--fg:#1f2328;--mu:#656d76;--ac:#0969da;--ac2:#8250df}}
@media (prefers-color-scheme:dark){{:root{{--bg:#0d1117;--bd:#30363d;--fg:#e6edf3;--mu:#8b949e;--ac:#58a6ff;--ac2:#bc8cff}}}}
text{{font-family:{FONT}}}
.mono{{font-family:{MONO}}}
.bg{{fill:var(--bg);stroke:var(--bd)}}
.trk{{fill:var(--bd)}}
.sh{{fill:var(--ac);opacity:.9}}
.t{{font-size:11px;font-weight:600;letter-spacing:.09em;fill:var(--ac)}}
.k{{font-size:12px;fill:var(--mu)}}
.v{{font-size:12px;font-weight:600;fill:var(--fg);text-anchor:end}}
.k2{{font-size:11px;fill:var(--mu)}}
.v2{{font-size:11px;font-weight:600;fill:var(--fg);text-anchor:end}}
.s{{font-size:10px;fill:var(--mu)}}
.sub{{font-size:13px;fill:var(--mu)}}
.acc{{fill:var(--ac)}}
.l0{{fill:var(--bd);fill-opacity:.5}}
.l1{{fill:var(--ac);fill-opacity:.28}}
.l2{{fill:var(--ac);fill-opacity:.5}}
.l3{{fill:var(--ac);fill-opacity:.75}}
.l4{{fill:var(--ac)}}
.orb{{fill:none;stroke:var(--ac);stroke-opacity:.4}}
.el{{fill:var(--ac2)}}
.ring{{fill:none;stroke:var(--bd);stroke-dasharray:2 5}}
.live{{fill:#3fb950}}
.in{{animation:rise .7s ease-out both}}
.grow{{animation:sweep 1.4s .4s ease-out both}}
.cell{{animation:pop .5s ease-out both}}
.now,.dot{{animation:pulse 1.6s ease-in-out infinite}}
.line{{opacity:0;animation:cycle 16s infinite}}
.spin{{transform-origin:700px 62px;animation:spin 40s linear infinite}}
@keyframes rise{{from{{opacity:0;transform:translateY(8px)}}to{{opacity:1;transform:none}}}}
@keyframes sweep{{from{{transform:scaleX(0)}}to{{transform:scaleX(1)}}}}
@keyframes pop{{from{{opacity:0}}to{{opacity:1}}}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.3}}}}
@keyframes cycle{{0%{{opacity:0;transform:translateY(6px)}}4%,22%{{opacity:1;transform:none}}26%,100%{{opacity:0;transform:translateY(-6px)}}}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}.line{{opacity:0}}.line.f{{opacity:1}}}}
"""

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


DEFS = ('<defs><linearGradient id="bgg" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" style="stop-color:var(--ac);stop-opacity:.10"/>'
        '<stop offset="1" style="stop-color:var(--ac2);stop-opacity:0"/></linearGradient>'
        '<linearGradient id="bn" x1="0" y1="0" x2="1" y2="0">'
        '<stop offset="0" style="stop-color:var(--ac)"/><stop offset="1" style="stop-color:var(--ac2)"/></linearGradient></defs>')


def card(title, body, w, h, i=0, m=18):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><style>{CSS}</style>{DEFS}'
            f'<rect class="bg" x=".5" y=".5" width="{w-1}" height="{h-1}" rx="12"/>'
            f'<rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="12" fill="url(#bgg)"/>'
            f'<g class="in" style="animation-delay:{i*0.12:.2f}s">'
            f'<text class="t" x="{m}" y="24">{esc(title.upper())}</text>'
            f'<rect class="sh" x="{m}" y="31" width="24" height="2" rx="1">'
            f'<animateTransform attributeName="transform" type="translate" values="0 0;{w-2*m-24} 0;0 0" '
            f'dur="5s" begin="{i*0.4:.1f}s" repeatCount="indefinite"/></rect>{body}</g></svg>')


def rows(pairs, y, dy, w, m=18, k="k", v="v"):
    return "".join(f'<text class="{k}" x="{m}" y="{y+i*dy}">{esc(a)}</text>'
                   f'<text class="{v}" x="{w-m}" y="{y+i*dy}">{esc(b)}</text>' for i, (a, b) in enumerate(pairs))


def project(title, big, sub, pairs, i, bar=None, w=200, h=150):
    for a, b in pairs:
        assert len(a) + len(b) <= 29, (a, b)
    assert len(sub) <= 32, sub
    b = ""
    if bar:
        b = (f'<rect class="trk" x="14" y="68" width="{w-28}" height="4" rx="2"/>'
             f'<rect class="grow" style="transform-origin:14px 0" x="14" y="68" width="{(w-28)*bar:.1f}" height="4" rx="2" fill="url(#bn)"/>')
    body = (f'<text x="14" y="62" font-size="24" font-weight="800" fill="url(#bn)">{esc(big)}</text>{b}'
            f'<text class="s" x="14" y="88">{esc(sub)}</text>' + rows(pairs, 108, 16, w, 14, "k2", "v2"))
    return card(title, body, w, h, i, 14)


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
    x0 = WW - 120
    legend = (f'<text class="s" x="{x0-6}" y="133" text-anchor="end">Less</text>'
              + "".join(f'<rect class="l{k}" x="{x0+k*13}" y="125" width="10" height="10" rx="2"/>' for k in range(5))
              + f'<text class="s" x="{x0+69}" y="133">More</text>')
    foot = f'<text class="s" x="18" y="133" style="font-size:11px">{num(cal["totalContributions"])} contributions in the last year</text>'
    return card("Contributions", grid + labels + foot + legend, WW, h, 0)


def c_streaks(u, w=270, h=140):
    c, cal = u["contributionsCollection"], u["contributionsCollection"]["contributionCalendar"]
    cur, best = streaks(days_of(u))
    d = lambda n: f"{n} day{'s' * (n != 1)}"
    return card("Activity · 12 months", rows([
        ("Contributions", num(cal["totalContributions"])), ("Commits", num(c["totalCommitContributions"])),
        ("Pull requests", num(c["totalPullRequestContributions"])), ("Current streak", d(cur)), ("Longest streak", d(best))],
        54, 17, w), w, h, 1)


def hero():
    w, h, cy = 830, 124, 62
    lines = ["Running QAOA on real quantum hardware", "Building quantum simulators from scratch in C++",
             "Translating research papers into working code", "Chasing noise instead of averaging it away"]
    tl = "".join(f'<text class="mono line{" f" if i == 0 else ""}" x="30" y="88" font-size="13" style="animation-delay:{i*4}s">'
                 f'<tspan class="acc">›</tspan> {esc(t)}</text>' for i, t in enumerate(lines))
    orbits = "".join(
        f'<g transform="rotate({a} 700 {cy})"><ellipse class="orb" cx="700" cy="{cy}" rx="52" ry="18"/>'
        f'<circle class="el" r="3"><animateMotion dur="{3+a/60:.1f}s" repeatCount="indefinite" '
        f'path="M648,{cy} a52,18 0 1,0 104,0 a52,18 0 1,0 -104,0"/></circle></g>' for a in (0, 60, 120))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><style>{CSS}</style>'
            '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="0" spreadMethod="reflect">'
            '<stop offset="0" style="stop-color:var(--ac)"/><stop offset=".5" style="stop-color:var(--ac2)"/>'
            '<stop offset="1" style="stop-color:var(--ac)"/>'
            '<animate attributeName="x1" values="0;1" dur="5s" repeatCount="indefinite"/>'
            '<animate attributeName="x2" values="1;2" dur="5s" repeatCount="indefinite"/></linearGradient>'
            '<radialGradient id="rg"><stop offset="0" style="stop-color:var(--ac);stop-opacity:.2"/>'
            '<stop offset="1" style="stop-color:var(--ac);stop-opacity:0"/></radialGradient></defs>'
            f'<rect class="bg" x=".5" y=".5" width="{w-1}" height="{h-1}" rx="14"/>'
            f'<circle cx="700" cy="{cy}" r="115" fill="url(#rg)"/><g class="in">'
            '<text x="30" y="44" font-size="28" font-weight="800" letter-spacing=".02em" fill="url(#g)">PRIYANSH BHAVSAR</text>'
            '<text class="sub" x="30" y="64">BS Physics · Quantum Technologies — IIT Jodhpur</text>'
            f'{tl}'
            '<rect x="30" y="98" width="290" height="18" rx="9" fill="none" stroke="var(--bd)"/>'
            '<circle class="live dot" cx="42" cy="107" r="3"/>'
            '<text class="s" x="52" y="110">building Lightning-Lite · surface-code QEC</text></g>'
            f'<circle class="ring" cx="700" cy="{cy}" r="56"/><g class="spin">{orbits}</g>'
            f'<circle class="acc dot" cx="700" cy="{cy}" r="4.5"/>'
            f'<text class="s mono" x="762" y="{cy+4}" style="font-size:12px">|0⟩</text>'
            f'<text class="s mono" x="612" y="{cy+4}" style="font-size:12px">|1⟩</text></svg>')


def stack():
    items = ["Python", "C++20", "Qiskit", "PennyLane", "pyQuil", "Cirq", "QuTiP", "Stim", "NumPy", "SciPy",
             "OpenMP", "CUDA", "SIMD", "pybind11", "PostgreSQL", "PyTorch"]
    seg = " ◆ ".join(items) + " ◆ "
    L = round(len(seg) * 7.2)
    t = lambda x: f'<text class="s mono" x="{x}" y="17" textLength="{L}" lengthAdjust="spacing" style="font-size:12px">{seg}</text>'
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="830" height="26" viewBox="0 0 830 26">'
            f'<style>{CSS}</style><defs><linearGradient id="f"><stop offset="0" stop-color="#000"/>'
            '<stop offset=".08" stop-color="#fff"/><stop offset=".92" stop-color="#fff"/><stop offset="1" stop-color="#000"/>'
            '</linearGradient><mask id="m"><rect width="830" height="26" fill="url(#f)"/></mask></defs>'
            '<rect class="bg" x=".5" y=".5" width="829" height="25" rx="8"/>'
            f'<g mask="url(#m)"><g><animateTransform attributeName="transform" type="translate" from="0 0" to="-{L} 0" '
            f'dur="45s" repeatCount="indefinite"/>{t(0)}{t(L)}</g></g></svg>')


def main():
    u = fetch()
    os.makedirs(OUT, exist_ok=True)
    cards = {
        "hero": hero(), "stack": stack(), "heatmap": c_heatmap(u), "streaks": c_streaks(u),
        "gridiq": project("GridIQ", "96.03%", "ratio on Rigetti Ankaa-3 QPU", [
            ("Q-volution 2026", "Best Overall"), ("Best simulated", "97.31%"), ("vs vanilla SA", "+3.8%")], 2, bar=0.9603),
        "lightning": project("Lightning-Lite", "3.5×", "faster than Qiskit Aer", [
            ("Memory bandwidth", "94%"), ("Validation", "gate-by-gate"), ("Stack", "C++20 · SIMD")], 3),
        # EDIT: put a real Tox21 result in `big` (e.g. "0.82") and `sub` (e.g. "mean ROC-AUC")
        "tox21": project("Tox21 · Hybrid QML", "Hybrid", "quantum-classical toxicity model", [
            ("Dataset", "Tox21"), ("Task", "toxicity prediction"), ("Model", "hybrid quantum")], 4),
        "entangle": project("Entanglement", "99.8%", "fidelity on IBM Quantum", [
            ("Explores", "entanglement"), ("Studies", "noise"), ("Validated on", "IBM hardware")], 5, bar=0.998),
    }
    for name, svg in cards.items():
        with open(f"{OUT}/{name}.svg", "w", encoding="utf-8") as f:
            f.write(svg)
    print("wrote", ", ".join(cards))


if __name__ == "__main__":
    main()
