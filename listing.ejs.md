<%
// Custom homepage listing.
//
// Class names are deliberately Quarto's own (.quarto-post, .listing-title,
// .listing-date, .listing-categories, .listing-category). List.js is wired up
// by Quarto against those exact names plus the data- attributes below, so
// reusing them keeps category filtering and search working. What changes here
// is only the ORDER -- the date leads, above the title -- and the removal of
// the thumbnail. Appearance lives in custom.scss.
//
// A custom template receives `items` and `options` only; the `listing` object
// with its utilities is not in scope, so the data- attributes that Quarto's
// built-in template would add are constructed by hand.

const b64 = (s) => {
  if (typeof utils !== 'undefined' && utils && utils.b64encode) return utils.b64encode(s);
  return btoa(encodeURIComponent(s));
};

const epoch = (d) => {
  if (!d) return '';
  const t = (d instanceof Date) ? d.getTime() : Date.parse(d);
  return Number.isNaN(t) ? '' : t;
};

// Quarto builds the excerpt by truncating the post at a fixed length, which on
// a maths-heavy blog often cuts an inline equation in half and leaves a stray
// "$…" or "\(…" dangling at the end. Only strip when a delimiter is genuinely
// unmatched, so descriptions that happen to end in real maths are left alone.
// NOTE: item.description is only a placeholder here -- literally a comment of
// the form <!-- desc(HASH)[max=175]:path -->. Quarto swaps in the real excerpt
// during post-processing, after this template has run, so the truncated text
// cannot be tidied from here. That happens in the browser instead; see
// _listing-tidy.html.
%>
::: {.list .quarto-listing-default}

<% items.forEach(function (item, index) { %>

::: {.quarto-post data-index="<%= index %>" <% if (item.categories) { %>data-categories="<%= b64(item.categories.join(',')) %>"<% } %> data-listing-date-sort="<%= epoch(item.date) %>"}

::: {.body}

```{=html}
<div class="listing-meta">
<% if (item.date) { %><span class="listing-date"><%= item.date %></span><% } %>
<% if (item['reading-time']) { %><span class="listing-reading-time"><%= item['reading-time'] %></span><% } %>
<% if (item.categories) { %><span class="listing-categories">
<% for (const category of item.categories) { %>
<span class="listing-category" onclick="window.quartoListingCategory('<%= b64(category) %>'); return false;"><%= category %></span>
<% } %>
</span><% } %>
</div>
<h3 class="no-anchor listing-title"><a href="<%- item.path %>" class="no-external"><%= item.title %></a></h3>
<% if (item.subtitle) { %>
<div class="listing-subtitle"><a href="<%- item.path %>" class="no-external"><%= item.subtitle %></a></div>
<% } %>
```

<% if (item.description) { %>

```{=html}
<div class="delink listing-description"><a href="<%- item.path %>" class="no-external">
```

<%= item.description %>

```{=html}
</a></div>
```

<% } %>

:::

:::

<% }); %>

:::
