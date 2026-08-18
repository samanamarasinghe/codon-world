# Running things

What to run, where, and what it costs.

## Nothing here needs funding

GitHub Actions is free with unlimited standard-runner minutes on public
repositories, and this repository is public. The minute allowance and spending
limits in GitHub's billing settings apply to private repositories only.

The one thing in this project that does cost money is **OpenAlex**, which bills per
request against a daily allowance. That is a separate account at
<https://openalex.org/pricing> and is unrelated to Actions. The harvesters call it,
so if a run reports `Insufficient budget`, that is the thing to top up -- not
Anything on GitHub.

## The three workflows

All of them live under **Actions** in the repository:
<https://github.com/samanamarasinghe/codon-world/actions>

### 1. Build index and publish site

**Runs by itself** on every push to `main`. Rebuilds `data/codon-index.json` from
the lane files and redeploys the site. There is normally no reason to trigger it by
hand; do so only if a push landed while Pages was misconfigured.

Site: <https://samanamarasinghe.github.io/codon-world/>

### 2. Harvest citations

**Manual.** Run once when the paper candidate list is missing or stale.

1. Open <https://github.com/samanamarasinghe/codon-world/actions/workflows/harvest-citations.yml>
2. **Run workflow** -> **Run workflow**

Takes a few minutes. Writes `data/papers-candidates.json` and commits it only if the
citing-work set changed. Calls OpenAlex and Semantic Scholar.

### 3. Fetch paper contexts

**Manual, and the long one.** This is the job to start before going away.

1. Open <https://github.com/samanamarasinghe/codon-world/actions/workflows/fetch-contexts.yml>
2. **Run workflow**
3. Leave **limit** blank to attempt every remaining work. Leave the two pacing
   fields at their defaults unless a previous run hit rate limits, in which case
   raise them.
4. **Run workflow**

Roughly 45 minutes per 100 papers at the default pacing, against a 330-minute
timeout. It writes `data/paper-contexts.json`, checkpointing after every paper, and
commits whatever it gathered even if the job is cancelled or times out.

It is resumable: papers already recorded, and papers already marked blocked, are
skipped. Running it again after a failure costs nothing but the papers it had not
reached.

Watch it live by clicking into the running job -- output is unbuffered, so each
paper prints as it finishes, and each wait prints why.

## Running the same thing locally instead

Everything works on a laptop with Python 3 and `pip install pypdf`:

```
git clone https://github.com/samanamarasinghe/codon-world
cd codon-world
python3 harvest/citations.py --write        # candidate list
python3 harvest/fetch_contexts.py --write   # the long fetch
git add data && git commit -m "fetch contexts" && git push
```

To go slower, set the pacing in the environment:

```
PACE_WORK=40 PACE_HOST=20 python3 harvest/fetch_contexts.py --write
```

Setting `UNPAYWALL_EMAIL` to your address adds Unpaywall as a fourth route for
finding open copies, which the CI run does not have.

## Checking the site after a change

```
python3 build.py --write     # rebuild the index from the lane files
node test/harness.js         # nine checks on the rendered counts
python3 -m http.server 8000  # then open http://localhost:8000/
```

`build.py` validates the data; `test/harness.js` validates what the page displays.
A filter bug shows up only in the second.
