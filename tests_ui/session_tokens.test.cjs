const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(require('node:path').join(__dirname, '../web/app.js'), 'utf8');
const expired = {error:'Session token missing or expired. Reload the app.',code:'session_token_expired'};
const response = (status, data) => ({status,ok:status===200,json:async()=>data});
function tab(fetch) {
  const context = vm.createContext({document:{addEventListener(){}},window:{addEventListener(){}},fetch,AbortController,setTimeout,clearTimeout});
  vm.runInContext(source.slice(0,source.lastIndexOf('(async()=>{try{boot=')),context);
  vm.runInContext("token='old'; localCode='unsaved draft'; state={marker:'keep'}",context);
  return context;
}
test('older tabs recover after server token changes without replacing drafts or state', async()=>{
  const writes=[];
  const fetch = async(path,options)=>{
    if(path==='/api/bootstrap') return response(200,{token:'new',state:{marker:'replace'}});
    if(options.headers['X-Lab-Token']!=='new') return response(403,expired);
    writes.push(options.body);
    return response(200,{saved:true});
  };
  const tabs=[tab(fetch),tab(fetch)];
  await Promise.all(tabs.map(context=>vm.runInContext("api('/api/save',{text:localCode})",context)));
  assert.deepEqual(writes,[JSON.stringify({text:'unsaved draft'}),JSON.stringify({text:'unsaved draft'})]);
  for(const context of tabs){
    assert.equal(vm.runInContext('localCode',context),'unsaved draft');
    assert.equal(vm.runInContext('state.marker',context),'keep');
  }
});

for(const [name,status,data] of [
  ['origin rejection',403,{error:'Cross-origin requests are rejected.'}],
  ['login rejection',401,{error:'Sign in'}],
  ['server error',500,{error:'Failed'}],
]) test(`${name} does not retry a write`,async()=>{
  let calls=0;
  const context=tab(async()=>{calls++;return response(status,data);});
  await assert.rejects(vm.runInContext("api('/api/save',{text:localCode})",context));
  assert.equal(calls,1);
});

test('repeated token rejection stops after one retry',async()=>{
  let writes=0,refreshes=0;
  const context=tab(async(path)=>{
    if(path==='/api/bootstrap'){refreshes++;return response(200,{token:'new'});}
    writes++;return response(403,expired);
  });
  await assert.rejects(vm.runInContext("api('/api/save',{text:localCode})",context),/Session token/);
  assert.equal(writes,2);assert.equal(refreshes,1);
});

test('network failure does not replay a possibly executed write',async()=>{
  let calls=0;
  const context=tab(async()=>{calls++;throw new Error('connection lost');});
  await assert.rejects(vm.runInContext("api('/api/save',{text:localCode})",context),/unreachable/);
  assert.equal(calls,1);
});
