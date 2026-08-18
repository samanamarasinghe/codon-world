# The site

<https://samanamarasinghe.github.io/codon-world/>

One page. It reads `data/codon-index.json` and renders every entry with its filters
applied client-side. There is no server and no framework.

## Files

| Path | What it is |
|---|---|
| `index.html` | The page. Control markup and the tooltip text for every filter. |
| `assets/js/codon-index.js` | All behaviour: facet counting, filtering, grouping, sorting, rendering. |
| `assets/css/style.css` | Styling. |
| `build.py` | Merges `data/entries/*.json` and `data/pilot/*.json` into `data/codon-index.json`. Fails on duplicate ids. |
| `.github/workflows/build.yml` | Runs `build.py --write` on every push, commits the result if it changed, then publishes the site to GitHub Pages. |

The generated `data/codon-index.json` is not edited by hand and is not the source of
truth. The per-lane files under `data/entries/` are. To add or correct an entry, edit
the lane file; CI rebuilds the index.

## Which filters exist, and why those

See `docs/site-filters.md` for the full comparison against the SDV-world panel,
including what was dropped and for what reason. In short: everything that depended on
harvested popularity, author or affiliation data was dropped because none of it was
collected, and five controls with no SDV equivalent were added — Codon role, how Codon
is reached, provenance, evidence quality, and the machine-authored flag.

## Two things the page says out loud

**The header count is a floor, not a count.** The round-two closing pass found 58 more
repositories that the `.codon` extension search could not see, and none of them is in
the index yet. `docs/gaps.md` explains why the extension search misses them.

**Codon lines of code is not project size.** It is the default sort because nothing
better was harvested, and the tooltip on the sort control says what it costs: codonx is
a Rust tool with a thirteen-line Codon fixture, and jutge-tests is ten files holding
fifteen lines in total. Both outrank substantial projects on this measure.

## The evidence filter

Worth knowing before reading entries: 45 of the 73 rest on an inference rather than
anything the repository says. Most repositories that use Codon never mention it. Every
entry prints its reasoning, prefixed *Stated* or *Inferred*, and the inferred ones name
the observation the reading rests on. Selecting **Stated by the repo** under Evidence
leaves only the entries where the project makes the claim itself.

## Testing the page without a browser

The filters are the part that breaks silently: a filtering bug shows up in the header
count and nothing in the repository checks it. A stub-DOM harness does — roughly forty
lines of fake `document` and `fetch` in node, `vm.runInThisContext` on the real
`assets/js/codon-index.js`, then read `count.textContent` and drive the facets through
`window._codonIndex.state` and `render()`.

Run it after any change to the JS and compare the counts against the data: 73 at the
default, 11 for Codon role Benchmark, 26 for Evidence Stated, 3 for feature GPU.
