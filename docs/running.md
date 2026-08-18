# Running things

What to run, where, and what it costs.

## Nothing here needs funding

GitHub Actions is free with unlimited standard-runner minutes on public
repositories, and this repository is public. The minute allowance and spending
limits in GitHub's billing settings apply to private repositories only.

The one thing in this project that costs money is **OpenAlex**, which bills per
request against a daily allowance. That is a separate account at
<https://openalex.org/pricing>. If a run prints `Insufficient budget`, that is what
to top up -- nothing on GitHub.

## The three workflows

All under **Actions**: <https://github.com/samanamarasinghe/codon-world/actions>

### 1. Build index and publish site

**Runs by itself** on every push to `main`. Rebuilds `data/codon-index.json`, runs
the page harness, redeploys the site. No reason to trigger it by hand.

Site: <https://samanamarasinghe.github.io/codon-world/>

### 2. Harvest citations

**Manual.** Run when the paper candidate list is missing or stale. Takes a few
minutes. Writes `data/papers-candidates.json`.

### 3. Fetch paper contexts

**Manual, long-running.** This is the one that does real work.

#### Step by step

1. Open
   <https://github.com/samanamarasinghe/codon-world/actions/workflows/fetch-contexts.yml>
2. On the right of the blue banner, click the **Run workflow** dropdown.
3. A small panel opens with five fields:

   | field | what to put |
   |---|---|
   | Use workflow from | `main` (already selected) |
   | How many new works to attempt this run | **leave empty** -- empty means all of them |
   | mode | pick from the dropdown, see below |
   | Seconds to wait between papers | `20` (leave it) |
   | Minimum seconds between two requests to the same host | `12` (leave it) |

4. Click the green **Run workflow** button inside the panel.
5. Wait about ten seconds and reload the page. A new run appears at the top of the
   list with a yellow dot. Click it, then click the **fetch** job to watch the log
   live -- output is unbuffered, so each paper prints as it finishes.

#### Which mode

| mode | what it does | when |
|---|---|---|
| `normal` | fetches works not yet recorded, and retries anything deferred last run | the usual choice |
| `retry-blocked` | also re-attempts works previously judged to have no open copy | after adding a new fetch route |
| `refetch` | **throws away every recorded context and redoes the whole corpus** | after the extraction logic changes |

#### What a healthy run looks like

The log should open with something like:

```
migrating 56 pre-split blocks to deferred
96 works left to try, pacing 20s each, rough estimate 41 minutes
ok       10.1007/s10207-026-01223-3  4 contexts  ATTUNE-SHARE: an agent-based ...
DEFERRED 10.3390/electronics15020399  forbidden  Privacy-Preserving Protocols ...
BLOCKED  10.1016/j.jisa.2025.103976  no open copy  General-purpose multi-user ...
```

and end with a counts block and `wrote data/paper-contexts.json`. Expect an hour or
so for a full pass; the timeout is 330 minutes.

#### How to tell it worked

The repository gets a commit from `github-actions[bot]` titled
`CI: fetch paper citation contexts`. Open `data/paper-contexts.json` and read the
`counts` block: `with_contexts` should have grown, and `blocked` and `deferred`
should both be populated rather than one holding everything.

`blocked` means no open copy exists anywhere and an institutional login is needed.
`deferred` means a copy exists but the host refused this run -- rate limiting, or a
publisher that serves only browsers. Deferrals retry automatically next time, so a
second `normal` run a day later usually recovers several.

#### If it goes wrong

- `Insufficient budget` -- OpenAlex, not GitHub. Top up and re-run; nothing is lost,
  because the job checkpoints after every paper and commits on failure too.
- Everything `DEFERRED` -- a host is rate limiting hard. Re-run with the pacing
  fields raised, say `60` and `30`.
- Job cancelled or timed out -- just run it again in `normal` mode. It resumes.

## Running the same thing locally instead

```
git clone https://github.com/samanamarasinghe/codon-world
cd codon-world
pip install pypdf
python3 harvest/citations.py --write          # candidate list
python3 harvest/fetch_contexts.py --write     # the long fetch
python3 harvest/fetch_contexts.py --refetch --write   # or redo everything
git add data && git commit -m "fetch contexts" && git push
```

Pacing is set by environment variable:

```
PACE_WORK=40 PACE_HOST=20 python3 harvest/fetch_contexts.py --write
```

Setting `UNPAYWALL_EMAIL` to your address adds Unpaywall as an extra route for
finding open copies, which the CI run does not have. That should shrink the blocked
list, so a local run is worth doing at least once.

## Checking the site after a change

```
python3 build.py --write     # rebuild the index from the lane files
node test/harness.js         # twelve checks on the rendered counts
python3 -m http.server 8000  # then open http://localhost:8000/
```

`build.py` validates the data; `test/harness.js` validates what the page displays.
A filter bug shows up only in the second, which is why CI runs it too.
