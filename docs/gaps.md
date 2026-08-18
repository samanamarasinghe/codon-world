# Known gaps in the discovery method

## Codon source does not have to be in a `.codon` file

Codon compiles `.py` directly. The population in `data/repos-candidates.json` was
enumerated from `extension:codon`, so any repo that writes Codon in `.py` files is
invisible to it.

This is not hypothetical. `chase2512/fall25-csc-bioinf` is a CSC427 student repo
with zero `.codon` files; its Codon ports are named `nj_codon.py`,
`upgma_codon.py`, `__init___codon.py`, and its week 3 evaluation script runs the
Python and Codon versions of the same algorithm and prints a runtime table. It
entered the index only because it happened to mention `codon.jit` in a notes file.

Seven of its eight coursemates use `.codon`, so within this course the convention
is nearly uniform and the miss rate looks low. Outside a course with a shared
harness there is no reason to expect that.

### What a closing pass would need

Neither of the obvious searches works on its own. Searching `codon run` in shell
scripts, CI and Makefiles catches invocations but not libraries. Searching for
`.py` files containing `@par` or `from python import` catches Codon-specific
syntax but misses ported Python that uses none, which is most of the coursework
case. A CI-based sweep -- workflows that download `exaloop/codon` releases -- would
have caught every CSC427 repo including this one, and is the most promising single
signal.

Until that pass is run, the population figure should be read as a floor, not a
count.

## Naming collisions keep appearing

Three classes of `.codon` file are not Codon source:

- codon-usage tables and codeml alignments in genetics, eleven repos
- agent notation: markdown or YAML seeds using `.codon` as a private extension,
  two repos so far, both created in 2026
- documentation mirrors, which carry Codon's own examples rather than a user's

The genetics collision is decades old and stable. The agent-notation one is new and
should be expected to grow.
