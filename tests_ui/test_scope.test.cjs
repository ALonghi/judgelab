const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('web/app.js','utf8');
const context = vm.createContext({document:{addEventListener(){}},window:{addEventListener(){}}});
vm.runInContext(source.slice(0,source.lastIndexOf('(async()=>{try{boot=')),context);
context.fixtureCatalog=JSON.parse(fs.readFileSync('app/catalog.json','utf8'));
vm.runInContext('catalog=fixtureCatalog',context);
function render(id){context.fixtureId=id;return vm.runInContext('testScope(findLesson(fixtureId))',context);}
test('scoring names its limited scope and links full search validation',()=>{
 const html=render('g-score');
 assert.match(html,/Only.*score_document/);
 assert.match(html,/9 acceptance tests/);
 assert.match(html,/data-id="g-search"/);
 assert.match(html,/search_documents/);
 assert.match(html,/does not validate the other functions/);
});
test('shared warmups expose the other activity without implying it passed',()=>{
 const html=render('c-latest');
 assert.match(html,/Only.*latest_documents/);
 assert.match(html,/data-id="c-counts"/);
});
test('full guided search identifies integration scope',()=>{
 const html=render('g-search');
 assert.match(html,/44 acceptance tests/);
 assert.match(html,/score_document/);
 assert.match(html,/search_documents/);
 assert.ok(!html.includes('Only'));
});
