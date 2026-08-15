# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is **econometrics.blog**, an academic blog focused on econometrics and statistics. The site is built with **Quarto** and deployed to **GitHub Pages** via GitHub Actions. Posts are written in `.qmd` files that combine narrative text with executable R code and LaTeX math.

**Key Technologies:**
- Quarto (static site generator)
- R (for executable code chunks)
- GitHub Actions (CI/CD)
- GitHub Pages (hosting)
- Utterances (GitHub-based comments)
- GoatCounter (privacy-respecting analytics)

## Content Architecture

### Post Structure
Posts live in `post/slug-name/` directories. Each post directory contains:
- `index.qmd` — Source file with YAML frontmatter, text, R code, and LaTeX math
- Supporting files — images, data files, etc.

**Post Frontmatter Format:**
```yaml
---
title: "Post Title"
author: Francis J. DiTraglia
date: 'YYYY-MM-DD'
subject: 'Econometric theory'
categories:
- econometrics
tags:
- regression
---
```

`subject` places the post on the home page's by-subject view and, by default, leads the metadata line above the title. The values, which must match `listing.ejs.md` exactly: the five numbered subjects `Causal inference & identification`, `Inference & uncertainty`, `Econometric theory`, `Teaching & explainers`, `Computing & applied work`, plus the appendix `Odds & ends` (rendered with an "A." in place of a roman numeral) for meta posts. Puzzlers take the topical subject they belong to — they are listed there like any other post AND presented as a set in the puzzler block — and add `eyebrow: 'Puzzler No. N'`, which replaces the subject in the metadata line only.

Posts in a multi-part series carry four more fields, e.g. the second part of a pair:
```yaml
series: 'Overlapping Confidence Intervals'    # same string on every part
series-label: 'Part II'                       # roman numerals, matching the site's I.-V. sections
series-position: 'Part II of II'              # shown in the title-block metadata line
series-part-title: 'Correlated estimates and the law of cosines'  # what this part is about
```
The home page renders a series as a group: the series name as an unlinked label, then one indented line per part reading "Part II — Correlated estimates and the law of cosines", each a link. Part numbering is roman everywhere (titles included); the puzzlers' arabic #0–#3 is a deliberately separate convention.

### Site Structure
- `index.qmd` — Homepage (post listing)
- `about/index.qmd` — About page (URL: `/about/`)
- `r-feed.qmd` — Unlisted page whose only job is to generate the R-only feed for R-bloggers (see below)
- `post/` — All blog posts
- `_quarto.yml` — Site configuration
- `custom.scss` — Theme customization (currently empty, uses cosmo)
- `CNAME` — Custom domain (`www.econometrics.blog`)
- `_freeze/` — Cached code execution results (must be committed)
- `.github/workflows/publish.yml` — GitHub Actions deployment workflow

### Taxonomy
- **Categories** (10, lowercase): `econometrics`, `statistics`, `causal inference`, `measurement error`, `time series`, `computing`, `applied`, `teaching`, `meta`, `puzzler`
- **Tags** (follow English conventions — acronyms uppercase `CLT`, proper nouns capitalized `Bayesian`): `instrumental variables`, `regression`, `confidence interval`, `CLT`, `asymptotics`, `treatment effects`, `mean independence`, `prediction vs. causation`, `bias-variance tradeoff`, `FWL`, `covid`, `shrinkage`, `Bayesian`, `statistical power`, `effect size`

`puzzler` is the odd one out: the other nine name a topic, while this one names a format, the *Econometrics Puzzler* series of shorter posts. It is a category rather than a tag because **only categories reach the reader**. The homepage listing is built with `categories: true`, which produces the sidebar filter, and post pages show category chips; the `tags` field appears nowhere in the rendered HTML. Anything meant to be found must be a category.

## Writing and Editing Posts

### Create a new post
1. Create directory: `mkdir post/my-new-post`
2. Create `post/my-new-post/index.qmd` with frontmatter (see format above)
3. Start live preview: `quarto preview` (auto-reloads as you save)
4. Write content — R code chunks use standard syntax:
   ````
   ```{r}
   library(tidyverse)
   ```
   ````
5. Mathematical notation: inline `$...$`, display `$$...$$`. Use `\begin{aligned}` not `\begin{align*}` inside `$$...$$`.
6. If the post shows R code a reader can see, add one line for it to the `contents:` list in `r-feed.qmd` (see "Keeping the R-bloggers feed current" below).
7. When done: stop preview (Ctrl+C), then:
   ```
   git add post/my-new-post/ _freeze/
   git commit -m "New post: my new post"
   git push
   ```
8. GitHub Actions builds and deploys automatically (~1 minute)

### Edit an existing post
Same pattern: `quarto preview` → edit → stop → `git add` → commit → push. Prose-only edits don't touch `_freeze/`; code edits do.

### CRITICAL: run `quarto render` before every push
GitHub Actions has **no R installed**. Builds rely entirely on the committed `_freeze/` cache. If the cache is stale, CI fails with `ERROR: Unable to locate an installed version of R`.

**The freeze cache can also go stale the other way.** On a *project-wide* `quarto render`, `freeze: auto` under Quarto 1.9 does NOT re-execute a post whose only changes are in body prose — frontmatter and code edits invalidate the cache, but a body-text edit can leave the frozen (old) markdown feeding pandoc, silently publishing the pre-edit prose. This bit us on 2026-08-14: a footnote rewrite rendered fine from a single-file render, then a later project render quietly reverted it. After editing a post's body, render that post directly — `quarto render post/slug/index.qmd` always re-executes — or delete its `_freeze/post/slug/` subdirectory first, then check the rendered HTML actually contains the edit.

Workflow for any `.qmd` change:
1. Edit the `.qmd`
2. `quarto render post/slug/index.qmd` (forces re-execution and updates `_freeze/`), then `quarto render` if site-wide pages (the listing) need the change
3. `git add` both the `.qmd` and any changed `_freeze/` files
4. `git commit && git push`
5. Verify green check at https://github.com/fditraglia/econometrics.blog/actions

### Hiding a puzzler solution

A puzzler post keeps its solution behind a fold so that a reader meets the question first. Two pieces are needed:

1. A `## Solution` heading.
2. The fold itself, a collapsed Quarto callout styled in the "solution folds" section of `custom.scss`, running **from the reveal to the end of the post** — nothing comes after it.

```
## Solution

::: {.callout-note .solution icon=false collapse="true" appearance="simple" title="Solution"}

## Taking it to the Data
...everything from the reveal to the end of the post...

:::
```

The heading carries the name, and the bar below it reads "CLICK TO REVEAL" when shut and "HIDE" when open. Both labels come from `custom.scss`; the `title="Solution"` in the markup is sized away and remains only for screen readers.

Footnotes in a puzzler are ordinary margin footnotes, like every other post — no `reference-location` override. What makes that safe: Quarto hoists margin notes out of the fold's collapse container, so notes cited inside the fold would sit readable in the margin beside it, and a rule in `custom.scss` (`.callout.solution:has(.callout-header.collapsed) ~ .column-margin`) hides every margin note that follows a collapsed fold until it opens. This is why the fold must run to the end of the post: a margin note after the fold is assumed to belong to it. `_theme.html` re-aligns the revealed notes to their markers when the fold opens.

Four things to know before adding one:

- **Headings inside a fold stay out of the table of contents**, so a section title cannot give the answer away. This is Quarto's behavior, not something the CSS arranges.
- **Run `uv run tools-check-folds.py` when the fold structure changes.** It opens each fold-bearing page twice — fold shut, fold open — and fails unless every note is readable exactly when its marker is readable. This is what catches a leaked solution or a dangling marker; nothing else does. It is only worth running when something it can actually see has changed: adding or removing a fold, moving where one starts or ends, adding or removing a footnote inside or after a fold, or editing the fold and margin-note rules in `custom.scss`. Editing prose or code *inside* an existing fold cannot move a fold boundary or a footnote marker, so do not re-run it for wording changes — it takes a while and the answer cannot differ.
- **`tools-check-layout.py` cannot see inside a closed fold.** After adding one, open it and check for sideways scroll at 390px separately.
- **Render the post directly** (`quarto render post/slug/index.qmd`) after editing it — see the freeze warning above.

### R conventions
Use tidyverse: native pipe `|>`, anonymous functions `\(x)`, dplyr verbs, ggplot2.

### Keeping the R-bloggers feed current

The site publishes two feeds. `/index.xml` comes from the homepage listing and carries every post. `/r-feed.xml` comes from `r-feed.qmd` and carries only posts that use R; that is the one [R-bloggers](https://www.r-bloggers.com/) subscribes to, because they require a feed that is "ONLY about R" and most posts here are pure econometric theory. The site's reciprocal link back to them, which is a condition of staying listed, is in the footer in `_quarto.yml`.

**The list is hand-maintained.** After publishing a post that shows R code, add its path to the `contents:` list in `r-feed.qmd` or it will never reach R-bloggers. The test for inclusion is R code the *reader* sees: a post whose only chunks are `include: false` or `echo: false` figure generation does not qualify, and neither does a long theory post with one incidental chunk. Code in a collapsed appendix does count.

Four things about that file are easy to get wrong:

- **It must stay at the project root.** Quarto resolves `contents:` paths against the listing page's own directory, and a leading slash does not escape that: `expandGlob()` resolves the slash against the project directory when testing for a directory, then hands the still slash-prefixed glob on to be matched as an absolute filesystem path. It matches nothing, and the feed renders with zero items and no error. Moving this page into a subdirectory silently empties the feed.
- **The list lives here rather than in post front matter on purpose.** Filtering on a per-post frontmatter flag also works, but `_freeze/` keys on `.qmd` source, so flagging 19 posts would force all 19 to re-execute their R — including the ones needing `ManyIV`, `ggdag` and `tictoc`. Do not "tidy" this into per-post flags.
- **It uses `type: table` deliberately, with `sort-ui` and `filter-ui` off.** `custom.scss` hides `.list.quarto-listing-default` site-wide to keep the homepage's stub list out of sight. Quarto's default listing template emits exactly those two classes together, so switching this page to the default type would render it invisible while the feed kept working. The table type in turn switches on a filter box and sortable headers by default, neither of which is styled for this site.
- **`feed: items: 100` is set on purpose.** Quarto's default cap is 20, which fits the 19 posts listed today; the 21st would silently push the oldest out of the feed.

**Links in the feeds are fixed up after rendering.** Quarto makes image sources absolute when it builds a feed and strips same-page anchors, but leaves links to other posts in the page-relative form it emits (`../../post/slug/`). Those resolve against the republisher's domain once an aggregator rehosts the item, so they 404 — about a third of the posts here link to a previous post. `tools-absolutize-feed-links.py` rewrites them, and `project: post-render` in `_quarto.yml` runs it at the end of every render. It uses only the standard library, so CI needs nothing installed, and it is idempotent, so re-running is harmless. There is no Quarto setting for this and no version has changed it; a Lua filter cannot do it either, because the feed content is assembled after rendering from the finished HTML.

Always run a full `quarto render` before pushing a feed change, never `quarto render r-feed.qmd`. Quarto assembles a full-content feed by reading each post's already-rendered `_site/post/<slug>/index.html`, so a single-file render against a cleaned `_site` writes an `.xml` full of raw `{B4F502887207:...}` placeholders and reports no error. Then check:

```
grep -c '<item>' _site/r-feed.xml        # expected number of posts; 0 means the paths did not match
grep -c 'B4F502887207' _site/r-feed.xml  # must be 0; nonzero means unfilled placeholders
```

## Build and Development Commands

### Local preview
```
quarto preview          # live preview with auto-reload
quarto render           # full render to _site/
quarto render post/my-post/index.qmd   # render one post
```

### Layout check

`tools-check-layout.py` loads every rendered page at 360, 390, 768, 900 and 1200px and fails if any of them scrolls sideways, naming the widest element that is not inside a scrolling container. Run it after `quarto render` when changing anything in `custom.scss`:

```
uv run tools-check-layout.py
```

It needs browsers that uv does not install; once per machine run `uv run --with playwright playwright install chromium webkit`. Overflow is detected by scrolling the page and reading `window.scrollX` back, rather than by comparing `scrollWidth` to `clientWidth`, which reports content inside a scrolling box as an overflow when that is the intended behavior.

All 43 pages pass at all five widths. Keep it that way: the rules that got them there are collected under "narrow screens" at the end of `custom.scss`, each with the case that motivated it.

### Deployment
Deployment is automatic on push to `master`. The GitHub Actions workflow at `.github/workflows/publish.yml` installs Quarto, renders the site using the `_freeze/` cache, and pushes the output to the `gh-pages` branch. GitHub Pages serves from `gh-pages`.

To monitor: https://github.com/fditraglia/econometrics.blog/actions

Or from the command line:
```
gh run list --limit 3 --branch master
gh run view <run-id> --log-failed   # if a run failed
```

## Configuration

- `_quarto.yml` — main site config (theme, navbar, comments, analytics, freeze, post-render)
- `tools-absolutize-feed-links.py` — post-render step; rewrites relative links in the feeds (see below)
- `post/_metadata.yml` — post-wide defaults (author, freeze)
- `custom.scss` — theme overrides on top of cosmo (typography, color, layout, chrome)
- `fonts/` — self-hosted woff2 files; `_fonts.html` declares the `@font-face` rules
- `_math-fit.html` — script that shrinks over-wide display equations
- `.github/workflows/publish.yml` — CI/CD deployment

### Theme

The 2026 redesign (spec: the "Personalizing blog design" handoff from Claude Design) sets the site's own typography and color on top of cosmo. Three self-hosted typefaces do all the work:

- **EB Garamond** for body text. Its x-height is small, which is why the base size is 21px where Source Serif 4 sat at 19px.
- **Libre Caslon Text** for titles, headings, the masthead wordmark and nav. Caslon at weight 400 IS the heading weight — do not bold headings.
- **JetBrains Mono** only where a number or code token needs it: dates, reading times, section numerals, code, printed output, figure captions, table headers, and the small specified labels (the title-block metadata line, `ON THIS PAGE`, the view toggle, `CLICK TO REVEAL`). Never as a label style for prose. The old `%chrome` placeholder is gone; each site is styled at its own call site in `custom.scss`.

Color: cream paper `#f8f6f1`, near-black inks, hairlines `#dcd7cd`, and **one accent** — vermilion `#a63a1c` (6.0:1 on the paper). It appears on links, the double rule under the masthead, the `.blog` half of the wordmark, section and equation numerals, index section headings and rules, margin asides, table header rows, and the solution folds' rules and labels. Post-body section headings stay ink; only the numeral before them is red. Figures keep a chart blue (`econblog_accent` in `_common.R`) because two posts pair it against the vermilion as a two-way contrast — do not turn it red.

One exemption, in the tables section: a `thead th` that contains math is matched by `:has(mjx-container)` and opts back out of the mono header treatment. MathJax inherits the surrounding font size and color, so a column label like `$Y = 0$` would otherwise render tiny and red beside a row label like `$X = -1$` set full size in the body cell below it. The rule keys on content rather than on any one post, so it covers future tables too; only the independence-zoo table uses it today.

All faces live in `fonts/` as woff2 and are declared in `_fonts.html`, which is pulled in via `include-in-header`. They are deliberately **not** loaded from the Google Fonts CDN, so no reader IP addresses go to Google. Do not "simplify" this back to a CDN link. (Figure SVGs still embed **Source Serif 4** subsets from `fonts/subset/`; the page-level Source Serif declarations were removed, but the figure pipeline is unchanged.)

Font URLs in that file are site-root absolute (`/fonts/...`). Declaring them in a `.css` file listed under `format.html.css` does **not** work — Quarto rewrites the paths and produces a broken `/fonts/..fonts/...`.

**Editing the theme never invalidates `_freeze/`.** Freeze keys on `.qmd` source, so restyling costs a re-render of HTML only and never re-runs R.

A few fragile spots, all of which degrade to "looks more like stock Quarto" rather than breaking:

- Several selectors target Quarto-internal class names (`.quarto-title-meta-heading`, `.quarto-category`, `#title-block-header`). A Quarto upgrade could rename these.
- The post title block is a custom template partial, `_partials/title-block.html`, wired up in `post/_metadata.yml`. It renders the metadata line (subject · date · reading time · series position) from front matter; the reading time comes from `_reading-time.lua`, a Pandoc filter that counts words at render time (200 wpm, matching Quarto's listing field), so no R and no JavaScript are involved. A Quarto upgrade that restructures its title-block partial could need this file revisited.
- The home page is `listing.ejs.md`: a hero for the latest post (text-only unless the post opts in with an `image:` frontmatter line, which the hero shows at 150px), a by-subject view (default) and a by-date view behind a client-side toggle, a puzzler block, and a hidden flat list of per-post stubs. The stubs are what List.js — and therefore the category filter — actually operates on; `_theme.html` mirrors the filter state onto the visible views via their `data-indexes` attributes, moves the margin block into the sidebar, wires the toggle (localStorage, subject view rendered first so the page is correct before JS runs), and collapses long sections behind an italic "five more". The `Puzzlers` nav item points at `/#category=puzzler`, which Quarto's listing JS reads on load; puzzler and meta filters force the date view, since those posts have no subject-view lines.
- The `!important` flags on `.quarto-category` are required, not stylistic. Quarto ships a more specific rule that restores the default pill border without them.
- The table of contents is held back to 900px, above Quarto's own 768px breakpoint, because the wide `$grid-column-gutter-width` leaves the page grid about 862px wide and it does not shrink in that band. Without the override the sidebar hangs off the right edge and the page scrolls sideways. If the gutter is ever narrowed, recheck the breakpoint — the two are tied together, as `$math-bleed` already is.
- Below 768px the page grid is restated with `$grid-column-gutter-width-mobile` in place of the desktop gutter, because Quarto applies one gutter at every viewport and the desktop value left a 216px reading column on a 360px phone. The rule reproduces Quarto's own track list for that breakpoint with only the two edge values changed, so a Quarto upgrade that renames the grid lines would need it updated. It carries `!important` because Quarto states the same rule through several more specific body-class selectors.

### Figures

R figures are styled by `_common.R`, sourced from a hidden chunk at the top of every post that draws a plot:

````
```{r}
#| include: false
source(here::here("_common.R"))
```
````

**The governing rule: the invisible layer may change styling and must never change anything that carries meaning.** Fonts, gridlines, backgrounds, margins and text sizes are safe to set there. Color palettes that encode groups, scale transformations and axis limits are not — those stay in the post, visible, and use stock functions like `scale_colour_brewer()` so a reader can carry them into their own work.

**Never add a complete theme in a post.** `theme_minimal()`, `theme_bw()`, `theme_classic()` and friends *replace* whatever `theme_set()` established, silently reverting the figure to stock ggplot. Just write `ggplot(df, aes(x, y)) + geom_point()` and let the shared theme apply. A post-specific `theme(...)` call adding individual elements is fine — that composes. For schematics with no axes, call `theme_econblog_void()` rather than `theme_void()`.

**Base R needs no changes at all.** A knitr `par` hook in `_common.R` restyles base graphics before each chunk, so the seven base-R posts were never edited. Don't add `par()` calls to fix appearance.

**Two faces, split by role.** JetBrains Mono for tick labels, legend values and facet strips — things that are data. Source Serif 4 for axis titles, plot titles, legend titles and `annotate()`/`geom_text()` — things that are words or notation. The serif half exists so plotmath like `expression(hat(rho))` matches the MathJax beside it. Base R can only carry one family per device, so the hook detects `expression(`/`bquote(` in the chunk source and gives those chunks serif throughout.

**Figures are SVG, with fonts embedded.** An SVG referenced as `<img src="...svg">` renders in a sandbox: it cannot fetch external resources and the page's `@font-face` rules do not reach inside it. A `fig.process` hook therefore injects subset copies of only the faces each figure uses. Those subsets live in `fonts/subset/` and are regenerated by `tools-make-figure-fonts.py` (`uv run tools-make-figure-fonts.py`); they are committed, so rendering needs no Python.

**Plotmath Greek does not come from the plot's font family.** R draws `expression(mu)` through its "Symbol" font, so svglite writes `font-family: "Symbol"` even when the device family is Source Serif 4. Nothing embeds that, so each reader substitutes their own — the glyphs are ordinary Unicode, they just arrive in an arbitrary face. The same `fig.process` hook rewrites Symbol to the serif and strips the `textLength`/`lengthAdjust` svglite pins to Symbol's metrics, which would otherwise stretch the substituted glyph. This is why the subset font carries the full basic Greek range: **narrowing the glyph set in `tools-make-figure-fonts.py` will silently break Greek in figures.**

**Dense plots must be pinned back to PNG.** Vector output is smaller than PNG for ordinary charts but explodes when every observation becomes a path — `plot(ecdf(z))` and `qqnorm(z)` over 100,000 draws came to 9.9 MB and 17.4 MB. Two chunks in `thirty-isn-t-the-magic-number` carry:

````
#| dev: ragg_png
#| dev.args: {background: "#f8f6f1", pointsize: 14}
````

Check figure sizes after adding any plot with more than a few thousand marks. Note the argument name differs by device: `svglite` takes `bg`, `ragg_png` takes `background`; both must stay in step with `$paper` in `custom.scss`.

**The one tikz figure is styled separately, in LaTeX.** `why-econometrics-is-confusing-part-ii-the-independence-zoo` draws its diagram in a `{tikz}` chunk rather than an `{r}` one. knitr compiles that through LaTeX, not through an R graphics device, so nothing in `_common.R` reaches it — the theme, the `par` hook and the SVG font-embedding hook all apply to R figures only. The chunk therefore carries its own styling in `engine.opts`:

- `classoption: "dvisvgm,tikz"` makes pgf write SVG drawing commands directly. Without it pgf emits PostScript, which the TeX Live build of `dvisvgm` cannot read unless Ghostscript is also installed. Two inert PostScript specials are still reported as a warning on every render; output with and without Ghostscript is pixel-identical, so the warning can be ignored.
- `dvisvgm.opts: "--no-fonts"` converts glyphs to outlines. The figure then carries no font references at all, which is why it needs none of the subset-font machinery the R figures use.
- `extra.preamble` loads `sourceserif` for the words and defines the ink color. Setting a color matters twice over: it matches `econblog_ink`, and it keeps the image from being pure grayscale. The old PNG was flattened onto white precisely because ImageMagick saw an all-gray image and dropped its alpha channel.

Math deliberately stays in Computer Modern, because that is what MathJax draws on the page. Only the text takes Source Serif 4. This route needs `latex` and `dvisvgm`, both part of TeX Live, and no R packages.

**Editing `_common.R` does NOT invalidate `_freeze/`.** Freeze keys on `.qmd` source, so a change to the shared theme reaches only posts that happen to re-render. To propagate one, delete the cache for every post that sources it and render:

```
for p in $(grep -rl "_common.R" post/ --include="*.qmd" | sed 's|post/||;s|/index.qmd||'); do rm -rf "_freeze/post/$p"; done
quarto render
```

Two loose ends: figure widths inherit Quarto's 7in default, which matches the ~680px column at scale 1 — override only for genuinely wide figures, and give those `#| column: page` too, as `overlapping-confidence-intervals-part-ii` does. And the UK excess-deaths facets keep `scale_color_brewer(palette = "Set1")`, whose saturated red and blue are the last stock-looking thing on the site; it stays because the palette encodes which series is which.

### Wide display equations

Equations are routinely wider than the 680px reading column. Three layers handle this, in order:

1. `custom.scss` lets `mjx-container[display="true"]` bleed `$math-bleed` into each margin. `$grid-column-gutter-width` is held wider than `$math-bleed` so equations never touch the TOC — **change the two together**.
2. `_math-fit.html` measures anything still too wide and sets a `--math-fit` multiplier that `custom.scss` folds into the font size.
3. Below a 0.78 floor it stops shrinking and the equation scrolls, marked by an edge fade. The script logs any equation that hits the floor to the browser console.

Coverage was checked on the two math-heaviest posts, not all 38.

### Key settings
- Theme: `cosmo` + `custom.scss`
- Math: **MathJax**, Quarto's default, since `html-math-method` is not set anywhere in the config. Rendered math appears in the DOM as `mjx-container` elements, *not* `.katex` — target `mjx-container` when writing CSS for equations. Use `\begin{aligned}` inside `$$...$$`, not `\begin{align*}`.
- Comments: Utterances, repo `fditraglia/econometrics.blog-comments`, `issue-term: pathname`
- Analytics: GoatCounter at `econometrics.goatcounter.com`
- `freeze: auto` — code re-runs on source change, cached otherwise

## Important Notes

- **Never edit generated files** in `_site/` — they're ignored and regenerated on render
- **Always commit `_freeze/`** when it changes — GitHub Actions needs it
- **Internal links** should use site-root relative paths, never absolute URLs:

| You want to link to | Markdown |
|---|---|
| The homepage | `[text](/)` |
| The about page | `[text](/about/)` |
| A specific post | `[text](/post/slug-name/)` |
| An anchor within a post | `[text](/post/slug-name/#section-heading)` |

  Why relative: survives domain changes, works in local preview, doesn't need updating if the site moves.
- **Image/asset references** in posts should use relative paths within the post directory
- **Never delete `.quarto/`** — it's Quarto's local cache, needed for rendering. Gitignored, safe to leave alone.
- **Never delete `_freeze/`** — the committed cache that lets CI build without R. Only Quarto should modify this directory (via `quarto render`). The one exception is deliberately clearing a post's subdirectory to force re-execution after a change to `_common.R`, which `freeze` cannot see.
- **Several posts depend on packages that are not on CRAN.** `rcovidUK` (`remotes::install_github("fditraglia/rcovidUK")`) and `ManyIV` (`kolesarm/ManyIV`) hold datasets; `ggdag` and `tictoc` come from CRAN. The `_freeze` cache hides their absence until something forces a re-render, at which point the build fails. If you are setting up a new machine, install all four before touching any `.qmd`.
- **The independence-zoo post also needs a LaTeX toolchain**, for the reasons in the Figures section: `latex`, `dvisvgm`, `standalone`, `pgf` and `sourceserif`. A full TeX Live has all five, but a minimal one does not — `sourceserif` comes from `collection-fontsextra`. `_freeze` hides this the same way it hides the R packages, so the failure appears only when that post is next edited.
