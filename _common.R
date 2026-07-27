# Shared figure styling for econometrics.blog
#
# Sourced from a hidden setup chunk in each post. Nothing here is visible to
# readers, so nothing here may carry meaning: no colour palettes that encode
# groups, no scale transformations, no axis limits. Typography, gridlines,
# backgrounds and margins only. See CLAUDE.md.
#
# Palette is taken from custom.scss. Keep the two in step.

econblog_paper <- "#fdfcfa"  # page background
econblog_ink   <- "#23211e"  # body text
econblog_muted <- "#585249"  # chrome: axis text, strip labels
econblog_rule  <- "#d5cfc3"  # hairlines, gridlines
econblog_accent<- "#1f5488"  # links; the site's one chromatic note
econblog_warm  <- "#a3402a"  # counterpart to the accent, for two-way contrasts

# Two faces, matching the roles they already play on the page: mono for chart
# chrome (axis labels, ticks, legends), serif for anything that reads as prose
# or as mathematics, so in-figure notation matches MathJax.
econblog_font      <- "JetBrains Mono"
econblog_font_text <- "Source Serif 4"

# --- ggplot2 ----------------------------------------------------------------
# Chart labels are metadata rather than prose, which is why they take the same
# monospace face the site already uses for dates, categories and table headers.

theme_econblog <- function(base_size = 14, base_family = econblog_font) {
  ggplot2::theme_minimal(base_size = base_size, base_family = base_family) +
    ggplot2::theme(
      # backgrounds: figure sits on the page, not on a white card
      plot.background   = ggplot2::element_rect(fill = econblog_paper, colour = NA),
      panel.background  = ggplot2::element_rect(fill = econblog_paper, colour = NA),
      legend.background = ggplot2::element_rect(fill = econblog_paper, colour = NA),
      legend.key        = ggplot2::element_rect(fill = econblog_paper, colour = NA),

      # gridlines: present but quiet, major only
      panel.grid.major = ggplot2::element_line(colour = econblog_rule, linewidth = 0.3),
      panel.grid.minor = ggplot2::element_blank(),
      panel.border     = ggplot2::element_blank(),

      # axes: the gridlines already carry the scale, so no axis rule or ticks
      # on top of them. One layer of furniture, not three.
      axis.line   = ggplot2::element_blank(),
      axis.ticks  = ggplot2::element_blank(),
      # Tick labels are data values, so they stay monospace. Axis titles are
      # words or notation -- often plotmath, as in expression(hat(rho)) -- so
      # they take the serif face and match the MathJax around them.
      axis.text   = ggplot2::element_text(colour = econblog_muted, size = ggplot2::rel(0.85)),
      axis.title  = ggplot2::element_text(colour = econblog_muted, size = ggplot2::rel(1.0),
                                          family = econblog_font_text),

      # titles: left-aligned, as on the page
      # Titles and captions are prose or notation: serif, like the body text.
      plot.title.position = "plot",
      plot.title    = ggplot2::element_text(colour = econblog_ink, size = ggplot2::rel(1.2),
                                            family = econblog_font_text,
                                            hjust = 0, margin = ggplot2::margin(b = 8)),
      plot.subtitle = ggplot2::element_text(colour = econblog_muted, size = ggplot2::rel(1.0),
                                            family = econblog_font_text,
                                            hjust = 0, margin = ggplot2::margin(b = 10)),
      plot.caption  = ggplot2::element_text(colour = econblog_muted, size = ggplot2::rel(0.8),
                                            family = econblog_font_text, hjust = 0),

      # legend: bottom, no key box
      legend.position  = "bottom",
      legend.direction = "horizontal",
      legend.title     = ggplot2::element_text(colour = econblog_muted, size = ggplot2::rel(0.95),
                                               family = econblog_font_text),
      legend.text      = ggplot2::element_text(colour = econblog_muted, size = ggplot2::rel(0.9)),

      # facets: label text, not a grey box
      strip.background = ggplot2::element_blank(),
      strip.text       = ggplot2::element_text(colour = econblog_ink, size = ggplot2::rel(0.9),
                                               hjust = 0, margin = ggplot2::margin(b = 4)),

      plot.margin = ggplot2::margin(4, 4, 4, 4)
    )
}

# Schematic diagrams (no axes, no data scales) still need the page background
# and the serif face for their labels.
theme_econblog_void <- function(base_size = 14, base_family = econblog_font_text) {
  ggplot2::theme_void(base_size = base_size, base_family = base_family) +
    ggplot2::theme(
      plot.background   = ggplot2::element_rect(fill = econblog_paper, colour = NA),
      panel.background  = ggplot2::element_rect(fill = econblog_paper, colour = NA),
      legend.background = ggplot2::element_rect(fill = econblog_paper, colour = NA),
      legend.key        = ggplot2::element_rect(fill = econblog_paper, colour = NA),
      plot.title.position = "plot",
      plot.title = ggplot2::element_text(colour = econblog_ink, hjust = 0,
                                         size = ggplot2::rel(1.1),
                                         margin = ggplot2::margin(b = 8)),
      plot.margin = ggplot2::margin(4, 4, 4, 4)
    )
}

if (requireNamespace("ggplot2", quietly = TRUE)) {
  ggplot2::theme_set(theme_econblog())

  # Default mark colour for plots with no colour aesthetic. This is styling: it
  # applies only when nothing is being encoded.
  suppressMessages({
    ggplot2::update_geom_defaults("point",   list(colour = econblog_ink))
    ggplot2::update_geom_defaults("line",    list(colour = econblog_ink))
    ggplot2::update_geom_defaults("smooth",  list(colour = econblog_accent))
    ggplot2::update_geom_defaults("bar",     list(fill   = econblog_ink))
    ggplot2::update_geom_defaults("col",     list(fill   = econblog_ink))
    ggplot2::update_geom_defaults("density", list(colour = econblog_ink))

    # In-figure text and plotmath annotations read as prose/notation, so they
    # take the serif face that MathJax uses rather than the chrome mono.
    ggplot2::update_geom_defaults("text",  list(colour = econblog_ink,
                                                family = econblog_font_text))
    ggplot2::update_geom_defaults("label", list(colour = econblog_ink,
                                                family = econblog_font_text))
  })
}

# --- SVG font embedding -----------------------------------------------------
# An SVG referenced as <img src="...svg"> renders in a sandbox: it cannot fetch
# external resources, and the page's own @font-face rules do not reach inside
# it. Without this, figure labels fall back to whatever the reader's machine
# happens to have. A font embedded as a data URI does work, in both Blink and
# WebKit, so each figure carries the faces it actually uses and nothing more.
#
# The subsets in fonts/subset/ are built by tools-make-figure-fonts.py and are
# committed, so rendering needs no Python.

econblog_embed_svg_fonts <- function(path, options = NULL) {
  if (!grepl("\\.svg$", path)) return(path)

  root <- tryCatch(here::here(), error = function(e) ".")
  faces <- list(
    list(family = econblog_font,      file = file.path(root, "fonts/subset/mono.woff2")),
    list(family = econblog_font_text, file = file.path(root, "fonts/subset/serif.woff2"))
  )

  svg <- readLines(path, warn = FALSE)
  svg <- paste(svg, collapse = "\n")

  # Anything the figure asks for that we cannot embed would be substituted by
  # the reader's machine, so redirect it to the serif. Two ways this arises:
  # plotmath draws Greek and operators through R's "Symbol" font, and some
  # packages hard-code a family of their own (ggdag labels its DAG nodes in
  # Arial). Both emit ordinary Unicode, so the serif renders them correctly.
  ours <- c(econblog_font, econblog_font_text)
  used <- unique(regmatches(svg, gregexpr('(?<=font-family: ")[^"]+', svg, perl = TRUE))[[1]])
  foreign <- setdiff(used, ours)
  for (fam in foreign) {
    svg <- gsub(sprintf('font-family: "%s"', fam),
                sprintf('font-family: "%s"', econblog_font_text), svg, fixed = TRUE)
  }
  if (length(foreign)) {
    # svglite pins each run to the advance width of the font it measured with;
    # left in place, the browser stretches the substituted glyphs to match.
    svg <- gsub(sprintf('(<text[^>]*font-family: "%s";[^>]*?)\\s*textLength=\'[^\']*\'',
                        econblog_font_text), "\\1", svg, perl = TRUE)
    svg <- gsub(sprintf('(<text[^>]*font-family: "%s";[^>]*?)\\s*lengthAdjust=\'[^\']*\'',
                        econblog_font_text), "\\1", svg, perl = TRUE)
  }

  css <- character(0)
  for (f in faces) {
    # only embed a face the figure actually references
    if (!grepl(f$family, svg, fixed = TRUE)) next
    if (!file.exists(f$file)) {
      warning("missing subset font: ", f$file, call. = FALSE)
      next
    }
    b64 <- base64enc::base64encode(f$file)
    css <- c(css, sprintf(
      '@font-face{font-family:"%s";src:url(data:font/woff2;base64,%s) format("woff2");font-display:block;}',
      f$family, b64))
  }
  if (!length(css)) return(path)

  style <- paste0("<style type=\"text/css\">", paste(css, collapse = ""), "</style>")
  # insert immediately after the opening <svg ...> tag
  svg <- sub("(<svg[^>]*>)", paste0("\\1", style), svg)
  writeLines(svg, path)
  path
}

# --- base graphics ----------------------------------------------------------
# knitr resets par() between chunks, so device-level defaults have to be
# reapplied by a hook that runs before each chunk. This reaches the base-R
# posts without any visible code changing.

`%||%` <- function(x, y) if (is.null(x)) y else x

if (requireNamespace("knitr", quietly = TRUE)) {
  knitr::knit_hooks$set(par = function(before, options, envir) {
    if (before) {
      # par() sets one font family for the whole device: there is no way to give
      # axis titles a different face from tick labels, as the ggplot theme does.
      # So when a chunk draws plotmath -- expression() or bquote() -- the whole
      # plot takes the serif face, which keeps its Greek and hats matching the
      # MathJax around it. Chunks without plotmath keep the monospace numerals.
      has_math <- any(grepl("expression\\(|bquote\\(", options$code %||% ""))
      graphics::par(
        family    = if (has_math) econblog_font_text else econblog_font,
        bty       = "n",              # no box; axis lines only
        las       = 1,                # horizontal tick labels
        col.axis  = econblog_muted,
        col.lab   = econblog_muted,
        col.main  = econblog_ink,
        fg        = econblog_muted,
        col        = econblog_ink,
        cex.axis  = 0.9,
        cex.lab   = 1.0,
        cex.main  = 1.1,
        tcl       = -0.3,             # shorter ticks
        mgp       = c(2.4, 0.6, 0),   # tighter label spacing
        mar       = c(4, 4, 2, 1)
      )
    }
  })
  knitr::opts_chunk$set(par = TRUE, fig.process = econblog_embed_svg_fonts)
}
