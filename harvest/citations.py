#!/usr/bin/env python3
"""Harvest the citing works for the Codon anchors.

    python3 harvest/citations.py            # dry run, prints counts
    python3 harvest/citations.py --write    # writes data/papers-candidates.json

Reverse citations for the four Tier 1 anchors in data/anchors.json plus the three
Tier 2 Codon-family papers, unioned across two sources and deduplicated on
normalised title.

Why two sources: neither has recall on its own. On the first run OpenAlex held 77
citing works and Semantic Scholar added 32 it does not have -- roughly a third of
the total invisible to either source alone. Google Scholar is not queried here and
usually exceeds both, so the result is a floor.

Anchors are excluded from their own results. The Codon family papers cite each
other, so an unfiltered harvest returns Codon CC 2023, both Seq papers, Sequre and
Vectron as citing works -- five of the first run's 109, which would have become
entries duplicating data/anchors.json. See docs/paper-triage.md.

Neither API needs a key from a normal network. OpenAlex bills per request against a
daily allowance and 429s on sustained paging, so the fetch retries with a pause; its
?search= endpoint is limited separately and should be avoided in favour of
/works/doi:. OpenCitations, used in the Halide lane, now 301-redirects.
"""
import json, sys, time, urllib.request, collections

UA = {"User-Agent": "codon-world-index/1.0 (research)"}
OUT = "data/papers-candidates.json"

ANCHORS = {
    "codon-cc-2023":      ("T1", "10.1145/3578360.3580275"),
    "seq-oopsla-2019":    ("T1", "10.1145/3360551"),
    "seq-nbt-2021":       ("T1", "10.1038/s41587-021-00985-6"),
    "seq-biorxiv-2020":   ("T1", "10.1101/2020.10.29.361402"),
    "sequre-ipdpsw-2022": ("T2", "10.1109/IPDPSW55747.2022.00040"),
    "sequre-gb-2023":     ("T2", "10.1186/s13059-022-02841-5"),
    "vectron-cgo-2025":   ("T2", "10.1145/3696443.3708963"),
}

# Anchor DOIs, lowercased, for self-citation exclusion.
ANCHOR_DOIS = {doi.lower() for _tier, doi in ANCHORS.values()}


def get(url, tries=3):
    for _ in range(tries):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=45))
        except Exception as exc:
            if "429" in str(exc):
                time.sleep(15)
                continue
            return {"_err": str(exc)}
    return {"_err": "429 after retries"}


def norm(t):
    return (t or "").lower().strip()


def is_anchor(doi):
    return (doi or "").replace("https://doi.org/", "").lower() in ANCHOR_DOIS


def openalex(label, doi, union, by_title):
    work = get("https://api.openalex.org/works/doi:" + doi)
    wid = work.get("id", "").split("/")[-1]
    if not wid:
        print("  %s: no OpenAlex record" % label)
        return 0
    seen, cursor = 0, "*"
    while cursor:
        page = get("https://api.openalex.org/works?filter=cites:%s&per-page=200&cursor=%s" % (wid, cursor))
        if "_err" in page:
            print("  %s: openalex %s" % (label, page["_err"][:50]))
            break
        for r in page.get("results", []):
            if is_anchor(r.get("doi")):
                continue
            key = norm(r.get("display_name"))
            e = by_title.get(key)
            if e is None:
                e = {"doi": r.get("doi"), "title": r.get("display_name"),
                     "year": r.get("publication_year"), "cites": [], "source": "openalex"}
                union.append(e)
                by_title[key] = e
            if label not in e["cites"]:
                e["cites"].append(label)
            seen += 1
        if not page.get("results"):
            break
        cursor = page.get("meta", {}).get("next_cursor")
        time.sleep(0.5)
    return seen


def semantic_scholar(label, doi, union, by_title):
    page = get("https://api.semanticscholar.org/graph/v1/paper/DOI:%s/citations"
               "?fields=title,year,externalIds&limit=100" % doi)
    seen = 0
    for c in page.get("data", []):
        p = c.get("citingPaper", {})
        ext = p.get("externalIds") or {}
        if is_anchor(ext.get("DOI")):
            continue
        key = norm(p.get("title"))
        if not key:
            continue
        e = by_title.get(key)
        if e is None:
            e = {"doi": ("https://doi.org/" + ext["DOI"]) if ext.get("DOI") else None,
                 "title": p.get("title"), "year": p.get("year"),
                 "cites": [], "source": "semantic_scholar_only"}
            union.append(e)
            by_title[key] = e
        if label not in e["cites"]:
            e["cites"].append(label)
        seen += 1
    time.sleep(2)
    return seen


def main():
    union, by_title, per_anchor = [], {}, {}
    for label, (_tier, doi) in ANCHORS.items():
        per_anchor[label] = openalex(label, doi, union, by_title)
    for label, (_tier, doi) in ANCHORS.items():
        n = semantic_scholar(label, doi, union, by_title)
        per_anchor[label] = max(per_anchor[label], n)

    union.sort(key=lambda e: (-(e["year"] or 0), e["title"] or ""))
    rows = [[e["year"], e["title"], (e["doi"] or "").replace("https://doi.org/", ""),
             ",".join(sorted(e["cites"])), "S2" if e["source"] != "openalex" else "OA"]
            for e in union]
    out = {
        "generated": time.strftime("%Y-%m-%d"),
        "phase": "paper lane, phase 0 sizing",
        "method": "Reverse citations for the Tier 1 anchors plus the Tier 2 Codon-family "
                  "papers, unioned across OpenAlex and Semantic Scholar, deduplicated on "
                  "normalised title. Anchors are excluded from their own results.",
        "floor_warning": "Google Scholar has not been consulted and usually exceeds both "
                         "sources. Treat the count as a floor.",
        "counts": {
            "distinct_citing_works": len(union),
            "from_openalex": sum(1 for e in union if e["source"] == "openalex"),
            "semantic_scholar_only": sum(1 for e in union if e["source"] != "openalex"),
            "cite_more_than_one_anchor": sum(1 for e in union if len(e["cites"]) > 1),
            "without_doi": sum(1 for e in union if not e["doi"]),
        },
        "per_anchor_cited_by": per_anchor,
        "by_year": dict(sorted(collections.Counter(e["year"] for e in union).items(),
                               key=lambda kv: (kv[0] is None, kv[0]))),
        "works_schema": ["year", "title", "doi", "cites", "found_in"],
        "works": rows,
    }
    print(json.dumps(out["counts"], indent=1))
    if "--write" in sys.argv:
        json.dump(out, open(OUT, "w"), separators=(",", ":"))
        print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
