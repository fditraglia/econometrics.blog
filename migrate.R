#!/usr/bin/env Rscript
# Mechanical conversion of Hugo/blogdown .Rmd posts to Quarto .qmd posts
# Run from the repo root: Rscript migrate.R

library(yaml)

# Posts already converted manually
already_done <- c(

  "from-the-poisson-distribution-to-stirling-s-approximation",
  "sims-and-uhlig-1991-replication"
)

# Hugo YAML fields to drop (keep: title, author, date, categories, tags)
drop_fields <- c("slug", "lastmod", "featured", "image", "projects",
                  "authors", "subtitle", "summary", "linktitle")

# Chunk option name mapping: R Markdown → Quarto
opt_name_map <- c(
  "fig.width"  = "fig-width",
  "fig.height" = "fig-height",
  "fig.cap"    = "fig-cap",
  "fig.align"  = "fig-align",
  "out.width"  = "out-width",
  "out.height" = "out-height"
)

# Convert a single R chunk option value to Quarto YAML value
convert_opt_value <- function(val) {
  val <- trimws(val)
  # Strip outer quotes
  if (grepl("^['\"].*['\"]$", val)) {
    val <- gsub("^['\"]|['\"]$", "", val)
  }
  # TRUE/FALSE → true/false
  if (toupper(val) == "TRUE") return("true")
  if (toupper(val) == "FALSE") return("false")
  val
}

# Parse chunk header and return converted lines
convert_chunk_header <- function(line) {
  # Match ```{r ...}
  m <- regmatches(line, regexec("^```\\{r([^}]*)\\}", line))[[1]]
  if (length(m) < 2) return(line)  # not a match

  inside <- trimws(m[2])
  if (nchar(inside) == 0) return("```{r}")

  # Remove leading comma if present
  inside <- sub("^,\\s*", "", inside)

  # Split on commas, respecting quoted strings
  # Simple approach: split on commas not inside quotes
  parts <- strsplit(inside, ",(?=(?:[^'\"]*['\"][^'\"]*['\"])*[^'\"]*$)", perl = TRUE)[[1]]
  parts <- trimws(parts)

  label <- NULL
  opts <- list()

  for (i in seq_along(parts)) {
    p <- parts[i]
    if (grepl("=", p)) {
      # It's an option: key = value
      kv <- strsplit(p, "\\s*=\\s*", perl = TRUE)[[1]]
      key <- trimws(kv[1])
      val <- trimws(paste(kv[-1], collapse = "="))
      # Map option name if needed
      if (key %in% names(opt_name_map)) key <- opt_name_map[key]
      opts[[key]] <- convert_opt_value(val)
    } else if (i == 1 && !grepl("=", p)) {
      # First part without = is the chunk label
      label <- trimws(p)
    }
  }

  # Build output lines
  result <- "```{r}"
  if (!is.null(label)) {
    result <- c(result, paste0("#| label: ", label))
  }
  for (nm in names(opts)) {
    result <- c(result, paste0("#| ", nm, ": ", opts[[nm]]))
  }
  result
}

# Convert %>% to |> (only in code chunks)
convert_pipes <- function(lines) {
  in_chunk <- FALSE
  for (i in seq_along(lines)) {
    if (grepl("^```\\{r", lines[i])) {
      in_chunk <- TRUE
    } else if (in_chunk && grepl("^```\\s*$", lines[i])) {
      in_chunk <- FALSE
    }
    if (in_chunk) {
      lines[i] <- gsub("%>%", "|>", lines[i])
    }
  }
  lines
}

# Extract slug from Hugo frontmatter
extract_slug <- function(fm) {
  if (!is.null(fm$slug)) return(fm$slug)
  # Fallback: derive from directory name
  NULL
}

# Convert YAML frontmatter
convert_frontmatter <- function(fm) {
  # Keep only desired fields
  keep <- fm[!names(fm) %in% drop_fields]
  # Ensure categories and tags are present
  if (is.null(keep$categories)) keep$categories <- list()
  if (is.null(keep$tags)) keep$tags <- list()
  keep
}

# Process a single post
process_post <- function(post_dir) {
  rmd_path <- file.path(post_dir, "index.Rmd")
  if (!file.exists(rmd_path)) {
    message("  SKIP: no index.Rmd in ", post_dir)
    return(NULL)
  }

  raw <- readLines(rmd_path, warn = FALSE)

  # Find YAML boundaries
  yaml_markers <- which(raw == "---")
  if (length(yaml_markers) < 2) {
    message("  SKIP: can't find YAML frontmatter in ", rmd_path)
    return(NULL)
  }

  yaml_text <- paste(raw[(yaml_markers[1] + 1):(yaml_markers[2] - 1)],
                     collapse = "\n")
  fm <- yaml::yaml.load(yaml_text)
  slug <- extract_slug(fm)
  if (is.null(slug)) {
    # Derive from directory name: strip date prefix
    dirname <- basename(post_dir)
    slug <- sub("^\\d{4}-\\d{2}-\\d{2}-", "", dirname)
  }

  # Skip if already done
  if (slug %in% already_done) {
    message("  SKIP (already converted): ", slug)
    return(NULL)
  }

  # Convert frontmatter
  new_fm <- convert_frontmatter(fm)
  new_yaml <- yaml::as.yaml(new_fm)

  # Get body (after YAML)
  body <- raw[(yaml_markers[2] + 1):length(raw)]

  # Convert chunk headers
  new_body <- character(0)
  for (line in body) {
    if (grepl("^```\\{r", line)) {
      new_body <- c(new_body, convert_chunk_header(line))
    } else {
      new_body <- c(new_body, line)
    }
  }

  # Convert pipes in code chunks
  new_body <- convert_pipes(new_body)

  # Assemble output
  output <- c("---", strsplit(sub("\n$", "", new_yaml), "\n")[[1]], "---",
              new_body)

  # Create output directory
  out_dir <- file.path("post", slug)
  dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  out_path <- file.path(out_dir, "index.qmd")
  writeLines(output, out_path)

  # Flag potential issues
  flags <- character(0)

  # Check for $$\begin{align in body
  body_text <- paste(new_body, collapse = "\n")
  if (grepl("\\$\\$\\s*\n\\\\begin\\{align", body_text)) {
    flags <- c(flags, "align* wrapped in $$ (may work in HTML but check)")
  }

  # Check for unusual packages
  pkg_lines <- grep("^library\\(", new_body, value = TRUE)
  unusual <- grep("rcovidUK|ManyIV|ivreg|ggdag|estimatr|plotrix", pkg_lines, value = TRUE)
  if (length(unusual) > 0) {
    flags <- c(flags, paste("Unusual package:", unusual))
  }

  # Check for external data loading
  if (any(grepl("read_csv|read\\.csv|readRDS|load\\(", new_body))) {
    flags <- c(flags, "External data loading detected")
  }

  # Check for tikz
  if (any(grepl("tikz", new_body, ignore.case = TRUE))) {
    flags <- c(flags, "TikZ content detected")
  }

  list(slug = slug, path = out_path, flags = flags)
}

# --- Main ---
message("=== Quarto Migration Script ===\n")

post_dirs <- list.dirs("content/post", recursive = FALSE)
post_dirs <- sort(post_dirs)

results <- list()
for (d in post_dirs) {
  message("Processing: ", basename(d))
  res <- process_post(d)
  if (!is.null(res)) results[[length(results) + 1]] <- res
}

message("\n=== Summary ===")
message("Converted: ", length(results), " posts\n")

# Report flags
has_flags <- Filter(\(r) length(r$flags) > 0, results)
if (length(has_flags) > 0) {
  message("=== Posts with potential issues ===")
  for (r in has_flags) {
    message("\n", r$slug, ":")
    for (f in r$flags) message("  - ", f)
  }
} else {
  message("No potential issues flagged.")
}
