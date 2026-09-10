const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const root = path.join(__dirname, '..');
const catalog = JSON.parse(fs.readFileSync(path.join(root, 'app/catalog.json'), 'utf8'));
const source = fs.readFileSync(path.join(root, 'web/app.js'), 'utf8');
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

test('every problem is concise and contains no glossary, code or solution dump', () => {
  for (const lesson of catalog.lessons) {
    const html = render(lesson.id, 'scenarioView');
    assert.ok(html.includes('data-content="scenario"'), lesson.id);
    assert.ok(!/<dl|<pre|implementation-guide|decision-question/.test(html), lesson.id);
    assert.ok(!html.includes('Start with the situation'), lesson.id);
    assert.ok(lesson.scenario.prompt.length > 0);
    assert.ok(lesson.scenario.requirements.length >= 2);
    const words = [lesson.scenario.prompt, ...lesson.scenario.requirements, lesson.scenario.deliverable].join(' ').split(/\s+/);
    assert.ok(words.length < 150, `${lesson.id}: ${words.length} problem words`);
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
    assert.ok(html.includes('Design choices explained'), lesson.id);
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
