const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('web/app.js', 'utf8');
const context = vm.createContext({document:{addEventListener(){}},window:{addEventListener(){}},CodeMirror:{Pos:(line,ch)=>({line,ch}),hintWords:{python:['return']}}});
vm.runInContext(source.slice(0,source.lastIndexOf('(async()=>{try{boot=')),context);
context.refs=[{name:'practice/models.py',text:fs.readFileSync('packs/v2/practice/models.py','utf8')},{name:'tests/test_example.py',text:'class Secret:\n    answer: str'}];
vm.runInContext('current={references:refs}',context);
function complete(line,type=null){context.cm={getCursor:()=>({line:0,ch:line.length}),getLine:()=>line,getTokenAt:()=>({type}),getValue:()=>line};return vm.runInContext('exerciseCompletions(cm)',context);}
test('field completion preserves the receiver and provides model/type details',()=>{
 const result=complete('doc.tenant');
 assert.equal(result.from.ch,4);
 assert.equal(result.list[0].text,'tenant_id');
 assert.match(result.list[0].displayText,/str/);
 assert.ok(!complete('doc.').list.some(item=>item.text==='answer'));
});
test('comments and strings have no suggestions; model panel is accessible',()=>{
 assert.equal(complete('# doc.', 'comment'),null);
 assert.equal(complete('"doc.', 'string'),null);
 const html=vm.runInContext('modelReference(current)',context);
 assert.match(html,/id="model-reference"/);
 assert.match(html,/tabindex="0"/);
 assert.ok(!html.includes('Secret'));
});
test('changing packs clears previous model fields',()=>{
 vm.runInContext("current={references:[{name:'models.py',text:'class Other:\\n    unique_field: int'}]}",context);
 const names=complete('item.').list.map(item=>item.text);
 assert.ok(names.includes('unique_field'));
 assert.ok(!names.includes('tenant_id'));
});
test('models declared in the starter supply fields without including exercise implementations',()=>{
 context.starter=fs.readFileSync('packs/v1/practice/exercise1_fetch_documents.py','utf8');
 vm.runInContext("current={references:[],starter,file:'practice/exercise1_fetch_documents.py'}",context);
 assert.ok(complete('doc.').list.some(item=>item.text==='id'));
 const html=vm.runInContext('modelReference(current)',context);
 assert.match(html,/Document/);
 assert.ok(!html.includes('NotImplementedError'));
});

test('Python string methods complete partial and fully typed names',()=>{
 assert.ok(complete('text.sp').list.some(item=>item.text==='split'));
 assert.ok(complete('text.split').list.some(item=>item.text==='split'));
 assert.equal(complete('text.sp').from.ch,5);
});
test('a method local annotation is not exposed as a model field',()=>{
 vm.runInContext("current={starter:'class Example:\\n    name: str\\n    def method(self):\\n        secret: str',references:[]}",context);
 assert.ok(!complete('obj.').list.some(item=>item.text==='secret'));
});
