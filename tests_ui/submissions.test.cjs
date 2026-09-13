const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(require('node:path').join(__dirname, '../web/app.js'), 'utf8');

function harness(fetch) {
  const timers = new Map();
  const messages = [];
  const context = vm.createContext({
    document: {addEventListener() {}}, window: {addEventListener() {}},
    fetch, AbortController,
    setTimeout(fn) { const id = {}; timers.set(id, fn); return id; },
    clearTimeout(id) { timers.delete(id); },
  });
  vm.runInContext(source.slice(0, source.lastIndexOf('(async()=>{try{boot=')), context);
  context.messages = messages;
  vm.runInContext(`current={id:'q-tenants',kind:'quiz'}; selectedChoice=1;
    toast=message=>messages.push(message); renderLesson=()=>{};`, context);
  return {context, timers, messages};
}

for (const stage of ['connection', 'response body']) {
  test(`stalled quiz ${stage} releases the UI and allows retry`, async () => {
    let attempts = 0;
    const h = harness(async (path, options) => {
      attempts++;
      if (attempts > 1) return {ok:true, json:async()=>({state:{},result:{success:true}})};
      const stalled = () => new Promise((resolve, reject) => {
        const abort = () => reject(Object.assign(new Error('aborted'), {name:'AbortError'}));
        if (options.signal?.aborted) abort();
        else options.signal?.addEventListener('abort', abort);
      });
      return stage === 'connection' ? stalled() : {ok:true,json:stalled};
    });
    const pending = vm.runInContext('submitQuiz()', h.context);
    await Promise.resolve();
    assert.equal(vm.runInContext('busy', h.context), true);
    assert.ok(h.timers.size > 0, 'A stalled request must have a deadline');
    for (const expire of [...h.timers.values()]) expire();
    await pending;
    assert.equal(vm.runInContext('busy', h.context), false);
    assert.match(h.messages[0], /timed out/i);
    assert.equal(vm.runInContext('selectedChoice', h.context), 1);
    await vm.runInContext('submitQuiz()', h.context);
    assert.equal(vm.runInContext('quizResult.success', h.context), true);
    assert.equal(h.timers.size, 0);
  });
}
