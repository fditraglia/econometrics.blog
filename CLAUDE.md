# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is **econometrics.blog**, an academic blog focused on econometrics and statistics. The site is built with Hugo using the Wowchemy (formerly Academic) theme and R/blogdown for content creation. Posts are written in R Markdown (.Rmd files) that combine narrative text with executable R code and mathematical notation.

**Key Technologies:**
- Hugo 0.81.0 (static site generator)
- Wowchemy/Academic theme (Hugo modules)
- R/blogdown (R package for R Markdown integration)
- Netlify (hosting and deployment)

## Build and Development Commands

### Building the site
```bash
# Build the site for production
hugo --gc --minify

# Build with future-dated posts (for previews)
hugo --gc --minify --buildFuture

# Serve the site locally for development
hugo server
```

### Working with R/blogdown
The preferred workflow is to use R/blogdown from within RStudio:

```r
# Serve the site (R console)
blogdown::serve_site()

# Stop serving
blogdown::stop_server()

# Create a new post
blogdown::new_post(title = "Post Title", ext = ".Rmd")

# Build the site
blogdown::build_site()
```

**Important blogdown settings** (configured in `.Rprofile`):
- `blogdown.hugo.version = "0.81.0"` - Hugo version is locked
- `blogdown.ext = '.Rmd'` - Default format is R Markdown
- `blogdown.method = 'html'` - Build .Rmd to .html via Pandoc
- `blogdown.subdir = 'post'` - Posts go in content/post/
- `blogdown.knit.on_save = FALSE` - Manual control over knitting

## Content Architecture

### Post Structure
Posts live in `content/post/YYYY-MM-DD-slug-name/` directories. Each post directory contains:
- `index.Rmd` - Source R Markdown file with YAML frontmatter, text, R code, and LaTeX math
- `index.html` - Generated HTML output (do not edit directly)
- Supporting files - images, data files, R objects (.rds files)

**Post Frontmatter Format:**
```yaml
---
title: Post Title
author: Francis J. DiTraglia
date: 'YYYY-MM-DD'
slug: slug-name
categories: [category1, category2]
tags: []
subtitle: ''
summary: ''
---
```

### Content Types
- `/content/post/` - Blog posts (R Markdown with code and math)
- `/content/home/` - Homepage widget pages
- `/content/about/` - About page content
- `/content/admin/` - Admin/CMS content

### Writing Posts

**Mathematical notation:** Use LaTeX within R Markdown. The site is configured with `math: true` and uses Goldmark with `unsafe: true` for raw HTML/LaTeX rendering.

**R code chunks:** Standard R Markdown syntax:
````markdown
```{r chunk-name}
# R code here
```
````

**Images and assets:** Place in the post's directory alongside index.Rmd. Reference with relative paths.

## Configuration

### Main config files
- `config.yaml` - Root Hugo configuration (theme, permalinks, taxonomies)
- `config/_default/params.yaml` - Wowchemy theme parameters (appearance, features, integrations)
- `config/_default/menus.yaml` - Site navigation menus
- `config/_default/languages.yaml` - Language/internationalization settings
- `.Rprofile` - R/blogdown project options

### Key configuration notes
- Hugo version: 0.81.0 (locked in both `.Rprofile` and `netlify.toml`)
- Theme: "starter-academic" via Hugo modules
- Base URL: https://www.econometrics.blog
- Comments: Utterances (GitHub-based, repo: fditraglia/econometrics.blog-comments)
- Math rendering: Enabled with goldmark markdown handler
- Ignored files: `.ipynb`, `.ipynb_checkpoints`, `.Rmd`, `.Rmarkdown`, `_cache`

## Deployment

The site deploys automatically to Netlify on git push. Configuration in `netlify.toml`:
- Production build: `hugo --gc --minify -b $URL`
- Deploy previews: `hugo --gc --minify --buildFuture -b $DEPLOY_PRIME_URL`
- Hugo version: Set to 0.81.0 in build environment
- Publish directory: `public/`
- Uses netlify-plugin-hugo-cache-resources

## Theme Customization

### Custom layouts and partials
Located in `layouts/` to override theme defaults:
- `layouts/partials/custom_head.html` - Custom head content
- `layouts/partials/custom_js.html` - Custom JavaScript
- `layouts/partials/site_footer.html` - Footer override
- `layouts/partials/comments/utterances.html` - Comments integration
- `layouts/shortcodes/blogdown/postref.html` - Blogdown cross-references

### Static assets
- `static/media/` - Static images and files served directly
- `assets/media/` - Asset pipeline images (processed by Hugo)

## Important Workflows

### Creating a new post
1. Use `blogdown::new_post()` in R or create directory manually
2. Directory name format: `YYYY-MM-DD-slug-name/`
3. Create `index.Rmd` with proper frontmatter
4. Write content with R code chunks and LaTeX math
5. Knit to HTML (happens automatically with blogdown::serve_site())
6. Commit both .Rmd and generated .html files

### Editing an existing post
1. Edit the `index.Rmd` file (not the .html)
2. Re-knit to regenerate .html
3. Commit both modified files

### Working with math
- Inline math: `$...$`
- Display math: `$$...$$`
- Math rendering is enabled site-wide via config.yaml

## Development Notes

- The site uses Hugo modules for theme management (not git submodules)
- R objects can be saved/loaded between posts using .rds files
- The blogdown.method='html' means posts are rendered to HTML, not Markdown
- ignoreFiles in config.yaml prevents Hugo from processing .Rmd source files
- Timeout is set to 600000ms (10 min) for long builds with complex R code
