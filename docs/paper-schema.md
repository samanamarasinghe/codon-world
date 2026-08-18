# Paper entry schema (draft 1)

Repository entries are described in `docs/schema.md`. Papers need their own shape:
`integration_mode` and `codon_features` mean nothing for a work of literature, and
nothing else in the repository vocabulary answers what a paper does with Codon.

Ruling 7 settled two things. `codon_role` is shared with repositories, and papers
get one field of their own. The SDV importance ladder was considered and rejected:
at a hundred-odd works a seven-point scale distinguishes more than the corpus can
support.

## Shared with repositories

| field | notes |
|---|---|
| `id`, `url`, `name`, `summary` | as for repositories; the summary ends by saying what the work does with Codon |
| `codon_role` | `implementation`, `benchmark`, `exploration` -- what Codon is *for* in this work |
| `why_codon`, `why_codon_source` | `stated` or `inferred`, and an inferred value carries the observation it rests on |
| `provenance` | `paper_backed` is meaningless here; papers use `published`, `preprint`, `thesis`, `survey` |
| `confidence` | `high` only where the paper was read, not just its abstract |
| `machine_authored` | as ruling 6 |

## Papers only

`codon_relation` is the paper-side counterpart of `integration_mode`: the mechanism
by which the work touches Codon, recorded separately from how central Codon is to it.

| value | test |
|---|---|
| `extends` | the work builds a compiler, plugin or framework on Codon -- Sequre, Vectron, Shechi |
| `uses` | Codon runs in the work's experiments or pipeline, unmodified |
| `evaluates` | Codon is measured against alternatives, or is one subject of a study |
| `prior_art` | Codon is cited as related work and never run |

The line between `uses` and `prior_art` is whether Codon executed. The line between
`extends` and `uses` is whether the work changed Codon or merely called it.

## Citation metadata

| field | notes |
|---|---|
| `doi` | absent for eight of the harvested works; a landing-page url stands in |
| `year`, `venue` | |
| `cites_anchors` | which anchors the work cites, from `data/papers-candidates.json` |
| `found_in` | `openalex`, `semantic_scholar_only`, or both. Kept because the two sources disagree on a third of the corpus, and a later recall check needs to know which found what |

## What is deliberately absent

No importance score, no popularity signal, no author or affiliation harvest. The
same reasoning as the site's filter panel in `docs/site-filters.md`: at this scale a
graded scale invents precision that the reading cannot support, and a citation count
ranks a survey above the paper that extends the compiler.
