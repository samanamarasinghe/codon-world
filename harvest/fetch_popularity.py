#!/usr/bin/env python3
"""Fetch the two reception numbers the index cannot compute for itself:
stars for repository entries, citation counts for paper entries.

Usage:  python3 harvest/fetch_popularity.py --papers            # keyless, ~2 calls
        python3 harvest/fetch_popularity.py --repos             # needs GITHUB_TOKEN
        python3 harvest/fetch_popularity.py --repos --papers --write

Writes data/popularity.json. Each half is written independently, so running
one half never clears the other: the file is read first and merged.

Both numbers are moving targets, so every record carries the date it was read
and the source it came from. Neither is a measure of Codon: stars measure the
repository, which for a packaging recipe is a distribution tracked by thousands
of people whose Codon content is one line of YAML.
"""
import json, os, sys, time, urllib.error, urllib.request
from datetime import date

OUT = "data/popularity.json"
OA_BATCH = ("https://api.openalex.org/works?per-page=50&select=doi,cited_by_count"
            "&filter=doi:%s")
S2_BATCH = "https://api.semanticscholar.org/graph/v1/paper/batch?fields=citationCount,externalIds"
GH_REPO = "https://api.github.com/repos/%s"
UA = "codon-world (https://github.com/samanamarasinghe/codon-world)"


def get(url, data=None, headers=None, timeout=60):
    req = urllib.request.Request(url, data=data, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def load_entries(pattern_kind):
    import glob
    out = []
    globs = {"repo": ["data/entries/*.json", "data/pilot/*.json"],
             "paper": ["data/papers/*.json"]}[pattern_kind]
    for g in globs:
        for f in sorted(glob.glob(g)):
            d = json.load(open(f))
            if d and isinstance(d[0], dict) and "_class" in d[0]:
                continue  # sidecar, not an entry
            out += [r for r in d if isinstance(r, dict) and r.get("id")]
    return out


def repo_slug(url):
    """github.com/owner/name -> owner/name. Returns None for anything else."""
    if not url or "github.com/" not in url:
        return None
    tail = url.split("github.com/", 1)[1].strip("/")
    parts = tail.split("/")
    return "/".join(parts[:2]) if len(parts) >= 2 else None


def fetch_repos(entries):
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("GITHUB_TOKEN is required: the unauthenticated API refuses these calls")
    headers = {"Authorization": "Bearer " + token, "Accept": "application/vnd.github+json",
               "User-Agent": UA}
    got, missing = {}, []
    for e in entries:
        slug = repo_slug(e.get("url"))
        if not slug:
            missing.append({"id": e["id"], "url": e.get("url"), "reason": "not a github repo url"})
            continue
        try:
            r = get(GH_REPO % slug, headers=headers)
            got[e["id"]] = {"slug": slug, "stars": r.get("stargazers_count"),
                            "forks": r.get("forks_count"), "pushed_at": r.get("pushed_at"),
                            "archived": r.get("archived"), "source": "github",
                            "fetched": str(date.today())}
        except urllib.error.HTTPError as ex:
            # 404 here is a real finding: the repository was deleted or made private
            # since it was read. It is recorded, not silently dropped.
            missing.append({"id": e["id"], "slug": slug, "reason": "http %d" % ex.code})
        time.sleep(0.5)
    return got, missing


def fetch_papers(entries):
    """OpenAlex first, in batches of 25 DOIs per request, then Semantic Scholar for
    whatever OpenAlex does not hold. Two sources count differently, so the source
    is recorded per paper and a mixed field is not a clean ranking."""
    withdoi = [(e["id"], e["doi"].lower()) for e in entries if e.get("doi")]
    today = str(date.today())
    oa = {}
    for i in range(0, len(withdoi), 25):
        batch = [d for _, d in withdoi[i:i + 25]]
        r = get(OA_BATCH % "|".join(batch), headers={"User-Agent": UA})
        for w in r.get("results", []):
            oa[(w.get("doi") or "").replace("https://doi.org/", "")] = w.get("cited_by_count")
        time.sleep(2)

    got, gap = {}, []
    for eid, doi in withdoi:
        if doi in oa:
            got[eid] = {"doi": doi, "citations": oa[doi], "source": "openalex", "fetched": today}
        else:
            gap.append((eid, doi))

    missing = []
    if gap:
        rows = get(S2_BATCH, data=json.dumps({"ids": ["DOI:" + d for _, d in gap]}).encode(),
                   headers={"Content-Type": "application/json", "User-Agent": UA})
        for (eid, doi), r in zip(gap, rows):
            if r:
                got[eid] = {"doi": doi, "citations": r.get("citationCount"),
                            "source": "semanticscholar", "fetched": today}
            else:
                missing.append({"id": eid, "doi": doi,
                                "reason": "in neither openalex nor semantic scholar"})
    for e in entries:
        if not e.get("doi"):
            missing.append({"id": e["id"], "doi": None, "reason": "no doi"})
    return got, missing


def main():
    doing_repos = "--repos" in sys.argv
    doing_papers = "--papers" in sys.argv
    if not (doing_repos or doing_papers):
        sys.exit(__doc__)
    old = json.load(open(OUT)) if os.path.exists(OUT) else {}
    out = {"generated": str(date.today()),
           "note": ("Stars from the GitHub API; citations from OpenAlex, falling back to "
                    "Semantic Scholar. Both numbers move, so each record carries its own "
                    "fetched date and its source. Every index of citations undercounts "
                    "against Google Scholar; read a citation count as a floor."),
           "repos": old.get("repos", {}), "papers": old.get("papers", {}),
           "missing": old.get("missing", {})}
    if doing_repos:
        got, missing = fetch_repos(load_entries("repo"))
        out["repos"] = got
        out["missing"]["repos"] = missing
        print("repos: %d with stars, %d missing" % (len(got), len(missing)))
    if doing_papers:
        got, missing = fetch_papers(load_entries("paper"))
        out["papers"] = got
        out["missing"]["papers"] = missing
        print("papers: %d with citations, %d missing" % (len(got), len(missing)))
    if "--write" in sys.argv:
        json.dump(out, open(OUT, "w"), indent=1)
        print("wrote " + OUT)
    else:
        print("(dry run, pass --write)")


if __name__ == "__main__":
    main()
