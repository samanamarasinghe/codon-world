# Rulings

His calls, in the order they were made. Entries carry `needs` until a ruling lands
here; nothing is decided on his behalf.

## 1. Inferred why_codon is allowed, but must be marked

Where a repo makes no claim about Codon, an inference may be recorded. It carries
`why_codon_source: inferred` and states the observation it rests on. Forced by FLOX,
which declares 1,347 C entry points and says nothing about Codon anywhere.

## 2. Coursework and documentation mirrors are entries

Not filtered out. The CSC427 student repos and the three `mpearrow` documentation
copies are indexed like anything else.

## 3. Vendored installs are entries

A repo that ships a Codon installation is indexed at the size of its own source,
with the vendored stdlib counted separately in `vendored_stdlib_files` and never
folded into `own_codon_loc`.

## 4. Shechi stays a separate entry from Sequre

87 of Shechi's 88 `.codon` paths also exist in `0xTCG/sequre` and 20 are
byte-identical, but the two are distinct papers -- Sequre in Genome Biology 2023,
Shechi at USENIX Security 2025. The SDV published-survives rule does not transfer,
because neither is a version of the other. Two entries; the shared codebase is
recorded by `derived_from`.

## 5. Benchmark use is recorded as benchmark use

A repo that uses Codon to benchmark is an entry like any other, and the fact is
recorded rather than inferred away. `codon_role` closes as three values:

| value | test |
|---|---|
| `implementation` | Codon builds the thing the repo is for |
| `benchmark` | Codon is measured against alternatives, or used to run the measurement |
| `exploration` | Codon is tried out with no comparison published |

This replaces the provisional `evaluated_alternative`, which was renamed to
`benchmark` across all existing entries.

The `benchmark` / `exploration` line is drawn on whether a comparison is actually
published, not on whether one could be made. tsp-solver has a Python counterpart to
its single Codon file and reports no timings, so it is `exploration`; mce-sandbox
names its three implementation technologies and labels what each Codon variant
exercises, so it is `benchmark`.

## 6. Machine-authored Codon is flagged, not excluded

`machine_authored: true` marks code a model wrote rather than a person. The entry
stays in the index and keeps its ordinary role and provenance; the flag records how
the code came to exist. First and so far only case: PL-ultimate-llm, where a model
chose Codon at random and wrote an eighteen-line Fibonacci program.

## Open, awaiting a ruling

- **A `thesis` provenance value.** RedKinda/mojo-benchmarks is 2024 Bachelor's
  thesis work, currently filed `coursework` because nothing closer exists.

- **Whether to run the `.py` closing pass.** Codon compiles `.py` directly, so the
  `extension:codon` enumeration has a blind spot. See `docs/gaps.md`; one repo
  already in the index was caught only by accident.
