'use strict';

// All grading is local. Python results come from pytest; interview cues are not AI scores.
const $ = (s, root=document) => root.querySelector(s);
const $$ = (s, root=document) => [...root.querySelectorAll(s)];
const escapeHTML = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const icons = {
 home:'M3 10 12 3l9 7M5 9v12h14V9M9 21v-8h6v8',
 code:'m8 5-7 7 7 7m8-14 7 7-7 7m-3-17-2 20',
 mic:'M8 5a4 4 0 0 1 8 0v7a4 4 0 0 1-8 0zm-3 6v1a7 7 0 0 0 14 0v-1M12 19v4m-4 0h8',
 review:'M3 11a9 9 0 1 1 2 7M3 3v8h8m1-5v6l4 2',
 settings:'M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8M12 2v3m0 14v3M2 12h3m14 0h3M5 5l2 2m10 10 2 2M5 19l2-2M17 7l2-2',
 spark:'m12 2 2.5 7.5L22 12l-7.5 2.5L12 22l-2.5-7.5L2 12l7.5-2.5z',
 search:'M17 10a7 7 0 1 1-14 0 7 7 0 0 1 14 0m-2 5 6 6',
 bolt:'m13 2-9 12h7l-1 8 10-13h-7z',
 layers:'m12 2 10 5-10 5L2 7zm-10 10 10 5 10-5M2 17l10 5 10-5',
 network:'M9 2h6v6H9zM2 16h6v6H2zm14 0h6v6h-6zM12 8v4m-7 4v-4h14v4',
 check:'m5 12 4 4L19 6',
 arrow:'M4 12h15m-6-6 6 6-6 6',
 back:'M20 12H5m6-6-6 6 6 6',
 close:'m6 6 12 12M6 18 18 6',
 info:'M12 16v-5m0-4v.1M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0',
 clock:'M12 7v5l3 2m7-2a10 10 0 1 1-20 0 10 10 0 0 1 20 0',
 play:'m8 4 13 8-13 8z',
 pause:'M8 4v16M16 4v16',
 book:'M3 3h7l2 2 2-2h7v17h-7l-2 2-2-2H3zM12 5v17',
 save:'M5 3h12l4 4v14H3V3zm2 0v6h10V3M7 21v-8h10v8',
 download:'M12 2v13m-5-5 5 5 5-5M4 17v5h16v-5',
 upload:'M12 16V3m-5 5 5-5 5 5M4 17v5h16v-5',
 bookmark:'M6 3h12v19l-6-4-6 4z',
 menu:'M3 5h18M3 12h18M3 19h18',
 terminal:'m4 6 6 6-6 6m9 0h7',
 flag:'M5 23V2l7 3 7-3v13l-7 3-7-3',
 focus:'M3 9V3h6m6 0h6v6M3 15v6h6m6 0h6v-6',
 help:'M9 8a3 3 0 0 1 6 0c0 2-3 2-3 5m0 3v.1M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0',
 chevron:'m9 5 7 7-7 7',
 leaf:'M20 3C8 1 0 11 7 18s16-1 13-15zM4 22 16 8',
};
const icon = name => `<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="${icons[name] || icons.spark}"/></svg>`;
const btn = (text, action, classes='primary', extra='') => `<button class="btn ${classes}" data-action="${action}" ${extra}>${text}</button>`;
const badge = (text, cls='') => `<span class="badge ${cls}">${text}</span>`;
const progress = percent => `<div class="progress"><i style="width:${Math.min(100,Math.max(0,percent))}%"></i></div>`;

let boot, catalog, state, token, current=null, phase=0, editor=null;
let localCode='', localAnswer='', selectedChoice=null, quizResult=null, feedback=null;
let hintCount=0, followupCount=0, rubricChecks=[], timer=null, timerInterval=null;
let savingTimeout=null, busy=false, focusMode=false, testFilter='failed', listFilter='all';
const lessons = () => catalog.lessons;
const findLesson = id => lessons().find(x=>x.id===id);
const trackFor = id => catalog.tracks.find(x=>x.id===id);
const complete = id => !!state.completed[id];
const xp = () => Object.values(state.completed).reduce((n,x)=>n+(x.xp||0),0);
const byTrack = id => lessons().filter(x=>x.track===id);
const queued = () => lessons().filter(l => (l.kind==='code' && state.results[l.id] && !state.results[l.id].success) || (l.kind==='quiz' && state.results[l.id] && !state.results[l.id].success) || (l.kind==='interview' && state.reviews[l.id]?.checks.includes('revise')));
const dayKey = date => new Date(date).toLocaleDateString('en-CA');

async function api(path, body) {
  const options = body===undefined ? {} : {method:'POST',headers:{'Content-Type':'application/json','X-Lab-Token':token},body:JSON.stringify(body)};
  let response;
  try {response = await fetch(path,options);} catch(e) {throw new Error('The local server is unreachable. Start python run.py again; your browser draft is preserved.');}
  let data;
  try {data=await response.json();} catch(e) {throw new Error(`Unexpected server response (${response.status}). Check the terminal.`);}
  if(!response.ok) throw new Error(data.error || `Request failed (${response.status}).`);
  return data;
}
function toast(message) {const box=$('#toast');box.textContent=message;box.classList.add('show');clearTimeout(toast.timeout);toast.timeout=setTimeout(()=>box.classList.remove('show'),4200);}
function inline(text) {return escapeHTML(text).replace(/`([^`]+)`/g,'<code>$1</code>').replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>');}
function markdown(text) {
  return String(text||'').split(/```[^\n]*\n([\s\S]*?)```/g).map((part,index)=>{
    if(index%2) return `<pre><code>${escapeHTML(part.trimEnd())}</code></pre>`;
    return part.replace(/^(#{1,3} [^\n]+)\n(?!\n)/gm, '$1\n\n').split(/\n\s*\n/).filter(x=>x.trim()).map(block=>{
      if(block.startsWith('### ')) return `<h3>${inline(block.slice(4))}</h3>`;
      if(block.startsWith('## ')) return `<h2>${inline(block.slice(3))}</h2>`;
      if(block.startsWith('# ')) return `<h2>${inline(block.slice(2))}</h2>`;
      return `<p>${inline(block)}</p>`;
    }).join('');
  }).join('');
}
function localBackup(key,text) {try {localStorage.setItem('judgelab:'+key,JSON.stringify({text,at:Date.now()}));}catch(e){toast('Browser backup is full; keep the server running or export your work.');}}
function readBackup(key) {try{return JSON.parse(localStorage.getItem('judgelab:'+key)||'null');}catch(e){return null;}}
function savedLabel(text,warning=false){const box=$('#save-state');if(box){box.innerHTML=icon(warning?'info':'check')+escapeHTML(text);box.style.color=warning?'#a66637':'';}}
function noteDraft(text) {
  if(!current)return;
  if(current.kind==='code') localCode=text; else localAnswer=text;
  const key=current.kind==='code'?current.workspace:current.id;
  localBackup(key,text);savedLabel('Saving…');
  clearTimeout(savingTimeout);
  const id=current.id;
  savingTimeout=setTimeout(()=>saveDraft(id,text),650);
}
async function saveDraft(id,text) {
  if(!id)return;
  try {
    const r=await api('/api/save',{id,text});
    const l=findLesson(id);
    if(l.kind==='code')state.drafts[l.workspace]={text,at:r.at};else state.answers[id]=text;
    if(current?.id===id)savedLabel('Saved on this computer');
  }catch(e){savedLabel('Browser backup only',true);toast(e.message);}
}
function flushDraft() {
  clearTimeout(savingTimeout);
  if(current && current.kind!=='quiz')return saveDraft(current.id,current.kind==='code'?localCode:localAnswer);
  return Promise.resolve();
}
function shell(section) {
  const title={home:'Learning path',code:'Code arena',interviews:'Interview studio',review:'Review queue',settings:'Your lab',track:'Learning path',lesson:'Practice'}[section]||'Learning path';
  const count=queued().length;
  $('#shell').innerHTML=`<aside class="sidebar">
    <button class="brand" data-action="navigate" data-route="home"><span class="brand-mark">J<span>↗</span></span><span><strong>JudgeLab</strong><small>Practice that clicks</small></span></button>
    <nav class="nav" aria-label="Main navigation">
      ${[['home','home','Learning path'],['code','code','Code arena'],['interviews','mic','Interview studio'],['review','review','Review queue'],['settings','settings','Your lab']].map(([id,i,name])=>`<button data-action="navigate" data-route="${id}" class="${section===id||(id==='home'&&['track','lesson'].includes(section))?'active':''}">${icon(i)}${name}${id==='review'&&count?`<span class="count">${count}</span>`:''}</button>`).join('')}
    </nav>
    <div class="sidebar-section">YOUR CHAPTERS</div>
    <div class="chapter-nav">${catalog.tracks.map((t,i)=>`<button data-action="navigate" data-route="track/${t.id}"><i class="chapter-dot"></i><span>${String(i+1).padStart(2,'0')} &nbsp; ${escapeHTML(t.title)}</span></button>`).join('')}</div>
    <div class="sidebar-bottom"><div class="local-indicator"><i></i>Local Python · no API keys</div><div class="profile"><div class="avatar">AL</div><div><strong>Alessio’s practice lab</strong><small>Independent interview preparation</small></div></div></div>
  </aside>
  <div class="main-wrap"><header class="topbar"><button class="mobile-menu" data-action="menu" aria-label="Toggle menu">${icon('menu')}</button><div class="breadcrumbs"><span>Your workspace</span>${icon('chevron')}<span>${title}</span></div><div class="top-stats"><span class="top-stat">${icon('bolt')}<span id="xp-total">${xp()} XP</span></span><span class="top-stat muted">${icon('check')}<span id="done-total">${Object.keys(state.completed).length} / ${lessons().length} activities</span></span></div></header><main id="main" tabindex="-1"></main></div>`;
  document.body.classList.remove('menu-open');
  document.body.classList.toggle('focus-mode',focusMode && section==='lesson');
}
function refreshTotals(){if($('#xp-total'))$('#xp-total').textContent=xp()+' XP';if($('#done-total'))$('#done-total').textContent=Object.keys(state.completed).length+' / '+lessons().length+' activities';}
function nextFor(id){const l=findLesson(id);const group=byTrack(l.track);const index=group.findIndex(x=>x.id===id);return group[index+1] || lessons().find(x=>!complete(x.id)&&x.id!==id) || group[0];}
function row(l,i=0) {
 const isDone=complete(l.id),method=l.kind==='code'?'Tested coding':l.kind==='quiz'?'Quick check':'Rubric review';
 return `<button class="lesson-row" data-action="lesson" data-id="${l.id}"><span class="step-number ${isDone?'done':''}">${isDone?icon('check'):String(i+1).padStart(2,'0')}</span><span class="lesson-row-text"><h3>${escapeHTML(l.title)}</h3><p>${escapeHTML(l.summary)}</p></span><span class="lesson-row-meta">${badge(isDone?(l.kind==='interview'?'Reviewed':'Completed'):method,isDone?'done':'outline')}<span class="subtle">${l.minutes} min</span>${icon('chevron')}</span></button>`;
}
function renderHome(){
 shell('home');
 const today=state.activity.filter(x=>dayKey(x.at)===dayKey(Date.now())).length;
 const next=lessons().find(x=>x.track==='guided'&&!complete(x.id))||lessons().find(x=>!complete(x.id))||lessons()[0];
 $('#main').innerHTML=`<section class="hero"><div class="hero-main"><div class="eyebrow">YOUR INTERVIEW CONFIDENCE, UNDER CONSTRUCTION</div><h1>Turn “I get it” into<br>“I built it.”</h1><p>Your Python practice, one clear challenge at a time. Write real code, run real tests, and learn exactly what to fix next.</p><div class="hero-actions">${btn(`${complete('g-score')?'Continue learning':'Start guided search'} ${icon('arrow')}`,'lesson','primary',`data-id="${next.id}"`)}${btn('Quick warm-up','lesson','ghost',`data-id="q-sets"`)}</div></div><aside class="today-card"><div class="eyebrow">SMALL STEPS, REAL PROGRESS</div><h3>Your daily rhythm</h3><div class="daily-ring" style="--p:${Math.min(today/3*100,100)}"><div class="ring-text"><strong>${today}<span class="subtle"> / 3</span></strong><small>practice attempts</small></div></div><p>${today>=3?'You showed up. That’s how fluency grows.':'One attempt is a start. Three makes a good practice session.'}</p></aside></section>
 <div class="section-head"><div><h2>Choose your next chapter</h2><p>Start guided. Build independently. Explain your decisions.</p></div>${badge('No LeetCode puzzles','outline')}</div>
 <div class="track-grid">${catalog.tracks.map((t,i)=>{const group=byTrack(t.id),done=group.filter(l=>complete(l.id)).length;return `<button class="track-card" data-action="navigate" data-route="track/${t.id}"><div class="track-card-top"><span class="track-icon ${t.color}">${icon(t.icon)}</span><span class="subtle">CHAPTER ${String(i+1).padStart(2,'0')}</span></div><h3>${escapeHTML(t.title)}</h3><p>${escapeHTML(t.subtitle)}</p><div class="track-footer"><span>${group.length} activities</span><span>${done} of ${group.length} complete</span></div>${progress(done/group.length*100)}</button>`;}).join('')}</div>
 <div class="info-strip">${icon('info')}<div><strong>A playground for backend engineering.</strong> Explore Python, search, ingestion and architecture through small exercises with real tests.</div></div>
 <div class="footer-note">${lessons().filter(x=>x.kind==='code').length} code missions · ${lessons().filter(x=>x.kind==='quiz').length} quick checks · ${lessons().filter(x=>x.kind==='interview').length} interview and architecture rehearsals. Completion badges record past achievements, not a guarantee that later edits still pass.</div>`;
}
function renderList(type,id){
 shell(type);
 let group,title,description;
 if(type==='track') {const t=trackFor(id);if(!t){renderHome();return;}group=byTrack(id);title=t.title;description=t.subtitle;}
 else if(type==='code'){group=lessons().filter(x=>x.kind==='code');title='Code it. Test it. Understand it.';description='16 coding missions using the supplied practice tests. The guided search stages share a file, so each builds on your previous work.';}
 else {group=lessons().filter(x=>x.kind==='interview');title='Make your experience easy to hear.';description='Practise specific answers and architecture trade-offs. Get transparent structure cues, then review a visible rubric. No fake AI quality score.';}
 if(listFilter==='unfinished')group=group.filter(l=>!complete(l.id));
 $('#main').innerHTML=`<div class="page-title"><div><div class="eyebrow">${type==='track'?'YOUR LEARNING PATH':type==='code'?'PYTHON 3.13+ · LOCAL PYTEST':'SPEAK ALOUD. CAPTURE THE ESSENTIALS.'}</div><h1>${escapeHTML(title)}</h1><p>${escapeHTML(description)}</p></div></div><div class="filter-bar"><button class="filter-pill ${listFilter==='all'?'active':''}" data-action="list-filter" data-value="all">All activities</button><button class="filter-pill ${listFilter==='unfinished'?'active':''}" data-action="list-filter" data-value="unfinished">Not completed yet</button></div><div class="lesson-list">${group.length?group.map((l,i)=>row(l,i)).join(''):'<div class="empty"><h2>This chapter is complete.</h2><p>Switch to all activities to repeat a lesson without hints.</p></div>'}</div><div class="footer-note">${type==='interviews'?'“Reviewed” means you completed a self-review, not that an interviewer would accept the answer.':'Suggested times are practice timeboxes, not claimed interview durations. You can open any activity; there are no artificial locks.'}</div>`;
}
function renderReview(){
 shell('review');const queue=queued(),bookmarks=lessons().filter(l=>state.bookmarks.includes(l.id));
 $('#main').innerHTML=`<div class="page-title"><div><div class="eyebrow">YOUR NEXT IMPROVEMENT IS ALREADY HERE</div><h1>A second pass makes it stick.</h1><p>Latest failed submissions, self-review points that need work, and anything you saved for later.</p></div></div><section class="review-section"><h2>Ready for another attempt <span class="subtle">(${queue.length})</span></h2>${queue.length?`<div class="lesson-list">${queue.map((l,i)=>row(l,i)).join('')}</div>`:`<div class="empty">${icon('leaf')}<h2>A clean slate.</h2><p>Failed checks will appear here automatically. No lost hearts, no penalty for trying.</p>${btn('Choose an activity','navigate','primary','data-route="home"')}</div>`}</section><section class="review-section"><h2>Saved for later <span class="subtle">(${bookmarks.length})</span></h2>${bookmarks.length?`<div class="lesson-list">${bookmarks.map((l,i)=>row(l,i)).join('')}</div>`:'<p class="subtle">Use the bookmark button on any activity to save it here.</p>'}</section>`;
}
function renderSettings(){
 shell('settings');$('#main').innerHTML=`<div class="page-title"><div><div class="eyebrow">LOCAL BY DESIGN</div><h1>Your lab. Your progress.</h1><p>No login, no tracking, no model API. Your code and answers are saved on this computer.</p></div></div><div class="settings-grid"><section class="card"><h3>Your Python engine</h3><table class="status-table"><tr><td>Interpreter</td><td>CPython ${escapeHTML(boot.python)}</td></tr><tr><td>Test runner</td><td>pytest ${escapeHTML(boot.pytest)}</td></tr><tr><td>Test process deadline</td><td>20 seconds</td></tr><tr><td>Progress file</td><td>.judgelab/progress.json</td></tr></table><p>Tests run in a fresh temporary workspace. The interpreter is the one that launched this app.</p></section><section class="card"><h3>Take your work with you</h3><p>Export drafts, answers and achievements to JSON. Importing replaces the current progress file; export first. Imported code needs to be tested again.</p>${btn(`${icon('download')} Export progress`,'export','primary')}${btn(`${icon('upload')} Import backup`,'import','secondary')}<input id="import-file" type="file" accept=".json,application/json" hidden></section><section class="card"><h3>What gets checked?</h3><p><strong>Coding:</strong> the supplied pytest assertions run against the submitted file. Failure messages and coaching cues refer to those actual cases.</p><p><strong>Quick checks:</strong> a fixed answer key explains the exercise contract.</p><p><strong>Interviews:</strong> word count and keyword cues, followed by your self-review. There is no semantic grading, truth verification or hiring prediction.</p></section><section class="card"><h3>Sources & boundaries</h3><p>The three practice packs live in <code>packs/</code>. Tests define the exercise contracts. Guidance, reference implementations and review rubrics are included for learning and experimentation.</p><p>The V1 and V2 ingestion/search contracts differ intentionally. Each activity names the pack it uses.</p>${btn('Read the safety note','safety','secondary')}</section></div><div class="info-strip warning">${icon('info')}<div><strong>Only run your own trusted code.</strong> A subprocess and timeout are not an operating-system sandbox. Code runs with your account’s permissions. The server binds only to localhost; do not expose or deploy it publicly.</div></div>`;
}
async function openLesson(id){
 const l=findLesson(id);if(!l){location.hash='home';return;}
 shell('lesson');$('#main').innerHTML='<div class="loading-inline"><span class="spinner"></span> Opening your activity…</div>';
 try {current=await api('/api/lesson/'+encodeURIComponent(id));}catch(e){$('#main').innerHTML=`<div class="empty"><h2>Couldn’t open the activity.</h2><p>${escapeHTML(e.message)}</p></div>`;return;}
 phase=0;hintCount=0;followupCount=0;selectedChoice=null;quizResult=null;rubricChecks=[];
 feedback=state.results[id]||null;
 const base=current.kind==='code'?state.drafts[current.workspace]?.text||current.starter:state.answers[id]||'';
 const backup=readBackup(current.kind==='code'?current.workspace:id);
 const serverAt=current.kind==='code'?Date.parse(state.drafts[current.workspace]?.at||0):0;
 const text=backup && backup.at>serverAt?backup.text:base;
 if(current.kind==='code')localCode=text;else localAnswer=text;
 if(current.kind==='interview'&&state.reviews[id])rubricChecks=[...state.reviews[id].checks];
 clearInterval(timerInterval);timer={remaining:current.minutes*60,running:false};timerInterval=setInterval(tickTimer,1000);
 renderLesson();
}
function lessonHeader(){
 const t=trackFor(current.track),group=byTrack(t.id),n=group.findIndex(x=>x.id===current.id)+1;
 return `<button class="back-link" data-action="navigate" data-route="track/${t.id}">${icon('back')} Back to chapter</button><div class="lesson-heading"><div><div class="eyebrow">${escapeHTML(t.title)} · ${String(n).padStart(2,'0')} / ${String(group.length).padStart(2,'0')}</div><h1>${escapeHTML(current.title)}</h1><p>${escapeHTML(current.summary)}</p></div><div class="lesson-meta">${badge('+'+current.xp+' XP','outline')}<button class="bookmark ${state.bookmarks.includes(current.id)?'on':''}" data-action="bookmark" aria-label="Bookmark this activity" title="Save for later">${icon('bookmark')}</button></div></div>`;
}
function phaseTabs(){
 const names=current.kind==='code'?['Understand','Write code','Test feedback']:['The prompt','Your answer','Review & refine'];
 return `<div class="phase-tabs" role="tablist" aria-label="Activity steps">${names.map((name,i)=>`<button role="tab" aria-selected="${phase===i}" class="phase-tab ${phase===i?'active':''}" data-action="phase" data-phase="${i}"><span class="phase-dot">${i+1}</span>${name}</button>`).join('')}</div>`;
}
function renderLesson(){
 if(!current)return;
 editor=null;
 document.body.classList.toggle('focus-mode',focusMode);
 $('#main').innerHTML=lessonHeader()+(current.kind==='quiz'?quizView():phaseTabs()+(current.kind==='code'?codeView():interviewView()));
 if(current.kind==='code'&&phase===1)mountEditor();
 if(current.kind==='interview'&&phase===1)mountAnswer();
 refreshTotals();
}
function timerButton(){return `<button class="timer ${timer?.running?'active':''}" data-action="timer" title="Optional practice timer; it does not submit or fail your work">${icon(timer?.running?'pause':'clock')}<span id="timer-label">${timerText()}</span></button>`;}
function timerText(){if(!timer)return 'Start timer';const m=Math.floor(timer.remaining/60),s=timer.remaining%60;return `${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}${timer.running?'':' · start/pause'}`;}
function tickTimer(){if(timer?.running&&timer.remaining>0){timer.remaining--;if(timer.remaining===0){timer.running=false;toast('Timebox finished. Keep working or submit when you’re ready.');}const el=$('#timer-label');if(el)el.textContent=timerText();}}
function lessonOverview(lesson) {
 if(!lesson.worked_example)return '';
 return `<div class="lesson-overview" aria-label="The task: compare query words with one document and return points"><div>${icon('search')}<strong>Query words</strong><span>What to look for</span></div><span aria-hidden="true">+</span><div>${icon('book')}<strong>One document</strong><span>Title and body</span></div><span aria-hidden="true">→</span><div>${icon('check')}<strong>A score</strong><span>Matching points</span></div></div>`;
}
function workedExample(lesson) {
 const example=lesson.worked_example;
 if(!example)return '';
 const total=example.rows.reduce((sum,row)=>sum+row.title+row.body,0);
 return `<figure class="scoring-example"><figcaption>Worked example: follow the matches</figcaption>
 <div class="query-example">${icon('search')}<div><span>Query · what someone types</span><strong>${escapeHTML(example.query)}</strong></div></div>
 <div class="document-example">${icon('book')}<div><span>One document</span><p><strong>Title</strong> ${escapeHTML(example.title)}</p><p><strong>Body</strong> ${escapeHTML(example.body)}</p></div></div>
 <div class="score-table-wrap"><table class="score-table"><caption>Points for each unique query term</caption><thead><tr><th scope="col">Term</th><th scope="col">Title<br>+3 if present</th><th scope="col">Body<br>+1 if present</th><th scope="col">Points</th></tr></thead><tbody>${example.rows.map(row=>`<tr><th scope="row">${escapeHTML(row.term)}</th><td>${row.title?'Match · +3':'Absent · 0'}</td><td>${row.body?'Match · +1':'Absent · 0'}</td><td>${row.title+row.body}</td></tr>`).join('')}</tbody><tfoot><tr><th scope="row" colspan="3">Return this total score</th><td>${total}</td></tr></tfoot></table></div>
 <p>Each row checks the title and body separately. Add the points across both rows.</p></figure>`;
}
function practiceCheck(lesson) {
 const check=lesson.practice_check;
 if(!check)return '';
 return `<section class="practice-check"><h2>Check your understanding</h2><p>${escapeHTML(check.question)}</p><details><summary>Reveal the explanation</summary><p>${escapeHTML(check.answer)}</p></details></section>`;
}
function codeView(){
 if(phase===0){
 const unmet=(current.depends||[]).filter(id=>!complete(id));
 return `${unmet.length?`<div class="info-strip warning" style="margin:0 0 20px">${icon('info')}<div>This stage uses earlier helpers in the same file. Recommended first: ${unmet.map(id=>`<button class="inline-link" data-action="lesson" data-id="${id}">${escapeHTML(findLesson(id).title)}</button>`).join(', ')}. You can still open it now.</div></div>`:''}<div class="brief-grid"><section class="card"><div class="card-title">${icon('book')} THE IDEA, BEFORE THE CODE</div><div class="markdown">${lessonOverview(current)}${markdown(current.concept)}${workedExample(current)}${markdown(current.after_example)}${practiceCheck(current)}</div></section><aside class="card"><div class="card-title">${icon('flag')} YOUR NEXT SMALL STEPS</div><ol class="steps">${current.steps.map((s,i)=>`<li><span>${i+1}</span><div>${inline(s)}</div></li>`).join('')}</ol>${badge(current.expected_tests?`${current.expected_tests} acceptance cases`:'Real pytest validation','outline')}<div class="source-note">SOURCE · ${escapeHTML(current.source)}<br>Keep the public signatures and original tests intact.</div></aside></div><div class="brief-actions"><span class="subtle">${current.minutes}-minute suggested timebox · learn at your own pace</span>${btn(`Open the workspace ${icon('arrow')}`,'phase','primary','data-phase="1"')}</div>`;
 }
 if(phase===2)return codeFeedback();
 return `<div class="timer-note">Optional timebox · syntax references are allowed during practice</div><div class="workspace"><aside class="task-panel"><h3>Your acceptance contract</h3><pre class="contract">${escapeHTML(current.contract)}</pre>${btn(`${icon('book')} Models & test source`,'references','secondary small')}<div class="hint-box"><h3>A nudge, not the answer</h3><div id="hints">${hintHTML()}</div>${btn(`${icon('help')} ${hintCount?'Another hint':'Show a hint'}`,'hint','ghost small',hintCount>=current.hints.length?'disabled':'')}</div><div class="source-note">${escapeHTML(current.file)}<br>${current.pack==='guided'?'All four guided stages share this file. Your other functions are preserved.':'A separate workspace for this original exercise.'}</div></aside><section class="editor-panel"><div class="editor-toolbar"><span class="file">${icon('code')} ${escapeHTML(current.file.split('/').pop())}</span><div class="editor-tools"><button class="tool-button" data-action="jump">Jump to target</button><button class="tool-button" data-action="focus" title="Toggle focus mode" aria-label="Toggle focus mode">${icon('focus')}</button><button class="tool-button" data-action="reset" title="Reset entire shared file" aria-label="Reset file">${icon('review')}</button></div></div><textarea id="code-source" aria-label="Python code editor"></textarea><div class="editor-status"><span>Python · 4 spaces · no AI completion</span><button class="tool-button" data-action="download-code">Export .py ${icon('download')}</button></div><div class="editor-bottom"><span id="save-state" class="save-state">${icon('check')} Saved on this computer</span><div class="layout-actions">${timerButton()}<span class="shortcut">⌘ / Ctrl ↵</span>${btn(`${icon('play')} Run tests`,'run','primary',busy?'disabled':'')}</div></div></section></div>${feedback?`<div class="info-strip">${icon('info')}<div>Your last submission: <strong>${feedback.passed||0} passed</strong>${feedback.failed?`, ${feedback.failed} failed`:''}. Edits are not validated until you run tests again. <button class="inline-link" data-action="phase" data-phase="2">Open last feedback</button></div></div>`:''}`;
}
function hintHTML(){return current.hints.slice(0,hintCount).map((h,i)=>`<div class="hint"><small>Hint ${i+1} of ${current.hints.length}</small>${escapeHTML(h)}</div>`).join('');}
function mountEditor(){
 const area=$('#code-source');area.value=localCode;
 editor=CodeMirror.fromTextArea(area,{mode:{name:'python',version:3},lineNumbers:true,indentUnit:4,tabSize:4,indentWithTabs:false,matchBrackets:true,styleActiveLine:true,lineWrapping:false,
  extraKeys:{'Tab':cm=>cm.somethingSelected()?cm.indentSelection('add'):cm.replaceSelection('    ','end'), 'Shift-Tab':'indentLess','Ctrl-Enter':()=>submitCode(),'Cmd-Enter':()=>submitCode(),'Ctrl-S':()=>saveDraft(current.id,editor.getValue()),'Cmd-S':()=>saveDraft(current.id,editor.getValue())}});
 editor.on('change',cm=>noteDraft(cm.getValue()));
 setTimeout(()=>{editor?.refresh();jumpToTarget(false);},40);
}
function jumpToTarget(focus=true){if(!editor)return;const target=current.targets[0],lines=editor.getValue().split('\n');let index=lines.findIndex(line=>new RegExp(`^(async )?def ${target}\\(`).test(line));if(index<0)index=0;editor.setCursor({line:index,ch:0});editor.scrollIntoView({line:index,ch:0},45);if(focus)editor.focus();}
function readableCase(nodeid){return nodeid.split('::').slice(1).join(' / ').replace(/^test_/,'').replace(/_/g,' ');}
function codeFeedback(){
 const r=feedback;
 if(!r || r.passed===undefined)return `<div class="empty">${icon('terminal')}<h2>Your feedback starts with a run.</h2><p>Submit your Python from the workspace. You’ll get the real passing and failing assertions—not a simulated score.</p>${btn('Open the workspace','phase','primary','data-phase="1"')}</div>`;
 const records=(r.records||[]).filter(x=>testFilter==='all'||x.outcome!=='passed');
 const all= r.records||[];const isStale=r.submitted_text!==undefined && r.submitted_text!==localCode;
 const title=r.success?'That’s a working implementation.':r.timed_out?'Let’s find what’s stuck.':r.collection_errors?.length?'Fix the file, then test again.':'Not there yet. Now you know where.';
 const count=`${r.passed} / ${r.collected||current.expected_tests||0} cases passed`;
 return `${isStale?`<div class="info-strip warning" style="margin:0 0 20px">${icon('info')}<div><strong>Your code has changed since this run.</strong> These are historical results. Run the current draft to validate it.</div></div>`:''}<div class="feedback-summary ${r.success?'':'retry'} completion-pop"><span class="feedback-symbol">${icon(r.success?'check':'review')}</span><div><h2>${title}</h2><p>${count} · ${r.elapsed ?? '?'}s · CPython ${escapeHTML(r.python||boot.python)}${r.success?' · '+current.xp+' XP on first completion':''}</p></div></div>
 <div class="result-grid"><div><div class="section-head" style="margin-top:0"><h2>What the tests actually said</h2><div class="filter-bar" style="margin:0"><button class="filter-pill ${testFilter==='failed'?'active':''}" data-action="test-filter" data-value="failed">Needs work</button><button class="filter-pill ${testFilter==='all'?'active':''}" data-action="test-filter" data-value="all">All ${all.length}</button></div></div>
 ${(r.collection_errors||[]).map(error=>`<div class="test-list" style="margin-bottom:15px"><details class="test-row fail" open><summary>${icon('info')}<span class="name">Test collection / Python error</span></summary><div class="test-details"><pre>${escapeHTML(error)}</pre></div></details></div>`).join('')}
 ${records.length?`<div class="test-list">${records.map((record,i)=>`<details class="test-row ${record.outcome==='passed'?'':'fail'}" ${i===0&&record.outcome!=='passed'?'open':''}><summary>${icon(record.outcome==='passed'?'check':'close')}<span class="name">${escapeHTML(readableCase(record.nodeid))}</span><small>${escapeHTML(record.outcome)}</small></summary><div class="test-details">${record.tip?`<p><strong>Coaching cue:</strong> ${escapeHTML(record.tip)}</p>`:''}${record.detail?`<pre>${escapeHTML(record.detail)}</pre>`:'<p>This acceptance case passed for the submitted code.</p>'}${record.stdout?`<pre>${escapeHTML(record.stdout)}</pre>`:''}</div></details>`).join('')}</div>`:r.success?`<div class="info-strip success" style="margin-top:0">${icon('check')}<div>No failing cases in this run. Switch to All to inspect every checked behaviour.</div></div>`:''}
 <details class="console"><summary>Open raw pytest console output</summary><pre>${escapeHTML(r.output||'No console output; the file could not be parsed.')}</pre></details></div>
 <aside class="card feedback-tips"><h3>${r.success?'Make the reasoning stick':'Your next correction'}</h3>${(r.tips||[]).map(t=>`<p>${escapeHTML(t)}</p>`).join('')}${btn(`${icon('back')} ${r.success?'Review your code':'Back to code'}`,'phase',r.success?'secondary':'primary','data-phase="1"')}${r.success?btn(`Continue ${icon('arrow')}`,'lesson','primary',`data-id="${nextFor(current.id).id}"`):''}${btn('Compare a reference approach','reveal','ghost')}${btn('Read the test source','references','ghost')}<div class="source-note">Hints are rule-based. The assertion output is from a real local pytest run. This is not an AI code review.</div></aside></div>
 <div class="info-strip">${icon('info')}<div>Results belong to the last <strong>submitted</strong> code. Editing or copying a reference does not validate it. Run again after changes.</div></div>`;
}
function quizView(){
 const r=quizResult;
 return `<div class="quiz-stage"><div class="quiz-card"><div class="question-type">ONE CONCEPT · ONE CLEAR CHECK</div><h2>${escapeHTML(current.question)}</h2><div class="quiz-options" role="group" aria-label="Answer choices">${current.choices.map((choice,i)=>`<button class="quiz-option ${selectedChoice===i?'selected':''} ${r&&r.correct===i?'correct':''} ${r&&!r.success&&r.choice===i?'incorrect':''}" data-action="quiz-choice" data-choice="${i}" aria-pressed="${selectedChoice===i}"><span class="keycap">${i+1}</span><span>${escapeHTML(choice)}</span>${r&&r.correct===i?icon('check'):''}</button>`).join('')}</div>${r?`<div class="quiz-answer ${r.success?'':'wrong'}"><strong>${r.success?'Exactly. That distinction matters.':'A useful mistake. Here’s the correction.'}</strong>${r.tip?escapeHTML(r.tip)+'<br>':''}${escapeHTML(r.explanation)}</div>`:''}<div class="quiz-bottom"><span class="subtle">Keys 1–4 to select · Enter to check</span>${r?.success?btn(`Next activity ${icon('arrow')}`,'lesson','primary',`data-id="${nextFor(current.id).id}"`):r?btn('Try it again','quiz-retry','primary'):btn(`Check answer ${icon('arrow')}`,'quiz-submit','primary',selectedChoice===null?'disabled':'')}</div></div><div class="source-note">${escapeHTML(current.source)}. This fixed answer key explains the practice contract.</div></div>`;
}
function interviewView(){
 if(phase===0)return `<div class="brief-grid"><section class="card"><div class="card-title">${icon('mic')} YOUR PRACTICE PROMPT</div><div class="markdown"><h2>${escapeHTML(current.question)}</h2><p>Say your answer aloud, then type a transcript or structured summary in the next step. No microphone recording or transcription is used.</p><p>You can use the timer as a rehearsal aid. It does not decide whether an answer is good.</p></div><div class="source-note">${escapeHTML(current.source)}</div></section><aside class="card"><div class="card-title">${icon('flag')} WHAT YOU’LL REVIEW</div><ol class="steps">${current.criteria.map((c,i)=>`<li><span>${i+1}</span><div>${escapeHTML(c)}</div></li>`).join('')}</ol></aside></div><div class="brief-actions"><span class="subtle">Specificity beats a memorized script.</span>${btn(`Start the rehearsal ${icon('arrow')}`,'phase','primary','data-phase="1"')}</div>`;
 if(phase===1)return `<div class="answer-layout"><section class="card"><div class="section-head" style="margin-top:0"><h3 style="margin:0">Your answer</h3>${timerButton()}</div><textarea id="interview-answer" class="answer-editor" placeholder="Write what you would actually say. For an experience question: situation → your task → your action → result. Only include events and details you can defend." aria-label="Your interview answer"></textarea><div class="answer-meta"><span id="answer-length">0 words</span><span id="save-state" class="save-state">${icon('check')} Saved on this computer</span></div>${btn(`Review this answer ${icon('arrow')}`,'interview-submit','primary')}</section><aside class="card"><div class="card-title">${icon('mic')} ${current.track==='architecture'?'ARCHITECTURE REHEARSAL':'ENGINEER-TO-ENGINEER'}</div><p style="font-size:14px">${escapeHTML(current.question)}</p><p class="subtle">The automatic checks look for structure cues only. They cannot verify your experience or judge semantic quality.</p><div id="followups">${followupHTML()}</div>${btn('Give me a follow-up','followup','secondary small',followupCount>=current.followups.length?'disabled':'')}<div class="source-note">Follow-ups help you explore decisions, trade-offs and alternatives.</div></aside></div>`;
 return interviewFeedbackView();
}
function followupHTML(){return current.followups.slice(0,followupCount).map((q,i)=>`<div class="followup"><small>Follow-up ${i+1}</small>${escapeHTML(q)}</div>`).join('');}
function mountAnswer(){const area=$('#interview-answer');area.value=localAnswer;updateAnswerLength();area.addEventListener('input',()=>{noteDraft(area.value);updateAnswerLength();});}
function updateAnswerLength(){const count=(localAnswer.trim().match(/\S+/g)||[]).length;if($('#answer-length'))$('#answer-length').textContent=`${count} words · ~${Math.round(count/135*60)}s at 135 words/min` ;}
function interviewFeedbackView(){
 const r=feedback;
 if(!r||r.word_count===undefined)return `<div class="empty">${icon('mic')}<h2>Start with your own answer.</h2><p>Type at least 25 words, get structure cues, then mark each rubric point honestly.</p>${btn('Write an answer','phase','primary','data-phase="1"')}</div>`;
 return `<div class="info-strip warning" style="margin:0 0 22px">${icon('info')}<div><strong>Structure cues, not an AI grade.</strong> ${escapeHTML(r.note)} Speaking time below is estimated from word count, not a recording.</div></div><div class="result-grid"><section><div class="section-head" style="margin-top:0"><h2>Review your own answer</h2>${badge(`${r.word_count} words · ~${r.estimated_seconds}s`,'outline')}</div><div class="rubric-list">${current.criteria.map((criterion,i)=>`<div class="rubric-item"><p>${i+1}. ${escapeHTML(criterion)}</p><button class="rubric-choice ${rubricChecks[i]==='yes'?'selected':''}" data-action="rubric" data-index="${i}" data-value="yes">${icon('check')} Covered</button><button class="rubric-choice revise ${rubricChecks[i]==='revise'?'selected':''}" data-action="rubric" data-index="${i}" data-value="revise">${icon('review')} Needs another pass</button></div>`).join('')}</div><div class="brief-actions"><span class="subtle">Review every point. “Needs work” is a valid answer.</span>${btn('Save my self-review','save-review','primary',!r.can_review?'disabled':'')}</div>${!r.can_review?'<p class="subtle">Add at least 25 words to your answer before saving a review.</p>':''}</section><aside class="card"><h3>What the text mentions</h3>${r.cues.map(c=>`<div class="cue-row"><div>${escapeHTML(c.label)}<small>${c.matches.length?'Matched: '+escapeHTML(c.matches.join(', ')):'No matching cue words detected.'}</small></div><span class="${c.found?'cue-found':'cue-missing'}">${c.found?'Mentioned':'Check manually'}</span></div>`).join('')}<div class="source-note">A keyword can appear in a weak answer or be absent from a strong one. These are prompts for your review, not a quality score.</div><div class="small-stack" style="margin-top:18px">${btn(`${icon('back')} Refine my answer`,'phase','secondary','data-phase="1"')}${btn('Compare preparation notes','reveal','ghost')}</div></aside></div>`;
}
async function submitCode(){
 if(busy||current?.kind!=='code')return;
 if(!state.consent){showSafety(true);return;}
 if(editor)localCode=editor.getValue();
 busy=true;clearTimeout(savingTimeout);if(editor)editor.setOption('readOnly',true);
 const button=$('[data-action="run"]');if(button){button.disabled=true;button.innerHTML='<span class="spinner"></span> Running real tests…';}
 const lessonId=current.id,text=localCode,had=complete(lessonId);
 try{const data=await api('/api/run',{id:lessonId,text});state=data.state;feedback=data.result;phase=2;testFilter=feedback.success?'all':'failed';renderLesson();if(data.result.success&&!had)toast(`+${current.xp} XP · All selected tests passed.`);}
 catch(e){toast(e.message);if(button){button.disabled=false;button.innerHTML=icon('play')+' Run tests';}if(editor)editor.setOption('readOnly',false);}
 finally{busy=false;}
}
async function submitQuiz(){
 if(busy||selectedChoice===null)return;
 busy=true;try{const data=await api('/api/quiz',{id:current.id,choice:selectedChoice});state=data.state;quizResult=data.result;renderLesson();}catch(e){toast(e.message);}finally{busy=false;}
}
async function submitInterview(){
 if(busy)return;busy=true;clearTimeout(savingTimeout);
 try{const data=await api('/api/interview',{id:current.id,text:localAnswer});state=data.state;feedback=data.result;phase=2;renderLesson();}catch(e){toast(e.message);}finally{busy=false;}
}
function modal(title,subtitle,body,footer='',narrow=false){
 $('#modal-root').innerHTML=`<div class="modal-backdrop"><section class="modal ${narrow?'narrow':''}" role="dialog" aria-modal="true" aria-labelledby="modal-title"><header class="modal-head"><div><h2 id="modal-title">${escapeHTML(title)}</h2><p>${escapeHTML(subtitle)}</p></div><button data-action="close-modal" aria-label="Close dialog">${icon('close')}</button></header><div class="modal-body">${body}</div>${footer?`<footer class="modal-footer">${footer}</footer>`:''}</section></div>`;
 document.body.style.overflow='hidden';setTimeout(()=>$('#modal-root button')?.focus(),0);
}
function closeModal(){ $('#modal-root').innerHTML='';document.body.style.overflow=''; }
function showSafety(runAfter=false){
 modal('Your code runs on your computer.','A real interpreter, not a pretend test result.',`<p>When you press Run tests, JudgeLab copies the exercise into a fresh temporary folder and executes it using the Python interpreter that started this app.</p><div class="info-strip warning">${icon('info')}<div><strong>This is not a security sandbox.</strong> Python runs with your account’s permissions. Only run your own trusted code. Do not paste unknown code or expose the app on a public/shared network.</div></div><p>The app binds only to 127.0.0.1, checks request origin/session tokens, limits output, and stops long-running test processes. These safeguards do not make arbitrary code safe.</p><p>After setup, no internet service, API key, account or model call is needed. Interview answers receive transparent structure cues and a self-review rubric, not semantic AI grading.</p>`,btn('Not now','close-modal','secondary')+btn('I understand · continue','consent','primary',`data-run="${runAfter}"`),true);
}
function showReferences(){
 const refs=current.references||[];
 modal('The contract is inspectable.','Original supporting files and tests from this exercise’s pack.',`<label for="reference-select" class="subtle">Choose a file</label><br><select id="reference-select">${refs.map((ref,i)=>`<option value="${i}">${escapeHTML(ref.name)}</option>`).join('')}</select><div id="reference-content"></div>`,btn('Back to my code','close-modal','secondary'));
 const select=$('#reference-select');select.addEventListener('change',()=>paintReference(refs[Number(select.value)]));paintReference(refs[0]);
}
function paintReference(ref){if(!ref)return;$('#reference-content').innerHTML=ref.name.endsWith('.py')?`<pre class="modal-code">${escapeHTML(ref.text)}</pre>`:`<div class="raw-doc">${escapeHTML(ref.text)}</div>`;}
async function reveal(){
 try{const r=await api('/api/reveal',{id:current.id});if(!state.revealed.includes(current.id))state.revealed.push(current.id);
  modal(current.kind==='code'?'One way to solve it':'Preparation notes, not a script',r.label,
   `${r.explanation?`<p>${escapeHTML(r.explanation)}</p>`:''}${current.kind==='code'?`<pre id="reference-answer" class="modal-code">${escapeHTML(r.text)}</pre>`:`<div class="raw-doc">${escapeHTML(r.text)}</div>`}<div class="info-strip">${icon('info')}<div>${current.kind==='code'?'Compare your reasoning first. Nothing has been inserted into your code. A reference may include stronger cleanup than the original test coverage.':'Use only details you can support. Missing events, exact mechanics or future plans must come from your real experience.'}</div></div>`,(current.kind==='code'?btn('Copy reference','copy-reference','secondary'):'')+btn('Keep practising','close-modal','primary'));
 }catch(e){toast(e.message);}
}
function download(name,text,type='application/json') {const url=URL.createObjectURL(new Blob([text],{type}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
async function importBackup(file){
 if(!file)return;
 try{const imported=JSON.parse(await file.text());if(!confirm('Replace the progress on this computer with this backup? Export your current progress first if needed.'))return;const result=await api('/api/import',{state:imported});state=result.state;
  for(let i=localStorage.length-1;i>=0;i--){const k=localStorage.key(i);if(k?.startsWith('judgelab:'))localStorage.removeItem(k);}
  toast(result.message);current=null;renderSettings();
 }catch(e){toast('Import failed: '+e.message);}
}
async function navigate(route){if(busy){toast('Let the current test run finish before leaving.');return;}await flushDraft();location.hash=route;}
async function handleRoute(){
 if(busy){return;}
 await flushDraft();current=null;editor=null;clearInterval(timerInterval);focusMode=false;
 const route=decodeURIComponent(location.hash.replace(/^#\/?/,''))||'home';const [type,id]=route.split('/');
 if(type==='lesson')await openLesson(id);else if(type==='track')renderList('track',id);else if(type==='code'||type==='interviews')renderList(type);else if(type==='review')renderReview();else if(type==='settings')renderSettings();else renderHome();
 window.scrollTo(0,0);
}
// One delegated handler keeps the interface free of inline scripts and unsafe HTML events.
document.addEventListener('click',async event=>{
 const target=event.target.closest('[data-action]');if(!target||target.disabled)return;
 const a=target.dataset.action;
 if(busy && !['close-modal','menu'].includes(a)){toast('Tests are running. One moment.');return;}
 try{
  switch(a){
   case 'navigate':listFilter='all';await navigate(target.dataset.route);break;
   case 'lesson':await navigate('lesson/'+target.dataset.id);break;
   case 'menu':document.body.classList.toggle('menu-open');break;
   case 'phase':await flushDraft();phase=Number(target.dataset.phase);renderLesson();break;
   case 'list-filter':listFilter=target.dataset.value;{const [type,id]=location.hash.replace('#','').split('/');renderList(type,id);}break;
   case 'test-filter':testFilter=target.dataset.value;renderLesson();break;
   case 'run':await submitCode();break;
   case 'jump':jumpToTarget();break;
   case 'focus':focusMode=!focusMode;document.body.classList.toggle('focus-mode',focusMode);setTimeout(()=>editor?.refresh(),40);break;
   case 'hint':hintCount=Math.min(hintCount+1,current.hints.length);$('#hints').innerHTML=hintHTML();target.disabled=hintCount>=current.hints.length;target.innerHTML=icon('help')+' Another hint';break;
   case 'references':showReferences();break;
   case 'reveal':await reveal();break;
   case 'copy-reference':{const text=$('#reference-answer').textContent;try{await navigator.clipboard.writeText(text);toast('Reference copied. Compare it with your code before running again.');}catch(e){toast('Clipboard unavailable. Select the reference text and copy it manually.');}break;}
   case 'download-code':download(current.file.split('/').pop(),localCode,'text/x-python');break;
   case 'reset':if(confirm('Reset the ENTIRE shared file to its starter? This also removes your other functions in that file. Export your .py first to keep a copy.')){localCode=current.starter;localBackup(current.workspace,localCode);editor?.setValue(localCode);await saveDraft(current.id,localCode);toast('File reset. Past completion badges remain historical achievements.');}break;
   case 'timer':timer.running=!timer.running;renderLesson();break;
   case 'quiz-choice':if(!quizResult){selectedChoice=Number(target.dataset.choice);renderLesson();}break;
   case 'quiz-submit':await submitQuiz();break;
   case 'quiz-retry':quizResult=null;selectedChoice=null;renderLesson();break;
   case 'interview-submit':await submitInterview();break;
   case 'rubric':rubricChecks[Number(target.dataset.index)]=target.dataset.value;renderLesson();break;
   case 'save-review':{if(current.criteria.some((_,i)=>!rubricChecks[i])){toast('Review every point as covered or needs another pass.');break;}const r=await api('/api/review',{id:current.id,checks:rubricChecks});state=r.state;refreshTotals();toast(`Rehearsal reviewed. ${r.needs_work?r.needs_work+' point(s) saved for another pass.':'Keep your answer natural.'}`);modal('A useful rehearsal.','Reviewed does not mean objectively correct.',`<p>You marked ${current.criteria.length-r.needs_work} rubric points covered and ${r.needs_work} for revision. Points needing work appear in your review queue.</p><p>Next, practise a follow-up without reading your written answer.</p>`,btn('Refine this answer','review-back','secondary')+btn('Next activity','review-next','primary'),true);break;}
   case 'review-back':closeModal();phase=1;renderLesson();break;
   case 'review-next':closeModal();await navigate('lesson/'+nextFor(current.id).id);break;
   case 'followup':followupCount=Math.min(followupCount+1,current.followups.length);$('#followups').innerHTML=followupHTML();target.disabled=followupCount>=current.followups.length;break;
   case 'bookmark':{const r=await api('/api/bookmark',{id:current.id});state.bookmarks=r.bookmarks;target.classList.toggle('on',r.bookmarks.includes(current.id));toast(r.bookmarks.includes(current.id)?'Saved to your review queue.':'Bookmark removed.');break;}
   case 'close-modal':closeModal();break;
   case 'safety':showSafety(false);break;
   case 'consent':await api('/api/consent',{accepted:true});state.consent=true;closeModal();if(target.dataset.run==='true')await submitCode();break;
   case 'export':await flushDraft();download('judgelab-progress.json',JSON.stringify(await api('/api/export'),null,2));toast('Progress exported. Keep it somewhere safe.');break;
   case 'import':$('#import-file').click();break;
  }
 }catch(e){toast(e.message);}
});
document.addEventListener('change',event=>{if(event.target.id==='import-file')importBackup(event.target.files[0]);});
document.addEventListener('keydown',event=>{
 if(event.key==='Escape'){if($('#modal-root').firstChild)closeModal();document.body.classList.remove('menu-open');}
 if($('#modal-root').firstChild&&event.key==='Tab'){
  const focusable=$$('#modal-root button, #modal-root select, #modal-root textarea, #modal-root a[href]').filter(x=>!x.disabled);
  if(focusable.length){const first=focusable[0],last=focusable[focusable.length-1];if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus();}else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus();}}
 }
 if(current?.kind==='quiz'&&!$('#modal-root').firstChild&&!['INPUT','TEXTAREA'].includes(document.activeElement.tagName)){
  if(/^[1-4]$/.test(event.key)&&!quizResult){selectedChoice=Number(event.key)-1;renderLesson();}
  if(event.key==='Enter'&&selectedChoice!==null&&!quizResult){event.preventDefault();submitQuiz();}
 }
});
window.addEventListener('hashchange',handleRoute);
window.addEventListener('beforeunload',()=>{if(current&&current.kind!=='quiz')localBackup(current.kind==='code'?current.workspace:current.id,current.kind==='code'?localCode:localAnswer);});
(async()=>{try{boot=await api('/api/bootstrap');catalog=boot.catalog;state=boot.state;token=boot.token;await handleRoute();}catch(e){$('#shell').innerHTML=`<div class="boot"><h1>The lab needs its local server.</h1><p>${escapeHTML(e.message)}</p><pre>python run.py</pre></div>`;}})();
