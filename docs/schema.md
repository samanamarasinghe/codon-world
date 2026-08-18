# Repo entry schema (draft 5)

Codon-world goes deeper per entry than the SDV index did, because the population is
smaller. Every repo entry carries the SDV fields (url, summary, authors, use case)
plus the fields below.

## Integration mode

One value, decided by what the repo actually contains:

| value | test |
|---|---|
| `source` | own Codon source, in `.codon` files or in `.py` |
| `c_api_frontend` | Codon drives a C or C++ core through `from C import` declarations |
| `jit_decorator` | Python files using `@codon.jit` |
| `ir_plugin` | C++ against `codon/cir` or `codon/dsl`, a compiler pass rather than a program |
| `runtime_port` | Codon's C++ runtime retargeted to another environment (WASM, bare metal) |
| `packaging` | Codon itself packaged, built or tracked for distribution to others |
| `vendored_install` | ships a Codon installation; no own source |
| `docs_mirror` | a copy of the Codon documentation |
| `mention_only` | names Codon in prose, runs none of it |
| `false_positive` | `.codon` files that are codon-usage tables, codeml alignments, or agent notation |

A repo may carry `integration_mode_secondary` where it does two things at once --
Sequre and Shechi are both `source` and `ir_plugin`, and scATAC-seq is `source` and
`vendored_install`.

`first_party: true` marks Exaloop's own repositories.

## How Codon is reached

`codon_via` records whether Codon is used directly or through something else:

| value | test |
|---|---|
| `direct` | the repo invokes Codon itself |
| `plugin` | the repo runs `codon run -plugin X`, loading another project's Codon plugin |
| `framework` | the repo is written against a Codon framework and never names Codon |

`codon_version_pinned` records an exact version where the repo pins one. Worth
collecting: across the index it dates each adoption, and the packaging lane pins
everything from 0.15.1 to 0.19.6.

## What Codon is for here

`codon_role`, closed by ruling 5: `implementation`, `benchmark`, `exploration`.
The line between the last two is whether a comparison is actually published.

`machine_authored: true` marks code or documentation a model wrote (ruling 6).

## Codon features exercised

Counted over own source only. `par`, `gpu`, `llvm_inline`, `pipeline`,
`python_interop`, `c_interop`, `numpy`, `static_typing`, `seq_plugin`, `tuple`.
Counts are occurrences plus the number of distinct files carrying them -- a
feature confined to one generated file means something different from one spread
across thirty.

Entries whose Codon lives in `.py` files, or that were read through the JIT,
mention and packaging lanes, carry no feature counts. Their scale reads zero for the
same reason: the counters key on the `.codon` extension.

## Scale

`own_codon_files`, `own_codon_loc`, `vendored_stdlib_files`. Reported separately;
a repo with 151 files of which 140 are a vendored stdlib is a small repo.

Scale in `.codon` lines is not scale of the project. codonx is a Rust tool with a
thirteen-line Codon fixture; jutge-tests is ten files holding fifteen lines in
total. Neither should be ranked by `.codon` volume alone.

## Why Codon

The performance claim the repo itself makes, with any benchmark number it reports.

Where the repo makes no such claim, an inference is allowed but must be marked:
`why_codon_source` is `stated` or `inferred`, and an `inferred` value carries the
observation it rests on. FLOX is the case that forced this -- it declares 1,347 C
entry points and claims nothing about Codon anywhere.

## Provenance

`paper_backed` (with the DOI), `production`, `research_prototype`, `coursework`,
`toy`, `doc_mirror`.

Coursework and documentation mirrors are INCLUDED as entries, not filtered out.
So are repos that vendor a Codon installation -- their scale is reported at their
own source size, with the vendored stdlib counted separately and never folded in.

## Sidecars: recorded, but not entries

Two files under `data/entries/` are not lists of entries but a single wrapper object
with a `_class` key and a `repos` list. `build.py` keeps each in its own section and
never merges them into the entry count.

| class | what it holds |
|---|---|
| `false_positive/genetics` | 11 repos whose `.codon` files are codon-usage tables or codeml alignments |
| `fork_of_packaging` | 23 forks carrying a packaging recipe already indexed upstream |

Both exist for the same reason: a raw repository count of a search signal measures
redistribution rather than adoption. Six of the eleven genetics repos carry one
nematode gene-finder table; nineteen of the twenty-three forks carry one termux
recipe. Recording them stops a later pass rediscovering them as candidates.

The two agent-notation false positives are full entries rather than sidecar rows,
because each needed its own reading to establish what the file actually was.

## Health

`last_commit`, `stars`, `license`, `ci_builds_codon` with the workflow paths.

## Evidence

Path plus a short quote for every non-obvious field, as in the SDV index.
`confidence: high` only where the source was read.
