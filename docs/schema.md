# Repo entry schema (draft 2)

Codon-world goes deeper per entry than the SDV index did, because the population is
smaller. Every repo entry carries the SDV fields (url, summary, authors, use case)
plus the fields below.

## Integration mode

One value, decided by what the repo actually contains:

| value | test |
|---|---|
| `source` | own `.codon` files that are not a vendored stdlib copy |
| `c_api_frontend` | Codon drives a C or C++ core through `from C import` declarations |
| `jit_decorator` | Python files using `@codon.jit` |
| `ir_plugin` | C++ against `codon/cir`, a compiler pass rather than a program |
| `vendored_install` | ships a Codon installation; no own source |
| `docs_mirror` | a copy of the Codon documentation |
| `mention_only` | names Codon in prose, runs none of it |
| `false_positive` | `.codon` files that are codon-usage tables or codeml alignments |

## Codon features exercised

Counted over own source only. `par`, `gpu`, `llvm_inline`, `pipeline`,
`python_interop`, `c_interop`, `numpy`, `static_typing`, `seq_plugin`.
Counts are occurrences plus the number of distinct files carrying them -- a
feature confined to one generated file means something different from one spread
across thirty.

## Scale

`own_codon_files`, `own_codon_loc`, `vendored_stdlib_files`. Reported separately;
a repo with 151 files of which 140 are a vendored stdlib is a small repo.

## Why Codon

The performance claim the repo itself makes, with any benchmark number it reports.

Where the repo makes no such claim, an inference is allowed but must be marked:
`why_codon_source` is `stated` or `inferred`, and an `inferred` value carries the
observation it rests on. FLOX is the case that forced this -- it declares 1,347 C
entry points and claims nothing about Codon anywhere, so the reading that Codon is
the native-speed strategy surface is an inference from the binding layer.

## Provenance

`paper_backed` (with the DOI), `production`, `research_prototype`, `coursework`,
`toy`, `doc_mirror`.

Coursework and documentation mirrors are INCLUDED as entries, not filtered out.
So are repos that vendor a Codon installation -- their scale is reported at their
own source size, with the vendored stdlib counted separately and never folded in.
Only `false_positive` is an exclusion: `.codon` files that are codon-usage tables
or codeml alignments and have nothing to do with the language.

## Health

`last_commit`, `stars`, `license`, `ci_builds_codon` with the workflow paths.

## Evidence

Path plus a short quote for every non-obvious field, as in the SDV index.
`confidence: high` only where the source was read.
