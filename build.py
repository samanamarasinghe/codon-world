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
import json, glob, sys

OUT = "data/codon-index.json"


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
    line = "%d entries (%s); sidecars %s" % (len(entries), out["kind_counts"], out["sidecar_counts"])
    if "--write" in sys.argv:
        json.dump(out, open(OUT, "w"), indent=1)
        print("wrote %s: %s" % (OUT, line))
    else:
        print("%s (dry run)" % line)


if __name__ == "__main__":
    main()
