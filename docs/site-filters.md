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
| Kind | Repository or paper. Dropped while every entry was a repository; it returned with the paper lane, and it now also gates which sorts are on offer. |
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

The default is Codon lines of code descending, with one caution written into the page:
a `.codon` line count is not a project size. codonx is a Rust tool with a thirteen-line
fixture; jutge-tests is ten files holding fifteen lines. Sorting by it ranks a
conformance suite above a trading framework, so the site says so next to the control
rather than leaving the reader to infer it.

Three further sorts appear only when the Kind facet is narrowed to a single kind.
Stars measure a repository and citations measure a paper; ordering the two against each
other needs a conversion that does not exist, and rather than invent one the site
withholds the control until the question is asked of one kind at a time. Deselecting
the kind puts the list back on Codon lines rather than leaving it ordered by a key no
longer on offer.

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

**Codon mentions**, for papers: the places in the full text that discuss the Codon
family, counting numbered citation sites and prose mentions and excluding the
reference-list entry itself, which every citing work has exactly one of. This is the
paper-side answer to Codon lines -- how much Codon is in the work, saying nothing about
the work's importance -- and it is a floor rather than a count. Papers that cite by
superscript are invisible to the inline scan, the extractor keeps at most twelve
passages per paper, and Secure MICE, which extends Sequre with distributed data types,
counts zero here. The two papers that genuinely extend Codon sit at opposite ends of
this sort, which is the measure's own argument against being read as engagement.

## The count in the header is a floor

SDV's header count is a count. This one is not, and the page says so: the round-two
closing pass found 58 further repositories that the `.codon` extension search could
not see, none of them yet opened. See `docs/gaps.md`.
