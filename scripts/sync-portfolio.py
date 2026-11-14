#!/usr/bin/env python3
"""Pull academic content from the academic-portfolio repository into this site.

Generates:
  publications.md                       from profile/publications.md + profile/presentations.md
  _papers/<slug>.md                     one page per selected publication (see SELECTED), from
                                        profile/publications.md, profile/presentations.md and the
                                        publication folder's README and citation.bib
  assets/cv.pdf                         from cv/cv.pdf

Usage: python3 scripts/sync-portfolio.py [path/to/academic-portfolio]
Never edit the generated files by hand; change the portfolio (or SELECTED) and re-run.
"""
import datetime
import json
import pathlib
import re
import shutil
import sys

SITE = pathlib.Path(__file__).resolve().parent.parent
PORTFOLIO = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "~/Research/academic-portfolio").expanduser()
TODAY = datetime.date.today().isoformat()

# Selected publications, in the order of the home page's list. Each gets a page at
# /papers/<slug>/. Facts (title, authors, venue, links, TL;DR, summary, key findings,
# related talks) come from the portfolio. Chosen here are only the short venue label
# for the home page, which README link is the official page (the title on the home
# page links there), and the media: the papers' own figures and the explainer video,
# with their sources noted next to each.
SELECTED = [
    {
        "folder": "2026-bistable-images",
        "slug": "mllm-bistable-images",
        "venue": "*EMNLP 2026*",
        "official": {"label": "ACL Anthology", "name": "ACL Anthology"},
        "thumb": "/assets/img/papers/bistable-images-thumb.jpg",
        # Figure 1, from ~/Research/vlm-bistable-images/paper/figs/main_fig.png
        "figure": {
            "src": "/assets/img/papers/bistable-images-fig1.png", "width": 1000, "height": 1167,
            "alt": "Figure 1 of the paper: overview of the framework.",
            "caption": "Figure 1 of the paper. Overview of our framework. We test whether MLLM reports on the "
                       "duck–rabbit show *modulability* and *exclusivity*, and then analyze how these behaviors "
                       "are implemented along the vision-to-language pipeline.",
        },
        # ~/Research/vlm-bistable-images/video_x_emnlp2026/out/explainer_v10.mp4; the poster is its title card at 24 s.
        "video": {
            "src": "/assets/video/bistable-images-explainer.mp4",
            "poster": "/assets/img/papers/bistable-images-video.jpg",
            "width": 1280, "height": 720, "length": "2:11", "note": "No sound",
        },
    },
    {
        "folder": "2025-meta-representations",
        "slug": "meta-representations",
        "venue": "*Neuroscience of Consciousness*, 2025",
        "official": {"label": "DOI", "name": "Neuroscience of Consciousness"},
        "thumb": "/assets/img/papers/meta-representations-thumb.jpg",
        # Figure 2 (Figure 1 exists only as three small panels). MinerU crop from
        # ~/Research/literature/extracted/kanai_2025_meta_representations_processes/images/0cb43897….jpg
        "figure": {
            "src": "/assets/img/papers/meta-representations-fig2.jpg", "width": 1140, "height": 510,
            "alt": "Figure 2 of the paper: construction of the meta-autoencoders.",
            "caption": "Figure 2 of the paper. Overall structure of the construction of meta-autoencoders.",
        },
    },
    {
        "folder": "2025-diffusion-steering-lens",
        "slug": "diffusion-steering-lens",
        "venue": "*Workshop on Mechanistic Interpretability for Vision, CVPR 2025*",
        # The DOI (IEEE Xplore), whose pages (4819–4824) match the citation and BibTeX; the CVF open-access
        # page numbers the paper 4858–4863. The free full text is on arXiv, linked on the paper's page.
        "official": {"label": "DOI", "name": "IEEE Xplore"},
        "thumb": "/assets/img/papers/diffusion-steering-lens-thumb.jpg",
        # Figure 1. MinerU crop from
        # ~/Research/literature/extracted/takatsuki_2025_diffusion_steering_lens/images/af4503b1….jpg
        "figure": {
            "src": "/assets/img/papers/diffusion-steering-lens-fig1.jpg", "width": 526, "height": 537,
            "alt": "Figure 1 of the paper: schematic of the Diffusion Steering Lens.",
            "caption": "Figure 1 of the paper. Schematic of Diffusion Steering Lens. Visualizing the direct "
                       "contribution of *h*<sub>*m*</sub> at layer *n*.",
        },
    },
    {
        "folder": "2026-in-context-neurofeedback",
        "slug": "in-context-neurofeedback",
        "venue": "*Findings of EMNLP 2026*",
        "official": {"label": "ACL Anthology", "name": "ACL Anthology"},
        "thumb": "/assets/img/papers/in-context-neurofeedback-thumb.jpg",
        # Figure 1. MinerU crop from
        # ~/Research/literature/extracted/aoki_2026_context_neurofeedback_llms_control/images/d177c1ca….jpg
        "figure": {
            "src": "/assets/img/papers/in-context-neurofeedback-fig1.jpg", "width": 1079, "height": 568,
            "alt": "Figure 1 of the paper: the six steps of the in-context neurofeedback procedure.",
            "caption": "Figure 1 of the paper. Overview of our in-context neurofeedback (ICN) procedure.",
        },
    },
]

# README link labels shown as icons on a paper's page, besides the official page.
LINK_KINDS = {"arxiv": "arxiv", "code": "code", "code and data": "code", "x thread": "thread"}
# Section headings of profile/presentations.md, as shown on a paper's page.
PRESENTATION_KINDS = {"Oral presentations": "Oral presentation", "Posters": "Poster", "Invited talks": "Invited talk"}

TODO_RE = re.compile(r",?\s*\[TODO:[^\]]*\]")
ARROW_LINK_RE = re.compile(r"\s*→\s*\[[^\]]*\]\([^)]*\)")
INTERNAL_PAREN_RE = re.compile(
    r"\s*\((?:see|paper|paper and poster|related paper):?\s*\[[^\]]*\]\((?:\.\./|[\w./-]+\.md)[^)]*\)\)"
)
RECORDED_RE = re.compile(r"\s*\(acceptance recorded [^)]*\)")
PROGRAM_NOTE_RE = re.compile(r",? per (?:the )?official program[^)]*")
ACCEPTED_RE = re.compile(r"\*{0,2}Accepted; camera-ready submitted\.?\*{0,2}")
INTRO_RE = re.compile(r"^Concise categorized list.*$", re.M)
FIELD_RE = re.compile(r"^- \*\*(?P<name>[^*]+):\*\*\s*(?P<value>.*)$", re.M)
LINK_RE = re.compile(r"\s*(?P<label>[^:|]+?)(?:\s*\([^)]*\))?:\s*(?P<url>https?://[^\s|]+)")
TRAILING_LINKS_RE = re.compile(r"(?:\s*(?:·\s*)?\[[^\]]+\]\([^)]+\))+\s*$")
CORRESPONDING_RE = re.compile(r"\\\*\s*\(corresponding author\)")
EARLIER_RE = re.compile(r"\s*Earlier version:\s*(?P<rest>.*)$")

warnings = []


def compact_bibtex(text: str) -> str:
    """One line per field. The ACL Anthology breaks author and editor lists over several lines;
    join them (whitespace only: the fields and their values stay exactly as the source gives them)."""
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if lines and stripped and not re.match(r"(@|\}|[A-Za-z]+\s*=)", stripped):
            lines[-1] = lines[-1].rstrip() + " " + stripped
        else:
            lines.append(line.rstrip())
    # Collapse the double spaces the Anthology puts before "and", leaving the indentation alone.
    return "\n".join(re.sub(r"(?<=\S) {2,}(?=\S)", " ", line) for line in lines)


def mark_corresponding(text: str) -> str:
    """The site marks the corresponding author with * after the name (legend under the heading)."""
    return CORRESPONDING_RE.sub(lambda _: "\\*", text)


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
    pubs = mark_corresponding(clean(strip_h1(read("profile/publications.md")), "profile/publications.md"))
    pres = mark_corresponding(clean(strip_h1(read("profile/presentations.md")), "profile/presentations.md"))
    pres = re.sub(r"^## ", "### ", pres, flags=re.M)
    return pubs + "\n## Presentations\n\n" + pres


def write(rel: str, text: str) -> None:
    path = SITE / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(f"wrote {rel}")


# --- Paper pages -----------------------------------------------------------------

def yaml_scalar(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    return json.dumps(str(value), ensure_ascii=False)  # a JSON string is a valid YAML double-quoted scalar


def yaml_lines(data: dict, indent: int = 0) -> list:
    pad = " " * indent
    lines = []
    for key, value in data.items():
        if value is None or value == "" or value == [] or value == {}:
            continue
        if isinstance(value, dict):
            lines.append(f"{pad}{key}:")
            lines += yaml_lines(value, indent + 2)
        elif isinstance(value, list):
            lines.append(f"{pad}{key}:")
            for item in value:
                if isinstance(item, dict):
                    sub = yaml_lines(item, indent + 4)
                    sub[0] = f"{pad}  - " + sub[0].lstrip()
                    lines += sub
                else:
                    lines.append(f"{pad}  - {yaml_scalar(item)}")
        else:
            lines.append(f"{pad}{key}: {yaml_scalar(value)}")
    return lines


def readme_section(text: str, name: str) -> str:
    m = re.search(rf"^## {re.escape(name)}[ \t]*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    return m.group(1).strip() if m else ""


def citation_line(folder: str) -> str:
    """The publication's line in profile/publications.md, cleaned, without its links."""
    for line in read("profile/publications.md").splitlines():
        if f"(../publications/{folder}/)" in line:
            line = clean(line, "profile/publications.md").strip()
            line = re.sub(r"^- ", "", line)
            return TRAILING_LINKS_RE.sub("", line).strip()
    sys.exit(f"profile/publications.md has no line for publications/{folder}")


def presentation_lines(folders: list) -> list:
    """Lines of profile/presentations.md for the given presentation folders, with their kind."""
    out = []
    kind = ""
    lines = read("profile/presentations.md").splitlines()
    for folder in folders:
        for line in lines:
            if line.startswith("## "):
                kind = PRESENTATION_KINDS.get(line[3:].strip(), line[3:].strip())
            elif f"(../presentations/{folder}/)" in line:
                if "[TODO" in line:
                    warnings.append(f"profile/presentations.md: left {folder} off its paper's page (open [TODO])")
                    break
                text = re.sub(r"^- ", "", clean(line, "profile/presentations.md").strip())
                out.append(f"{kind}: {TRAILING_LINKS_RE.sub('', text).strip()}")
                break
    return out


def paper_page(entry: dict, order: int) -> None:
    folder, slug = entry["folder"], entry["slug"]
    source = f"publications/{folder}/README.md"
    readme = read(source)
    title = re.match(r"# (.+)", readme).group(1).strip()
    head = readme.split("\n## ", 1)[0]
    fields = {m["name"].strip(): m["value"].strip() for m in FIELD_RE.finditer(head)}

    links = []
    for m in LINK_RE.finditer(fields.get("Links", "")):
        links.append((m["label"].strip(), m["url"].rstrip(".,;")))
    official = next((url for label, url in links if label.lower() == entry["official"]["label"].lower()), None)
    if not official:
        sys.exit(f"{source}: no '{entry['official']['label']}' link for the official page")
    icons = [{"kind": LINK_KINDS[label.lower()], "url": url} for label, url in links if label.lower() in LINK_KINDS]

    cite = citation_line(folder)
    m = re.match(r"(?P<authors>.+?) \((?P<year>\d{4})\)\. (?P<rest>.+)$", cite)
    if not m:
        sys.exit(f"profile/publications.md: cannot split the line for {folder}: {cite}")
    rest = m["rest"]
    if rest.startswith(title):
        venue_full = rest[len(title):].lstrip(".").strip()
    else:
        warnings.append(f"{folder}: the README title and the citation differ; the page shows the whole citation tail")
        venue_full = rest
    # An earlier version (the ICN workshop spotlight) is shown on its own line under the short venue,
    # by its venue name only; the citation under "How to cite" is the paper itself.
    venue_extra = ""
    earlier = EARLIER_RE.search(venue_full)
    if earlier:
        name = re.search(r"\*([^*]+)\*", earlier["rest"])
        if name:
            venue_extra = f"*{name.group(1)}*" + (" (spotlight)" if "spotlight" in earlier["rest"].lower() else "")
        venue_full = venue_full[:earlier.start()].strip()
    # "How to cite": one plain paragraph, without bold or the corresponding-author mark.
    authors_plain = re.sub(r"\*\*(.+?)\*\*", r"\1", CORRESPONDING_RE.sub("", m["authors"]))
    bibliography = f"{authors_plain} ({m['year']}). {title}{'' if title[-1] in '?!.' else '.'} {venue_full}"

    bib = PORTFOLIO / "publications" / folder / "citation.bib"
    bibtex = ""
    if bib.exists():
        bibtex = compact_bibtex("\n".join(line for line in bib.read_text(encoding="utf-8").splitlines()
                                          if not line.lstrip().startswith("%")).strip())
    else:
        warnings.append(f"publications/{folder}/citation.bib not found; the page has no BibTeX")

    summary = readme_section(readme, "Summary")
    if "[TODO" in summary:
        summary = ""
    findings = [b[2:].strip() for b in readme_section(readme, "Main contributions").splitlines()
                if b.startswith("- ") and "[TODO" not in b]
    talks = presentation_lines(re.findall(r"presentations/([\w-]+)/", readme_section(readme, "Related presentations")))
    # Talks by others, media and teaching that feature the paper (README "## Elsewhere").
    elsewhere = [b[2:].strip() for b in readme_section(readme, "Elsewhere").splitlines()
                 if b.startswith("- ") and "[TODO" not in b]

    tldr = fields.get("TL;DR (website)", "")
    if not tldr or "[TODO" in tldr:
        warnings.append(f"{source}: no TL;DR (website)")
        tldr = ""

    video = dict(entry["video"]) if entry.get("video") else None
    if video:
        path = SITE / video["src"].lstrip("/")
        if path.exists():
            video["size"] = f"{path.stat().st_size / 1e6:.1f} MB"
        else:
            warnings.append(f"{video['src']} not found")

    data = {
        "title": title,
        "description": tldr,
        "order": order,
        "year": int(m["year"]),
        "authors": mark_corresponding(m["authors"]),
        "corresponding": bool(CORRESPONDING_RE.search(m["authors"])),
        "venue": entry["venue"],
        "venue_extra": venue_extra,
        "official": {"url": official, "name": entry["official"]["name"]},
        "links": icons,
        "tldr": tldr,
        "thumb": entry["thumb"],
        "figure": entry.get("figure"),
        "summary": summary,
        "video": video,
        "findings": findings,
        "presentations": talks,
        "elsewhere": elsewhere,
        "bibliography": bibliography,
        "bibtex": bibtex,
    }
    note = f"# GENERATED by scripts/sync-portfolio.py from academic-portfolio/{source} — do not edit by hand."
    write(f"_papers/{slug}.md", "---\n" + note + "\n" + "\n".join(yaml_lines(data)) + "\n---\n")


def main() -> None:
    body = publications_body()
    # Jekyll expands the Liquid tag, so the URL stays in _config.yml only.
    # A small legend under the heading (as on the home page), then the Scholar link.
    note = ('<p class="heading-note"><strong>Bold</strong>: my name · *: corresponding author</p>\n\n'
            "See also my [Google Scholar profile]({{ site.links.scholar }}).\n\n")
    write("publications.md", front_matter(
        title="Publications", permalink="/publications/",
        description="Publications and presentations by Ryota Takatsuki.", synced=TODAY) + note + body)

    for order, entry in enumerate(SELECTED, start=1):
        paper_page(entry, order)
    stale = {p.stem for p in (SITE / "_papers").glob("*.md")} - {e["slug"] for e in SELECTED}
    for slug in sorted(stale):
        warnings.append(f"_papers/{slug}.md is not in SELECTED; delete it if it should no longer have a page")

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
