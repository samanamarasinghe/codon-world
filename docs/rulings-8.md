## 8. No `unclear` relation: papers are resolved from full text

Asked whether to add a fifth `codon_relation` value for papers whose relation cannot
be determined, or to resolve each case from the full text, he took the second.

So `codon_relation` stays at four values and there is no way to record an unresolved
relation. A paper whose relation is not yet established carries the field **absent**
plus a `needs`, and stays that way until someone reads it. This is stricter than the
SDV index, which has an `unclear` value.

The cost is real and was visible immediately: of the five pilot papers, three were
resolved from full text, one remains at abstract-only confidence, and one -- Pyls at
CGO 2026 -- is closed access with no open copy anywhere, so it cannot be resolved
without an institutional login. Routes and their order are in `docs/paper-fetching.md`.

The ruling was worth its cost on the first attempt. UniTe reads like `prior_art` from
its abstract and is `extends`: CoLa adds roughly 7,500 lines of C++ to Codon's own
compiler. An `unclear` value would have let that stand unread.
