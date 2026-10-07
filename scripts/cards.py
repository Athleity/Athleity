#!/usr/bin/env python3
"""Profile cards (SVG) from the GitHub API. Standard library only.
Usage: GH_TOKEN=... GH_USER=Athleity python3 scripts/cards.py   (add --demo for sample data)"""
import datetime, html, json, os, sys, urllib.request

USER = os.environ.get("GH_USER", "Athleity")
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
DEMO = "--demo" in sys.argv
OUT, MONTHS = "cards", "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
CSS = f"""
:root{{--bg:#fff;--bd:#d1d9e0;--fg:#1f2328;--mu:#59636e;--ac:#1a7f37;--ac2:#2da44e}}
@media (prefers-color-scheme:dark){{:root{{--bg:#0d1117;--bd:#30363d;--fg:#e6edf3;--mu:#8b949e;--ac:#3fb950;--ac2:#56d364}}}}
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
.l0{{fill:var(--bd);fill-opacity:.55}}
.l1{{fill:var(--ac);fill-opacity:.3}}
.l2{{fill:var(--ac);fill-opacity:.5}}
.l3{{fill:var(--ac);fill-opacity:.75}}
.l4{{fill:var(--ac)}}
.live{{fill:var(--ac2)}}
.in{{animation:rise .6s ease-out both}}
.grow{{transform-box:fill-box;transform-origin:left;animation:sweep 1.2s .4s ease-out both}}
.cell{{animation:pop .5s ease-out both}}
.now,.dot{{animation:pulse 1.6s ease-in-out infinite}}
.line{{opacity:0;animation:cycle 16s infinite}}
@keyframes rise{{from{{opacity:0;transform:translateY(6px)}}to{{opacity:1;transform:none}}}}
@keyframes sweep{{from{{transform:scaleX(0)}}to{{transform:scaleX(1)}}}}
@keyframes pop{{from{{opacity:0}}to{{opacity:1}}}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.3}}}}
@keyframes cycle{{0%{{opacity:0}}4%,22%{{opacity:1}}26%,100%{{opacity:0}}}}
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


def card(title, body, w, h, i=0, m=18):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><style>{CSS}</style>'
            f'<rect class="bg" x=".5" y=".5" width="{w-1}" height="{h-1}" rx="10"/>'
            f'<g class="in" style="animation-delay:{i*0.1:.2f}s">'
            f'<rect class="acc" x="{m}" y="16" width="7" height="7" rx="1.5"/>'
            f'<text class="t" x="{m+13}" y="24">{esc(title.upper())}</text>{body}</g></svg>')


def rows(pairs, y, dy, w, m=18, k="k", v="v"):
    return "".join(f'<text class="{k}" x="{m}" y="{y+i*dy}">{esc(a)}</text>'
                   f'<text class="{v}" x="{w-m}" y="{y+i*dy}">{esc(b)}</text>' for i, (a, b) in enumerate(pairs))


def project(title, big, sub, pairs, i, bar=None, w=200, h=150):
    for a, b in pairs:
        assert len(a) + len(b) <= 29, (a, b)
    assert len(sub) <= 34, sub
    b = ""
    if bar:
        b = (f'<rect class="trk" x="14" y="68" width="{w-28}" height="3" rx="1.5"/>'
             f'<rect class="grow acc" x="14" y="68" width="{(w-28)*bar:.1f}" height="3" rx="1.5"/>')
    body = (f'<text class="big" x="14" y="60">{esc(big)}</text>{b}'
            f'<text class="s" x="14" y="86">{esc(sub)}</text>' + rows(pairs, 107, 15, w, 14, "k2", "v2"))
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
    w, h = 830, 112
    lines = ["QAOA on Rigetti Ankaa-3 · Best Overall, Q-volution 2026",
             "Lightning-Lite: C++20 statevector simulator, 3.5x vs Qiskit Aer",
             "Now: surface-code quantum error correction",
             "Translating papers into working code"]
    tl = "".join(f'<text class="mono line{" f" if i == 0 else ""}" x="30" y="84" font-size="13" fill="var(--fg)" '
                 f'style="animation-delay:{i*4}s"><tspan class="acc">$</tspan> {esc(t)}</text>' for i, t in enumerate(lines))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><style>{CSS}</style>'
            f'<rect class="bg" x=".5" y=".5" width="{w-1}" height="{h-1}" rx="12"/>'
            f'<rect class="acc" x="0.5" y="22" width="4" height="40" rx="2"/><g class="in">'
            '<text x="30" y="46" font-size="28" font-weight="800" letter-spacing=".01em" fill="var(--fg)">Priyansh Bhavsar</text>'
            '<text class="sub" x="30" y="66">BS Physics · Quantum Technologies, IIT Jodhpur</text>'
            f'{tl}</g>'
            '<rect x="600" y="22" width="200" height="22" rx="11" fill="none" stroke="var(--bd)"/>'
            '<circle class="live dot" cx="614" cy="33" r="3.5"/>'
            '<text class="s" x="624" y="36">open to quantum research</text></svg>')


def stack():
    items = ["Python", "C++20", "Qiskit", "PennyLane", "pyQuil", "Cirq", "QuTiP", "Stim", "NumPy", "SciPy",
             "OpenMP", "CUDA", "SIMD", "pybind11", "PostgreSQL", "PyTorch"]
    seg = " / ".join(items) + " / "
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
    print("wrote", ", ".join(cards))


if __name__ == "__main__":
    main()
