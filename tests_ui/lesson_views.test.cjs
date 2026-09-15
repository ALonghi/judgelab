const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {disconnectedEnds} = require('./flow_geometry.cjs');

const root = path.join(__dirname, '..');
const catalog = JSON.parse(fs.readFileSync(path.join(root, 'app/catalog.json'), 'utf8'));
catalog.flows = JSON.parse(fs.readFileSync(path.join(root, 'app/flows.json'), 'utf8'));
const guides = JSON.parse(fs.readFileSync(path.join(root, 'app/lesson_guides.json'), 'utf8'));
for (const lesson of catalog.lessons) lesson.orientation = guides[lesson.id];
const source = fs.readFileSync(path.join(root, 'web/app.js'), 'utf8');
const styles = fs.readFileSync(path.join(root, 'web/app.css'), 'utf8');
const bootstrap = source.lastIndexOf('(async()=>{try{boot=');
assert.ok(bootstrap > 0, 'Browser bootstrap marker is present');
const context = vm.createContext({
  document: {addEventListener() {}},
  window: {addEventListener() {}},
  console,
});
// Load the real render functions; the HTTP bootstrap is exercised in the browser.
vm.runInContext(source.slice(0, bootstrap), context);
context.fixtureCatalog = catalog;
vm.runInContext('catalog=fixtureCatalog; boot={hosted:false}; state={completed:{}};', context);

function render(id, fn) {
  context.fixtureId = id;
  return vm.runInContext(`current=findLesson(fixtureId); ${fn}(current)`, context);
}

test('every problem is self-contained and contains no glossary, code or solution dump', () => {
  for (const lesson of catalog.lessons) {
    const html = render(lesson.id, 'scenarioView');
    assert.ok(html.includes('data-content="scenario"'), lesson.id);
    assert.ok(!/<dl|<pre|implementation-guide|decision-question/.test(html), lesson.id);
    assert.ok(!html.includes('Start with the situation'), lesson.id);
    assert.ok(lesson.scenario.prompt.length > 0);
    assert.ok(lesson.scenario.requirements.length >= 2);
    assert.ok(lesson.scenario.deliverable.length > 0, lesson.id);
    assert.ok(lesson.strategy.use_case.length > 0, `${lesson.id}: production use case`);
    assert.ok(lesson.strategy.mechanism.length > 0, `${lesson.id}: mechanism`);
    assert.ok(lesson.strategy.recognize.length > 0, `${lesson.id}: design questions`);
    assert.ok(lesson.strategy.proposal.length > 0, `${lesson.id}: production proposal`);
    assert.ok(lesson.strategy.caveats.length > 0, `${lesson.id}: limitations`);
  }
});

test('walkthroughs retain examples and implementation steps separately', () => {
  for (const lesson of catalog.lessons) {
    const html = render(lesson.id, 'walkthroughView');
    assert.ok(html.includes('data-content="walkthrough"'), lesson.id);
    assert.ok(html.includes('implementation-guide'), lesson.id);
    assert.ok(!html.includes('knowledge-terms'), lesson.id);
    assert.ok(!html.includes('decision-context'), lesson.id);
  }
  assert.ok(render('q-context', 'walkthroughView').includes('selected.append'));
  assert.ok(render('q-context', 'walkthroughView').includes('Budget trace'));
  assert.ok(render('g-score', 'walkthroughView').includes('score-table'));
});

test('knowledge base retains definitions, design alternatives and supporting notes', () => {
  for (const lesson of catalog.lessons) {
    const html = render(lesson.id, 'knowledgeView');
    assert.ok(html.includes('knowledge-terms'), lesson.id);
    assert.ok(html.includes('What changes the design?'), lesson.id);
  }
  const contextHtml = render('q-context', 'knowledgeView');
  assert.ok(contextHtml.includes('Python ranking example'));
  assert.ok(contextHtml.includes('#lesson/c-index-query'));
  assert.ok(render('c-index-build', 'knowledgeView').includes('Models, full contract'));
});

test('tab navigation separates reference material and exposes the active panel', () => {
  for (const id of ['g-score', 'q-context', 's-search']) {
    context.fixtureId = id;
    const html = vm.runInContext('current=findLesson(fixtureId); phase=3; feedback=null; phaseTabs()', context);
    assert.ok(html.includes('knowledge-tab'));
    assert.ok(html.includes('id="lesson-tab-3" role="tab" aria-controls="lesson-panel" aria-selected="true" tabindex="0"'));
    assert.equal((html.match(/role="tab"/g) || []).length, 4);
  }
});

test('scenario and reference content is HTML escaped', () => {
  context.malicious = structuredClone(catalog.lessons[0]);
  context.malicious.scenario.prompt = '<img src=x onerror=alert(1)>';
  const html = vm.runInContext('scenarioView(malicious)', context);
  assert.ok(html.includes('&lt;img'));
  assert.ok(!html.includes('<img'));
});

test('optional search recap is accessible but skipped by chapter progression', () => {
  assert.equal(vm.runInContext("findLesson('c-search').optional", context), true);
  assert.equal(vm.runInContext("byTrack('core').length", context), 6);
  assert.equal(vm.runInContext("nextFor('g-search').id", context), 'c-index-build');
  assert.equal(vm.runInContext("nextFor('c-search').id", context), 'c-index-build');
  const html = vm.runInContext("state.bookmarks=[]; current=findLesson('c-search'); lessonHeader()", context);
  assert.ok(html.includes('OPTIONAL RECAP'));
  assert.ok(!html.includes('01 / 06'));
  assert.ok(html.includes('href="#lesson/c-index-build"'));
  assert.ok(vm.runInContext("row(findLesson('c-search'))", context).includes('href="#lesson/c-search"'));
  const indexHeader = vm.runInContext("current=findLesson('c-index-build'); lessonHeader()", context);
  assert.ok(indexHeader.includes('01 / 06'));
});

test('chapter lists separate recaps and home continuation skips them', () => {
  const elements = {};
  context.document.querySelector = selector => elements[selector] ||= {innerHTML: ''};
  context.document.body = {classList: {remove() {}, toggle() {}}};
  vm.runInContext('state={completed:{},results:{},reviews:{},bookmarks:[],activity:[]}; listFilter="all"; renderList("track","core")', context);
  const html = elements['#main'].innerHTML;
  assert.ok(html.indexOf('data-id="c-search"') > html.indexOf('<h2>Optional recap</h2>'));
  assert.equal((html.match(/data-id="c-search"/g) || []).length, 1);
  vm.runInContext('for(const l of requiredLessons())state.completed[l.id]={xp:1}; delete state.completed["c-index-build"]; renderHome()', context);
  assert.ok(elements['#main'].innerHTML.includes('data-id="c-index-build"'));
  assert.ok(elements['#main'].innerHTML.includes('5 of 6 complete'));
  vm.runInContext('state.completed["c-index-build"]={xp:1}; renderHome()', context);
  assert.ok(elements['#main'].innerHTML.includes('6 of 6 complete'));
  assert.ok(!elements['#main'].innerHTML.includes('data-id="c-search"'));
  vm.runInContext('state.completed={}', context);
});

test('walkthroughs explain the approach before the example and implementation', () => {
  for (const lesson of catalog.lessons) {
    const html = render(lesson.id, 'walkthroughView');
    const production = html.indexOf('aria-label="Understand the task"');
    assert.ok(production >= 0, lesson.id);
    assert.ok(production < html.indexOf('class="walk-example"'), lesson.id);
    assert.ok(html.indexOf('class="walk-example"') < html.indexOf('class="walk-implementation"'), lesson.id);
    assert.ok(html.includes('What comes out'), lesson.id);
  }
  const html = render('c-index-build', 'walkthroughView');
  const overview = html.indexOf('aria-label="Solution overview"');
  assert.ok(overview > html.indexOf('aria-label="Understand the task"'));
  assert.ok(overview < html.indexOf('class="walk-example"'));
  assert.ok(html.indexOf('Full-text search means') < html.indexOf('Build once, query many times'));
  assert.ok(html.includes('PDF/OCR extraction is not implemented'));
  context.overviewFixture = structuredClone(catalog.lessons[0]);
  context.overviewFixture.overview = [{heading:'<script>bad()</script>',paragraphs:['<img src=x onerror=bad()>']}];
  const escaped = vm.runInContext('walkthroughOverview(overviewFixture)', context);
  assert.ok(escaped.includes('&lt;script&gt;'));
  assert.ok(escaped.includes('&lt;img'));
  assert.ok(!escaped.includes('<script>'));
  assert.ok(!escaped.includes('<img'));
});

test('production guidance remains available and escaped for every lesson', () => {
  for (const lesson of catalog.lessons) {
    const html = render(lesson.id, 'walkthroughView');
    const decision = lesson.implementation.decisions[0];
    assert.ok(html.includes('How would this change in a real service?'), lesson.id);
    assert.ok(html.includes(decision.question), lesson.id);
    assert.ok(html.includes(decision.branches[0].answer), lesson.id);
    assert.ok(html.includes(decision.branches[0].action), lesson.id);
    assert.ok(html.includes('The idea'), lesson.id);
    assert.ok(html.includes('How to put the approach into practice'), lesson.id);
    assert.ok(html.includes('When would you choose differently?'), lesson.id);
  }
  context.productionFixture = structuredClone(catalog.lessons[0]);
  context.productionFixture.strategy.use_case = '<img src=x onerror=bad()>';
  context.productionFixture.strategy.mechanism = '<script>bad()</script>';
  context.productionFixture.implementation.decisions[0].question = '<iframe>';
  context.productionFixture.implementation.decisions[0].branches[0].action = '<object>';
  const html = vm.runInContext('lessonOrientation(productionFixture) + productionContext(productionFixture)', context);
  assert.ok(html.includes('&lt;img'));
  assert.ok(html.includes('&lt;script&gt;'));
  assert.ok(html.includes('&lt;iframe&gt;'));
  assert.ok(html.includes('&lt;object&gt;'));
  assert.ok(!html.includes('<img'));
  assert.ok(!html.includes('<script>'));
  assert.ok(!html.includes('<iframe>'));
  assert.ok(!html.includes('<object>'));
});

test('every walkthrough introduces its handoff before details without author-facing headings', () => {
  assert.deepEqual(Object.keys(guides).sort(), catalog.lessons.map(l => l.id).sort());
  for (const lesson of catalog.lessons) {
    const html = render(lesson.id, 'walkthroughView');
    for (const field of ['input', 'output', 'scope', 'example']) assert.ok(lesson.orientation[field], lesson.id);
    assert.ok(html.indexOf('lesson-handoff') < html.indexOf('walk-example'), lesson.id);
    assert.ok(html.indexOf('walk-implementation') < html.indexOf('<details class="production-context">'), lesson.id);
    assert.doesNotMatch(html, /<(?:h[23]|summary)[^>]*>(?:Mechanism|Production direction|A worked example|Exercise boundary)</);
  }
  context.orientationFixture = structuredClone(catalog.lessons[0]);
  context.orientationFixture.orientation.input = '<img src=x onerror=bad()>';
  const html = vm.runInContext('lessonOrientation(orientationFixture)', context);
  assert.ok(html.includes('&lt;img'));
  assert.ok(!html.includes('<img'));
});

test('index walkthroughs separate writes, reads and the optional worker flow', () => {
  for (const id of ['c-index-build', 'c-index-query']) {
    const html = render(id, 'walkthroughView');
    assert.ok(html.indexOf('Build once, query many times') < html.indexOf('class="walk-example"'));
    assert.ok(html.includes('BUILD · after upload or edit'));
    assert.ok(html.includes('<svg class="flow-graph"'));
    assert.ok(html.includes('graph-decision'));
    assert.ok(html.includes('marker-end="url(#flow-arrow-main)"'));
    assert.ok(html.includes('SEARCH · per request'));
    assert.ok(html.includes('The search path performs no index writes.'));
    assert.ok(html.includes('calls the builder synchronously'));
    assert.ok(html.includes('<details class="flow-async">'));
    assert.ok(html.includes('makes search temporarily stale'));
  }
  context.flowFixture = structuredClone(catalog.flows['search-index']);
  context.flowFixture.graph.nodes[0].lines = ['<img>'];
  context.flowFixture.graph.edges[0].label = '<script>';
  context.flowFixture.graph.description = '<img>';
  const html = vm.runInContext('walkthroughFlow(flowFixture)', context);
  assert.ok(!html.includes('<img>'));
  assert.ok(!html.includes('<script>'));
  assert.ok(html.includes('&lt;img&gt;'));
});

test('complex system diagrams are shared by reference', () => {
  const expected = {
    'search-index': ['c-index-build', 'c-index-query'],
    'version-guard': ['q-version', 'c-events'],
    'bounded-fanout': ['a-fetch', 'q-cancel', 'a-federated', 's-latency'],
    'rag-context': ['c-chunking', 'q-context', 'c-context', 's-chat'],
    'durable-ingestion': ['s-ingestion'],
  };
  for (const [flow, ids] of Object.entries(expected)) {
    assert.ok(catalog.flows[flow], flow);
    for (const id of ids) {
      const lesson = catalog.lessons.find(item => item.id === id);
      assert.equal(lesson.flow_ref, flow, id);
      assert.ok(render(id, 'walkthroughView').includes(catalog.flows[flow].title), id);
    }
  }
  assert.ok(catalog.lessons.every(lesson => !Object.hasOwn(lesson, 'flow')));
  assert.equal(vm.runInContext('lessonFlow({flow:{title:"inline"}})', context), null);
});

test('shared diagrams use plain labels and model cancellation before work finishes', () => {
  const flowText = JSON.stringify(Object.values(catalog.flows)).toLowerCase();
  for (const phrase of ['payload', 'in this tenant', 'fan-out', 'exclude candidate']) {
    assert.ok(!flowText.includes(phrase), phrase);
  }
  const bounded = catalog.flows['bounded-fanout'];
  assert.ok(bounded.graph.description.includes('caller cancels or the deadline expires first'));
  assert.ok(bounded.graph.nodes.some(node => node.lines.includes('Caller +')));
  assert.ok(bounded.graph.nodes.some(node => node.lines.includes('Cancel + await')));
  assert.ok(bounded.graph.nodes.some(node => node.lines.includes('Partial, timeout')));
});

test('new walkthrough labels use the established reading scale', () => {
  assert.match(styles, /\.section-kicker\{[^}]*font-size:14px/);
  assert.match(styles, /\.design-decision summary span\{[^}]*font-size:14px/);
  assert.match(styles, /\.lesson-flow \.flow-pan-hint\{[^}]*font-size:14px/);
});

test('diagram connectors touch node outlines, including alternative flows', () => {
  for (const [name, flow] of Object.entries(catalog.flows)) {
    for (const graph of [flow.graph, flow.async?.graph].filter(Boolean)) {
      assert.deepEqual(disconnectedEnds(graph), [], `${name}: ${graph.title}`);
    }
  }
});

test('connectivity checks allow layout changes and detect detached endpoints', () => {
  const graph = {
    nodes: [{x:10,y:20,w:100,h:60,shape:'process'}, {x:200,y:20,w:100,h:60,shape:'decision'}],
    edges: [{path:'M110 50 H200'}],
  };
  assert.deepEqual(disconnectedEnds(graph), []);
  const moved = {nodes:graph.nodes.map(node=>({...node,y:node.y+100})),edges:[{path:'M110 150 H200'}]};
  assert.deepEqual(disconnectedEnds(moved), []);
  moved.edges[0].path='M110 150 H180';
  assert.equal(disconnectedEnds(moved).length, 1);
});

test('decision introductions precede the question and stay outside its disclosure', () => {
  for (const lesson of catalog.lessons) {
    context.decisionFixture = lesson;
    const html = vm.runInContext('productionDecision(decisionFixture)', context);
    assert.ok(html.indexOf('<p>') < html.indexOf('<details'), lesson.id);
    assert.ok(html.indexOf('</p>') < html.indexOf('<summary'), lesson.id);
  }
});


test('home follows curriculum order for fresh, returning and completed learners', () => {
  const elements = {};
  context.document.querySelector = selector => elements[selector] ||= {innerHTML: ''};
  context.document.body = {classList: {remove() {}, toggle() {}}};
  const primary = () => elements['#main'].innerHTML.match(/<div class="hero-actions">([\s\S]*?)<\/div>/)[1];
  vm.runInContext('state={completed:{},results:{},reviews:{},bookmarks:[],activity:[]}; renderHome()', context);
  assert.match(primary(), /data-id="q-sets"/);
  assert.match(primary(), /Start learning/);
  vm.runInContext('for(const l of byTrack("basics"))state.completed[l.id]={xp:1}; renderHome()', context);
  assert.match(primary(), /data-id="p-fastapi"/);
  assert.match(primary(), /Continue learning/);
  // Completing a later chapter must not cause an earlier missing API to be skipped.
  vm.runInContext('for(const l of byTrack("guided"))state.completed[l.id]={xp:1}; renderHome()', context);
  assert.match(primary(), /data-id="p-fastapi"/);
  vm.runInContext('for(const l of requiredLessons())state.completed[l.id]={xp:1}; renderHome()', context);
  assert.match(primary(), /Review from the start/);
  assert.match(primary(), /data-id="q-sets"/);
  vm.runInContext('state.completed={}', context);
});

test('continue traverses all chapters, skips recaps and completed activities', () => {
  const required = catalog.lessons.filter(l => !l.optional);
  vm.runInContext('state.completed={}', context);
  for (let i=0; i<required.length-1; i++) {
    context.currentId = required[i].id;
    const next = vm.runInContext('state.completed[currentId]={xp:1}; nextFor(currentId).id', context);
    assert.equal(next, required[i+1].id, `after ${required[i].id}`);
  }
  vm.runInContext('state.completed={"g-score":{xp:1}}', context);
  assert.equal(vm.runInContext('nextFor("q-score").id', context), 'q-tenants');
  vm.runInContext('for(const l of requiredLessons())state.completed[l.id]={xp:1}; delete state.completed["p-fastapi"]', context);
  assert.equal(vm.runInContext('nextFor("s-chat").id', context), 'p-fastapi');
  vm.runInContext('state.completed={}', context);
});

test('indexed examples separate shared document metadata from identified chunks', () => {
  for (const id of ['c-index-build', 'c-index-query', 'c-chunking']) {
    const html = render(id, 'walkthroughView');
    for (const name of ['documents', 'document_access', 'chunks', 'chunk_texts', 'term_chunks']) {
      assert.ok(html.includes(`<caption>${name}</caption>`), `${id}: ${name}`);
    }
    const chunkTable = html.match(/<caption>chunks<\/caption>([\s\S]*?)<\/table>/)[1];
    assert.ok(chunkTable.includes('chunk_id'));
    assert.ok(!chunkTable.includes('title'));
    assert.ok(!chunkTable.includes('public'));
    assert.ok(!html.includes('An empty chunk_id means'));
    assert.ok(html.includes('Thirty days'));
  }
});
