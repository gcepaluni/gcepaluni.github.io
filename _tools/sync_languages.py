"""Write the cross-language links into every page and rebuild sitemap.xml.

Run from the repository root after adding or editing a language page:
    python _tools/sync_languages.py

Each language page gets: hreflang alternates, og:locale alternates, the
language items in the side menu, and the switcher above the name. The book
page gets the menu items only. Bump CSS_VERSION when css/site.css changes so
browsers drop their cached copy.
"""
import re
from datetime import date
from pathlib import Path

SITE = "https://gcepaluni.github.io/"
CSS_VERSION = "4"

# (code, hreflang, og locale, label, path from site root)
LANGS = [
    ("en", "en", "en_US", "English", ""),
    ("pt", "pt-BR", "pt_BR", "Português", "pt/"),
    ("es", "es", "es_ES", "Español", "es/"),
    ("fr", "fr", "fr_FR", "Français", "fr/"),
    ("de", "de", "de_DE", "Deutsch", "de/"),
    ("zh", "zh-Hans", "zh_CN", "中文", "zh/"),
]
BOOK = "capitalism-and-development/"

root = Path(__file__).resolve().parent.parent


def rel(from_path, to_path):
    """Relative link between two directory-style site paths."""
    depth = from_path.count("/")
    return "../" * depth + to_path if (depth or to_path) else "./"


def alternates():
    lines = [f'  <link rel="alternate" hreflang="{h}" href="{SITE}{p}">' for _, h, _, _, p in LANGS]
    lines.append(f'  <link rel="alternate" hreflang="x-default" href="{SITE}">')
    return "\n".join(lines) + "\n"


def nav_items(page_path, current):
    return "".join(
        f'        <li class="nav-item"><a class="nav-link" href="{rel(page_path, p)}" hreflang="{h}" lang="{h}">{label}</a></li>\n'
        for code, h, _, label, p in LANGS if code != current
    )


def switcher(page_path, current):
    links = "".join(
        f'<a href="{rel(page_path, p)}" hreflang="{h}" lang="{h}">{label}</a>'
        for code, h, _, label, p in LANGS if code != current
    )
    return f'        <div class="lang-switch">{links}</div>\n'


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def sync_common(s, page_path, current):
    # Menu: drop any existing language items, then add the full set before </ul>.
    s = re.sub(r'        <li class="nav-item"><a class="nav-link" href="[^"#]*" hreflang="[^"]+" lang="[^"]+">[^<]+</a></li>\n', "", s)
    s = s.replace("        <!-- LANG-NAV -->\n", "")
    s = re.sub(r"(      </ul>\n    </div>\n  </nav>)", lambda m: nav_items(page_path, current) + m.group(1), s, count=1)
    s = re.sub(r'href="((?:\.\./)*)css/site\.css(?:\?v=\w+)?"', rf'href="\1css/site.css?v={CSS_VERSION}"', s)
    return s


for code, _, locale, _, path in LANGS:
    f = root / path / "index.html"
    s = f.read_text(encoding="utf-8")
    s = re.sub(r'  <link rel="alternate" hreflang="[^"]+" href="[^"]+">\n', "", s)
    s = s.replace("  <!-- LANG-ALTERNATES -->\n", "")
    s = re.sub(r'(  <link rel="canonical" href="[^"]+">\n)', lambda m: m.group(1) + alternates(), s, count=1)
    s = re.sub(r'  <meta property="og:locale:alternate" content="[^"]+">\n', "", s)
    others = "".join(f'  <meta property="og:locale:alternate" content="{l}">\n' for c, _, l, _, _ in LANGS if c != code)
    s = re.sub(r'(  <meta property="og:locale" content="[^"]+">\n)', lambda m: m.group(1) + others, s, count=1)
    s = re.sub(r'        <div class="lang-switch">.*?</div>\n', "", s)
    s = s.replace("        <!-- LANG-SWITCH -->\n", "")
    s = re.sub(r'(      <div class="w-100">\n)', lambda m: m.group(1) + switcher(path, code), s, count=1)
    write(f, sync_common(s, path, code))

book = root / BOOK / "index.html"
write(book, sync_common(book.read_text(encoding="utf-8"), BOOK, "en"))

today = date.today().isoformat()
links = "".join(f'    <xhtml:link rel="alternate" hreflang="{h}" href="{SITE}{p}"/>\n' for _, h, _, _, p in LANGS)
urls = "".join(f"  <url>\n    <loc>{SITE}{p}</loc>\n    <lastmod>{today}</lastmod>\n{links}  </url>\n" for _, _, _, _, p in LANGS)
urls += f"  <url>\n    <loc>{SITE}{BOOK}</loc>\n    <lastmod>{today}</lastmod>\n  </url>\n"
urls += f"  <url>\n    <loc>{SITE}GabrielCepaluniCV.pdf</loc>\n  </url>\n"
write(root / "sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n'
      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
      '        xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + urls + "</urlset>\n")
print("synced", len(LANGS), "language pages + book page")
