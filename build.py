#!/usr/bin/env python3
"""Merge the per-lane entry files into one data/codon-index.json for the site.

Usage:  python3 build.py            # dry run, reports counts
        python3 build.py --write    # writes data/codon-index.json

Repository entries come from data/entries/ and data/pilot/, paper entries from
data/papers/. Every entry is tagged with a "kind" of repo or paper, which is what
the site's Kind facet filters on.

Most files are plain lists of entries. Two are SIDECARS: a single wrapper
object carrying a _class key and a repos list, used for repositories that are
recorded so a later pass does not rediscover them, but that are not entries.
Those are kept in their own section, keyed by _class, and never merged into the
entries. Keeping them apart matters: 012 holds eleven genetics false positives
and 015 holds twenty-three forks of an already-indexed packaging recipe, and
summing the two would report a number that means nothing.
"""
import json, glob, os, sys

OUT = "data/codon-index.json"
POP = "data/popularity.json"
CONTEXT_FILES = ["data/paper-contexts.json", "data/local-contexts.json"]
# harvest/fetch_contexts.py keeps at most this many contexts per work, so a work
# at the cap may have had more that were never written down.
CONTEXT_CAP = 12


def popularity():
    """Stars and citation counts, keyed by entry id. Absent until the workflow runs."""
    return json.load(open(POP)) if os.path.exists(POP) else {"repos": {}, "papers": {}}


def mention_counts():
    """How many places in a paper actually discuss the Codon family, keyed by DOI.

    A bibliography context is the reference list entry itself, which every citing
    work has exactly one of, so it says nothing about engagement and is not
    counted. What is counted is inline citation sites, deduplicated by reference
    number, plus prose mentions found by name.

    The number is a floor and is marked as one. Papers that cite by superscript
    are invisible to the inline scan, and a work at the extractor's cap may have
    had more. Secure MICE extends Sequre and counts zero here.
    """
    out = {}
    for f in CONTEXT_FILES:
        if not os.path.exists(f):
            continue
        for w in json.load(open(f)).get("works", []):
            doi = (w.get("doi") or "").lower()
            if not doi:
                continue
            cs = w.get("contexts") or []
            inline = {str(c.get("ref")) for c in cs if c.get("kind") == "inline"}
            body = sum(1 for c in cs if c.get("kind") == "body")
            rec = out.setdefault(doi, {"count": 0, "inline": 0, "body": 0, "capped": False})
            rec["inline"] += len(inline)
            rec["body"] += body
            rec["count"] = rec["inline"] + rec["body"]
            rec["capped"] = rec["capped"] or len(cs) >= CONTEXT_CAP
    return out


def load():
    entries, sidecars = [], {}
    files = ([("repo", f) for f in sorted(glob.glob("data/entries/*.json"))]
             + [("repo", f) for f in sorted(glob.glob("data/pilot/*.json"))]
             + [("paper", f) for f in sorted(glob.glob("data/papers/*.json"))])
    for kind, f in files:
        d = json.load(open(f))
        if d and isinstance(d[0], dict) and "_class" in d[0]:
            cls = d[0]["_class"]
            bucket = sidecars.setdefault(cls, {"class": cls, "note": d[0].get("note"),
                                               "source_file": f, "repos": []})
            bucket["repos"].extend(d[0]["repos"])
            continue
        for r in d:
            entries.append(dict(r, source_file=f, kind=kind))
    return entries, sidecars


def main():
    entries, sidecars = load()
    pop, mentions = popularity(), mention_counts()
    for e in entries:
        half = pop.get("repos" if e["kind"] == "repo" else "papers", {})
        if e["id"] in half:
            e["popularity"] = half[e["id"]]
        if e["kind"] == "paper":
            m = mentions.get((e.get("doi") or "").lower())
            if m:
                e["codon_mentions"] = m
    ids = [e["id"] for e in entries]
    for b in sidecars.values():
        ids += [r["id"] for r in b["repos"]]
    if len(ids) != len(set(ids)):
        dupes = {i for i in ids if ids.count(i) > 1}
        sys.exit("duplicate ids: %s" % sorted(dupes))
    # Repositories sort by Codon volume, papers by year. Neither measure applies to
    # the other, so entries without one fall to the end of their own group.
    entries.sort(key=lambda e: (e["kind"] != "repo",
                                -((e.get("scale") or {}).get("own_codon_loc") or 0),
                                -(e.get("year") or 0),
                                e["id"]))
    out = {
        "generated_from": "data/entries/*.json + data/pilot/*.json + data/papers/*.json",
        "entry_count": len(entries),
        "kind_counts": {k: sum(1 for e in entries if e["kind"] == k) for k in ("repo", "paper")},
        "sidecar_counts": {c: len(b["repos"]) for c, b in sorted(sidecars.items())},
        "entries": entries,
        "sidecars": [sidecars[c] for c in sorted(sidecars)],
    }
    out["popularity_counts"] = {
        "repos_with_stars": sum(1 for e in entries if e["kind"] == "repo" and e.get("popularity")),
        "papers_with_citations": sum(1 for e in entries if e["kind"] == "paper" and e.get("popularity")),
        "papers_with_mentions": sum(1 for e in entries if e.get("codon_mentions")),
    }
    line = "%d entries (%s); sidecars %s; popularity %s" % (
        len(entries), out["kind_counts"], out["sidecar_counts"], out["popularity_counts"])
    if "--write" in sys.argv:
        json.dump(out, open(OUT, "w"), indent=1)
        print("wrote %s: %s" % (OUT, line))
    else:
        print("%s (dry run)" % line)


if __name__ == "__main__":
    main()
