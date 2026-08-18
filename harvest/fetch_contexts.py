#!/usr/bin/env python3
"""Fetch open full texts for the paper candidates and extract the Codon citation context.

    python3 harvest/fetch_contexts.py               # all works not already done
    python3 harvest/fetch_contexts.py --limit 20    # first N undone works
    python3 harvest/fetch_contexts.py --write       # write data/paper-contexts.json

This does the mechanical half of the paper lane: find a readable copy, pull the
text, and cut out the sentences where the work actually cites Codon or Seq. It
makes no judgement -- codon_relation is still set by a person reading the extract,
as ruling 8 requires.

It is resumable, and it checkpoints after every paper, so an interrupted run loses
only the fetch in flight. Works already recorded, and works already marked blocked,
are skipped.

Routes, in order (docs/paper-fetching.md):
  1. arXiv pdf, when the doi is a 10.48550 arXiv doi or a location points there
  2. every OpenAlex location carrying a pdf_url, not just the primary one
  3. a publisher landing page, read once for a citation_pdf_url meta tag or a
     link ending .pdf
  4. Unpaywall, if UNPAYWALL_EMAIL is set
Anything still unreachable is listed under "blocked" for institutional access.

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
    """Fetch a pdf. If the url serves html, look inside it for a pdf link once."""
    _throttle(url)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (research)"})
        data = urllib.request.urlopen(req, timeout=timeout).read()
    except Exception as exc:
        if "429" in str(exc) or "503" in str(exc):
            _sleep(BACKOFF, "rate limited fetching a pdf")
        return None
    if data[:4] == b"%PDF":
        return data
    if not follow_html:
        return None
    html = data[:400000].decode("utf-8", "ignore")
    cands = re.findall(r'citation_pdf_url"\s+content="([^"]+)"', html)
    cands += re.findall(r'href="([^"]+\.pdf[^"]*)"', html)
    base = re.match(r"(https?://[^/]+)", url)
    for c in cands[:4]:
        if c.startswith("/") and base:
            c = base.group(1) + c
        if not c.startswith("http"):
            continue
        got = fetch_pdf(c, timeout=timeout, follow_html=False)
        if got:
            return got
    return None


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
        # The reference number sits just before the author list, but not always
        # flush against it -- "[61] Ariya Shajii" puts a given name in between.
        head = text[max(0, m.start() - 160):m.start()]
        bracketed = re.findall(r"\[(\d{1,3})\]", head)
        if bracketed:
            numbers.add(bracketed[-1])
        else:
            plain = re.findall(r"(?:^|\s)(\d{1,3})\.\s", head)
            if plain:
                numbers.add(plain[-1])
    first = min((m.start() for m in NAME.finditer(text)), default=len(text))
    body = text[:first]
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


def summary(results, blocked, works):
    return {"generated": time.strftime("%Y-%m-%d"),
            "note": "Mechanical extraction only. codon_relation is set by a person "
                    "reading these, as ruling 8 requires.",
            "counts": {"with_contexts": len(results), "blocked": len(blocked),
                       "total_candidates": len(works)},
            "works": results, "blocked": blocked}


def checkpoint(results, blocked, works):
    """Write after every paper, so a killed run loses nothing but the current fetch."""
    if "--write" in sys.argv:
        json.dump(summary(results, blocked, works), open(OUT, "w"), indent=1)


def main():
    works = json.load(open(CAND))["works"]
    done, blocked = {}, []
    if os.path.exists(OUT):
        prev = json.load(open(OUT))
        done = {w["doi"]: w for w in prev["works"] if w.get("doi")}
        blocked = prev.get("blocked", [])
    blocked_dois = {b["doi"] for b in blocked}
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else 10 ** 6

    results, n = list(done.values()), 0
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
        blob = None
        for url in pdf_urls(doi):
            blob = fetch_pdf(url)
            if blob:
                break
            _sleep(PACE_TRY)
        if not blob:
            blocked.append({"year": year, "title": title, "doi": doi, "cites": cites})
            print("BLOCKED %s  %s" % (doi, (title or "")[:60]), flush=True)
            checkpoint(results, blocked, works)
            _sleep(PACE_WORK)
            continue
        text = text_of(blob)
        ctx = contexts(text)
        results.append({"year": year, "title": title, "doi": doi, "cites": cites,
                        "chars": len(text), "contexts": ctx})
        print("ok      %s  %d contexts  %s" % (doi, len(ctx), (title or "")[:50]), flush=True)
        checkpoint(results, blocked, works)
        _sleep(PACE_WORK)

    out = summary(results, blocked, works)
    print(json.dumps(out["counts"], indent=1))
    if "--write" in sys.argv:
        json.dump(out, open(OUT, "w"), indent=1)
        print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
