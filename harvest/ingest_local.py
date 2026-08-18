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
candidate work by its contents: a candidate doi, failing that a candidate title
near the start. Anything unmatched, or matching more than one candidate, is
reported rather than guessed at -- a wrong match would attach one paper's passages
to another's entry. See identify() for the two rules that decide between dois.

BOOKS AND PARTIAL DOWNLOADS
Two shapes from the first hand-collected batch need care:

  - A whole book downloaded for one chapter. The book carries many bibliographies,
    and contexts() takes the last "References" heading in the document, which
    would be some other chapter's. A page range in the manifest is exact and is
    what to use; failing that the chapter is located by its doi, or by its title
    as a fallback, and the run reports which route it took.
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
import json, os, re, sys, io, logging

# pypdf narrates malformed cross-reference tables ("Ignoring wrong pointing
# object N") on every page of a browser-printed pdf, which buries the report.
# The pages still extract; the complaint is not actionable.
logging.getLogger("pypdf").setLevel(logging.ERROR)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_contexts import contexts, BIB_HIT


def require_pypdf():
    """Fail once with the fix, rather than once per file with a mystery.

    The first run of this against a real directory reported "No module named
    'pypdf'" thirty-three times, once per pdf, filed under `unreadable` as though
    the papers were at fault. A missing dependency is a setup problem and belongs
    at the top of the run, said once.
    """
    try:
        import pypdf  # noqa: F401
    except ImportError:
        sys.exit(
            "pypdf is not installed, and it is what reads the pdfs.\n\n"
            "    python3 -m venv .venv\n"
            "    source .venv/bin/activate\n"
            "    pip install pypdf\n\n"
            "A plain `pip install` fails on a homebrew python under PEP 668, and\n"
            "homebrew warns that --break-system-packages can break the install, so\n"
            "the virtual environment is the route to take.")


# A document this long is a book or proceedings volume, not an article. It will
# carry many bibliographies, and contexts() reads the last "References" heading in
# the document -- which in a book belongs to some other chapter. Saying so is the
# difference between a wrong reference number and a question.
BOOK_CHARS = 400000

# How close two dois must be, both appearing before the bibliography, before the
# document is judged not to distinguish them.
FRONT_MATTER = 5000

# A chapter's own bibliography follows its body. Twenty thousand characters is
# generous for one chapter's references and short enough not to swallow the next
# chapter's body.
CHAPTER_BIB = 20000

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
    """Return (matches, how). matches is a list of candidate rows.

    Two rules here were both learned from the first real directory of 33 papers.

    Candidates are collapsed by doi before anything is called ambiguous. The
    harvest holds five works twice, differing only by a trailing period or a
    capital letter in the title, and its dedup key is the normalised title. Two
    rows describing one doi are not two candidates, and reporting them as an
    ambiguity sent three perfectly identifiable papers back to be pinned by hand.

    Where two DIFFERENT dois really do appear, the bibliography decides. A doi
    printed after the references heading is one the paper CITES; only a doi before
    it can be the paper's own. The Oxford paper bbae356 carries the SECRET-GWAS
    preprint doi in its bibliography and was reported ambiguous against it.

    The first attempt at this ruled by absolute position -- a doi within the first
    few thousand characters was "front matter" -- and it passed a synthetic test
    only because the synthetic paper was four thousand characters long. Real papers
    are ten times that, so the rule was never exercised. Splitting on the
    bibliography instead is independent of length, which is the property that
    matters. Ambiguity now means two distinct dois before the references heading
    and close together, where nothing in the document separates them.
    """
    low = text.lower()
    found = {}
    for w in works:
        if not w[2]:
            continue
        key = w[2].lower()
        pos = low.find(key)
        if pos >= 0 and (key not in found or pos < found[key][1]):
            found[key] = (w, pos)
    if found:
        m = re.search(r"\n\s*(REFERENCES|References|BIBLIOGRAPHY|Bibliography)\s*\n",
                      text)
        cut = m.start() if m else len(text)
        own = sorted((v for v in found.values() if v[1] < cut), key=lambda t: t[1])
        ordered = own or sorted(found.values(), key=lambda t: t[1])
        if len(ordered) > 1 and ordered[1][1] - ordered[0][1] < FRONT_MATTER:
            return [o[0] for o in ordered], "doi"
        return [ordered[0][0]], "doi"
    nhead = norm(text[:6000])
    by_doi, untitled = {}, []
    for w in works:
        if not w[1] or len(norm(w[1])) <= 25 or norm(w[1])[:60] not in nhead:
            continue
        (by_doi.setdefault(w[2].lower(), w) if w[2] else untitled.append(w))
    hits = list(by_doi.values()) + untitled
    if hits:
        return hits, "title"
    return [], "none"


def scope_chapter(text, title, doi=None):
    """Narrow a book to one chapter: its opening through its own bibliography.

    Five of the collected files are whole volumes downloaded for a single chapter.
    contexts() reads the LAST references heading in a document, which in a book
    belongs to whatever chapter comes last, so a reference number taken from a
    whole volume is meaningless. Page ranges in the manifest are exact and are
    preferred; this is what happens when none was given.

    FINDING THE CHAPTER IS THE WHOLE DIFFICULTY, and the first version got it
    wrong in a way that looked like success. It took the first occurrence of the
    chapter title, which in any edited volume is the line in the table of
    contents, and then the first references heading after that -- the FIRST
    chapter's bibliography. Every one of the four collected volumes came back
    "bibliography present but nothing matched", which reads as though the chapter
    does not cite Codon when in fact the wrong bibliography was read. A false
    negative that arrives with a plausible explanation is worse than a failure.

    So the chapter doi is tried first: Springer prints it on the chapter's opening
    page and nowhere else, which is exactly the anchor needed. Failing that, the
    LAST title occurrence is used rather than the first, since the contents page
    precedes the chapter and running heads do not precede its bibliography.

    Returns (slice, note). The slice is the original text when the chapter cannot
    be located, because a wide window is better than a wrong one.
    """
    start, how = -1, ""
    if doi:
        at = text.lower().find(doi.lower())
        if at >= 0:
            start, how = at, "by chapter doi"
    if start < 0:
        n = norm(title)[:60]
        if len(n) < 25:
            return text, "chapter title too short to locate"
        # walk the text in normalised space to find where the chapter opens
        flat, index = [], []
        for i, ch in enumerate(text.lower()):
            if ch.isalnum():
                flat.append(ch)
                index.append(i)
        at = "".join(flat).rfind(n)
        if at < 0:
            return text, "chapter title not found in the volume"
        start, how = index[at], "by last title occurrence"
    tail = text[start:]
    m = re.search(r"\n\s*(REFERENCES|References|BIBLIOGRAPHY|Bibliography)\s*\n", tail)
    if not m:
        return text, "no bibliography follows the chapter opening"
    end = start + m.end() + CHAPTER_BIB
    return text[start:end], "scoped to the chapter " + how


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

    require_pypdf()
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
        scoped = None
        if len(text) > BOOK_CHARS and not row.get("pages"):
            text, scoped = scope_chapter(text, title, doi)
        cx = contexts(text)
        bib = has_bibliography(text)
        refs = sorted({c["ref"] for c in cx if c["kind"] == "inline"})
        results.append({"year": year, "title": title, "doi": doi, "cites": cites,
                        "chars": len(text), "source_file": name,
                        "matched_by": how, "pages": row.get("pages"),
                        "bibliography_found": bib, "scoped": scoped,
                        "contexts": cx})
        booklike = scoped is not None and not scoped.startswith("scoped")
        flag = "" if bib else "  NO-BIBLIOGRAPHY"
        if scoped:
            flag += "  BOOK[%s]" % ("auto-scoped" if not booklike else "WHOLE VOLUME")
        print("ok          %-44s %-32s %2d ctx  refs=%s%s"
              % (name[:44], doi[:32], len(cx), ",".join(refs) or "-", flag), flush=True)
        if booklike:
            problems.append((name, "book-length",
                             "%s; give a page range in the manifest, or the reference "
                             "numbers come from the last bibliography in the volume"
                             % scoped))
        if not bib:
            problems.append((name, "no bibliography",
                             "reference-number route unavailable; body scan only"))
        elif not cx:
            problems.append((name, "no contexts",
                             "bibliography present but nothing matched the Codon family"))

    # Two files resolving to one work is always a mistake -- a duplicate download,
    # or a printed page whose own doi was missing so it matched a neighbour's.
    # Silently recording both would double-count the work at curation time.
    claimed = {}
    for r in results:
        claimed.setdefault(r["doi"], []).append(r["source_file"])
    for doi, names in claimed.items():
        if len(names) > 1:
            problems.append((", ".join(names), "same work twice",
                             "%s is claimed by %d files" % (doi, len(names))))

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
