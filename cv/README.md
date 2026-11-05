# CV and publication maintenance

`publication.bib` is the only hand-edited publication database. The website's
`src/data/publications.json` and `public/pdf/zhuolun_he_cv.pdf` are generated files.
The old Overleaf project is a historical source, not a second active database.
No token, absolute user path, or Overleaf connection is needed by the website.

## Build and preview

First run `make setup` and `pnpm install`. From the repository root
(Python 3.9+, Node.js 22.12+, pnpm, and TeX Live with
XeLaTeX, latexmk and Biber):

```sh
make all          # validate data, compile/publish the PDF locally, build Astro
pnpm dev          # browse the local site
make check        # validate the database and check JSON is current
```

On macOS the Makefile adds MacTeX's `/Library/TeX/texbin` to PATH. On other systems
it uses the existing PATH. Pagella is loaded from TeX Live by filename, without
installing additional system fonts.

`make cv` generates data and compiles the CV. `pnpm build`, `make site`, and
`make all` all compile the current CV before building the website. Development
preview refreshes data at startup without compiling TeX. After editing BibTeX
while preview is running, execute `make data` in another terminal to refresh it. Nothing commits, pushes
or deploys. `cv/build/` is ignored; generated JSON and the public PDF are tracked.

## Add or update a publication

Use `@article` for a journal, `@inproceedings` for a conference/workshop, and
`@misc` for an arXiv preprint. All
records require `title`, `author`, `year`, `usera`, `sortkey`, and `journal` or
`booktitle` (preprints instead require `eprint` and `eprinttype = {arxiv}`). Pybtex parses standard BibTeX syntax, including string macros and concatenation.
Use UTF-8 names,
and `Family, Given and Family, Given` authors. Nested braces protecting acronyms
are supported. The website display adapter rejects unsupported TeX commands
rather than silently changing the text. Don't put bold commands into author data.

```bibtex
@inproceedings{surname2027shorttitle,
  title = {{EDA}: A Descriptive Paper Title},
  author = {Surname, Given and He, Zhuolun},
  booktitle = {Conference Name (ACRONYM)},
  year = {2027},
  location = {City, Country},
  eventdate = {2027-06-01/2027-06-04},
  usera = {surname2027shorttitle},
  sortkey = {0000},
  doi = {10.example/replace-with-actual-doi},
  paper = {https://example.org/paper.pdf},
  code = {https://example.org/code},
}
```

Replace example URLs/DOI with real values, or omit unavailable fields.

- Keys and `usera` website anchors must be unique and stable. Existing `pub-N`
  anchors are preserved because the homepage links to them. New anchors can use
  the BibTeX key; don't renumber existing papers when adding one.
- The website sorts by descending `year`, then ascending numeric `sortkey`.
  Choose a unique order value. Existing gaps/keys can be changed to make room;
  they do not affect anchors. Ordering within a year is editorial and is not
  guessed from online-first dates or conference dates.
- `doi` is the DOI identifier, without the URL prefix. `url` is an optional title
  link when no DOI is available. DOI takes precedence in both outputs. Optional website
  resource fields: `paper`, `slides`, `code`, `poster`, `preprint` (arXiv).
  Local resources start with `/pdf/` and must exist under `public/`.
- `note` carries factual distinctions such as Editor's Pick, Best Paper Award
  Nomination, Invited Paper or extended abstract. It is shared by CV and website.
- Conference and journal versions have separate keys. Identical titles are
  reported for review, not automatically merged. Duplicate keys/DOIs/anchors,
  missing required fields, year/date conflicts, and broken local resource paths
  fail generation. This does not check remote links' availability.
- Keep volume, issue (`number`), pages and publication dates when known; the CV
  intentionally prints a compact author/title/venue/year citation. Conference
  travel dates and locations remain available on the website.

## CV structure

`main.tex` contains verified profile/history content. `academiccv.sty` controls the
A4 layout, Pagella typography, spacing and page footer. Publication names are
highlighted by family + given name at render time; no manual list of citation keys
is needed. `make cv` generates `cv/build/publications.tex` from BibTeX, then
compiles it with Biber. Each publication stays together across page breaks. Paper titles link
to their DOI or URL. There are no invented teaching, advising, service or grant
entries; add those sections only after the underlying information is supplied.

### Publication categories, order and labels

Every entry has one `keywords` value: `journal`, `conference`, `workshop`, or `preprint`.
Articles must be `journal`; conference and workshop papers use `@inproceedings`.
This is an explicit classification, not a guess based on venue prestige or title.
MLCAD 2023 is included with conference papers, as requested by the owner. Invited
papers remain in their original venue category and carry an `Invited Paper` note.

The CV displays Journal Articles, Conference Papers, any Workshop Papers, then
Preprints. The website groups published/accepted papers by year descending, then by
journal, conference, and workshop within each year. Preprints appear last in a
separate section. Within each group it uses the CV order and descending labels.
Within
each category it sorts by year descending, then by known `date` (or `eventdate`
for conference/workshop papers) descending, then `sortkey`. Within the same year,
entries with a known month precede undated entries; missing dates are not inferred.
Preprint `date` is the first public arXiv submission date, not the latest revision
date; `eprint` is the unversioned arXiv identifier. When a preprint is accepted,
update the same record and stable anchor to its new type/venue/category rather
than counting it again.

Journal years use the issue year when known; online-first entries without an issue
use their available publication year. The generated JSON retains its editorial storage order; `cvOrder` and `label`
carry the shared CV display order and category numbering for the website.

Labels descend separately within each category: `[J13]` to `[J1]`, `[C44]` to
`[C1]`, and `[P4]` to `[P1]` in this edition (44 conference papers and four
preprints; no separate workshop list). Counts are generated, not stored or maintained by
hand. They are display labels, not stable identifiers: inserting an older paper
can change some labels. BibTeX keys and website anchors stay stable. All author
names are printed; the owner's name is highlighted during typesetting.

## Reconciliation notes (2026-11-05)

56 records were reconciled by title and venue rather than file order, retaining
all 56 website anchors and resource links. The source BibTeX contained duplicate
`he2025large` keys: these are now `he2025mirage` (TODAES) and `he2025assistants`
(FnT EDA). The same-title ISPD 2024 publication remains separate.

Corrections and provenance:

- FabGPT: **Yali Fu**, not Dali Fu, per the
  [CUHK publication record](https://research.cuhk.edu.hk/en/publications/fabgpt-an-efficient-large-multimodal-model-for-complex-wafer-defe/).
- ChatLS: 2025, consistent with its eventdate and the
  [CUHK record](https://research.cuhk.edu.hk/en/publications/chatls-multimodal-retrieval-augmented-generation-and-chain-of-tho/).
- Swift or Exact: retained the website's 2025 year, consistent with its DOI
  `10.1109/DAC63849.2025.11133073` and the source's June 2025 eventdate.
- ChatEDA journal version: 2024, DOI `10.1109/TCAD.2024.3383347`, volume 43,
  issue 10, per the [published paper](https://www.cse.cuhk.edu.hk/~byu/papers/J115-TCAD2024-ChatEDA.pdf).
- LSTP and Bit-Level Quantization use their full paper titles, also found in the
  [LSTP paper](https://www.cse.cuhk.edu.hk/~byu/papers/C192-ASPDAC2024-LSTP.pdf)
  and [quantization paper](https://www.cse.cuhk.edu.hk/~byu/papers/C161-ISEDA2023-QuanHSD.pdf).
- AutoGraph's full title and pages 11354–11362 match its
  [AAAI record](https://ojs.aaai.org/index.php/AAAI/article/view/26343).
- Editor's Pick was carried from the old CV into the shared TODAES record; the
  ICCAD 2024 award nomination was carried from the website into the shared record.
- Efficient Arithmetic Block Identification retains the website's 2023 issue
  year; the [published paper](https://www.cse.cuhk.edu.hk/~byu/papers/J87-TCAD2023-ReveGCN.pdf)
  confirms online publication in December 2022 and the August 2023 issue. Key
  `wang2022efficient` remains stable.
- Missing year in the old `ko2019deep` record is filled from the website (2019).

The original sources have not been exhaustively re-audited against every publisher
record. Remaining publication metadata and research-experience dates are preserved
from existing materials. In particular, the 2017 undergraduate award title and the
exact thesis titles should be confirmed if a formal institutional CV is needed.
The Academic Service section includes the owner-confirmed Associate Editor role
at Integration, the VLSI Journal, starting December 2025. Further teaching,
advising, service, grants and invited-talk details remain to be supplied.

## Additions and issue-year corrections (2026-11-05)

- Added FormalPCell as a 2027 ASPDAC conference paper, `To appear`, from the
  [official program](https://easychair.org/smart-program/ASP-DAC2027/2027-01-26.html).
  No DOI or final proceedings page numbers have been invented.
- CB-EVO: issue year 2026, volume 31, issue 6, article 119, 26 pages.
- Routing-aware Legal Hybrid Bonding Terminal Assignment: issue year 2026,
  volume 31, issue 3, article 48, 20 pages.
  These supersede the earlier 2025 online-first years; existing BibTeX keys and
  website anchors are retained. Source: [Bei Yu's publication list](https://www.cse.cuhk.edu.hk/~byu/publications.html).
- Added four records in a separate Preprints category, based on their public
  arXiv records and first submission dates:
  [SynAct](https://arxiv.org/abs/2608.12751),
  [Architect of the Bits World](https://arxiv.org/abs/2502.12751),
  [UniMoCo](https://arxiv.org/abs/2505.11815), and
  [ToTRL](https://arxiv.org/abs/2505.12717).
  No conference acceptance is inferred for these four.

Current total: 13 journal articles, 44 conference papers (including one accepted
2027 paper), and four separately listed preprints. Owner-supplied awards remain
in the shared Honors and Awards list without advising annotations.

MLCAD 2023 event dates were corrected from the accidentally copied ICCAD dates
to September 11–13, 2023, per the linked Bei Yu publication list.
