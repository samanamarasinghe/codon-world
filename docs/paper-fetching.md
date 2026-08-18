# Fetching full text for the paper lane

Ruling 8 requires the relation between a paper and Codon to be read from the full
text rather than guessed, and forbids an `unclear` value. This note records the
routes that work, in the order to try them.

## Why abstracts are not enough

The pilot makes the case. Two of its five works read one way from the abstract and
another from the body.

**UniTe** describes a tensor abstraction and never names an implementation language
in its abstract. The body shows CoLa, one of its two realisations, is a DSL built
*inside* Codon: roughly 700 lines of Codon for the frontend and about 7,500 lines of
C++ added to Codon's own compiler, contributing two optimization passes. It also uses
unmodified Codon as its performance baseline. From the abstract this looked like it
might be `prior_art`; it is `extends`.

**PopPy**'s abstract argues that optimizing compilers cannot help when latency sits
in external model calls, which reads as a paper positioning against Codon. The body
cites Codon exactly once, in a related-work list, and never runs it. That is
`prior_art`, but it took the PDF to know rather than assume.

## Routes, in order

1. **arXiv.** `https://arxiv.org/pdf/<id>` with a browser user agent, then `pypdf`.
   Worked for PopPy. Note the arXiv *API* returned nothing for that identifier while
   the PDF path served it, so a failed API lookup is not evidence of absence.

2. **OpenAlex `locations`.** Every location, not just the primary one. UniTe's
   publisher page carries no PDF, but a second location pointed at an open copy in
   DSpace@MIT. Institutional repositories are where MIT-authored closed papers are
   reachable, and this index is full of MIT-authored papers.

3. **Unpaywall**, for anything the first two miss.

4. **Institutional login.** What remains. Pyls at CGO 2026 is the first: OpenAlex
   reports `oa_status: closed` with no location carrying a PDF.

## Reading the citation context

Finding the word Codon in a PDF is not the same as finding how it is used. Author-year
styles put the name in both body and bibliography; numbered styles put it only in the
bibliography, and the body carries a bracketed number.

So: locate the bibliography entry, take its number, then search the body *before* the
bibliography for that number in brackets. PopPy's single inline citation was found
that way and would have been invisible to a search for the word alone.

## Budget

OpenAlex bills per request against a daily allowance rather than rate-limiting, so a
large harvest can exhaust what curation then needs. Its `?search=` endpoint is limited
separately and returns 429 while `/works/doi:` still answers -- resolve by DOI where
possible and pace roughly eight seconds between calls. Semantic Scholar 429s under
sustained use with no key.
