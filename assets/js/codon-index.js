/* codon-world index. Renders data/codon-index.json with facet filtering. */
(function () {
  "use strict";

  var LABEL = {
    source: "Source", c_api_frontend: "C API frontend", jit_decorator: "JIT decorator",
    ir_plugin: "IR plugin", runtime_port: "Runtime port", vendored_install: "Vendored install",
    docs_mirror: "Docs mirror", mention_only: "Mention only", false_positive: "False positive",
    implementation: "Implementation", benchmark: "Benchmark", exploration: "Exploration",
    direct: "Direct", plugin: "Via plugin", framework: "Via framework",
    paper_backed: "Paper-backed", production: "Production", research_prototype: "Research prototype",
    coursework: "Coursework", toy: "Toy", doc_mirror: "Docs mirror", excluded: "Excluded",
    stated: "Stated by the repo", inferred: "Inferred",
    static_typing: "Static typing", llvm_inline: "Inline LLVM", c_interop: "C interop",
    par: "@par", tuple: "@tuple", python_interop: "Python interop", numpy: "NumPy",
    gpu: "GPU", seq_plugin: "Seq plugin", pipeline: "Pipeline |>",
    __none__: "Not recorded"
  };

  var FACETS = [
    ["integration_mode", "Integration mode", "facet-mode"],
    ["codon_role", "Codon role", "facet-role"],
    ["codon_via", "How Codon is reached", "facet-via"],
    ["provenance", "Provenance", "facet-prov"],
    ["why_codon_source", "Evidence", "facet-evidence"],
    ["feature", "Codon feature", "facet-feature"],
    ["year", "Last active", "facet-year"]
  ];

  var data = null, state = { sel: {}, q: "", group: "none", sort: "loc", summaries: true };
  FACETS.forEach(function (f) { state.sel[f[0]] = {}; });

  function labelFor(v) { return LABEL[v] || v; }
  function el(id) { return document.getElementById(id); }

  function valuesOf(e, facet) {
    if (facet === "feature") return Object.keys(e.codon_features || {});
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
      cb.onclick = function () { state.sel[facet][v] = cb.checked; render(); };
      lab.appendChild(cb);
      lab.appendChild(document.createTextNode(" " + labelFor(v) + " (" + c[v] + ")"));
      holder.appendChild(lab);
    });
    var head = el(holderId + "-count");
    if (head) head.textContent = "(" + keys.length + ")";
  }

  function sortEntries(list) {
    var s = state.sort;
    return list.slice().sort(function (a, b) {
      if (s === "loc") {
        var la = (a.scale || {}).own_codon_loc || 0, lb = (b.scale || {}).own_codon_loc || 0;
        return lb - la || (a.name || "").localeCompare(b.name || "");
      }
      if (s === "recent") {
        var da = (a.health || {}).last_commit || "", db = (b.health || {}).last_commit || "";
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

  function renderItem(e) {
    var d = document.createElement("div");
    d.className = "entry";
    var h = document.createElement("div");
    h.className = "entry-head";
    var a = document.createElement("a");
    a.href = e.url; a.target = "_blank"; a.rel = "noopener";
    a.textContent = e.name || e.id;
    h.appendChild(a);
    var sc = (e.scale || {}).own_codon_loc;
    if (sc) h.appendChild(chip(sc.toLocaleString() + " Codon LOC", "chip-scale"));
    d.appendChild(h);

    var meta = document.createElement("div");
    meta.className = "entry-chips";
    [["integration_mode", ""], ["codon_role", "chip-role"], ["codon_via", ""],
     ["provenance", ""], ["why_codon_source", "chip-ev"]].forEach(function (p) {
      var v = e[p[0]];
      if (v) meta.appendChild(chip(labelFor(v), p[1]));
    });
    if (e.integration_mode_secondary) meta.appendChild(chip("+ " + labelFor(e.integration_mode_secondary), ""));
    if (e.machine_authored) meta.appendChild(chip("Machine-authored", "chip-flag"));
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
    return d;
  }

  function render() {
    FACETS.forEach(function (f) { buildFacet(f[0], f[2]); });
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
        valuesOf(e, state.group).forEach(function (v) {
          (buckets[v] = buckets[v] || []).push(e);
        });
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
    el("group").onchange = function () { state.group = this.value; render(); };
    el("sort").onchange = function () { state.sort = this.value; render(); };
    el("btn-clear").onclick = clearAll;
    el("btn-summaries").onclick = function () {
      state.summaries = !state.summaries;
      this.textContent = state.summaries ? "Hide summaries" : "Show summaries";
      render();
    };
    render();
  }

  fetch("data/codon-index.json")
    .then(function (r) { return r.json(); })
    .then(boot)
    .catch(function (err) { el("results").textContent = "Could not load the index: " + err; });

  window._codonIndex = { boot: boot, state: state, render: render };
})();
