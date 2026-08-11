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
categories:
- econometrics
tags:
- regression
---
```

### Site Structure
- `index.qmd` — Homepage (post listing)
- `about/index.qmd` — About page (URL: `/about/`)
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
6. When done: stop preview (Ctrl+C), then:
   ```
   git add post/my-new-post/ _freeze/
   git commit -m "New post: my new post"
   git push
   ```
7. GitHub Actions builds and deploys automatically (~1 minute)

### Edit an existing post
Same pattern: `quarto preview` → edit → stop → `git add` → commit → push. Prose-only edits don't touch `_freeze/`; code edits do.

### CRITICAL: run `quarto render` before every push
GitHub Actions has **no R installed**. Builds rely entirely on the committed `_freeze/` cache. If the cache is stale, CI fails with `ERROR: Unable to locate an installed version of R`.

`freeze: auto` invalidates the cache on **any** change to a `.qmd` file, including prose-only edits like fixing a typo or updating a URL. There is no "safe" edit that skips re-rendering.

Workflow for any `.qmd` change:
1. Edit the `.qmd`
2. `quarto render` (updates `_freeze/`)
3. `git add` both the `.qmd` and any changed `_freeze/` files
4. `git commit && git push`
5. Verify green check at https://github.com/fditraglia/econometrics.blog/actions

### Hiding a puzzler solution

A puzzler post keeps its solution behind a fold so that a reader meets the question first. Three pieces are needed, and all three matter:

1. `reference-location: section` in the frontmatter.
2. A `## Solution` heading, which gives the fold a section of its own.
3. The fold itself, a collapsed Quarto callout styled in the "solution folds" section of `custom.scss`.

```
---
reference-location: section
---

## Solution

::: {.callout-note .solution icon=false collapse="true" appearance="simple" title="Solution"}

## Taking it to the Data
...everything from the reveal to the end of the post...

:::
```

The heading carries the name, and the bar below it reads "CLICK TO REVEAL" when shut and "HIDE" when open. Both labels come from `custom.scss`; the `title="Solution"` in the markup is sized away and remains only for screen readers.

Four things to know before adding one:

- **Headings inside a fold stay out of the table of contents**, so a section title cannot give the answer away. This is Quarto's behavior, not something the CSS arranges.
- **Footnotes are why the heading is there.** Quarto prints notes at the foot of the page by default, where a note cited inside the fold answers the question for a reader who has not opened it. `reference-location: section` prints each note at the end of the section that cites it instead — but a section that *begins* before the fold ends inside it, which carries a visible marker's note into hiding. A heading immediately above the fold keeps the two apart.
- **Run `uv run tools-check-folds.py` after rendering.** It fails when any footnote marker and its note end up on opposite sides of a fold, which nothing else detects.
- **`tools-check-layout.py` cannot see inside a closed fold.** After adding one, open it and check for sideways scroll at 390px separately.

### R conventions
Use tidyverse: native pipe `|>`, anonymous functions `\(x)`, dplyr verbs, ggplot2.

## Build and Development Commands

### Local preview
```
quarto preview          # live preview with auto-reload
quarto render           # full render to _site/
quarto render post/my-post/index.qmd   # render one post
```

### Layout check

`tools-check-layout.py` loads every rendered page at 390, 768 and 1200px and fails if any of them scrolls sideways, naming the widest element that is not inside a scrolling container. Run it after `quarto render` when changing anything in `custom.scss`:

```
uv run tools-check-layout.py
```

It needs browsers that uv does not install; once per machine run `uv run --with playwright playwright install chromium webkit`. Overflow is detected by scrolling the page and reading `window.scrollX` back, rather than by comparing `scrollWidth` to `clientWidth`, which reports content inside a scrolling box as an overflow when that is the intended behavior.

All 41 pages pass at all four widths. Keep it that way: the rules that got them there are collected under "narrow screens" at the end of `custom.scss`, each with the case that motivated it.

### Deployment
Deployment is automatic on push to `master`. The GitHub Actions workflow at `.github/workflows/publish.yml` installs Quarto, renders the site using the `_freeze/` cache, and pushes the output to the `gh-pages` branch. GitHub Pages serves from `gh-pages`.

To monitor: https://github.com/fditraglia/econometrics.blog/actions

Or from the command line:
```
gh run list --limit 3 --branch master
gh run view <run-id> --log-failed   # if a run failed
```

## Configuration

- `_quarto.yml` — main site config (theme, navbar, comments, analytics, freeze)
- `post/_metadata.yml` — post-wide defaults (author, freeze)
- `custom.scss` — theme overrides on top of cosmo (typography, color, layout, chrome)
- `fonts/` — self-hosted woff2 files; `_fonts.html` declares the `@font-face` rules
- `_math-fit.html` — script that shrinks over-wide display equations
- `.github/workflows/publish.yml` — CI/CD deployment

### Theme

The site sets its own typography rather than using cosmo's defaults. Two self-hosted typefaces do all the work:

- **Source Serif 4** for body text, headings, and post titles. Serif matters here specifically because MathJax renders math in a serif face — a sans body would make every inline `$\hat\beta$` clash with the sentence around it. The variable font carries an 8–60pt optical size axis, and `font-optical-sizing: auto` in `custom.scss` is what gives large headings a true display cut.
- **JetBrains Mono** for everything that is metadata rather than prose: dates, categories, nav links, table headers, captions, the TOC heading. In `custom.scss` this is the `%chrome` placeholder selector — extend it rather than restating the rules.

One exemption, in the tables section: a `thead th` that contains math is matched by `:has(mjx-container)` and opts back out of `%chrome`. MathJax inherits the surrounding font size and color, so a column label like `$Y = 0$` would otherwise render small and gray beside a row label like `$X = -1$` set full size in the body cell below it. The rule keys on content rather than on any one post, so it covers future tables too; only the independence-zoo table uses it today.

Both live in `fonts/` as woff2 and are declared in `_fonts.html`, which is pulled in via `include-in-header`. They are deliberately **not** loaded from the Google Fonts CDN, so no reader IP addresses go to Google. Do not "simplify" this back to a CDN link.

Font URLs in that file are site-root absolute (`/fonts/...`). Declaring them in a `.css` file listed under `format.html.css` does **not** work — Quarto rewrites the paths and produces a broken `/fonts/..fonts/...`.

**Editing the theme never invalidates `_freeze/`.** Freeze keys on `.qmd` source, so restyling costs a re-render of HTML only and never re-runs R.

A few fragile spots, all of which degrade to "looks more like stock Quarto" rather than breaking:

- Several selectors target Quarto-internal class names (`.quarto-title-meta-heading`, `.quarto-category`, `#title-block-header`). A Quarto upgrade could rename these.
- The post date is moved above the title with flexbox `order`, which depends on Quarto's DOM order inside `#title-block-header`.
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
#| dev.args: {background: "#fdfcfa", pointsize: 14}
````

Check figure sizes after adding any plot with more than a few thousand marks. Note the argument name differs by device: `svglite` takes `bg`, `ragg_png` takes `background`.

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
