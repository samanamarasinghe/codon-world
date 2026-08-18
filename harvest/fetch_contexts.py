#!/usr/bin/env python3
"""Fetch open full texts for the paper candidates and extract the Codon citation context.

    python3 harvest/fetch_contexts.py                  # all works not already done
    python3 harvest/fetch_contexts.py --limit 20       # first N undone works
    python3 harvest/fetch_contexts.py --write          # write data/paper-contexts.json
    python3 harvest/fetch_contexts.py --retry-blocked  # also re-attempt past blocks
    python3 harvest/fetch_contexts.py --refetch        # redo everything, after an
                                                       # extraction change

This does the mechanical half of the paper lane: find a readable copy, pull the
text, and cut out the sentences where the work actually cites Codon or Seq. It
makes no judgement -- codon_relation is still set by a person reading the extract,
as ruling 8 requires.

It is resumable, and it checkpoints after every paper, so an interrupted run loses
only the fetch in flight.

A failure is not a failure. Two outcomes are recorded separately:
  blocked   -- no open copy found anywhere; needs an institutional login
  deferred  -- a copy exists but the host refused this run (429 rate limiting, or
               403 from publishers that serve only browsers). Retried next run.
The first version of this script filed both as blocked, and because the resumable
path skips blocked works, a momentary 429 wrote a paper off permanently.

Routes, in order (docs/paper-fetching.md):
  1. arXiv pdf, when the doi is a 10.48550 arXiv doi or a location points there
  2. every OpenAlex location carrying a pdf_url, not just the primary one
  3. a publisher landing page, read once for a citation_pdf_url meta tag or a
     link ending .pdf
  4. Europe PMC, which often holds a copy the publisher route cannot reach
  5. Unpaywall, if UNPAYWALL_EMAIL is set

Citation context: finding the word "Codon" is not finding the citation. Numbered
reference styles put the name only in the bibliography and a bracketed number in
the body. So the bibliography entry is located first, its number taken, and the
body searched for that number in brackets.
"""
import json, os, re, sys, time, urllib.request, io, urllib.parse, random

UA = {"User-Agent": "codon-world-index/1.0 (research)"}
CAND = "data/papers-candidates.json"
OUT = "data/paper-contexts.json"
EMAIL = os.environ.get("UNPAYWALL_EMAIL", "")

# Pacing. This job runs unattended for hours, so it is deliberately slow: being
# rate-limited costs far more than waiting, because a 429 partway through can
# poison a whole run of requests to that host, and OpenAlex bills against a daily
# allowance that the curation work then needs. Every value is overridable by
# environment variable if a run needs to be faster or slower.
PACE_WORK = float(os.environ.get("PACE_WORK", 20))    # between papers
PACE_TRY = float(os.environ.get("PACE_TRY", 6))       # between url attempts for one paper
PACE_HOST = float(os.environ.get("PACE_HOST", 12))    # minimum gap between hits on one host
BACKOFF = float(os.environ.get("BACKOFF", 60))        # first wait after a 429
BACKOFF_TRIES = int(os.environ.get("BACKOFF_TRIES", 5))

_last_hit = {}


def _throttle(url):
    """Wait until PACE_HOST seconds have passed since the last request to this host."""
    host = urllib.parse.urlparse(url).netloc
    gap = time.time() - _last_hit.get(host, 0)
    if gap < PACE_HOST:
        time.sleep(PACE_HOST - gap)
    _last_hit[host] = time.time()


def _sleep(seconds, why=""):
    if why:
        print("    waiting %.0fs (%s)" % (seconds, why), flush=True)
    time.sleep(seconds)


# Some publishers refuse anything that does not look like a browser. This is not
# enough for MDPI, which needs a real browser session, but it clears others.
BROWSER = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
           "Accept": "text/html,application/xhtml+xml,application/pdf;q=0.9,*/*;q=0.8",
           "Accept-Language": "en-US,en;q=0.9"}

NAME = re.compile(r"Shajii|Numanagi|Smajlovi", re.I)
# A bare "Seq" matches SPLiT-Seq, RNA-Seq and dozens of assay names, so the body
# scan takes only unambiguous forms. Bibliography matching is by author name.
WORD = re.compile(r"\bcodon\b|\bsequre\b|exaloop|\bseq language\b", re.I)


def get(url, timeout=60, tries=BACKOFF_TRIES):
    """JSON GET with host throttling and exponential backoff on 429."""
    wait = BACKOFF
    for attempt in range(tries):
        _throttle(url)
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout))
        except Exception as exc:
            if "429" in str(exc) or "503" in str(exc):
                _sleep(wait + random.uniform(0, 5), "rate limited, attempt %d" % (attempt + 1))
                wait *= 2
                continue
            return {"_err": str(exc)}
    return {"_err": "rate limited after %d attempts" % tries}


def fetch_pdf(url, timeout=90, follow_html=True):
    """Try to fetch a pdf.

    Returns (blob, reason). reason is one of:
      ok          -- got a pdf
      transient   -- 429 or 503; the copy exists, the host is refusing right now
      forbidden   -- 403; open access but not served to scripts (MDPI does this)
      none        -- the url simply does not yield a pdf
    """
    _throttle(url)
    try:
        req = urllib.request.Request(url, headers=BROWSER)
        data = urllib.request.urlopen(req, timeout=timeout).read()
    except Exception as exc:
        msg = str(exc)
        if "429" in msg or "503" in msg:
            _sleep(BACKOFF, "rate limited fetching a pdf")
            return None, "transient"
        if "403" in msg:
            return None, "forbidden"
        return None, "none"
    if data[:4] == b"%PDF":
        return data, "ok"
    if not follow_html:
        return None, "none"
    html = data[:400000].decode("utf-8", "ignore")
    cands = re.findall(r'citation_pdf_url"\s+content="([^"]+)"', html)
    cands += re.findall(r'href="([^"]+\.pdf[^"]*)"', html)
    base = re.match(r"(https?://[^/]+)", url)
    for c in cands[:4]:
        if c.startswith("/") and base:
            c = base.group(1) + c
        if not c.startswith("http"):
            continue
        got, why = fetch_pdf(c, timeout=timeout, follow_html=False)
        if got:
            return got, "ok"
        if why in ("transient", "forbidden"):
            return None, why
    return None, "none"


def pdf_urls(doi):
    """Yield candidate pdf urls for a doi, cheapest first."""
    if doi.lower().startswith("10.48550/arxiv."):
        yield "https://arxiv.org/pdf/" + doi.lower().split("arxiv.")[-1]
    rec = get("https://api.openalex.org/works/doi:" + doi)
    if "_err" not in rec:
        for loc in rec.get("locations") or []:
            if loc.get("pdf_url"):
                yield loc["pdf_url"]
            lp = loc.get("landing_page_url") or ""
            if "arxiv.org/abs/" in lp:
                yield lp.replace("/abs/", "/pdf/")
            if "biorxiv.org" in lp and doi:
                yield "https://www.biorxiv.org/content/%sv1.full.pdf" % doi
            if lp:
                yield lp
        oa = (rec.get("open_access") or {}).get("oa_url")
        if oa:
            yield oa
    # Europe PMC often holds a copy the publisher route cannot reach, and it is
    # the only alternative host for a bioRxiv preprint when bioRxiv is refusing.
    epmc = get("https://www.ebi.ac.uk/europepmc/webservices/rest/search"
               "?query=DOI:%%22%s%%22&format=json&resultType=core" % doi)
    for r in (epmc.get("resultList") or {}).get("result", [])[:2]:
        for u in ((r.get("fullTextUrlList") or {}).get("fullTextUrl") or []):
            if (u.get("documentStyle") or "") == "pdf" and u.get("url"):
                yield u["url"]
        if r.get("pmcid"):
            yield ("https://www.ebi.ac.uk/europepmc/webservices/rest/%s"
                   "/fullTextXML" % r["pmcid"])
    if EMAIL:
        up = get("https://api.unpaywall.org/v2/%s?email=%s" % (doi, EMAIL))
        for loc in (up.get("oa_locations") or []):
            if loc.get("url_for_pdf"):
                yield loc["url_for_pdf"]


def text_of(blob):
    from pypdf import PdfReader
    try:
        return "\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(blob)).pages)
    except Exception:
        return ""


def contexts(text):
    """Return the passages where this text cites the Codon family."""
    out = []
    numbers = set()
    for m in NAME.finditer(text):
        s = max(0, m.start() - 260)
        out.append({"kind": "bibliography", "text": re.sub(r"\s+", " ", text[s:m.start() + 300])})
    # Reference numbers are read ONLY from the bibliography, located as the last
    # references heading in the document. Scanning the whole text lets a body
    # sentence like "efforts such as the work of Numanagic [8]" contribute a
    # reference number belonging to something else, and one wrong number produces
    # inline passages about an unrelated citation -- worse than no passage at all.
    heads = [m.end() for m in re.finditer(
        r"\n\s*(REFERENCES|References|BIBLIOGRAPHY|Bibliography)\s*\n", text)]
    bib_start = heads[-1] if heads else None
    bib = text[bib_start:] if bib_start is not None else ""
    for m in re.finditer(r"\[(\d{1,3})\][^\[\]]{0,200}?(?:Shajii|Numanagi|Smajlovi)", bib):
        numbers.add(m.group(1))
    for m in re.finditer(r"(?:^|\s)(\d{1,3})\.\s[^\[\]]{0,200}?(?:Shajii|Numanagi|Smajlovi)", bib):
        numbers.add(m.group(1))

    # The body is everything before the bibliography; fall back to "before the
    # first author-name match" for documents with no detectable references heading.
    if bib_start is not None:
        body = text[:bib_start]
    else:
        body = text[:min((m.start() for m in NAME.finditer(text)), default=len(text))]
    for n in sorted(numbers):
        for m in re.finditer(r"\[[0-9,\s\-]*%s[,\]\s]" % n, body):
            s = max(0, m.start() - 420)
            out.append({"kind": "inline", "ref": n,
                        "text": re.sub(r"\s+", " ", body[s:m.end() + 160])})
    for m in WORD.finditer(body):
        s = max(0, m.start() - 300)
        out.append({"kind": "body", "text": re.sub(r"\s+", " ", body[s:m.start() + 300])})
    seen, keep = set(), []
    for c in sorted(out, key=lambda c: {"inline": 0, "body": 1, "bibliography": 2}[c["kind"]]):
        # dedupe on a normalised core, so overlapping windows over one bibliography
        # entry collapse to a single context
        k = (c["kind"], re.sub(r"[^a-z0-9]", "", c["text"].lower())[40:140])
        if k in seen:
            continue
        seen.add(k)
        keep.append(c)
    return keep[:12]


def summary(results, blocked, works, deferred):
    return {"generated": time.strftime("%Y-%m-%d"),
            "note": "Mechanical extraction only. codon_relation is set by a person "
                    "reading these, as ruling 8 requires.",
            "blocked_vs_deferred": "blocked means no open copy was found anywhere and "
                                   "an institutional login is needed. deferred means a "
                                   "copy exists but the host refused this run -- 429 "
                                   "rate limiting, or 403 for publishers that serve "
                                   "only browsers. Deferrals are retried automatically "
                                   "on the next run; blocks are not, unless "
                                   "--retry-blocked is passed.",
            "counts": {"with_contexts": len(results), "blocked": len(blocked),
                       "deferred": len(deferred), "total_candidates": len(works)},
            "works": results, "blocked": blocked, "deferred": deferred}


def checkpoint(results, blocked, works, deferred):
    """Write after every paper, so a killed run loses nothing but the current fetch."""
    if "--write" in sys.argv:
        json.dump(summary(results, blocked, works, deferred), open(OUT, "w"), indent=1)


def main():
    works = json.load(open(CAND))["works"]
    done, keep, blocked, deferred = {}, [], [], []
    if os.path.exists(OUT):
        prev = json.load(open(OUT))
        # Index by doi for the skip test, but carry EVERY recorded work forward.
        # Keying the carried list by doi silently drops any work without one.
        keep = list(prev["works"])
        done = {w["doi"]: w for w in keep if w.get("doi")}
        blocked = prev.get("blocked", [])
        deferred = prev.get("deferred", [])
        # Entries written before the blocked/deferred split carry no reason. They
        # were recorded by a version that filed rate limits as permanent failures,
        # so none of them can be trusted as "no open copy" -- retry them all once.
        stale = [b for b in blocked if "reason" not in b]
        if stale:
            print("migrating %d pre-split blocks to deferred" % len(stale), flush=True)
            for b in stale:
                b["reason"] = "unclassified: recorded before the blocked/deferred split"
            deferred = deferred + stale
            blocked = [b for b in blocked if "reason" in b]
    # A previous run's deferrals are always retried; its blocks are not, unless
    # asked, because "no open copy anywhere" does not change between runs.
    if "--retry-blocked" in sys.argv:
        deferred = deferred + blocked
        blocked = []
    # --refetch drops every recorded work so the whole corpus is fetched and
    # re-extracted. Needed when the extraction logic changes: contexts are stored,
    # the pdfs are not, so there is nothing to re-run offline.
    if "--refetch" in sys.argv:
        print("refetching all %d recorded works" % len(keep), flush=True)
        keep, done = [], {}
    blocked_dois = {b["doi"] for b in blocked}
    deferred = []   # rebuilt this run; last run's deferrals are all retried above
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else 10 ** 6

    results, n = list(keep), 0
    remaining = sum(1 for w in works if w[2] and w[2] not in done and w[2] not in blocked_dois)
    est = min(remaining, limit) * (PACE_WORK + PACE_TRY) / 60.0
    print("%d works left to try, pacing %.0fs each, rough estimate %.0f minutes"
          % (remaining, PACE_WORK, est), flush=True)
    for year, title, doi, cites, found in works:
        if not doi or doi in done or doi in blocked_dois:
            continue
        if n >= limit:
            break
        n += 1
        blob, worst = None, "none"
        for url in pdf_urls(doi):
            blob, why = fetch_pdf(url)
            if blob:
                break
            # remember the most recoverable reason seen across all routes
            if why == "transient" or (why == "forbidden" and worst != "transient"):
                worst = why
            _sleep(PACE_TRY)
        if not blob:
            rec = {"year": year, "title": title, "doi": doi, "cites": cites, "reason": worst}
            if worst == "none":
                blocked.append(rec)
                print("BLOCKED  %s  no open copy  %s" % (doi, (title or "")[:50]), flush=True)
            else:
                deferred.append(rec)
                print("DEFERRED %s  %s  %s" % (doi, worst, (title or "")[:50]), flush=True)
            checkpoint(results, blocked, works, deferred)
            _sleep(PACE_WORK)
            continue
        text = text_of(blob)
        ctx = contexts(text)
        results.append({"year": year, "title": title, "doi": doi, "cites": cites,
                        "chars": len(text), "contexts": ctx})
        print("ok       %s  %d contexts  %s" % (doi, len(ctx), (title or "")[:50]), flush=True)
        checkpoint(results, blocked, works, deferred)
        _sleep(PACE_WORK)

    out = summary(results, blocked, works, deferred)
    print(json.dumps(out["counts"], indent=1))
    if "--write" in sys.argv:
        json.dump(out, open(OUT, "w"), indent=1)
        print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
