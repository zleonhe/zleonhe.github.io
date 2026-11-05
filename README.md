# Zhuolun He — academic homepage

Static Astro pages and a BibLaTeX CV, sharing `cv/publication.bib`.
No React or client-side runtime.

## Setup

Requires Python 3.9+, Node.js 22.12+, pnpm, and TeX Live with XeLaTeX,
latexmk and Biber (MacTeX on macOS).

```sh
make setup       # project-local Python environment and Pybtex
pnpm install
pnpm dev         # refresh paper data and preview; no TeX build needed
make check       # validate data and run regression tests
pnpm build       # refresh data, compile CV, then build the static site
pnpm preview     # preview the production build
```

`make all`, `make site`, and `pnpm build` use the same production pipeline.
It fails if CV compilation fails; it cannot silently publish a stale PDF.
`make cv` updates only data and the CV. `make data` updates only paper data.
The pipeline reads BibTeX once per production build. Nothing commits, pushes,
uploads, or deploys automatically.

## Maintain

- `src/pages/index.astro`: profile, research, selected project links, honors, teaching.
- `cv/publication.bib`: only hand-edited paper database; see [field conventions](cv/README.md).
- `scripts/publications.py`: Pybtex parsing, validation, ordering, website/CV generation.
- `src/data/publications.json`: generated data; never edit by hand.
- `cv/main.tex`, `cv/academiccv.sty`: CV content and layout.
- `src/pages/publications.astro`: descending years, journals before conferences,
  with preprints last. Labels and within-category order match the CV.
- `src/components/Publication.astro`: shared paper formatting.
- `src/layouts/Layout.astro`: sticky navigation and document metadata.
- `src/styles/global.css`: white background, Verdana, blue links.
- `public/`: photos, PDFs and favicon, keeping existing public URL paths.

After editing `cv/publication.bib` during `pnpm dev`, run `make data` in another
terminal; Astro then refreshes the generated JSON. No background watcher is installed.

All paper content is generated into HTML. Stable BibTeX `usera` anchors keep
homepage project links valid when paper order changes. DOI links take precedence
over `url` in both the website and CV. External web links and the CV open new
tabs. Internal navigation and publication anchors stay in the current tab.

## Hosting

Astro targets `https://eda.cs.tsinghua.edu.cn/~zlhe/`; `dist/` contains the
complete school site, including assets with the `/~zlhe/` path prefix. Upload
the contents of `dist/` to `/home/zlhe/public_html/` on the school server.
Source files are not directly publishable.

The repository-root `index.html` and `404.html` are GitHub Pages redirect pages.
JavaScript preserves the requested path, query and fragment when redirecting
to the school site. Without JavaScript, the fallback points to the new homepage.
PDFs and images are maintained only in `public/` and shipped inside `dist/`
to the school server. GitHub Pages uses the redirect pages to send old resource
paths to the corresponding school files; it has no root asset copies.

Build with `pnpm build`, then upload `dist/` contents over SSH on port 40822.
Back up `/home/zlhe/public_html/` before deployment and verify the school site
before pushing the GitHub redirect. Nothing deploys automatically. Updating the
institutional profile link is a separate step.
The former public calendar is not in the navigation; its calendar ID is
`zleonhe@gmail.com`.
