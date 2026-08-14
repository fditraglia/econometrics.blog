-- Computes each post's reading time and stores it in metadata, where the
-- title-block partial (_partials/title-block.html) prints it in the eyebrow
-- line. Runs as a Pandoc filter at render time, after knitr, so it counts the
-- prose a reader actually sees and needs no R and no JavaScript.
--
-- 200 words a minute, matching the rate Quarto's own listing reading-time
-- field assumes, so the index and the post page agree.

function Pandoc(doc)
  local words = 0
  local filter = {
    Str = function(el)
      if el.text:match("%w") then words = words + 1 end
    end,
    Code = function(el)
      local _, n = el.text:gsub("%S+", "")
      words = words + n
    end,
    CodeBlock = function(el)
      local _, n = el.text:gsub("%S+", "")
      words = words + n
    end
  }
  for _, block in ipairs(doc.blocks) do
    pandoc.walk_block(block, filter)
  end
  local mins = math.max(1, math.floor(words / 200 + 0.5))
  doc.meta["reading-time"] = pandoc.MetaString(mins .. " min")
  return doc
end
