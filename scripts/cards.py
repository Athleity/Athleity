#!/usr/bin/env python3
"""Generate profile cards (SVG) from the GitHub API. Standard library only.
Usage: GH_TOKEN=... GH_USER=Athleity python3 scripts/cards.py   (add --demo for sample data)"""
import collections, html, json, os, sys, urllib.request

USER = os.environ.get("GH_USER", "Athleity")
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
DEMO = "--demo" in sys.argv
W, H, OUT = 270, 190, "cards"
FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
CSS = f"""
:root{{--bg:#fff;--bd:#d0d7de;--fg:#1f2328;--mu:#656d76;--ac:#0969da}}
@media (prefers-color-scheme:dark){{:root{{--bg:#0d1117;--bd:#30363d;--fg:#e6edf3;--mu:#8b949e;--ac:#58a6ff}}}}
text{{font-family:{FONT}}}
.bg{{fill:var(--bg);stroke:var(--bd)}}
.trk{{fill:var(--bd)}}
.bar{{fill:var(--ac);opacity:.85}}
.t{{font-size:11px;font-weight:600;letter-spacing:.09em;fill:var(--ac)}}
.k{{font-size:12px;fill:var(--mu)}}
.v{{font-size:12px;font-weight:600;fill:var(--fg);text-anchor:end}}
.big{{font-size:26px;font-weight:700;fill:var(--fg)}}
.s{{font-size:11px;fill:var(--mu)}}
"""

QUERY = """
query($login:String!){user(login:$login){
 createdAt followers{totalCount} following{totalCount}
 repositories(ownerAffiliations:OWNER,isFork:false,first:100,orderBy:{field:STARGAZERS,direction:DESC}){
  totalCount nodes{stargazerCount languages(first:6,orderBy:{field:SIZE,direction:DESC}){edges{size node{name color}}}}}
 contributionsCollection{
  totalCommitContributions totalPullRequestContributions totalIssueContributions totalPullRequestReviewContributions
  contributionCalendar{totalContributions weeks{contributionDays{contributionCount date}}}}
}}"""

DEMO_DATA = {
    "createdAt": "2022-08-01T00:00:00Z", "followers": {"totalCount": 12}, "following": {"totalCount": 30},
    "repositories": {"totalCount": 9, "nodes": [{"stargazerCount": 4, "languages": {"edges": [
        {"size": 9000, "node": {"name": "Python", "color": "#3572A5"}},
        {"size": 6000, "node": {"name": "C++", "color": "#f34b7d"}}]}}]},
    "contributionsCollection": {
        "totalCommitContributions": 120, "totalPullRequestContributions": 6,
        "totalIssueContributions": 2, "totalPullRequestReviewContributions": 1,
        "contributionCalendar": {"totalContributions": 129, "weeks": [{"contributionDays": [
            {"date": f"2026-0{m}-01", "contributionCount": m * 3} for m in range(1, 10)]}]}},
}

esc = lambda s: html.escape(str(s))
num = lambda n: f"{n:,}"


def fetch():
    if DEMO:
        return DEMO_DATA
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json", "User-Agent": "profile-cards"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if "errors" in data:
        sys.exit(json.dumps(data["errors"]))
    return data["data"]["user"]


def card(title, body, h=H):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}">'
            f'<style>{CSS}</style>'
            f'<rect class="bg" x=".5" y=".5" width="{W-1}" height="{h-1}" rx="12"/>'
            f'<text class="t" x="18" y="30">{esc(title.upper())}</text>{body}</svg>')


def rows(pairs, y=62, dy=22):
    return "".join(
        f'<text class="k" x="18" y="{y+i*dy}">{esc(k)}</text>'
        f'<text class="v" x="{W-18}" y="{y+i*dy}">{esc(v)}</text>' for i, (k, v) in enumerate(pairs))


def stat(big, sub, pairs):
    return (f'<text class="big" x="18" y="68">{esc(big)}</text>'
            f'<text class="s" x="18" y="86">{esc(sub)}</text>' + rows(pairs, y=124))


def c_general(u):
    stars = sum(r["stargazerCount"] for r in u["repositories"]["nodes"])
    return card(f"GitHub · @{USER}", rows([
        ("Followers", num(u["followers"]["totalCount"])),
        ("Following", num(u["following"]["totalCount"])),
        ("Public repositories", num(u["repositories"]["totalCount"])),
        ("Stars earned", num(stars)),
        ("Member since", u["createdAt"][:4])]))


def c_activity(u):
    c = u["contributionsCollection"]
    months = collections.OrderedDict()
    for wk in c["contributionCalendar"]["weeks"]:
        for d in wk["contributionDays"]:
            months[d["date"][:7]] = months.get(d["date"][:7], 0) + d["contributionCount"]
    vals = list(months.values())[-12:] or [0]
    mx, gap = max(vals) or 1, 4
    bw = (W - 36 - gap * (len(vals) - 1)) / len(vals)
    bars = "".join(
        f'<rect class="bar" x="{18+i*(bw+gap):.1f}" y="{176-max(2,30*v/mx):.1f}" '
        f'width="{bw:.1f}" height="{max(2,30*v/mx):.1f}" rx="2"/>' for i, v in enumerate(vals))
    return card("Activity · 12 months", rows([
        ("Commits", num(c["totalCommitContributions"])),
        ("Pull requests", num(c["totalPullRequestContributions"])),
        ("Issues", num(c["totalIssueContributions"])),
        ("Reviews", num(c["totalPullRequestReviewContributions"]))]) + bars)


def c_languages(u):
    tot, col = collections.Counter(), {}
    for r in u["repositories"]["nodes"]:
        for e in r["languages"]["edges"]:
            tot[e["node"]["name"]] += e["size"]
            col[e["node"]["name"]] = e["node"]["color"] or "#8b949e"
    s, inner, x = sum(tot.values()) or 1, W - 36, 18.0
    top, bars, legend = tot.most_common(5), "", ""
    for n, v in top:
        w = inner * v / s
        bars += f'<rect x="{x:.1f}" y="46" width="{w:.1f}" height="8" fill="{col[n]}"/>'
        x += w
    for i, (n, v) in enumerate(top):
        y = 82 + i * 22
        legend += (f'<circle cx="23" cy="{y-4}" r="4" fill="{col[n]}"/><text class="k" x="34" y="{y}">{esc(n)}</text>'
                   f'<text class="v" x="{W-18}" y="{y}">{v/s*100:.1f}%</text>')
    return card("Languages",
                f'<clipPath id="c"><rect x="18" y="46" width="{inner}" height="8" rx="4"/></clipPath>'
                f'<rect class="trk" x="18" y="46" width="{inner}" height="8" rx="4"/>'
                f'<g clip-path="url(#c)">{bars}</g>{legend}')


def main():
    u = fetch()
    os.makedirs(OUT, exist_ok=True)
    cards = {
        "general": c_general(u),
        "activity": c_activity(u),
        "languages": c_languages(u),
        "qaoa": card("Power Grid QAOA", stat("97.31%", "approximation ratio · Rigetti Ankaa-3", [
            ("Q-volution 2026", "Best Overall"), ("Beat", "15 countries"), ("Optimizer iterations", "−50%")])),
        "simulator": card("Lightning-Lite", stat("3.5×", "faster than Qiskit Aer · C++20, SIMD", [
            ("Memory bandwidth", "94%"), ("IBM pipeline", "156 qubits"), ("Measurement fidelity", "99.8%")])),
        "astro": card("Nuclear Astrophysics", stat("19", "notebooks · S-factor analysis", [
            ("Reactions", "5 (α,n)"), ("Cross-sections", "EXFOR"), ("Presented", "IAPT · 12th NSS")])),
    }
    for name, svg in cards.items():
        with open(f"{OUT}/{name}.svg", "w", encoding="utf-8") as f:
            f.write(svg)
    print("wrote", ", ".join(cards))


if __name__ == "__main__":
    main()
