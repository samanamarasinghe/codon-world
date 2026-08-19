# Which SDV-world filters this site needs, and which it does not

The SDV index carries a large filter panel: two sliders, a title search, a 3x3 facet
grid, two exclusion-toggle groups and an author search. That panel was built for 1,087
entries with curated scores and harvested author affiliations. This index has 146 --
108 repositories and 38 papers -- and neither of those things. Copying the panel
wholesale would give mostly empty controls, so each one was checked against the data
that actually exists.

## Dropped, because the data does not exist

| SDV control | Why not here |
|---|---|
| SDV importance slider (0-6) | No importance score exists, and none will: ruling 7 rejected an importance ladder as too much apparatus for a corpus this size. `codon_role` carries the nearby judgement in three values, which is a button group, not a slider. |
| Author/Contributor facet | No per-repo contributor lists were harvested. |
| Affiliation facet and region toggles | No affiliations. |
| Sector, and the academic/non-academic toggles | Not collected. `provenance` answers a nearby question and is kept instead. |

## Dropped, though the data now exists

| SDV control | Why not here |
|---|---|
| Popularity slider | Stars and citations are harvested, into `data/popularity.json`. They are offered as sorts and printed as chips, but not as a slider: a percentile cut over 1,087 entries is a meaningful bar, and over 146 it moves in jumps of most of a percent per entry. The distribution argues against it too -- 61 of 108 repositories have no stars at all, so most of the slider's travel would cover an empty range. |
| Toggle needs | No entry carries an unresolved `needs`. |

## Kept, renamed to the local vocabulary

| SDV control | Here |
|---|---|
| Integration | **Integration mode** -- the same idea, a different vocabulary: source, JIT decorator, IR plugin, runtime port, C API frontend, vendored install, packaging, docs mirror, mention only, false positive. |
| Kind | Repository or paper. Dropped while every entry was a repository; it returned with the paper lane, and it now also decides what the sort control offers. |
| SDV component / SDV concept | Collapsed into one **Codon feature** facet. SDV's split into packages and ideas has no analogue; what exists here is which language features a repo exercises. |
| Year | **Last active**, from `last_commit`. Not the same question SDV's Year facet asks -- it is staleness, not vintage -- and it earns its place because 18 repositories stopped moving before 2025. 32 have no commit date at all, along with every paper, and group as Not recorded. |
| Search title & summary | Kept unchanged. Every summary states where Codon is used and for what, so the search reaches the reasoning. |
| Group-by and sort-within | Kept, with local values. |

## Added, with no SDV equivalent

| Control | Why |
|---|---|
| **Codon role** | implementation, benchmark, exploration. Ruling 5. Separates the 51 repositories built on Codon from the 24 measuring it and the 31 trying it, and papers carry the same field. |
| **How the paper relates** | extends, uses, evaluates, cites as prior art. Ruling 7. Papers only, so selecting a value narrows the view to papers. |
| **How Codon is reached** | direct, plugin, framework. Decor and Secure MICE reach Codon through Sequre and would otherwise read as ordinary users. |
| **Provenance** | paper-backed, production, research prototype, coursework, toy, docs mirror for repositories; published, preprint, thesis, survey for papers. |
| **Evidence quality** | `why_codon_source`, stated or inferred. 62 of 146 entries rest on an inference rather than a claim the work makes. A reader deserves to see which, and to be able to keep only the stated ones. SDV has no analogue because its summaries always quote a source sentence. |
| **Machine-authored** | Ruling 6. Two entries so far. |

## Sorting

The default is **Codon impact**, one control over two measures: `.codon` lines for a
repository, Codon mentions in the full text for a paper. Narrow the Kind facet to one
kind and the sort is simply that kind's measure, so repositories alone rank by lines
and papers alone rank by mentions.

With both kinds on screen the two have to be put on one scale, and that takes a
conversion between a line of code and a citation passage, which is a choice and not a
fact. Lines are divided by two thousand, setting the rate at one mention to two
thousand lines: Sequre's 41,790 lines score 20.9 against UniTe's 12 mentions. The
score itself is never printed. Each entry shows its own measure in its own units, and
the ordering should be read as indicative while those two numbers are the real ones.

What the choice costs is worth stating. Eighteen papers carry exactly one mention,
most of them a single sentence naming Codon in passing, and thirty-six repositories
hold between one and 1,999 lines of Codon; at this rate every one of those papers
outranks every one of those repositories. A smaller divisor shrinks that set and a
larger one grows it. There is no divisor that makes the comparison true, only ones
that make it more or less flattering to code.

Neither measure is a size, and both are floors. A `.codon` line count says nothing
about a project: codonx is a Rust tool with a thirteen-line fixture, jutge-tests is ten
files holding fifteen lines, and more than half the repositories here write their Codon
in `.py` files and count zero. The mention count excludes the reference-list entry
itself, which every citing work has exactly one of, and misses papers that cite by
superscript entirely. Sixty-one entries therefore score nothing at all -- 56
repositories with no `.codon` file and five papers with no mentions extracted -- and
fall into alphabetical order behind everything else. Secure MICE, which extends Sequre
with distributed data types, is among them.

Two further sorts appear only when the Kind facet is narrowed to a single kind. Unlike
the impact measures these have no conversion between them at all, so the site withholds
the control until the question is asked of one kind at a time.

**Stars**, for repositories. The number is real and the ranking it produces is
misleading, which is why it carries the sharpest caution on the page: nine `packaging`
entries hold 96 per cent of every star in the index, and termux-packages alone holds
16,809. What the sort ranks is the distributions that ship Codon, not the work done
with it. The most-starred entry that actually writes Codon is FLOX at 221. The median
across 108 repositories is zero.

**Citations**, for papers, from OpenAlex where it holds the DOI and Semantic Scholar
otherwise. Of the whole paper, and not of anything Codon did in it -- the most-cited
work in the corpus is cited 126 times and barely mentions Codon. Every such index
undercounts against Google Scholar, so read the number as a floor, and both numbers
move, so each entry prints the date it was read.

## The count in the header is a floor

SDV's header count is a count. This one is not, and the page says so: the round-two
closing pass found 58 further repositories that the `.codon` extension search could
not see, none of them yet opened. See `docs/gaps.md`.
