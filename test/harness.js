// Stub-DOM harness for assets/js/codon-index.js.
//
//   node test/harness.js
//
// A filter regression shows up in the header count and nothing else in the repo
// checks it: build.py validates DATA, not what the page displays. This runs the
// real site JS against the real data in node, with about forty lines of fake
// document and fetch, and compares every rendered count against the data itself.
//
// Every expectation is computed from data/codon-index.json, so this does not need
// updating when entries are added -- only when the filtering semantics change on
// purpose. Exits non-zero on any mismatch.

const fs = require('fs'), vm = require('vm'), path = require('path');
const root = path.join(__dirname, '..');
const data = JSON.parse(fs.readFileSync(path.join(root, 'data/codon-index.json'), 'utf8'));

function mkEl(tag) {
  return {
    tagName: tag, children: [], childNodes: [], style: {},
    classList: { add() {}, remove() {} },
    set className(v) { this._c = v; }, get className() { return this._c || ''; },
    set textContent(v) { this._t = v; this.children = []; this.childNodes = []; },
    get textContent() { return this._t || ''; },
    appendChild(c) { this.children.push(c); this.childNodes.push(c); return c; },
    setAttribute() {}, addEventListener() {}
  };
}

const ids = {};
['q', 'group', 'sort', 'btn-clear', 'btn-summaries', 'count', 'results',
 'facet-kind', 'facet-relation', 'facet-mode', 'facet-role', 'facet-via',
 'facet-prov', 'facet-evidence', 'facet-feature', 'facet-year',
 'facet-kind-count', 'facet-relation-count', 'facet-mode-count', 'facet-role-count',
 'facet-via-count', 'facet-prov-count', 'facet-evidence-count',
 'facet-feature-count', 'facet-year-count'].forEach(i => { ids[i] = mkEl('div'); });
ids['q'].value = ''; ids['group'].value = 'none'; ids['sort'].value = 'impact';

global.document = {
  getElementById: id => ids[id] || null,
  createElement: mkEl,
  createTextNode: t => ({ textContent: t }),
  createDocumentFragment: () => mkEl('frag')
};
global.fetch = () => Promise.resolve({ json: () => Promise.resolve(data) });
global.window = {};

vm.runInThisContext(fs.readFileSync(path.join(root, 'assets/js/codon-index.js'), 'utf8'));

function shown() { return parseInt(ids['count'].textContent, 10); }

let failures = 0;
function check(label, got, want) {
  const ok = got === want;
  if (!ok) failures++;
  console.log((ok ? 'ok   ' : 'FAIL ') + label + ': rendered ' + got + ', expected ' + want);
}

setTimeout(() => {
  const api = global.window._codonIndex;
  const E = data.entries;

  check('default', shown(), E.length);
  check('default rendered nodes', ids['results'].children.length, E.length);

  api.state.sel['codon_role']['benchmark'] = true; api.render();
  check('codon_role=benchmark', shown(), E.filter(e => e.codon_role === 'benchmark').length);
  api.state.sel['codon_role']['benchmark'] = false;

  api.state.sel['why_codon_source']['stated'] = true; api.render();
  check('evidence=stated', shown(), E.filter(e => e.why_codon_source === 'stated').length);
  api.state.sel['why_codon_source']['stated'] = false;

  api.state.sel['feature']['gpu'] = true; api.render();
  check('feature=gpu', shown(), E.filter(e => (e.codon_features || {}).gpu).length);
  api.state.sel['feature']['gpu'] = false;

  api.state.sel['integration_mode']['source'] = true;
  api.state.sel['codon_role']['implementation'] = true; api.render();
  check('two facets combine (AND across, OR within)', shown(),
        E.filter(e => e.integration_mode === 'source' && e.codon_role === 'implementation').length);
  api.state.sel['integration_mode']['source'] = false;
  api.state.sel['codon_role']['implementation'] = false;

  api.state.q = 'sequre'; api.render();
  const q = E.filter(e => ((e.name || '') + ' ' + (e.summary || '') + ' ' + (e.url || ''))
                    .toLowerCase().includes('sequre')).length;
  check('search=sequre', shown(), q);
  api.state.q = '';

  api.state.group = 'integration_mode'; api.render();
  // Repositories bucket by their mode; papers have none and land in one
  // "Not applicable" bucket, which must exist rather than dropping them.
  const modes = new Set(E.filter(e => e.kind === 'repo').map(e => e.integration_mode)).size;
  const anyPapers = E.some(e => e.kind !== 'repo') ? 1 : 0;
  check('grouped by mode adds one heading per mode, plus one for papers',
        ids['results'].children.length, E.length + modes + anyPapers);

  api.state.group = 'kind'; api.render();
  check('grouped by kind keeps every entry',
        ids['results'].children.length,
        E.length + new Set(E.map(e => e.kind)).size);

  api.state.sel['kind']['paper'] = true; api.state.group = 'none'; api.render();
  check('kind=paper', shown(), E.filter(e => e.kind === 'paper').length);
  api.state.sel['kind']['paper'] = false;

  api.state.sel['codon_relation']['extends'] = true; api.render();
  check('relation=extends selects only papers', shown(),
        E.filter(e => e.codon_relation === 'extends').length);
  api.state.sel['codon_relation']['extends'] = false;
  api.state.group = 'none'; api.render();

  check('back to default', shown(), E.length);

  // Codon impact is one control over two measures. Under a single kind it must be
  // exactly that kind's measure; with both on screen it ranks on the combined
  // score. Stars and citations have no cross-kind meaning at all, so each appears
  // only under its own kind, and narrowing away from one must not leave the list
  // on a dead key.
  const names = () => api.availableSorts().map(s => s[0]);
  check('mixed kinds offer impact and the kind-neutral sorts', names().join(','),
        'impact,recent,name');
  const topImpact = api.sortEntries(api.visible())[0];
  const maxImpact = Math.max(...E.map(e => api.impact(e)));
  check('impact sort leads with the highest combined score', api.impact(topImpact), maxImpact);

  api.state.sel['kind']['repo'] = true; api.render();
  check('kind=repo adds stars', names().join(','), 'impact,recent,name,stars');
  const topRepo = api.sortEntries(api.visible())[0];
  const maxLoc = Math.max(...E.filter(e => e.kind === 'repo')
                           .map(e => (e.scale || {}).own_codon_loc || 0));
  check('impact under repos is Codon lines',
        (topRepo.scale || {}).own_codon_loc || 0, maxLoc);
  api.state.sort = 'stars'; api.render();
  const byStars = api.sortEntries(api.visible());
  const maxStars = Math.max(...E.filter(e => e.kind === 'repo')
                             .map(e => (e.popularity || {}).stars == null ? -1 : e.popularity.stars));
  check('stars sort leads with the most-starred repo',
        (byStars[0].popularity || {}).stars == null ? -1 : byStars[0].popularity.stars, maxStars);
  api.state.sel['kind']['repo'] = false; api.render();
  check('dropping the kind drops the sort with it', api.state.sort, 'impact');

  api.state.sel['kind']['paper'] = true; api.render();
  check('kind=paper adds citations', names().join(','), 'impact,recent,name,citations');
  const topPaper = api.sortEntries(api.visible())[0];
  const maxMentions = Math.max(...E.filter(e => e.kind === 'paper')
                                .map(e => (e.codon_mentions || {}).count || 0));
  check('impact under papers is Codon mentions',
        (topPaper.codon_mentions || {}).count || 0, maxMentions);
  api.state.sort = 'citations'; api.render();
  const byCites = api.sortEntries(api.visible());
  const maxCites = Math.max(...E.filter(e => e.kind === 'paper')
                             .map(e => (e.popularity || {}).citations == null ? -1 : e.popularity.citations));
  check('citations sort leads with the most-cited paper',
        (byCites[0].popularity || {}).citations == null ? -1 : byCites[0].popularity.citations, maxCites);
  api.state.sel['kind']['paper'] = false; api.state.sort = 'impact'; api.render();

  // Instrumentation runs on every interaction, so a throw inside it would take
  // the controls down with it. It must be silent when the analytics script is
  // not there -- blocked, offline, or here -- and forward faithfully when it is.
  check('track is a silent no-op without umami', api.track('smoke', { a: 1 }), undefined);

  const sent = [];
  global.window.umami = { track: (n, d) => sent.push([n, d]) };
  api.track('facet:kind', { value: 'paper', on: true });
  delete global.window.umami;
  check('track forwards the event name and data to umami',
        JSON.stringify(sent),
        JSON.stringify([['facet:kind', { value: 'paper', on: true }]]));

  console.log(failures ? '\n' + failures + ' FAILURES' : '\nall checks passed');
  process.exit(failures ? 1 : 0);
}, 50);
