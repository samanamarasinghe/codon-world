/* codon-world index. Renders data/codon-index.json with facet filtering. */
(function () {
  "use strict";

  var LABEL = {
    source: "Source", c_api_frontend: "C API frontend", jit_decorator: "JIT decorator",
    ir_plugin: "IR plugin", runtime_port: "Runtime port", vendored_install: "Vendored install",
    packaging: "Packaging", docs_mirror: "Docs mirror", mention_only: "Mention only",
    false_positive: "False positive",
    implementation: "Implementation", benchmark: "Benchmark", exploration: "Exploration",
    direct: "Direct", plugin: "Via plugin", framework: "Via framework",
    paper_backed: "Paper-backed", production: "Production", research_prototype: "Research prototype",
    coursework: "Coursework", toy: "Toy", doc_mirror: "Docs mirror", excluded: "Excluded",
    stated: "Stated by the source", inferred: "Inferred",
    repo: "Repository", paper: "Paper",
    extends: "Extends Codon", uses: "Uses Codon", evaluates: "Evaluates Codon",
    prior_art: "Cites as prior art",
    published: "Published", preprint: "Preprint", thesis: "Thesis", survey: "Survey",
    static_typing: "Static typing", llvm_inline: "Inline LLVM", c_interop: "C interop",
    par: "@par", tuple: "@tuple", python_interop: "Python interop", numpy: "NumPy",
    gpu: "GPU", seq_plugin: "Seq plugin", pipeline: "Pipeline |>",
    __none__: "Not recorded", __na__: "Not applicable"
  };

  var FACETS = [
    ["kind", "Kind", "facet-kind"],
    ["codon_relation", "How the paper relates", "facet-relation"],
    ["integration_mode", "Integration mode", "facet-mode"],
    ["codon_role", "Codon role", "facet-role"],
    ["codon_via", "How Codon is reached", "facet-via"],
    ["provenance", "Provenance", "facet-prov"],
    ["why_codon_source", "Evidence", "facet-evidence"],
    ["feature", "Codon feature", "facet-feature"],
    ["year", "Last active", "facet-year"]
  ];

  // Codon impact is one control over two measures: .codon lines for a repository,
  // Codon mentions in the full text for a paper. Under a single kind it is just
  // that kind's measure. With both on screen the two are put on one scale by
  // dividing lines by IMPACT_DIVISOR, which is a choice, not a fact: it sets the
  // rate at one mention to two thousand lines. The score is never displayed --
  // entries print their own measure, in its own units.
  var IMPACT_DIVISOR = 2000;

  // Stars and citations are different: there is no conversion between them at
  // all, so each is offered only when its own kind is the one being shown.
  var SORTS = [
    ["impact", "Codon impact (most first)", null],
    ["recent", "Most recent", null],
    ["name", "Name (A-Z)", null],
    ["stars", "Stars (most first)", "repo"],
    ["citations", "Citations (most first)", "paper"]
  ];

  var data = null, state = { sel: {}, q: "", group: "none", sort: "impact", summaries: true };
  FACETS.forEach(function (f) { state.sel[f[0]] = {}; });

  // ---- instrumentation -------------------------------------------------
  // umami (cloud.umami.is) is loaded from index.html. It is cookieless and
  // records no personal data; these events say what was done with the controls,
  // not who did it. Every call below is a no-op when the script is not there --
  // blocked, offline, or the node harness -- so instrumentation cannot take the
  // page down. What each event carries: docs/analytics.md.
  function track(name, props) {
    try {
      var u = typeof window !== "undefined" && window.umami;
      if (u && typeof u.track === "function") u.track(name, props);
    } catch (err) { /* analytics never interrupts the page */ }
  }

  // A keystroke is not a search and a half-typed query is not a miss, so the
  // query and the empty-result signal are reported once the view settles.
  var SETTLE_MS = 1200, settleTimer = null, lastQuery = "", lastEmpty = "";

  function facetSignature() {
    return FACETS.map(function (f) { return f[0] + "=" + selected(f[0]).join("|"); })
                 .filter(function (s) { return s.indexOf("=") !== s.length - 1; })
                 .join(";");
  }

  function settle() {
    var vis = visible();
    if (state.q && state.q !== lastQuery) {
      lastQuery = state.q;
      track("search", { q: state.q.slice(0, 60), hits: vis.length });
    }
    // An empty view is the useful negative: it says the index was asked for
    // something it does not hold, and names the filters that asked.
    var sig = facetSignature() + ";q=" + state.q;
    if (!vis.length && sig !== lastEmpty) {
      lastEmpty = sig;
      track("no-results", { q: state.q.slice(0, 60), filters: facetSignature().slice(0, 180) });
    }
  }

  function scheduleSettle() {
    if (settleTimer) clearTimeout(settleTimer);
    settleTimer = setTimeout(settle, SETTLE_MS);
  }

  function labelFor(v) { return LABEL[v] || v; }
  function el(id) { return document.getElementById(id); }

  function valuesOf(e, facet) {
    if (facet === "feature") return Object.keys(e.codon_features || {});
    // Fields that only exist on one kind of entry contribute nothing from the
    // other, so a paper never shows up under Integration mode and a repository
    // never shows up under How the paper relates.
    if (facet === "codon_relation" && e.kind !== "paper") return [];
    if (facet === "integration_mode" && e.kind !== "repo") return [];
    if (facet === "year") {
      var lc = (e.health || {}).last_commit;
      return [lc ? String(lc).slice(0, 4) : "__none__"];
    }
    var v = e[facet];
    return [v == null ? "__none__" : v];
  }

  function selected(facet) {
    return Object.keys(state.sel[facet]).filter(function (k) { return state.sel[facet][k]; });
  }

  function passes(e, skip) {
    for (var i = 0; i < FACETS.length; i++) {
      var f = FACETS[i][0];
      if (f === skip) continue;
      var sel = selected(f);
      if (!sel.length) continue;
      var vals = valuesOf(e, f);
      if (!vals.length) return false;
      var hit = sel.some(function (s) { return vals.indexOf(s) >= 0; });
      if (!hit) return false;
    }
    if (state.q) {
      var hay = ((e.name || "") + " " + (e.summary || "") + " " + (e.url || "")).toLowerCase();
      if (hay.indexOf(state.q) < 0) return false;
    }
    return true;
  }

  function visible() { return data.entries.filter(function (e) { return passes(e, null); }); }

  function counts(facet) {
    var c = {};
    data.entries.forEach(function (e) {
      if (!passes(e, facet)) return;
      valuesOf(e, facet).forEach(function (v) { c[v] = (c[v] || 0) + 1; });
    });
    return c;
  }

  function buildFacet(facet, holderId) {
    var holder = el(holderId);
    if (!holder) return;
    holder.textContent = "";
    var c = counts(facet), keys = Object.keys(c);
    keys.sort(function (a, b) {
      if (facet === "year") return b.localeCompare(a);
      return c[b] - c[a] || a.localeCompare(b);
    });
    keys.forEach(function (v) {
      var lab = document.createElement("label");
      lab.className = "facet-item";
      var cb = document.createElement("input");
      cb.type = "checkbox";
      cb.checked = !!state.sel[facet][v];
      cb.onclick = function () {
        state.sel[facet][v] = cb.checked;
        track("facet:" + facet, { value: v, on: cb.checked });
        render();
      };
      lab.appendChild(cb);
      lab.appendChild(document.createTextNode(" " + labelFor(v) + " (" + c[v] + ")"));
      holder.appendChild(lab);
    });
    var head = el(holderId + "-count");
    if (head) head.textContent = "(" + keys.length + ")";
  }

  function soleKind() {
    var k = selected("kind");
    return k.length === 1 ? k[0] : null;
  }

  function availableSorts() {
    var k = soleKind();
    return SORTS.filter(function (s) { return !s[2] || s[2] === k; });
  }

  function syncSort() {
    var sel = el("sort");
    if (!sel) return;
    var avail = availableSorts();
    // Narrowing the Kind facet can take away the sort in use. Fall back rather
    // than leaving the list ordered by a key that is no longer on offer.
    var ok = avail.some(function (s) { return s[0] === state.sort; });
    if (!ok) state.sort = "impact";
    sel.textContent = "";
    avail.forEach(function (s) {
      var o = document.createElement("option");
      o.value = s[0];
      o.textContent = s[1];
      if (s[0] === state.sort) o.selected = true;
      sel.appendChild(o);
    });
    sel.value = state.sort;
  }

  function impact(e) {
    if (e.kind === "paper") return (e.codon_mentions || {}).count || 0;
    return ((e.scale || {}).own_codon_loc || 0) / IMPACT_DIVISOR;
  }

  function popNumber(e, key) {
    var v = (e.popularity || {})[key];
    return v == null ? -1 : v;   // never read is not the same as zero, and sorts last
  }

  function sortEntries(list) {
    var s = state.sort;
    return list.slice().sort(function (a, b) {
      if (s === "impact") {
        return impact(b) - impact(a) || (a.name || "").localeCompare(b.name || "");
      }
      if (s === "stars" || s === "citations") {
        var key = s === "stars" ? "stars" : "citations";
        return popNumber(b, key) - popNumber(a, key) || (a.name || "").localeCompare(b.name || "");
      }
      if (s === "recent") {
        var da = (a.health || {}).last_commit || String(a.year || ""),
            db = (b.health || {}).last_commit || String(b.year || "");
        return db.localeCompare(da) || (a.name || "").localeCompare(b.name || "");
      }
      return (a.name || "").localeCompare(b.name || "");
    });
  }

  function chip(text, cls) {
    var s = document.createElement("span");
    s.className = "chip " + (cls || "");
    s.textContent = text;
    return s;
  }

  function chipT(text, cls, title) {
    var s = chip(text, cls);
    s.title = title;
    return s;
  }

  function renderItem(e) {
    var d = document.createElement("div");
    d.className = "entry";
    var h = document.createElement("div");
    h.className = "entry-head";
    var a = document.createElement("a");
    a.href = e.url; a.target = "_blank"; a.rel = "noopener";
    a.textContent = e.name || e.id;
    a.onclick = function () { track("open", { entry: e.id || e.name, kind: e.kind }); };
    h.appendChild(a);
    var sc = (e.scale || {}).own_codon_loc;
    if (sc) h.appendChild(chip(sc.toLocaleString() + " Codon LOC", "chip-scale"));
    if (e.kind === "paper" && e.venue) h.appendChild(chip(e.venue + (e.year ? " " + e.year : ""), "chip-scale"));
    var pop = e.popularity || {};
    if (pop.stars != null) {
      h.appendChild(chipT(pop.stars.toLocaleString() + " stars", "chip-scale",
        "Stars on the repository as a whole, read " + pop.fetched + ". It measures the "
        + "repository, not its Codon content: a packaging recipe is followed by thousands "
        + "of people for whom Codon is one line of a build file."));
    }
    if (pop.citations != null) {
      h.appendChild(chipT(pop.citations.toLocaleString() + " citations", "chip-scale",
        "Citations of the whole paper from " + (pop.source === "openalex" ? "OpenAlex" : "Semantic Scholar")
        + ", read " + pop.fetched + ". Every such index undercounts against Google Scholar, "
        + "and the number counts citations of the paper, not of anything Codon did in it."));
    }
    d.appendChild(h);

    var meta = document.createElement("div");
    meta.className = "entry-chips";
    [["kind", "chip-kind"], ["codon_relation", "chip-role"], ["integration_mode", ""],
     ["codon_role", "chip-role"], ["codon_via", ""],
     ["provenance", ""], ["why_codon_source", "chip-ev"]].forEach(function (p) {
      var v = e[p[0]];
      if (v) meta.appendChild(chip(labelFor(v), p[1]));
    });
    var mn = e.codon_mentions;
    if (mn) {
      meta.appendChild(chipT(
        mn.count ? mn.count + (mn.capped ? "+" : "") + " Codon mentions" : "no Codon mentions extracted",
        "chip-dim",
        "Places in the full text that discuss the Codon family: " + mn.inline + " numbered "
        + "citation sites and " + mn.body + " prose mentions. The reference list entry itself is "
        + "not counted.\n\nRead it as a floor. Papers that cite by superscript are invisible to "
        + "the scan, the extractor keeps at most twelve passages per paper, and Secure MICE, "
        + "which extends Sequre, counts zero here."));
    }
    if (e.integration_mode_secondary) meta.appendChild(chip("+ " + labelFor(e.integration_mode_secondary), ""));
    if (e.machine_authored) meta.appendChild(chip("Machine-authored", "chip-flag"));
    if (e.needs) meta.appendChild(chip("Unresolved", "chip-flag"));
    if (e.related_repo) meta.appendChild(chip("has a repository entry", "chip-dim"));
    if (e.codon_version_pinned) meta.appendChild(chip("Codon " + e.codon_version_pinned, ""));
    if ((e.health || {}).last_commit) meta.appendChild(chip("last commit " + e.health.last_commit, "chip-dim"));
    Object.keys(e.codon_features || {}).forEach(function (f) {
      var v = e.codon_features[f];
      meta.appendChild(chip(labelFor(f) + " " + v.occurrences + (v.files ? "/" + v.files : ""), "chip-feat"));
    });
    d.appendChild(meta);

    if (state.summaries && e.summary) {
      var p = document.createElement("p");
      p.className = "entry-summary";
      p.textContent = e.summary;
      d.appendChild(p);
    }
    if (e.why_codon) {
      var w = document.createElement("p");
      w.className = "entry-why " + (e.why_codon_source === "inferred" ? "why-inferred" : "why-stated");
      w.textContent = (e.why_codon_source === "inferred" ? "Inferred: " : "Stated: ") + e.why_codon;
      d.appendChild(w);
    }
    if (e.note) {
      var n = document.createElement("p");
      n.className = "entry-note";
      n.textContent = e.note;
      d.appendChild(n);
    }
    if (e.needs) {
      var q = document.createElement("p");
      q.className = "entry-note";
      q.textContent = "Unresolved: " + e.needs;
      d.appendChild(q);
    }
    return d;
  }

  function render() {
    FACETS.forEach(function (f) { buildFacet(f[0], f[2]); });
    syncSort();
    var vis = sortEntries(visible());
    el("count").textContent = vis.length + " of " + data.entries.length +
      " entries \u2014 a floor, not a count (see docs/gaps.md)";
    var out = el("results");
    out.textContent = "";
    if (state.group === "none") {
      vis.forEach(function (e) { out.appendChild(renderItem(e)); });
    } else {
      var buckets = {};
      vis.forEach(function (e) {
        // An entry with no value for the grouping facet -- a paper grouped by
        // integration mode, say -- goes in its own bucket rather than vanishing.
        var vals = valuesOf(e, state.group);
        if (!vals.length) vals = ["__na__"];
        vals.forEach(function (v) { (buckets[v] = buckets[v] || []).push(e); });
      });
      Object.keys(buckets).sort(function (a, b) {
        return buckets[b].length - buckets[a].length || a.localeCompare(b);
      }).forEach(function (k) {
        var h = document.createElement("h2");
        h.className = "group-head";
        h.textContent = labelFor(k) + " (" + buckets[k].length + ")";
        out.appendChild(h);
        sortEntries(buckets[k]).forEach(function (e) { out.appendChild(renderItem(e)); });
      });
    }
    scheduleSettle();
  }

  function clearAll() {
    FACETS.forEach(function (f) { state.sel[f[0]] = {}; });
    state.q = "";
    if (el("q")) el("q").value = "";
    render();
  }

  function boot(d) {
    data = d;
    el("q").oninput = function () { state.q = this.value.trim().toLowerCase(); render(); };
    el("group").onchange = function () {
      state.group = this.value;
      track("group", { group: state.group });
      render();
    };
    el("sort").onchange = function () {
      state.sort = this.value;
      // Which sort was chosen is only readable against the kind on screen: the
      // same "Codon impact" means lines, mentions, or the combined score.
      track("sort", { sort: state.sort, kind: soleKind() || "both" });
      render();
    };
    el("btn-clear").onclick = function () { track("clear"); clearAll(); };
    el("btn-summaries").onclick = function () {
      state.summaries = !state.summaries;
      this.textContent = state.summaries ? "Hide summaries" : "Show summaries";
      track("summaries", { on: state.summaries });
      render();
    };
    // Which method note gets opened is feedback too. Guarded: the stub document
    // in test/harness.js has no querySelectorAll.
    if (document.querySelectorAll) {
      Array.prototype.forEach.call(document.querySelectorAll("header a, footer a"), function (a) {
        a.addEventListener("click", function () {
          track("link", { href: a.getAttribute("href") || "" });
        });
      });
    }
    render();
  }

  fetch("data/codon-index.json")
    .then(function (r) { return r.json(); })
    .then(boot)
    .catch(function (err) { el("results").textContent = "Could not load the index: " + err; });

  window._codonIndex = { boot: boot, state: state, render: render,
                         availableSorts: availableSorts, sortEntries: sortEntries,
                         visible: visible, impact: impact, track: track };
})();
