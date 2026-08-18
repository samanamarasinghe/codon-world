// Stub-DOM harness for assets/js/codon-index.js.
//
//   node test/harness.js
//
// A filter regression shows up in the header count and nothing else in the repo
// checks it: build.py validates DATA, not what the page displays. This runs the
// real site JS against the real data in node, with about forty lines of fake
// document and fetch, and prints the counts to compare.
//
// Expected, as of 87 entries:
//   default                73 -> see EXPECTED below, regenerated when entries change
//   codon_role=benchmark   the benchmark count
//   why_codon_source=stated the stated count
//   feature=gpu            the gpu count
// The script computes each expected value from the data itself and fails loudly
// if the rendered count disagrees, so it does not need updating when entries are
// added -- only when the filtering semantics change on purpose.

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
 'facet-mode', 'facet-role', 'facet-via', 'facet-prov', 'facet-evidence',
 'facet-feature', 'facet-year', 'facet-mode-count', 'facet-role-count',
 'facet-via-count', 'facet-prov-count', 'facet-evidence-count',
 'facet-feature-count', 'facet-year-count'].forEach(i => { ids[i] = mkEl('div'); });
ids['q'].value = ''; ids['group'].value = 'none'; ids['sort'].value = 'loc';

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
  const modes = new Set(E.map(e => e.integration_mode)).size;
  check('grouped by mode adds one heading per mode',
        ids['results'].children.length, E.length + modes);
  api.state.group = 'none'; api.render();

  check('back to default', shown(), E.length);

  console.log(failures ? '\n' + failures + ' FAILURES' : '\nall checks passed');
  process.exit(failures ? 1 : 0);
}, 50);
