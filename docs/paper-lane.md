# The paper lane

Repositories were the first half of this index. The second is the literature: work
that cites the Codon or Seq papers. This note records the phase 0 sizing, which is
all that has been done so far.

## What was measured

Reverse citations for the four Tier 1 anchors in `data/anchors.json` -- Codon at CC
2023, Seq at OOPSLA 2019, the Nature Biotechnology paper and its bioRxiv preprint --
plus the three Tier 2 Codon-family papers, Sequre twice and Vectron.

Run `python3 harvest/citations.py --write` to regenerate
`data/papers-candidates.json`.

## The result

**109 distinct citing works.** Nine of them cite more than one anchor; one cites four.
Eight have no DOI.

| anchor | cited by |
|---|---|
| Codon, CC 2023 | 33 |
| Sequre, Genome Biology 2023 | 28 |
| Seq, OOPSLA 2019 | 18 |
| Seq, Nature Biotechnology 2021 | 15 |
| Sequre, IPDPSW 2022 | 4 |
| Vectron, CGO 2025 | 4 |
| Seq preprint, bioRxiv 2020 | 3 |

By year: 3 in 2020, 6 in 2021, 6 in 2022, 24 in 2023, 25 in 2024, 26 in 2025, 16 so
far in 2026. Three are undated. The literature is growing steadily rather than
tailing off.

## Neither citation source has recall

OpenAlex returned 77 works. Semantic Scholar returned 32 that OpenAlex does not
hold -- roughly a third of the total, invisible to either source alone. Both are
therefore queried and unioned on normalised title.

This repeats what the Halide lane found, where citation recall varied about fourfold
across sources. It is the same shape as this project's other discovery problem: the
`.codon` extension search and the invocation search returned disjoint repository
populations, and here two citation databases return partly disjoint literatures.

**Google Scholar has not been consulted and usually exceeds both.** Crossref and
OpenCitations are also not unioned in; OpenCitations, which worked for the Halide
lane, now redirects from this environment. 109 is a floor.

## Scale, against the repository half

108 repository entries and at least 109 citing works, so the literature is about the
same size as the code. That is unlike SDV-world, where papers outnumbered
repositories heavily, and unlike Halide-world, whose sizing found 1,316 citing works
from one source before any union.

A lane this size can be read in full rather than sampled.

## What has not been decided

Nothing here is curated. Each work still needs what the repository entries got: the
source read, a summary ending in how it uses or relates to Codon, and a role. The
repository vocabulary does not transfer unchanged -- `integration_mode` and
`codon_features` mean nothing for a paper, and the SDV index's importance ladder,
deliberately not used for repositories here, may be the right model for papers where
`codon_role` is not.

That is the first ruling the lane needs.
