<%
// Custom homepage listing: one page, two server-rendered views.
//
// The page renders, in order: a hero for the latest post, a "Contents" head
// with a BY SUBJECT / BY DATE toggle, the subject view (default), the puzzler
// block, the date view (hidden until toggled), a hidden block of margin
// content that _theme.html moves into the margin sidebar, and finally a
// hidden flat list of per-post stubs.
//
// The stubs are what keep Quarto's machinery working. Quarto wires List.js to
// the children of the .list element, and the category filter works by asking
// List.js to hide and show those children. The visible views are NOT List.js
// items -- each line carries data-indexes instead, and _theme.html listens to
// List.js updates and mirrors its filter state onto the lines. The feed is
// generated from the listing config independently of this template.
//
// The subject each post belongs to is its `subject:` front-matter field; the
// five section labels here must match those fields exactly. Series collapse
// onto one line via the `series:` / `series-label:` fields.

const SUBJECTS = [
  "Causal inference & identification",
  "Inference & uncertainty",
  "Econometric theory",
  "Teaching & explainers",
  "Computing & applied work",
];
const ROMAN = ["I", "II", "III", "IV", "V"];
const MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
                "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];
const WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven",
               "eight", "nine", "ten", "eleven", "twelve"];
const numWord = (n) => (WORDS[n] || String(n));

const b64 = (s) => {
  if (typeof utils !== 'undefined' && utils && utils.b64encode) return utils.b64encode(s);
  return btoa(encodeURIComponent(s));
};

const epoch = (item) => {
  const sv = item.sortableValues && item.sortableValues.date;
  const t = sv ? Number(sv) : Date.parse(item.date);
  return Number.isNaN(t) ? 0 : t;
};

const cats = (item) => item.categories || [];
const yearOf = (item) => new Date(epoch(item)).getFullYear();
const dayMonth = (item) => {
  const d = new Date(epoch(item));
  return String(d.getDate()).padStart(2, "0") + " " + MONTHS[d.getMonth()];
};

// Escape for HTML text content; titles routinely contain apostrophes only,
// but be safe about the rest.
const esc = (s) => String(s == null ? "" : s)
  .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

// Every item, newest first.
const all = items.slice().sort((a, b) => epoch(b) - epoch(a));
all.forEach((it, i) => { it.__idx = i; });

const latest = all[0];
const firstYear = Math.min.apply(null, all.map(yearOf));
const puzzlers = all.filter((it) => cats(it).includes("puzzler"));
const notes = all.filter((it) => cats(it).includes("meta"));

// One line per post, or per series. A line remembers which item indexes it
// stands for so the category filter can hide it.
const lineFor = (group) => {
  group.sort((a, b) => epoch(a) - epoch(b)); // parts in order of publication
  const first = group[0];
  const idxs = group.map((it) => it.__idx).join(",");
  const allCats = [...new Set(group.flatMap(cats))];
  const years = [...new Set(group.map(yearOf))].join(", ");
  let html = "";
  if (group.length === 1) {
    html = `<a href="${first.path}" class="no-external">${esc(first.title)}</a>`;
  } else if (first.series && first.title === first.series) {
    // "A Good Instrument is a Bad Control <em>& Part II</em>"
    const rest = group.slice(1).map((it) =>
      `<a href="${it.path}" class="no-external">&amp; ${esc(it["series-label"] || "Part II")}</a>`).join(" ");
    html = `<a href="${first.path}" class="no-external">${esc(first.series)}</a> <span class="series-suffix">${rest}</span>`;
  } else {
    // "Street Fighting Numerical Analysis <em>Parts 1 & 2</em>"
    const nums = group.map((it) =>
      `<a href="${it.path}" class="no-external">${esc(String(it["series-label"] || "").replace(/^Part\s+/, ""))}</a>`);
    const seq = nums.length === 2 ? nums.join(" &amp; ")
      : nums.slice(0, -1).join(", ") + " &amp; " + nums[nums.length - 1];
    html = `<a href="${first.path}" class="no-external">${esc(first.series)}</a> <span class="series-suffix">Parts ${seq}</span>`;
  }
  return { html, years, idxs, cats: allCats, sortEpoch: epoch(group[group.length - 1]) };
};

// Build each subject section: group its posts, fold series together, newest
// line first.
const sections = SUBJECTS.map((label, s) => {
  const posts = all.filter((it) => it.subject === label);
  const bySeries = new Map();
  const groups = [];
  for (const it of posts) {
    if (it.series) {
      if (!bySeries.has(it.series)) { bySeries.set(it.series, []); groups.push(bySeries.get(it.series)); }
      bySeries.get(it.series).push(it);
    } else {
      groups.push([it]);
    }
  }
  const lines = groups.map(lineFor).sort((a, b) => b.sortEpoch - a.sortEpoch);
  return { label, numeral: ROMAN[s], posts, lines };
});

// Date view: years, newest first.
const years = [...new Set(all.map(yearOf))].sort((a, b) => b - a);

const lineAttrs = (l) =>
  `data-indexes="${l.idxs}" data-categories="${b64(l.cats.join(","))}"`;
%>

```{=html}
<div class="home-hero" data-indexes="<%= latest.__idx %>" data-categories="<%= b64(cats(latest).join(',')) %>">
  <div class="hero-text">
    <p class="hero-eyebrow">Latest &mdash; <%= dayMonth(latest) %> <%= yearOf(latest) %></p>
    <h2 class="hero-title"><a href="<%= latest.path %>" class="no-external"><%= latest.title %></a></h2>
    <div class="hero-description listing-description"><a href="<%= latest.path %>" class="no-external"><%= latest.description %></a></div>
  </div>
  <% if (latest.image) { %>
  <div class="hero-figure">
    <a href="<%= latest.path %>" class="no-external"><img src="<%= latest.image %>" alt="<%= latest['image-alt'] || '' %>"></a>
  </div>
  <% } %>
</div>

<div class="home-contents-head">
  <h2 class="home-contents-title" id="contents">Contents</h2>
  <div class="view-toggle" role="group" aria-label="Arrange the contents">
    <button type="button" class="toggle-subject active" aria-pressed="true">By subject</button>
    <button type="button" class="toggle-date" aria-pressed="false">By date</button>
  </div>
</div>

<div class="view-by-subject">
<% sections.forEach(function (sec) { %>
  <section class="subject-section">
    <div class="subject-head">
      <span class="subject-numeral"><%= sec.numeral %>.</span>
      <h3 class="subject-title"><%= sec.label %></h3>
      <span class="subject-rule"></span>
      <span class="subject-count" data-total="<%= sec.posts.length %>"><%= sec.posts.length %></span>
    </div>
    <% sec.lines.forEach(function (l, i) { %>
    <div class="post-line<%= i >= 4 ? ' more-line' : '' %>" <%= lineAttrs(l) %>>
      <span class="post-line-title"><%= l.html %></span>
      <span class="post-line-years"><%= l.years %></span>
    </div>
    <% }); %>
    <% if (sec.lines.length > 4) { %>
    <button type="button" class="more-toggle"><%= numWord(sec.lines.length - 4) %> more</button>
    <% } %>
  </section>
<% }); %>

  <div class="puzzler-block" data-indexes="<%= puzzlers.map(p => p.__idx).join(',') %>" data-categories="<%= b64('puzzler') %>">
    <span class="puzzler-count"><%= puzzlers.length %></span>
    <div class="puzzler-body">
      <p class="puzzler-label">The puzzlers</p>
      <p class="puzzler-text">Short problems that test econometric intuition. Read the
      question, think, then open the fold.
      <em><a href="#category=puzzler" class="puzzler-so-far no-external"><%= numWord(puzzlers.length).replace(/^./, c => c.toUpperCase()) %> so far.</a></em></p>
    </div>
  </div>
</div>

<div class="view-by-date">
<% years.forEach(function (y) {
     const posts = all.filter((it) => yearOf(it) === y); %>
  <section class="year-section">
    <div class="year-head">
      <h3 class="year-title"><%= y %></h3>
      <span class="year-rule"></span>
      <span class="year-count" data-total="<%= posts.length %>"><%= posts.length %></span>
    </div>
    <% posts.forEach(function (it) { %>
    <div class="date-line" data-indexes="<%= it.__idx %>" data-categories="<%= b64(cats(it).join(',')) %>">
      <span class="date-line-date"><%= dayMonth(it) %></span>
      <span class="date-line-title"><a href="<%= it.path %>" class="no-external"><%= it.title %></a></span>
      <span class="date-line-time"><%= it['reading-time'] || '' %></span>
    </div>
    <% }); %>
  </section>
<% }); %>
</div>

<div class="home-margin-source">
  <div class="home-margin">
    <p class="home-margin-count"><%= all.length %> posts since <%= firstYear %></p>
    <p class="home-margin-description">Puzzles, intuitions, and sundry economic tricks.</p>
    <p class="home-margin-also-label">Also</p>
    <ul class="home-margin-also">
      <li><a href="#category=puzzler" onclick="window.quartoListingCategory('<%= b64('puzzler') %>'); return false;">Puzzlers <span class="also-count"><%= puzzlers.length %></span></a></li>
      <li><a href="#category=meta" onclick="window.quartoListingCategory('<%= b64('meta') %>'); return false;">Odds &amp; ends <span class="also-count"><%= notes.length %></span></a></li>
    </ul>
  </div>
</div>

<div class="list quarto-listing-default">
<% all.forEach(function (item) { %>
  <div class="quarto-post" data-index="<%= item.__idx %>" <% if (item.categories) { %>data-categories="<%= b64(item.categories.join(',')) %>"<% } %> data-listing-date-sort="<%= epoch(item) %>">
    <h3 class="no-anchor listing-title"><a href="<%= item.path %>" class="no-external"><%= item.title %></a></h3>
  </div>
<% }); %>
</div>
```
