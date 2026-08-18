#!/usr/bin/env python3
"""Extract Codon citation contexts from papers downloaded by hand.

    python3 harvest/ingest_local.py --dir pdfs                 # report only
    python3 harvest/ingest_local.py --dir pdfs --write         # write the contexts file
    python3 harvest/ingest_local.py --dir pdfs --manifest pdfs/manifest.json

`harvest/fetch_contexts.py` reaches everything that is openly available. What it
cannot reach -- Elsevier, IEEE, Springer -- has to be fetched through an
institutional login by a person, and this script takes it from there: it reads a
directory of downloaded files, works out which candidate work each one is, and
runs the same extraction the fetcher runs.

WHY THE RESULTS GO IN THEIR OWN FILE
Contexts land in `data/local-contexts.json`, not in `data/paper-contexts.json`.
The fetcher rewrites its own file, and `--refetch` drops every recorded work and
tries to fetch it again -- which for these papers means failing again and filing
them back as blocked. Keeping them separate means a refetch can never destroy work
that took an institutional login to get. The cost is that a work collected here
still appears in the fetcher's blocked list; read both files when curating.

THE PDFS THEMSELVES MUST NOT BE COMMITTED. codon-world is a public repository, and
these papers are licensed for personal scholarly use, not redistribution. The
extracted passages are short quotations and are fine; the sources are not. The
directory this reads from belongs in `.gitignore`.

IDENTIFYING A FILE
Filenames from publisher sites are meaningless, so the file is matched to a
candidate work by its contents, in this order:

  1. a candidate DOI appearing anywhere in the text
  2. a candidate title appearing in the first part of the text

Anything unmatched, or matching more than one candidate, is reported rather than
guessed at -- a wrong match would attach one paper's passages to another's entry.

BOOKS AND PARTIAL DOWNLOADS
Two cases from the first hand-collected batch need the manifest:

  - A whole book downloaded for one chapter. The book carries many bibliographies,
    and the extractor takes the last "References" heading in the document, which
    would be some other chapter's. Give the chapter's page range.
  - An article available only as html and printed to pdf. These often stop before
    the bibliography, so the reference-number route has nothing to work from. The
    body scan still finds passages naming Codon outright, and the report says when
    no bibliography was detected so the gap is visible rather than silent.

Manifest format, all fields but `file` optional:

    [
      {"file": "smith-book.pdf", "doi": "10.1016/b978-...", "pages": "412-431"},
      {"file": "printed-page.pdf", "doi": "10.1016/j.jlamp.2024.101032"}
    ]
"""
import json, os, re, sys, io

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_contexts import contexts, BIB_HIT

CAND = "data/papers-candidates.json"
OUT = "data/local-contexts.json"
EXTS = (".pdf", ".txt")


def norm(s):
    """Lowercase alphanumerics only, for comparing titles across typesetting."""
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def pages_of(blob, spec):
    """Extract text, optionally from a 1-based inclusive page range like '412-431'."""
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(blob))
    n = len(reader.pages)
    if spec:
        m = re.match(r"\s*(\d+)\s*-\s*(\d+)\s*$", str(spec))
        if not m:
            raise ValueError("page range %r is not of the form '12-34'" % spec)
        lo, hi = int(m.group(1)), min(int(m.group(2)), n)
        sel = range(lo - 1, hi)
    else:
        sel = range(n)
    return "\n".join((reader.pages[i].extract_text() or "") for i in sel), n


def text_of_file(path, pages=None):
    blob = open(path, "rb").read()
    if path.lower().endswith(".txt"):
        return blob.decode("utf-8", "ignore"), None
    return pages_of(blob, pages)


def identify(text, works):
    """Return (matches, how). matches is a list of candidate rows."""
    head = text[:6000]
    hits = [w for w in works if w[2] and w[2].lower() in text.lower()]
    if hits:
        return hits, "doi"
    nhead = norm(head)
    hits = [w for w in works if w[1] and len(norm(w[1])) > 25
            and norm(w[1])[:60] in nhead]
    if hits:
        return hits, "title"
    return [], "none"


def has_bibliography(text):
    return bool(re.search(
        r"\n\s*(REFERENCES|References|BIBLIOGRAPHY|Bibliography)\s*\n", text))


def main():
    args = sys.argv[1:]

    def opt(flag, default=None):
        return args[args.index(flag) + 1] if flag in args else default

    directory = opt("--dir", "pdfs")
    manifest = {}
    mpath = opt("--manifest")
    if mpath:
        for row in json.load(open(mpath)):
            manifest[os.path.basename(row["file"])] = row

    works = json.load(open(CAND))["works"]
    by_doi = {w[2].lower(): w for w in works if w[2]}

    if not os.path.isdir(directory):
        sys.exit("no such directory: %s (pass --dir)" % directory)
    files = sorted(f for f in os.listdir(directory)
                   if f.lower().endswith(EXTS) and not f.startswith("."))
    if not files:
        sys.exit("no .pdf or .txt files in %s" % directory)

    print("%d files in %s\n" % (len(files), directory), flush=True)
    results, problems = [], []

    for name in files:
        path = os.path.join(directory, name)
        row = manifest.get(name, {})
        try:
            text, npages = text_of_file(path, row.get("pages"))
        except Exception as exc:
            problems.append((name, "unreadable", str(exc)[:70]))
            print("UNREADABLE  %-44s %s" % (name[:44], str(exc)[:50]), flush=True)
            continue

        if len(text) < 500:
            problems.append((name, "no text layer",
                             "%d chars extracted; scan or image-only pdf" % len(text)))
            print("NO TEXT     %-44s %d chars" % (name[:44], len(text)), flush=True)
            continue

        if row.get("doi"):
            w = by_doi.get(row["doi"].lower())
            if not w:
                problems.append((name, "manifest doi not a candidate", row["doi"]))
                print("BAD DOI     %-44s %s" % (name[:44], row["doi"]), flush=True)
                continue
            hits, how = [w], "manifest"
        else:
            hits, how = identify(text, works)

        if not hits:
            problems.append((name, "unidentified",
                             "no candidate doi or title found in the text"))
            print("UNKNOWN     %-44s add it to the manifest" % name[:44], flush=True)
            continue
        if len(hits) > 1:
            problems.append((name, "ambiguous",
                             ", ".join(h[2] for h in hits[:4])))
            print("AMBIGUOUS   %-44s %d candidates; pin it in the manifest"
                  % (name[:44], len(hits)), flush=True)
            continue

        year, title, doi, cites, found = hits[0]
        cx = contexts(text)
        bib = has_bibliography(text)
        refs = sorted({c["ref"] for c in cx if c["kind"] == "inline"})
        results.append({"year": year, "title": title, "doi": doi, "cites": cites,
                        "chars": len(text), "source_file": name,
                        "matched_by": how, "pages": row.get("pages"),
                        "bibliography_found": bib, "contexts": cx})
        flag = "" if bib else "  NO-BIBLIOGRAPHY"
        print("ok          %-44s %-32s %2d ctx  refs=%s%s"
              % (name[:44], doi[:32], len(cx), ",".join(refs) or "-", flag), flush=True)
        if not bib:
            problems.append((name, "no bibliography",
                             "reference-number route unavailable; body scan only"))
        elif not cx:
            problems.append((name, "no contexts",
                             "bibliography present but nothing matched the Codon family"))

    print("\n%d identified, %d need attention" % (len(results), len(problems)))
    if problems:
        print("\nNEEDS ATTENTION")
        for name, kind, detail in problems:
            print("  %-14s %-40s %s" % (kind, name[:40], detail))

    got = {r["doi"].lower() for r in results}
    still = [w for w in works if w[2] and w[2].lower() not in got]
    print("\n%d of %d candidate works now have local full text" % (len(got), len(works)))

    out = {"generated": __import__("time").strftime("%Y-%m-%d"),
           "note": "Contexts extracted from full texts collected by hand through an "
                   "institutional login. Kept apart from data/paper-contexts.json so "
                   "that a --refetch cannot destroy them. The pdfs are not committed.",
           "counts": {"with_contexts": len(results),
                      "needing_attention": len(problems)},
           "problems": [{"file": n, "kind": k, "detail": d} for n, k, d in problems],
           "works": results}
    if "--write" in args:
        json.dump(out, open(OUT, "w"), indent=1)
        print("wrote %s" % OUT)
    else:
        print("\n(report only; pass --write to save %s)" % OUT)


if __name__ == "__main__":
    main()
