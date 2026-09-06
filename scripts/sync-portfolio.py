#!/usr/bin/env python3
"""Pull academic content from the academic-portfolio repository into this site.

Generates:
  publications.md                       from profile/publications.md + profile/presentations.md
  assets/cv.pdf                         from cv/cv.pdf

Usage: python3 scripts/sync-portfolio.py [path/to/academic-portfolio]
Never edit the generated files by hand; change the portfolio and re-run.
"""
import datetime
import pathlib
import re
import shutil
import sys

SITE = pathlib.Path(__file__).resolve().parent.parent
PORTFOLIO = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "~/academic-portfolio").expanduser()
TODAY = datetime.date.today().isoformat()

TODO_RE = re.compile(r",?\s*\[TODO:[^\]]*\]")
ARROW_LINK_RE = re.compile(r"\s*→\s*\[[^\]]*\]\([^)]*\)")
INTERNAL_PAREN_RE = re.compile(
    r"\s*\((?:see|paper|paper and poster|related paper):?\s*\[[^\]]*\]\((?:\.\./|[\w./-]+\.md)[^)]*\)\)"
)
RECORDED_RE = re.compile(r"\s*\(acceptance recorded [^)]*\)")
PROGRAM_NOTE_RE = re.compile(r",? per (?:the )?official program[^)]*")
ACCEPTED_RE = re.compile(r"\*{0,2}Accepted; camera-ready submitted\.?\*{0,2}")
INTRO_RE = re.compile(r"^Concise categorized list.*$", re.M)

warnings = []


def clean(text: str, source: str) -> str:
    for todo in TODO_RE.findall(text):
        warnings.append(f"{source}: dropped {todo.strip(', ')}")
    text = TODO_RE.sub("", text)
    text = ARROW_LINK_RE.sub("", text)
    text = INTERNAL_PAREN_RE.sub("", text)
    text = RECORDED_RE.sub("", text)
    text = PROGRAM_NOTE_RE.sub("", text)
    text = ACCEPTED_RE.sub("To appear", text)
    text = re.sub(r"\)\s*\|\s*\[", ") · [", text)  # "|" between links would start a Markdown table
    text = re.sub(r"Earlier version \(titled [^)]*\):", "Earlier version:", text)
    text = INTRO_RE.sub("", text)
    text = re.sub(r",\s*—", " —", text)  # ", —" left behind by a dropped TODO
    text = re.sub(r"[ \t]+$", "", text, flags=re.M)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def read(rel: str) -> str:
    path = PORTFOLIO / rel
    if not path.exists():
        sys.exit(f"missing {path}")
    return path.read_text(encoding="utf-8")


def front_matter(**fields) -> str:
    lines = ["---"]
    for key, value in fields.items():
        lines.append(f'{key}: "{value}"' if isinstance(value, str) and ":" in value else f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines) + "\n\n"


def strip_h1(text: str) -> str:
    return re.sub(r"^# .*\n", "", text, count=1, flags=re.M)


def publications_body() -> str:
    pubs = clean(strip_h1(read("profile/publications.md")), "profile/publications.md")
    pres = clean(strip_h1(read("profile/presentations.md")), "profile/presentations.md")
    pres = re.sub(r"^## ", "### ", pres, flags=re.M)
    return pubs + "\n## Presentations\n\n" + pres


def write(rel: str, text: str) -> None:
    path = SITE / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(f"wrote {rel}")


def main() -> None:
    body = publications_body()
    note = "My name is shown in bold.\n\n"
    write("publications.md", front_matter(
        title="Publications", permalink="/publications/",
        description="Publications and presentations by Ryota Takatsuki.", synced=TODAY) + note + body)

    pdf = PORTFOLIO / "cv/cv.pdf"
    if pdf.exists():
        shutil.copyfile(pdf, SITE / "assets/cv.pdf")
        print("wrote assets/cv.pdf")
    else:
        warnings.append("cv/cv.pdf not found; assets/cv.pdf left unchanged")

    for w in warnings:
        print("warning:", w)


if __name__ == "__main__":
    main()
