# Which SDV-world filters this site needs, and which it does not

The SDV index carries a large filter panel: two sliders, a title search, a 3x3 facet
grid, two exclusion-toggle groups and an author search. That panel was built for 1,087
entries with curated scores and harvested author affiliations. This index has 73 and
neither of those things. Copying the panel wholesale would give mostly empty controls,
so each one was checked against the data that actually exists.

## Dropped, because the data does not exist

| SDV control | Why not here |
|---|---|
| Popularity slider | No stars, forks or citations were harvested. Nothing to rank on. |
| SDV importance slider (0-6) | No importance score exists. `codon_role` carries the equivalent judgement in three values, which is a button group, not a slider. |
| Author/Contributor facet | No per-repo contributor lists were harvested. |
| Affiliation facet and region toggles | No affiliations. |
| Sector, and the academic/non-academic toggles | Not collected. `provenance` answers a nearby question and is kept instead. |

A slider is the wrong control at this size regardless. A percentile cut over 1,087
entries is a meaningful bar; over 73 it moves in jumps of more than one percent per
entry.

## Dropped, because the corpus is not there yet

| SDV control | Why not here |
|---|---|
| Kind (paper / repo / tutorial / dataset) | Every entry is a repository. The facet would have one value. It returns when the paper lane lands. |
| Toggle needs | No entry carries an unresolved `needs`; all six rulings are closed. |

## Kept, renamed to the local vocabulary

| SDV control | Here |
|---|---|
| Integration | **Integration mode** -- the same idea, a different vocabulary: source, JIT decorator, IR plugin, runtime port, C API frontend, vendored install, docs mirror, mention only, false positive. |
| SDV component / SDV concept | Collapsed into one **Codon feature** facet. SDV's split into packages and ideas has no analogue; what exists here is which language features a repo exercises. |
| Year | **Last active**, from `last_commit`. Not the same question SDV's Year facet asks -- it is staleness, not vintage -- and it earns its place because a third of this population stopped moving before 2025. 18 entries have no date and are grouped as Unknown. |
| Search title & summary | Kept unchanged. Every summary states where Codon is used and for what, so the search reaches the reasoning. |
| Group-by and sort-within | Kept, with local values. |

## Added, with no SDV equivalent

| Control | Why |
|---|---|
| **Codon role** | implementation, benchmark, exploration. Ruling 5. Separates the 38 repos built on Codon from the 11 measuring it and the 22 trying it. |
| **How Codon is reached** | direct, plugin, framework. Decor and Secure MICE reach Codon through Sequre and would otherwise read as ordinary users. |
| **Provenance** | paper-backed, production, research prototype, coursework, toy, docs mirror. |
| **Evidence quality** | `why_codon_source`, stated or inferred. 45 of 73 entries rest on an inference rather than a claim the repo makes. A reader deserves to see which, and to be able to keep only the stated ones. SDV has no analogue because its summaries always quote a source sentence. |
| **Machine-authored** | Ruling 6. Two entries so far. |

## Sorting

SDV sorts within a section by popularity or importance. Neither exists here. The
default is Codon lines of code descending, with one caution written into the page: a
`.codon` line count is not a project size. codonx is a Rust tool with a thirteen-line
fixture; jutge-tests is ten files holding fifteen lines. Sorting by it ranks a
conformance suite above a trading framework, so the site says so next to the control
rather than leaving the reader to infer it.

## The count in the header is a floor

SDV's header count is a count. This one is not, and the page says so: the round-two
closing pass found 58 further repositories that the `.codon` extension search could
not see, none of them yet opened. See `docs/gaps.md`.
