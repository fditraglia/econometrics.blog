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
- **Categories** (9, lowercase): `econometrics`, `statistics`, `causal inference`, `measurement error`, `time series`, `computing`, `applied`, `teaching`, `meta`
- **Tags** (follow English conventions — acronyms uppercase `CLT`, proper nouns capitalized `Bayesian`): `instrumental variables`, `regression`, `confidence interval`, `CLT`, `asymptotics`, `treatment effects`, `mean independence`, `prediction vs. causation`, `bias-variance tradeoff`, `FWL`, `covid`, `shrinkage`, `Bayesian`

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

### R conventions
Use tidyverse: native pipe `|>`, anonymous functions `\(x)`, dplyr verbs, ggplot2.

## Build and Development Commands

### Local preview
```
quarto preview          # live preview with auto-reload
quarto render           # full render to _site/
quarto render post/my-post/index.qmd   # render one post
```

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
- `custom.scss` — theme overrides (empty, inherits cosmo)
- `.github/workflows/publish.yml` — CI/CD deployment

### Key settings
- Theme: `cosmo` + `custom.scss`
- Math: KaTeX (Quarto default). Use `\begin{aligned}` inside `$$...$$`, not `\begin{align*}`.
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
- **Never delete `_freeze/`** — the committed cache that lets CI build without R. Only Quarto should modify this directory (via `quarto render`).
