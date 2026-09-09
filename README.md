# rtakatsky.github.io

Personal academic site of Ryota Takatsuki, served at <https://rtakatsky.github.io>.

Plain Jekyll, built natively by GitHub Pages from the `master` branch. No custom plugins, no JavaScript, no third-party assets, no CI.

## Layout

```
index.md                     Home page, written by hand
_data/news.yml               News items, newest first
publications.md              GENERATED from academic-portfolio — do not edit
assets/cv.pdf                COPIED from academic-portfolio by the sync script
_layouts/default.html        The single page template
assets/css/style.css         The stylesheet
scripts/sync-portfolio.py    Copies content from ../academic-portfolio
```

## Updating content

1. Update facts in `~/Research/academic-portfolio` (`profile/`, then regenerate `cv/cv.pdf` there).
2. Run `python3 scripts/sync-portfolio.py`. It rewrites the publications page, copies the CV PDF, and warns about any `[TODO]` markers it had to drop.
3. Add news to `_data/news.yml` and adjust the bio in `index.md` as needed.
4. Preview, then push to `master`. GitHub Pages rebuilds the site in about a minute.

## Local preview

Requires Ruby 3.3 from Homebrew (`brew install ruby@3.3`), the same version GitHub Pages uses. Then:

```
scripts/serve.sh
```

This installs the gems on first run and serves the site at <http://localhost:4000>. Run `scripts/serve.sh build` to only build into `_site/`.
