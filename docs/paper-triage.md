# Triaging the paper corpus: a negative result

The plan was to read all 109 abstracts, sort the works that plausibly extend or run
Codon from the ones that merely cite it, and full-text only the first group. That
would have traded some confidence for a great deal of speed.

**It does not work, and the reason is structural.**

## What was measured

Abstracts were pulled for 95 of the 109 works -- 8 have no DOI and 6 more had no
OpenAlex abstract -- and searched for any mention of Codon, Seq, Sequre or Exaloop.

| result | works |
|---|---|
| abstract names Codon or a family project | 9 |
| abstract does not | 72 |
| no abstract available | 28 |

Of those 9, five are the anchors and family papers themselves, not third-party work.
So the abstract signal identifies roughly four candidate papers out of a hundred.

## Why

An abstract states what a paper contributes. A citation of a tool the paper does not
contribute almost never appears there, and a citation of a tool the paper *does* build
on often does not either -- UniTe builds a DSL inside Codon by adding 7,500 lines to
its compiler, and its abstract does not name a language at all.

The pilot had already shown this from the other direction: two of five works read one
way from the abstract and another from the body. A triage built on abstracts would
inherit exactly that error rate, and it would inherit it silently, because the works
it filtered out would never be checked.

The informative signal -- how a paper cites Codon, and whether it runs it -- lives in
one sentence of the body, usually attached to a bracketed reference number. That is
precisely what ruling 8 requires reading, and there is no cheaper place to find it.

## What the triage did produce

Two useful things, neither of them the intended one.

**A contamination bug.** Five of the 109 harvested works are the anchors themselves,
picked up because the Codon family papers cite each other. Codon CC 2023, Sequre,
both Seq papers and Vectron all appear in their own citing-work list. The harvester
must exclude anchor DOIs. Left in, they would have become entries duplicating
`data/anchors.json`.

**A fetch plan by access.** Of the 109: 70 are openly fetchable (gold, green, hybrid,
diamond or bronze), 30 are closed, and 9 have no status recorded. So roughly two
thirds can be read without an institutional login, which sets the shape of the work:
batch the open ones, accumulate the closed ones, and hand that list over once.

The corpus also splits cleanly by anchor group: 69 works cite a Codon or Seq paper,
36 cite only Sequre. The Sequre-only group is mostly secure-computation and medical
privacy literature, where Codon is reached at one remove if at all, and it is the
natural batch to read last.

## The revised plan

No triage. Read full text in batches of four or five, openly available works first,
ordered by anchor group. The closed thirty accumulate into a single list for his
institutional access rather than blocking the lane one paper at a time.
