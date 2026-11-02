"""Generates the profile README cards as self-hosted SVGs, in dark and light variants.

Reads public GitHub data only. All data is fetched before any file is written,
so a failed API call leaves the existing cards in place.
"""
import datetime
import json
import os
import textwrap
import urllib.parse
import urllib.request
from collections import Counter
from xml.sax.saxutils import escape

USER = "edmontdants"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "cards")
FONT = "-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif"
MARKUP_LANGUAGES = {"HTML", "CSS", "SCSS"}

THEMES = {
    "dark": {"bg": "#0d1117", "line": "#30363d", "text": "#e6edf3", "muted": "#9198a1",
             "accent": "#4493f8", "chip": "#21262d"},
    "light": {"bg": "#ffffff", "line": "#d1d9e0", "text": "#1f2328", "muted": "#59636e",
              "accent": "#0969da", "chip": "#f6f8fa"},
}
LANGUAGE_COLORS = {"C#": "#178600", "Python": "#3572a5", "TypeScript": "#3178c6",
                   "JavaScript": "#f1e05a", "Jupyter Notebook": "#da5b0b"}
FALLBACK_COLOR = "#8b949e"

MAIN_LANGUAGES = ["C#", "TypeScript"]
MAIN_STACK = [".NET", "C#", "ASP.NET Core", "Angular", "TypeScript"]
OTHER_STACK = ["EF Core", "Python", "TensorFlow"]
SUMMARY = [
    ("Main stack", ".NET and Angular: C#, ASP.NET Core APIs, TypeScript front ends"),
    ("Architecture", "Clean Architecture, CQRS, MediatR, EF Core"),
    ("Research", "Learned image and video compression, computer vision"),
    ("Background", "ACPC 2018, ITI .NET full-stack track, Samsung Innovation Campus AI"),
]
PROJECTS = {
    "student-progress": ("Student Progress Tracker",
                         "Modular API that tracks K–12 student performance, with analytics and CSV export.",
                         "C#", "Clean Architecture, CQRS, MediatR"),
    "car4egar": ("Car4Egar",
                 "Car rental platform with an ASP.NET Core API and Angular front end. Team graduation project at ITI.",
                 "C#, TypeScript", "ASP.NET Core, Angular 15"),
    "image-compression": ("Learned Image Compression",
                          "Encoder and decoder trained with an adversarial loss, so decoded images stay sharper.",
                          "Python", "GANs"),
    "srgan": ("Single-Image Super-Resolution",
              "Generative model that upscales low-resolution images. Samsung Innovation Campus final project.",
              "Python", "TensorFlow, SRGAN"),
}


def api(path):
    request = urllib.request.Request(f"https://api.github.com/{path}", headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
    })
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def fetch_stats():
    user = api(f"users/{USER}")
    query = urllib.parse.quote(f"user:{USER} fork:false is:public")
    result = api(f"search/repositories?q={query}&per_page=100")
    repos = [r for r in result["items"] if r["name"] != USER]
    languages = Counter(r["language"] for r in repos
                        if r["language"] and r["language"] not in MARKUP_LANGUAGES)
    forks = urllib.parse.quote(f"user:{USER} fork:only is:public")
    return {
        "repos": len(repos),
        "forks": api(f"search/repositories?q={forks}&per_page=1")["total_count"],
        "followers": user["followers"],
        "since": user["created_at"][:4],
        "languages": sorted(languages.most_common(4), key=lambda item: item[0] not in MAIN_LANGUAGES),
        "updated": datetime.date.today().strftime("%d %b %Y"),
    }


def text(x, y, value, fill, size=13, weight=400, anchor="start"):
    return (f'<text x="{x}" y="{y}" fill="{fill}" font-size="{size}" font-weight="{weight}" '
            f'text-anchor="{anchor}">{escape(value)}</text>')


def card(width, height, title, theme, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}" '
            f'font-family="{FONT}">'
            f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="8" '
            f'fill="{theme["bg"]}" stroke="{theme["line"]}"/>'
            f'{"".join(body)}</svg>\n')


def summary_card(t):
    body = [f'<rect x="1" y="24" width="4" height="56" rx="2" fill="{t["accent"]}"/>',
            text(28, 50, "Moaaz I. Alomary", t["text"], 26, 600),
            text(28, 76, "Full-stack .NET and Angular engineer, with a research interest in AI", t["accent"], 15, 500)]
    y = 112
    for label, value in SUMMARY:
        body += [text(28, y, label, t["muted"], 13, 600), text(128, y, value, t["text"], 14)]
        y += 26
    x = 28
    for name in MAIN_STACK + OTHER_STACK:
        main = name in MAIN_STACK
        width = round(len(name) * 7.2) + 22
        body += [f'<rect x="{x}" y="{y - 6}" width="{width}" height="26" rx="13" '
                 f'fill="{t["chip"]}" stroke="{t["accent"] if main else t["line"]}"/>',
                 text(x + width / 2, y + 11, name, t["accent"] if main else t["muted"], 12,
                      600 if main else 500, "middle")]
        x += width + 8
    return card(860, 248, "Moaaz I. Alomary, profile summary", t, body)


def stats_card(t, stats):
    rows = [("Public non-fork repositories", stats["repos"]),
            ("Public forks", f"{stats['forks']:,}"),
            ("Followers", stats["followers"]),
            ("On GitHub since", stats["since"])]
    body = [text(24, 38, "GitHub stats", t["accent"], 16, 600)]
    y = 72
    for label, value in rows:
        body += [text(24, y, label, t["muted"], 14), text(401, y, str(value), t["text"], 14, 600, "end")]
        y += 28
    body.append(text(24, 186, f"Updated {stats['updated']}", t["muted"], 11))
    return card(425, 200, "GitHub stats", t, body)


def languages_card(t, stats):
    languages = stats["languages"]
    total = sum(count for _, count in languages)
    body = [text(24, 38, "Main languages", t["accent"], 16, 600)]
    x = 24.0
    for name, count in languages:
        width = 377 * count / total
        body.append(f'<rect x="{x:.1f}" y="54" width="{max(width - 2, 1):.1f}" height="8" rx="4" '
                    f'fill="{LANGUAGE_COLORS.get(name, FALLBACK_COLOR)}"/>')
        x += width
    y = 88
    for name, count in languages:
        unit = "repository" if count == 1 else "repositories"
        body += [f'<circle cx="30" cy="{y - 5}" r="6" fill="{LANGUAGE_COLORS.get(name, FALLBACK_COLOR)}"/>',
                 text(44, y, name, t["text"], 14),
                 text(401, y, f"{count} {unit}", t["muted"], 13, 400, "end")]
        y += 24
    body.append(text(24, 186, "By primary language of public non-fork repositories", t["muted"], 11))
    return card(425, 200, "Main languages", t, body)


def project_card(t, title, description, language, stack):
    body = [text(24, 38, title, t["accent"], 16, 600)]
    y = 66
    for line in textwrap.wrap(description, 54)[:3]:
        body.append(text(24, y, line, t["text"], 13))
        y += 20
    primary = language.split(",")[0]
    body += [f'<circle cx="30" cy="131" r="6" fill="{LANGUAGE_COLORS.get(primary, FALLBACK_COLOR)}"/>',
             text(44, 136, language, t["muted"], 12),
             text(401, 136, stack, t["muted"], 12, 400, "end")]
    return card(425, 156, title, t, body)


def main():
    stats = fetch_stats()
    os.makedirs(OUT, exist_ok=True)
    for mode, theme in THEMES.items():
        cards = {"summary": summary_card(theme), "stats": stats_card(theme, stats),
                 "languages": languages_card(theme, stats)}
        for name, project in PROJECTS.items():
            cards[name] = project_card(theme, *project)
        for name, svg in cards.items():
            with open(os.path.join(OUT, f"{name}-{mode}.svg"), "w", encoding="utf-8", newline="\n") as f:
                f.write(svg)
    print(stats)


if __name__ == "__main__":
    main()
