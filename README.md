# rtakatsky.github.io

Personal academic site of Ryota Takatsuki, served at <https://rtakatsky.github.io>.

Plain Jekyll, built natively by GitHub Pages from the `master` branch. No custom plugins, no JavaScript, no third-party assets, no CI.

## Layout

```
index.md                     Home page, written by hand (the selected publications come from _papers/)
_data/news.yml               News items, newest first
publications.md              GENERATED from academic-portfolio — do not edit
_papers/<slug>.md            GENERATED: one page per selected publication, at /papers/<slug>/ — do not edit
assets/cv.pdf                COPIED from academic-portfolio by the sync script
_layouts/default.html        The page template
_layouts/paper.html          A selected publication's page (inside default.html)
_includes/selected.html      The selected publications on the home page
assets/img/papers/           Thumbnails and figures for the selected publications (the papers' own figures)
assets/video/                Explainer videos, played in the page
assets/css/style.css         The stylesheet
scripts/sync-portfolio.py    Copies content from ../academic-portfolio; SELECTED at its top lists the selected publications
```

## Updating content

1. Update facts in `~/Research/academic-portfolio` (`profile/`, then regenerate `cv/cv.pdf` there). A selected publication's page also reads its folder README: the Links line, `TL;DR (website)`, `## Summary`, `## Main contributions` and `## Related presentations`.
2. Run `python3 scripts/sync-portfolio.py`. It rewrites the publications page and the selected publications' pages, copies the CV PDF, and warns about any `[TODO]` markers it had to drop.
3. To change which publications are selected, their order, the short venue shown on the home page, the official link, the figure, or the video, edit `SELECTED` at the top of the script and re-run it. Put images in `assets/img/papers/` (thumbnails 352 × 264, padded white) and videos in `assets/video/`.
4. Add news to `_data/news.yml` and adjust the bio in `index.md` as needed.
5. Preview, then push to `master`. GitHub Pages rebuilds the site in about a minute.

## Local preview

Requires Ruby 3.3 from Homebrew (`brew install ruby@3.3`), the same version GitHub Pages uses. Then:

```
scripts/serve.sh
```

This installs the gems on first run and serves the site at <http://localhost:4000>. Run `scripts/serve.sh build` to only build into `_site/`.
