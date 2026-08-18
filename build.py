#!/usr/bin/env python3
"""Merge the per-lane entry files into one data/codon-index.json for the site.

Usage:  python3 build.py            # dry run, reports counts
        python3 build.py --write    # writes data/codon-index.json

Entry files are data/entries/*.json and data/pilot/*.json. One of them
(012-false-positives-genetics.json) is a single wrapper object carrying a
_class key and a repos list rather than a list of entries; it is split out
into its own section instead of being merged with the entries.
"""
import json, glob, sys

OUT = "data/codon-index.json"


def load():
    entries, fps = [], []
    files = sorted(glob.glob("data/entries/*.json")) + sorted(glob.glob("data/pilot/*.json"))
    for f in files:
        d = json.load(open(f))
        if d and isinstance(d[0], dict) and "_class" in d[0]:
            for r in d[0]["repos"]:
                fps.append(dict(r, source_file=f, _class=d[0]["_class"]))
            continue
        for r in d:
            entries.append(dict(r, source_file=f))
    return entries, fps


def main():
    entries, fps = load()
    ids = [e["id"] for e in entries]
    if len(ids) != len(set(ids)):
        dupes = {i for i in ids if ids.count(i) > 1}
        sys.exit("duplicate ids: %s" % sorted(dupes))
    entries.sort(key=lambda e: (-(e.get("scale", {}).get("own_codon_loc") or 0), e["id"]))
    out = {
        "generated_from": "data/entries/*.json + data/pilot/*.json",
        "entry_count": len(entries),
        "genetics_false_positive_count": len(fps),
        "entries": entries,
        "genetics_false_positives": fps,
    }
    if "--write" in sys.argv:
        json.dump(out, open(OUT, "w"), indent=1)
        print("wrote %s: %d entries, %d genetics false positives" % (OUT, len(entries), len(fps)))
    else:
        print("%d entries, %d genetics false positives (dry run)" % (len(entries), len(fps)))


if __name__ == "__main__":
    main()
