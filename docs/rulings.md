# Rulings

His calls, in the order they were made. Entries carry `needs` until a ruling lands
here; nothing is decided on his behalf.

## 1. Inferred why_codon is allowed, but must be marked

Where a repo makes no claim about Codon, an inference may be recorded. It carries
`why_codon_source: inferred` and states the observation it rests on. Forced by FLOX,
which declares 1,347 C entry points and says nothing about Codon anywhere.

## 2. Coursework and documentation mirrors are entries

Not filtered out. The fall25-csc-bioinf student repos and the three `mpearrow`
documentation copies are indexed like anything else.

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

## Open, awaiting a ruling

- `codon_role`: added in the bioinformatics lane to separate repos that use Codon
  to build something from repos that evaluate Codon against alternatives. Triton-Seq
  is the case: Codon is one of six DSLs it benchmarks, not what it is built on.
  Provisional values `implementation`, `evaluated_alternative`, `exploration`.
