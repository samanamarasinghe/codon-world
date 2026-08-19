# What this page measures

The site loads [umami](https://umami.is) from `cloud.umami.is` and reports how its
controls are used. Umami sets no cookies, stores no personal data and builds no
profile across sites; what is collected is listed in full below.

The point is not traffic. The index has nine facets, five sorts and a search box,
and nothing in the repository says which of them anyone touches, which entries get
opened, or what is asked for and not found. These events are there to answer that.

## Automatic

One page view per visit, with referrer, country, browser and screen size, as any
umami install records. The site is a single page, so page views alone say nothing
about what was done on it. Everything below is sent explicitly by
`assets/js/codon-index.js`.

## Events

| Event | Sent when | Data |
| --- | --- | --- |
| `facet:<name>` | a facet checkbox is ticked or unticked; one event name per facet, so `facet:kind`, `facet:provenance` and so on | `value`, `on` |
| `sort` | the sort is changed | `sort`, `kind` (`repo`, `paper` or `both`) |
| `group` | the grouping is changed | `group` |
| `search` | a query settles, 1.2 seconds after the last keystroke | `q` (first 60 characters), `hits` |
| `no-results` | a settled view shows nothing | `q`, `filters` |
| `open` | an entry's link is clicked | `entry` (its id), `kind` |
| `link` | a header or footer link is clicked, which is how a method note gets read | `href` |
| `summaries` | summaries are hidden or shown | `on` |
| `clear` | Clear filters is pressed | none |

Two of these carry more than a count. `sort` carries the kind because the same
choice means different things under it: Codon impact is `.codon` lines for
repositories, extracted mentions for papers, and a combined score with both on
screen. `no-results` carries the filter state because a miss is only informative
alongside what was asked for -- it is the one event that can say the index was
asked for something it does not hold.

## Not collected

No names, no addresses, no logins -- the site has none of these. Query text is
truncated at 60 characters and sent only after the query settles, so half-typed
words are not reported. Nothing is stored in the browser.

## Reading the numbers

They are a floor, in the same sense as the entry count on the page. Blockers stop
the script for a fair share of this audience, and those visits are invisible here.
Treat a count as evidence that something is used at least this much, never as a
measure of how much it is not.

## Turning it off

Delete the `script` tag from the head of `index.html`. Nothing else needs to
change: `track()` in `assets/js/codon-index.js` checks for `window.umami` on every
call and does nothing when it is absent, which is also how the node harness runs.
`test/harness.js` asserts both halves of that -- silence without umami, faithful
forwarding with it.
