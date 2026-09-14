'use strict';

// All grading is local. Python results come from pytest; discussion cues are not AI scores.
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
const btn = (text, action, classes='primary', extra='') => {
  const destination = action==='lesson' ? 'lesson/'+extra.match(/data-id="([^"]+)"/)[1]
    : action==='navigate' ? extra.match(/data-route="([^"]+)"/)[1] : null;
  return destination
    ? `<a class="btn ${classes}" href="#${destination}" data-action="${action}" ${extra}>${text}</a>`
    : `<button class="btn ${classes}" data-action="${action}" ${extra}>${text}</button>`;
};
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
const xp = () => lessons().reduce((n,l)=>n+(state.completed[l.id]?.xp||0),0);
const requiredLessons = () => lessons().filter(x=>!x.optional);
const byTrack = id => requiredLessons().filter(x=>x.track===id);
const queued = () => lessons().filter(l => (l.kind==='code' && state.results[l.id] && !state.results[l.id].success) || (l.kind==='quiz' && state.results[l.id] && !state.results[l.id].success) || (l.kind==='discussion' && state.reviews[l.id]?.checks.includes('revise')));
const dayKey = date => new Date(date).toLocaleDateString('en-CA');

async function api(path, body, retrySession=true) {
  const options = body===undefined ? {} : {method:'POST',headers:{'Content-Type':'application/json','X-Lab-Token':token},body:JSON.stringify(body)};
  const controller = new AbortController();
  options.signal = controller.signal;
  // Include response-body reading; a connection can stall after headers arrive.
  // Python runs have a 20-second server deadline, plus startup/network allowance.
  const deadline = setTimeout(()=>controller.abort(), path==='/api/run'?45000:15000);
  try {
    let response;
    try {response = await fetch(path,options);} catch(e) {
      if(controller.signal.aborted) throw e;
      throw new Error(boot?.hosted?'The private instance is unreachable. Wait a moment and retry; your browser draft is preserved.':'The local server is unreachable. Start python run.py again; your browser draft is preserved.');
    }
    let data;
    try {data=await response.json();} catch(e) {
      if(controller.signal.aborted) throw e;
      throw new Error(`Unexpected server response (${response.status}). Reload the page and try again.`);
    }
    if(body!==undefined && retrySession && response.status===403 && data.code==='session_token_expired') {
      // The guard rejected this request before executing it, so one retry is safe.
      // Refresh only the token: replacing state would discard this tab's work.
      clearTimeout(deadline);
      const session = await api('/api/bootstrap');
      if(typeof session.token!=='string' || !session.token) throw new Error('Could not refresh the session. Reload the app.');
      token = session.token;
      return await api(path, JSON.parse(options.body), false);
    }
    if(!response.ok) throw new Error(data.error || `Request failed (${response.status}).`);
    return data;
  } catch(e) {
    if(controller.signal.aborted) throw new Error('The request timed out. Your submission may have reached the server. Try again, or reload if it keeps happening.');
    throw e;
  } finally {
    clearTimeout(deadline);
  }
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
    if(current?.id===id)savedLabel(boot.hosted?'Saved to your private instance':'Saved on this computer');
  }catch(e){savedLabel('Browser backup only',true);toast(e.message);}
}
function flushDraft() {
  clearTimeout(savingTimeout);
  if(current && current.kind!=='quiz')return saveDraft(current.id,current.kind==='code'?localCode:localAnswer);
  return Promise.resolve();
}
function shell(section) {
  const title={home:'Learning path',code:'Code arena',review:'Review queue',settings:'Your lab',track:'Learning path',lesson:'Practice'}[section]||'Learning path';
  const count=queued().length;
  $('#shell').innerHTML=`<aside class="sidebar">
    <a class="brand" data-action="navigate" data-route="home" href="#home"><span class="brand-mark">J<span>↗</span></span><span><strong>JudgeLab</strong><small>Practice that clicks</small></span></a>
    <nav class="nav" aria-label="Main navigation">
      ${[['home','home','Learning path'],['code','code','Code arena'],['review','review','Review queue'],['settings','settings','Your lab']].map(([id,i,name])=>`<a data-action="navigate" data-route="${id}" class="${section===id||(id==='home'&&['track','lesson'].includes(section))?'active':''}" href="#${id}">${icon(i)}${name}${id==='review'&&count?`<span class="count">${count}</span>`:''}</a>`).join('')}
    </nav>
    <div class="sidebar-section">YOUR CHAPTERS</div>
    <div class="chapter-nav">${catalog.tracks.map((t,i)=>`<a data-action="navigate" data-route="track/${t.id}" href="#track/${t.id}"><i class="chapter-dot"></i><span>${String(i+1).padStart(2,'0')} &nbsp; ${escapeHTML(t.title)}</span></a>`).join('')}</div>
    <div class="sidebar-bottom"><div class="local-indicator"><i></i>${boot.hosted?'Private hosted Python':'Local Python'} · no model API</div><div class="profile"><div class="avatar">AL</div><div><strong>Alessio’s practice lab</strong><small>Backend engineering playground</small></div></div></div>
  </aside>
  <div class="main-wrap"><header class="topbar"><button class="mobile-menu" data-action="menu" aria-label="Toggle menu">${icon('menu')}</button><div class="breadcrumbs"><span>Your workspace</span>${icon('chevron')}<span>${title}</span></div><div class="top-stats"><span class="top-stat">${icon('bolt')}<span id="xp-total">${xp()} XP</span></span><span class="top-stat muted">${icon('check')}<span id="done-total">${lessons().filter(l=>complete(l.id)).length} / ${lessons().length} activities</span></span></div></header><main id="main" tabindex="-1"></main></div>`;
  document.body.classList.remove('menu-open');
  document.body.classList.toggle('focus-mode',focusMode && section==='lesson');
}
function refreshTotals(){if($('#xp-total'))$('#xp-total').textContent=xp()+' XP';if($('#done-total'))$('#done-total').textContent=lessons().filter(l=>complete(l.id)).length+' / '+lessons().length+' activities';}
function nextFor(id){
 const ordered=lessons(),index=ordered.findIndex(x=>x.id===id);
 return ordered.slice(index+1).find(x=>!x.optional&&!complete(x.id))
  || requiredLessons().find(x=>!complete(x.id)&&x.id!==id)
  || requiredLessons()[0];
}
function row(l,i=0) {
 const isDone=complete(l.id),method=l.kind==='code'?'Tested coding':l.kind==='quiz'?'Quick check':'Rubric review';
 return `<a class="lesson-row" data-action="lesson" data-id="${l.id}" href="#lesson/${l.id}"><span class="step-number ${isDone?'done':''}">${isDone?icon('check'):l.optional?'↺':String(i+1).padStart(2,'0')}</span><span class="lesson-row-text"><h3>${escapeHTML(l.title)}</h3><p>${escapeHTML(l.summary)}</p></span><span class="lesson-row-meta">${badge(isDone?(l.kind==='discussion'?'Reviewed':'Completed'):method,isDone?'done':'outline')}<span class="subtle">${l.minutes} min</span>${icon('chevron')}</span></a>`;
}
function renderHome(){
 shell('home');
 const today=state.activity.filter(x=>dayKey(x.at)===dayKey(Date.now())).length;
 const pending=requiredLessons().find(x=>!complete(x.id));
 const next=pending||requiredLessons()[0];
 const actionLabel=!pending?'Review from the start':state.activity.length||requiredLessons().some(x=>complete(x.id))?'Continue learning':'Start learning';
 $('#main').innerHTML=`<section class="hero"><div class="hero-main"><div class="eyebrow">BUILD YOUR BACKEND ENGINEERING SKILLS</div><h1>Turn “I get it” into<br>“I built it.”</h1><p>Your Python practice, one clear challenge at a time. Write real code, run real tests, and learn exactly what to fix next.</p><div class="hero-actions">${btn(`${actionLabel} ${icon('arrow')}`,'lesson','primary',`data-id="${next.id}"`)}${next.id==='q-sets'?'':btn('Quick warm-up','lesson','ghost',`data-id="q-sets"`)}</div></div><aside class="today-card"><div class="eyebrow">SMALL STEPS, REAL PROGRESS</div><h3>Your daily rhythm</h3><div class="daily-ring" style="--p:${Math.min(today/3*100,100)}"><div class="ring-text"><strong>${today}<span class="subtle"> / 3</span></strong><small>practice attempts</small></div></div><p>${today>=3?'You showed up. That’s how fluency grows.':'One attempt is a start. Three makes a good practice session.'}</p></aside></section>
 <div class="section-head"><div><h2>Choose your next chapter</h2><p>Work through the chapters in order, or open a topic you want to practise.</p></div>${badge('No LeetCode puzzles','outline')}</div>
 <div class="track-grid">${catalog.tracks.map((t,i)=>{const group=byTrack(t.id),done=group.filter(l=>complete(l.id)).length;return `<a class="track-card" data-action="navigate" data-route="track/${t.id}" href="#track/${t.id}"><div class="track-card-top"><span class="track-icon ${t.color}">${icon(t.icon)}</span><span class="subtle">CHAPTER ${String(i+1).padStart(2,'0')}</span></div><h3>${escapeHTML(t.title)}</h3><p>${escapeHTML(t.subtitle)}</p><div class="track-footer"><span>${group.length} ${group.length===1?'activity':'activities'}</span><span>${done} of ${group.length} complete</span></div>${progress(done/group.length*100)}</a>`;}).join('')}</div>
 <div class="info-strip">${icon('info')}<div><strong>A playground for backend engineering.</strong> Explore Python, search, ingestion and architecture through small exercises with real tests.</div></div>
 <div class="footer-note">${lessons().filter(x=>x.kind==='code').length} code missions · ${lessons().filter(x=>x.kind==='quiz').length} quick checks · ${lessons().filter(x=>x.kind==='discussion').length} architecture discussions. Completion badges record past achievements, not a guarantee that later edits still pass.</div>`;
}
function renderList(type,id){
 shell(type);
 let group,title,description;
 const recaps=type==='track'?lessons().filter(l=>l.track===id&&l.optional):[];
 if(type==='track') {const t=trackFor(id);if(!t){renderHome();return;}group=byTrack(id);title=t.title;description=t.subtitle;}
 else if(type==='code'){group=lessons().filter(x=>x.kind==='code');title='Code it. Test it. Understand it.';description='16 coding missions using the supplied practice tests. The guided search stages share a file, so each builds on your previous work.';}
 if(listFilter==='unfinished')group=group.filter(l=>!complete(l.id));
 $('#main').innerHTML=`<div class="page-title"><div><div class="eyebrow">${type==='track'?'YOUR LEARNING PATH':type==='code'?'PYTHON 3.13+ · LOCAL PYTEST':'SPEAK ALOUD. CAPTURE THE ESSENTIALS.'}</div><h1>${escapeHTML(title)}</h1><p>${escapeHTML(description)}</p></div></div><div class="filter-bar"><button class="filter-pill ${listFilter==='all'?'active':''}" data-action="list-filter" data-value="all">All activities</button><button class="filter-pill ${listFilter==='unfinished'?'active':''}" data-action="list-filter" data-value="unfinished">Not completed yet</button></div><div class="lesson-list">${group.length?group.map((l,i)=>row(l,i)).join(''):'<div class="empty"><h2>This chapter is complete.</h2><p>Switch to all activities to repeat a lesson without hints.</p></div>'}</div>${recaps.length?`<section class="review-section"><h2>Optional recap</h2><p>Independent practice of an earlier exercise. This does not count toward chapter completion.</p><div class="lesson-list">${recaps.map(l=>row(l)).join('')}</div></section>`:''}<div class="footer-note">Suggested times are optional practice timeboxes. You can open any activity; there are no artificial locks.</div>`;
}
function renderReview(){
 shell('review');const queue=queued(),bookmarks=lessons().filter(l=>state.bookmarks.includes(l.id));
 $('#main').innerHTML=`<div class="page-title"><div><div class="eyebrow">YOUR NEXT IMPROVEMENT IS ALREADY HERE</div><h1>A second pass makes it stick.</h1><p>Latest failed submissions, self-review points that need work, and anything you saved for later.</p></div></div><section class="review-section"><h2>Ready for another attempt <span class="subtle">(${queue.length})</span></h2>${queue.length?`<div class="lesson-list">${queue.map((l,i)=>row(l,i)).join('')}</div>`:`<div class="empty">${icon('leaf')}<h2>A clean slate.</h2><p>Failed checks will appear here automatically. No lost hearts, no penalty for trying.</p>${btn('Choose an activity','navigate','primary','data-route="home"')}</div>`}</section><section class="review-section"><h2>Saved for later <span class="subtle">(${bookmarks.length})</span></h2>${bookmarks.length?`<div class="lesson-list">${bookmarks.map((l,i)=>row(l,i)).join('')}</div>`:'<p class="subtle">Use the bookmark button on any activity to save it here.</p>'}</section>`;
}
function renderSettings(){
 shell('settings');$('#main').innerHTML=`<div class="page-title"><div><div class="eyebrow">${boot.hosted?'PRIVATE HOSTED INSTANCE':'LOCAL BY DESIGN'}</div><h1>Your lab. Your progress.</h1><p>${boot.hosted?'Password-protected practice. Your code and answers are saved on this instance’s persistent volume.':'No login, no tracking, no model API. Your code and answers are saved on this computer.'}</p></div></div><div class="settings-grid"><section class="card"><h3>Your Python engine</h3><table class="status-table"><tr><td>Interpreter</td><td>CPython ${escapeHTML(boot.python)}</td></tr><tr><td>Test runner</td><td>pytest ${escapeHTML(boot.pytest)}</td></tr><tr><td>Test process deadline</td><td>20 seconds</td></tr><tr><td>Progress file</td><td>.judgelab/progress.json</td></tr></table><p>Tests run in a fresh temporary workspace. The interpreter is the one that launched this app.</p></section><section class="card"><h3>Take your work with you</h3><p>Export drafts, answers and achievements to JSON. Importing replaces the current progress file; export first. Imported code needs to be tested again.</p>${btn(`${icon('download')} Export progress`,'export','primary')}${btn(`${icon('upload')} Import backup`,'import','secondary')}<input id="import-file" type="file" accept=".json,application/json" hidden></section><section class="card"><h3>What gets checked?</h3><p><strong>Coding:</strong> the supplied pytest assertions run against the submitted file. Failure messages and coaching cues refer to those actual cases.</p><p><strong>Quick checks:</strong> a fixed answer key explains the exercise contract.</p><p><strong>Discussions:</strong> word count and keyword cues, followed by your self-review. There is no semantic grading, truth verification or hiring prediction.</p></section><section class="card"><h3>Sources & boundaries</h3><p>The practice packs live in <code>packs/</code>. Tests define the exercise contracts. Guidance, reference implementations and review rubrics are included for learning and experimentation.</p><p>The V1 and V2 ingestion/search contracts differ intentionally. Each activity names the pack it uses.</p>${btn('Read the safety note','safety','secondary')}</section></div><div class="info-strip warning">${icon('info')}<div><strong>Only run your own trusted code.</strong> A subprocess and timeout are not an operating-system sandbox. ${escapeHTML(boot.execution_warning)}</div></div>`;
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
 if(current.kind==='discussion'&&state.reviews[id])rubricChecks=[...state.reviews[id].checks];
 clearInterval(timerInterval);timer={remaining:current.minutes*60,running:false};timerInterval=setInterval(tickTimer,1000);
 renderLesson();
}
function lessonHeader(){
 const t=trackFor(current.track),group=byTrack(t.id),n=group.findIndex(x=>x.id===current.id)+1;
 return `<a class="back-link" data-action="navigate" data-route="track/${t.id}" href="#track/${t.id}">${icon('back')} Back to chapter</a><div class="lesson-heading"><div><div class="eyebrow">${escapeHTML(t.title)} · ${current.optional?'OPTIONAL RECAP':`${String(n).padStart(2,'0')} / ${String(group.length).padStart(2,'0')}`}</div><h1>${escapeHTML(current.title)}</h1>${current.problem?'':`<p>${escapeHTML(current.summary)}</p>`}${current.optional?`<p>This repeats the guided-search contract. Your saved work remains available.</p>${btn('Continue to indexing','lesson','secondary','data-id="c-index-build"')}`:''}</div><div class="lesson-meta">${badge('+'+current.xp+' XP','outline')}<button class="bookmark ${state.bookmarks.includes(current.id)?'on':''}" data-action="bookmark" aria-label="Bookmark this activity" title="Save for later">${icon('bookmark')}</button></div></div>`;
}
function phaseTabs(){
 const practice=current.kind==='code'?'Write code':current.kind==='quiz'?'Quick check':'Your answer';
 const tabs=[{id:0,label:'Problem'},{id:4,label:'Walkthrough'},{id:1,label:practice}];
 if(current.kind!=='quiz'&&(feedback||phase===2))tabs.push({id:2,label:'Feedback'});
 tabs.push({id:3,label:'Knowledge base'});
 return `<div class="phase-tabs activity-nav" role="tablist" aria-label="Lesson views">${tabs.map(tab=>`<button id="lesson-tab-${tab.id}" role="tab" aria-controls="lesson-panel" aria-selected="${phase===tab.id}" tabindex="${phase===tab.id?'0':'-1'}" class="phase-tab ${phase===tab.id?'active':''} ${tab.id===3?'knowledge-tab':''}" data-action="phase" data-phase="${tab.id}">${tab.id===3?icon('book'):''}${tab.label}</button>`).join('')}</div>`;
}
function renderLesson(){
 if(!current)return;
 editor=null;
 document.body.classList.toggle('focus-mode',focusMode&&phase===1&&current.kind==='code');
 const body=phase===0?scenarioView(current):phase===4?walkthroughView(current):phase===3?knowledgeView(current):current.kind==='quiz'?`<div class="quiz-lesson">${quizQuestionView(quizResult)}</div>`:current.kind==='code'?codeView():discussionView();
 $('#main').innerHTML=lessonHeader()+phaseTabs()+`<div id="lesson-panel" role="tabpanel" aria-labelledby="lesson-tab-${phase}">${body}</div>`;
 if(current.kind==='code'&&phase===1)mountEditor();
 if(current.kind==='discussion'&&phase===1)mountAnswer();
 refreshTotals();
}
function timerButton(){return `<button class="timer ${timer?.running?'active':''}" data-action="timer" title="Optional practice timer; it does not submit or fail your work">${icon(timer?.running?'pause':'clock')}<span id="timer-label">${timerText()}</span></button>`;}
function timerText(){if(!timer)return 'Start timer';const m=Math.floor(timer.remaining/60),s=timer.remaining%60;return `${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}${timer.running?'':' · start/pause'}`;}
function tickTimer(){if(timer?.running&&timer.remaining>0){timer.remaining--;if(timer.remaining===0){timer.running=false;toast('Timebox finished. Keep working or submit when you’re ready.');}const el=$('#timer-label');if(el)el.textContent=timerText();}}
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
// Read declarations from supplied scaffolding, never from tests or reference solutions.
function modelFiles(lesson){return (lesson.references||[]).filter(ref=>/(^|\/)models\.py$/.test(ref.name));}
function exerciseModels(lesson){
 const models=[];
 for(const ref of [...modelFiles(lesson),{name:lesson.file||'Exercise',text:lesson.starter||''}]){
  let model=null;
  for(const line of ref.text.split('\n')){
   const cls=line.match(/^class (\w+)(?:\([^)]*\))?:/);
   if(cls){model={name:cls[1],source:ref.name,fields:[]};models.push(model);continue;}
   if(/^\S/.test(line)||/^    (?:async )?def /.test(line))model=null;
   const field=line.match(/^    (\w+):\s*(.+)/);
   if(model&&field)model.fields.push({name:field[1],detail:field[2].split('#')[0].trim()});
  }
 }
 return models.filter(model=>model.fields.length);
}
function modelReference(lesson){
 const models=exerciseModels(lesson);
 return `<section id="model-reference" class="model-reference" aria-label="Data models"><p>Exact fields, types and defaults supplied with this exercise.</p><div class="model-list">${models.length?models.map(model=>`<div><h3>${escapeHTML(model.name)}</h3><pre class="model-source" tabindex="0" aria-label="${escapeHTML(model.name)} fields"><code>${model.fields.map(field=>escapeHTML(field.name+': '+field.detail)).join('\n')}</code></pre><small>${escapeHTML(model.source)}</small></div>`).join(''):'<p>This exercise has no supplied record classes. Its function signatures are in the code below.</p>'}</div></section>`;
}
// Small, explicit standard-library vocabulary; no claims of Python type inference.
const pythonMethods={
 str:['split','rsplit','splitlines','strip','lstrip','rstrip','lower','upper','casefold','join','replace','startswith','endswith','find','count','isdigit','isalpha','isalnum','partition','removeprefix','removesuffix'],
 list:['append','extend','insert','pop','remove','clear','index','count','sort','reverse','copy'],
 dict:['get','items','keys','values','setdefault','update','pop','popitem','clear','copy'],
 set:['add','update','discard','remove','union','intersection','difference','issubset','issuperset','isdisjoint','copy'],
};
function completionShortcut(){return typeof navigator!=='undefined'&&/Mac/.test(navigator.platform)?'⌃ . (Control + .)':'Ctrl + .';}
function exerciseCompletions(cm){
 const cursor=cm.getCursor(),line=cm.getLine(cursor.line),prefix=line.slice(0,cursor.ch).match(/[A-Za-z_][\w]*$/)?.[0]||'';
 const from=cursor.ch-prefix.length,member=line[from-1]==='.';
 if(/string|comment/.test(cm.getTokenAt(cursor).type||''))return null;
 const options=new Map();
 function add(name,detail){const old=options.get(name);options.set(name,{text:name,displayText:name+'  '+(old?old.detail+'; ':'')+detail,detail:(old?old.detail+'; ':'')+detail});}
 for(const model of exerciseModels(current)){
  if(!member)add(model.name,'model');
  for(const field of model.fields)add(field.name,model.name+': '+field.detail);
 }
 if(member)for(const [type,names] of Object.entries(pythonMethods))for(const name of names)add(name,type+' method');
 if(!member)for(const word of [...(cm.getValue().match(/[A-Za-z_]\w*/g)||[]),...(CodeMirror.hintWords?.python||[])])if(!options.has(word))options.set(word,{text:word});
 return {list:[...options.values()].filter(item=>item.text.startsWith(prefix)&&(member||item.text!==prefix)).sort((a,b)=>a.text.localeCompare(b.text)),from:CodeMirror.Pos(cursor.line,from),to:cursor};
}
function completeExercise(cm){cm.showHint({hint:exerciseCompletions,completeSingle:false});}
function testScope(lesson){
 const siblings=catalog.lessons.filter(item=>item.kind==='code'&&item.workspace===lesson.workspace&&item.id!==lesson.id);
 const integration=lesson.pack==='guided'&&!lesson.selection;
 const targets=integration?[...new Set([...siblings.flatMap(item=>item.targets),...lesson.targets])]:lesson.targets;
 return `<section class="test-scope" aria-label="Test scope"><strong>${lesson.selection?'Only':'Testing'} ${targets.map(name=>`<code>${escapeHTML(name)}</code>`).join(', ')}</strong><p>${lesson.expected_tests} acceptance tests${integration?', including the helpers and full search integration':''}. ${lesson.selection?'A pass here does not validate the other functions in this file.':'A pass applies to this activity’s acceptance contract.'}</p>${siblings.length&&!integration?`<div class="scope-links"><span>Test another part of this file:</span>${siblings.map(item=>btn(item.targets.map(name=>escapeHTML(name)).join(', '),'lesson','secondary small',`data-id="${escapeHTML(item.id)}"`)).join('')}</div>`:''}</section>`;
}
function codeView(){
 if(phase===2)return codeFeedback();
 return `${testScope(current)}<div class="timer-note">Optional timebox · syntax references are allowed during practice</div><div class="workspace"><aside class="task-panel"><h3>Your acceptance contract</h3><pre class="contract">${escapeHTML(current.contract)}</pre>${btn(`${icon('book')} Models & test source`,'references','secondary small')}<div class="hint-box"><h3>A nudge, not the answer</h3><div id="hints">${hintHTML()}</div>${btn(`${icon('help')} ${hintCount?'Another hint':'Show a hint'}`,'hint','ghost small',hintCount>=current.hints.length?'disabled':'')}</div><div class="source-note">${escapeHTML(current.file)}<br>${current.pack==='guided'?'All four guided stages share this file. Your other functions are preserved.':'A separate workspace for this original exercise.'}</div></aside><section class="editor-panel"><div class="editor-toolbar"><span class="file">${icon('code')} ${escapeHTML(current.file.split('/').pop())}</span><button class="btn secondary small models-toggle" data-action="models" aria-controls="model-reference" aria-expanded="true">${icon('book')} Data models</button><div class="editor-tools"><button class="tool-button" data-action="complete" title="Show names, fields and methods (${completionShortcut()})">Complete</button><button class="tool-button" data-action="jump">Jump to target</button><button class="tool-button" data-action="focus" title="Toggle focus mode" aria-label="Toggle focus mode">${icon('focus')}</button><button class="tool-button" data-action="reset" title="Reset entire shared file" aria-label="Reset file">${icon('review')}</button></div></div>${modelReference(current)}<textarea id="code-source" aria-label="Python code editor"></textarea><div class="editor-status"><span>Python · Suggestions: ${completionShortcut()}</span><button class="tool-button" data-action="download-code">Export .py ${icon('download')}</button></div><div class="editor-bottom"><span id="save-state" class="save-state">${icon('check')} ${boot.hosted?'Saved to your private instance':'Saved on this computer'}</span><div class="layout-actions">${timerButton()}<span class="shortcut">⌘ / Ctrl ↵</span>${btn(`${icon('play')} Run tests`,'run','primary',busy?'disabled':'')}</div></div></section></div>${feedback?`<div class="info-strip">${icon('info')}<div>Your last submission: <strong>${feedback.passed||0} passed</strong>${feedback.failed?`, ${feedback.failed} failed`:''}. Edits are not validated until you run tests again. <button class="inline-link" data-action="phase" data-phase="2">Open last feedback</button></div></div>`:''}`;
}
function hintHTML(){return current.hints.slice(0,hintCount).map((h,i)=>`<div class="hint"><small>Hint ${i+1} of ${current.hints.length}</small>${escapeHTML(h)}</div>`).join('');}
function mountEditor(){
 const area=$('#code-source');area.value=localCode;
 editor=CodeMirror.fromTextArea(area,{mode:{name:'python',version:3},lineNumbers:true,indentUnit:4,tabSize:4,indentWithTabs:false,matchBrackets:true,styleActiveLine:true,lineWrapping:false,
  extraKeys:{'Ctrl-.':completeExercise,'Tab':cm=>cm.somethingSelected()?cm.indentSelection('add'):cm.replaceSelection('    ','end'), 'Shift-Tab':'indentLess','Ctrl-Enter':()=>submitCode(),'Cmd-Enter':()=>submitCode(),'Ctrl-S':()=>saveDraft(current.id,editor.getValue()),'Cmd-S':()=>saveDraft(current.id,editor.getValue())}});
 editor.on('change',cm=>noteDraft(cm.getValue()));
 editor.on('inputRead',(cm,change)=>{if(change.origin==='+input'&&/[.A-Za-z_0-9]$/.test(change.text.join('')))completeExercise(cm);});
 setTimeout(()=>{editor?.refresh();jumpToTarget(false);},40);
}
function jumpToTarget(focus=true){if(!editor)return;const target=current.targets[0],lines=editor.getValue().split('\n');let index=lines.findIndex(line=>new RegExp(`^(async )?def ${target}\\(`).test(line));if(index<0)index=0;editor.setCursor({line:index,ch:0});editor.scrollIntoView({line:index,ch:0},45);if(focus)editor.focus();}
function readableCase(nodeid){return nodeid.split('::').slice(1).join(' / ').replace(/^test_/,'').replace(/_/g,' ');}
function codeFeedback(){
 const r=feedback;
 if(!r || r.passed===undefined)return `<div class="empty">${icon('terminal')}<h2>Your feedback starts with a run.</h2><p>Submit your Python from the workspace. You’ll get the real passing and failing assertions—not a simulated score.</p>${btn('Open the workspace','phase','primary','data-phase="1"')}</div>`;
 const records=(r.records||[]).filter(x=>testFilter==='all'||x.outcome!=='passed');
 const all= r.records||[];const isStale=r.submitted_text!==undefined && r.submitted_text!==localCode;
 const title=r.success?'This activity’s acceptance tests passed.':r.timed_out?'Let’s find what’s stuck.':r.collection_errors?.length?'Fix the file, then test again.':'Not there yet. Now you know where.';
 const count=`${r.passed} / ${r.collected||current.expected_tests||0} cases passed`;
 return `${testScope(current)}${isStale?`<div class="info-strip warning" style="margin:0 0 20px">${icon('info')}<div><strong>Your code has changed since this run.</strong> These are historical results. Run the current draft to validate it.</div></div>`:''}<div class="feedback-summary ${r.success?'':'retry'} completion-pop"><span class="feedback-symbol">${icon(r.success?'check':'review')}</span><div><h2>${title}</h2><p>${count} · ${r.elapsed ?? '?'}s · CPython ${escapeHTML(r.python||boot.python)}${r.success?' · '+current.xp+' XP on first completion':''}</p></div></div>
 <div class="result-grid"><div><div class="section-head" style="margin-top:0"><h2>What the tests actually said</h2><div class="filter-bar" style="margin:0"><button class="filter-pill ${testFilter==='failed'?'active':''}" data-action="test-filter" data-value="failed">Needs work</button><button class="filter-pill ${testFilter==='all'?'active':''}" data-action="test-filter" data-value="all">All ${all.length}</button></div></div>
 ${(r.collection_errors||[]).map(error=>`<div class="test-list" style="margin-bottom:15px"><details class="test-row fail" open><summary>${icon('info')}<span class="name">Test collection / Python error</span></summary><div class="test-details"><pre>${escapeHTML(error)}</pre></div></details></div>`).join('')}
 ${records.length?`<div class="test-list">${records.map((record,i)=>`<details class="test-row ${record.outcome==='passed'?'':'fail'}" ${i===0&&record.outcome!=='passed'?'open':''}><summary>${icon(record.outcome==='passed'?'check':'close')}<span class="name">${escapeHTML(readableCase(record.nodeid))}</span><small>${escapeHTML(record.outcome)}</small></summary><div class="test-details">${record.tip?`<p><strong>Coaching cue:</strong> ${escapeHTML(record.tip)}</p>`:''}${record.detail?`<pre>${escapeHTML(record.detail)}</pre>`:'<p>This acceptance case passed for the submitted code.</p>'}${record.stdout?`<pre>${escapeHTML(record.stdout)}</pre>`:''}</div></details>`).join('')}</div>`:r.success?`<div class="info-strip success" style="margin-top:0">${icon('check')}<div>No failing cases in this run. Switch to All to inspect every checked behaviour.</div></div>`:''}
 <details class="console"><summary>Open raw pytest console output</summary><pre>${escapeHTML(r.output||'No console output; the file could not be parsed.')}</pre></details></div>
 <aside class="card feedback-tips"><h3>${r.success?'Make the reasoning stick':'Your next correction'}</h3>${(r.tips||[]).map(t=>`<p>${escapeHTML(t)}</p>`).join('')}${btn(`${icon('back')} ${r.success?'Review your code':'Back to code'}`,'phase',r.success?'secondary':'primary','data-phase="1"')}${r.success?btn(`Continue ${icon('arrow')}`,'lesson','primary',`data-id="${nextFor(current.id).id}"`):''}${btn('Compare a reference approach','reveal','ghost')}${btn('Read the test source','references','ghost')}<div class="source-note">Hints are rule-based. The assertion output is from a real local pytest run. This is not an AI code review.</div></aside></div>
 <div class="info-strip">${icon('info')}<div>Results belong to the last <strong>submitted</strong> code. Editing or copying a reference does not validate it. Run again after changes.</div></div>`;
}
function practiceLabel(lesson){return lesson.kind==='code'?'Write code':lesson.kind==='quiz'?'Try the quick check':'Write your answer';}
function scenarioView(lesson){
 const scenario=lesson.scenario;
 const preparation=(lesson.depends||[]).map(findLesson).filter(Boolean);
 return `<div class="scenario-panel"><article class="scenario-main" data-content="scenario"><p class="scenario-opening">${escapeHTML(scenario.prompt)}</p><h2>Requirements</h2><ul class="scenario-requirements">${scenario.requirements.map(item=>`<li>${escapeHTML(item)}</li>`).join('')}</ul></article><aside class="scenario-sidebar"><h2>Your task</h2><p>${escapeHTML(scenario.deliverable)}</p>${preparation.length?`<div class="preparation-links"><h2>Builds on</h2>${preparation.map(l=>`<a href="#lesson/${escapeHTML(l.id)}" data-action="lesson" data-id="${escapeHTML(l.id)}">${escapeHTML(l.title)} ${icon('chevron')}</a>`).join('')}</div>`:''}<button class="knowledge-shortcut" data-action="phase" data-phase="3">${icon('book')} Definitions & reference notes</button></aside><div class="scenario-actions">${btn('Work through an example '+icon('arrow'),'phase','primary','data-phase="4"')}${btn(practiceLabel(lesson),'phase','ghost','data-phase="1"')}</div></div>`;
}
function flowGraph(graph, suffix){
 if(!graph)return '';
 const marker='flow-arrow-'+suffix;
 const nodes=graph.nodes.map(node=>{
  const {x,y,w,h}=node;
  let shape;
  if(node.shape==='database')shape=`<path d="M${x} ${y+14} A${w/2} 14 0 0 1 ${x+w} ${y+14} V${y+h-14} A${w/2} 14 0 0 1 ${x} ${y+h-14} Z M${x} ${y+14} A${w/2} 14 0 0 0 ${x+w} ${y+14}"/>`;
  else if(node.shape==='decision')shape=`<path d="M${x+w/2} ${y} L${x+w} ${y+h/2} L${x+w/2} ${y+h} L${x} ${y+h/2} Z"/>`;
  else if(node.shape==='document')shape=`<path d="M${x} ${y} H${x+w} V${y+h-10} Q${x+w*.75} ${y+h-22} ${x+w/2} ${y+h-10} T${x} ${y+h-10} Z"/>`;
  else shape=`<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${node.shape==='terminal'?h/2:2}"/>${node.shape==='queue'?`<path d="M${x+9} ${y} V${y+h} M${x+w-9} ${y} V${y+h}"/>`:''}`;
  return `<g class="graph-node graph-${escapeHTML(node.shape)}">${shape}<text x="${x+w/2}" y="${y+h/2-(node.lines.length-1)*11}" dominant-baseline="middle" text-anchor="middle">${node.lines.map((line,i)=>`<tspan x="${x+w/2}" dy="${i?22:0}">${escapeHTML(line)}</tspan>`).join('')}</text></g>`;
 }).join('');
 return `<p class="flow-pan-hint">Scroll sideways to follow the full diagram.</p><div class="flow-canvas" tabindex="0" role="region" aria-label="Flow diagram, scroll horizontally on small screens"><svg class="flow-graph" viewBox="0 0 ${graph.width} ${graph.height}" role="img" aria-labelledby="graph-title-${suffix} graph-desc-${suffix}"><title id="graph-title-${suffix}">${escapeHTML(graph.title||'System flow')}</title><desc id="graph-desc-${suffix}">${escapeHTML(graph.description)}</desc><defs><marker id="${marker}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 Z"/></marker></defs>${graph.labels.map(label=>`<text class="graph-heading" x="${label.x}" y="${label.y}">${escapeHTML(label.text)}</text>`).join('')}${graph.edges.map(edge=>`<path class="graph-edge" d="${escapeHTML(edge.path)}" marker-end="url(#${marker})"/>${edge.label?`<text class="graph-edge-label" x="${edge.x}" y="${edge.y}" text-anchor="middle">${escapeHTML(edge.label)}</text>`:''}`).join('')}${nodes}</svg></div>`;
}
function walkthroughFlow(flow){
 if(!flow)return '';
 return `<figure class="lesson-flow"><figcaption><h2>${escapeHTML(flow.title)}</h2><p>${escapeHTML(flow.summary)}</p></figcaption>${flowGraph(flow.graph,'main')}<p class="flow-note">${escapeHTML(flow.note)}</p>${flow.async?`<details class="flow-async"><summary>${escapeHTML(flow.async.title)}</summary>${flowGraph(flow.async.graph,'async')}<p>${escapeHTML(flow.async.note)}</p></details>`:''}</figure>`;
}
function productionDecision(lesson){
 const decision=lesson.implementation.decisions[0];
 if(!decision)return '';
 return `<section class="decision-introduction"><p>${escapeHTML(decision.lead_in)}</p><details class="design-decision"><summary><span>Decision that changes the design</span>${escapeHTML(decision.question)}</summary><dl>${decision.branches.map(branch=>`<div><dt>${escapeHTML(branch.answer)}</dt><dd>${escapeHTML(branch.action)}</dd></div>`).join('')}</dl></details></section>`;
}
function productionContext(lesson){
 const strategy=lesson.strategy;
 return `<section class="production-context" aria-label="Production context"><p class="section-kicker">Production context</p><h2>Where this appears in a real system</h2><p class="production-use-case">${escapeHTML(strategy.use_case)}</p><div class="production-grid"><div><h3>Mechanism</h3><p>${escapeHTML(strategy.mechanism)}</p></div><div><h3>Production direction</h3><p>${escapeHTML(strategy.proposal)}</p></div></div>${productionDecision(lesson)}<details class="production-limits"><summary>Limits and reasons to change the design</summary><ul class="reference-list">${strategy.caveats.map(item=>`<li>${escapeHTML(item)}</li>`).join('')}</ul></details></section>`;
}
function lessonFlow(lesson){return lesson.flow_ref?catalog.flows?.[lesson.flow_ref]||null:null;}
function walkthroughOverview(lesson){
 const sections=lesson.overview||[];
 const flow=lessonFlow(lesson);
 if(!sections.length&&!flow)return '';
 const paragraphs=section=>section.paragraphs.map(paragraph=>`<p>${escapeHTML(paragraph)}</p>`).join('');
 const lead=sections[0];
 return `<section class="walk-overview" aria-label="Solution overview">${lead?`<h2>${escapeHTML(lead.heading)}</h2>${paragraphs(lead)}${lead.comparison?`<div class="teaching-trace" tabindex="0" role="region" aria-label="${escapeHTML(lead.comparison.caption)}"><table><caption>${escapeHTML(lead.comparison.caption)}</caption><thead><tr>${lead.comparison.headers.map(header=>`<th scope="col">${escapeHTML(header)}</th>`).join('')}</tr></thead><tbody>${lead.comparison.rows.map(row=>`<tr>${row.map((cell,index)=>index===0?`<th scope="row">${escapeHTML(cell)}</th>`:`<td>${escapeHTML(cell)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`:''}`:''}${walkthroughFlow(flow)}${sections.length>1?`<div class="overview-details">${sections.slice(1).map(section=>`<details class="knowledge-section"><summary>${escapeHTML(section.heading)}</summary>${paragraphs(section)}</details>`).join('')}</div>`:''}</section>`;
}
function walkthroughView(lesson){
 return `<article class="lesson-walkthrough" data-content="walkthrough">${productionContext(lesson)}${walkthroughOverview(lesson)}<section class="walk-example"><h2>A worked example</h2>${lesson.worked_example?workedExample(lesson):`<ol class="learning-reasoning">${lesson.problem.reasoning.map(step=>`<li>${escapeHTML(step)}</li>`).join('')}</ol>`}</section><section class="walk-implementation"><p class="section-kicker">Exercise boundary</p><h2>${escapeHTML(lesson.strategy.name)}</h2><p class="exercise-contract">${escapeHTML(lesson.brief.rule)}</p>${implementationGuide(lesson)}</section>${lesson.practice_check?practiceCheck(lesson):''}<div class="scenario-actions">${btn(practiceLabel(lesson)+' '+icon('arrow'),'phase','primary','data-phase="1"')}${btn('Open knowledge base','phase','ghost','data-phase="3"')}</div></article>`;
}
function knowledgeView(lesson){
 const guide=lesson.implementation;
 return `<article class="lesson-knowledge" data-content="knowledge"><header class="knowledge-heading"><h2>Knowledge base</h2></header><section class="knowledge-terms"><h3>Definitions</h3><dl>${lesson.brief.vocabulary.map(item=>`<div><dt>${escapeHTML(item.term)}</dt><dd>${escapeHTML(item.meaning)}</dd></div>`).join('')}</dl></section><section class="knowledge-choices"><h3>Design choices explained</h3>${guide.decisions.map(decision=>`<section class="decision-introduction"><p>${escapeHTML(decision.lead_in)}</p><details class="knowledge-section"><summary>${escapeHTML(decision.question)}</summary><dl>${decision.branches.map(branch=>`<div><dt>${escapeHTML(branch.answer)}</dt><dd>${escapeHTML(branch.action)}</dd></div>`).join('')}</dl></details></section>`).join('')}</section>${guide.ranking_code?`<details class="knowledge-section"><summary>How chunk ranking produces an order</summary><pre class="teaching-code" tabindex="0" aria-label="Python ranking example"><code>${escapeHTML(guide.ranking_code)}</code></pre><p>${escapeHTML(guide.ranking_note)}</p></details>`:''}${lesson.concept?`<details class="knowledge-section"><summary>Python & implementation notes</summary><div class="markdown">${markdown(lesson.concept)}${markdown(lesson.after_example)}</div></details>`:''}${guide.connections?.length?`<section class="knowledge-related"><h3>Related lessons</h3>${guide.connections.map(link=>`<div><a href="#lesson/${escapeHTML(link.id)}" data-action="lesson" data-id="${escapeHTML(link.id)}">${escapeHTML(findLesson(link.id).title)}</a><p>${escapeHTML(link.text)}</p></div>`).join('')}</section>`:''}${lesson.strategy.references?.length||guide.ranking_reference?`<section class="knowledge-related"><h3>Technical reading</h3>${[...(lesson.strategy.references||[]),...(guide.ranking_reference?[guide.ranking_reference]:[])].map(ref=>`<a href="${escapeHTML(ref.url)}" target="_blank" rel="noopener noreferrer">${escapeHTML(ref.title)} ↗</a>`).join('')}</section>`:''}${lesson.kind==='code'?btn('Models, full contract & tests','references','secondary'):''}</article>`;
}
function implementationGuide(lesson){
 const guide=lesson.implementation;
 if(!guide)return '';
 return `<div class="implementation-guide"><h3>${lesson.kind==='discussion'?'Responsibilities':'State to maintain'}</h3><p>${escapeHTML(guide.state)}</p><h3>${lesson.kind==='discussion'?'Operations and failure handling':'Implementation steps'}</h3><ol class="learning-reasoning">${guide.steps.map(step=>`<li>${escapeHTML(step)}</li>`).join('')}</ol>${guide.code?`<h3>Python example</h3><pre class="teaching-code" tabindex="0" aria-label="Python selection example"><code>${escapeHTML(guide.code)}</code></pre>`:''}${guide.trace?`<div class="teaching-trace" role="region" aria-label="${escapeHTML(guide.trace.caption||'Budget trace')}" tabindex="0"><table><caption>${escapeHTML(guide.trace.caption||'Track the budget through the loop (tokens)')}</caption><thead><tr>${guide.trace.headers.map(header=>`<th scope="col">${escapeHTML(header)}</th>`).join('')}</tr></thead><tbody>${guide.trace.rows.map(row=>`<tr>${row.map(cell=>`<td>${escapeHTML(cell)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`:''}</div>`;
}
function quizQuestionView(r){
 return `<div class="quiz-stage"><div class="quiz-card"><div class="question-type">QUICK CHECK</div><h2>${escapeHTML(current.question)}</h2><div class="quiz-options" role="group" aria-label="Answer choices">${current.choices.map((choice,i)=>`<button class="quiz-option ${selectedChoice===i?'selected':''} ${r&&r.correct===i?'correct':''} ${r&&!r.success&&r.choice===i?'incorrect':''}" data-action="quiz-choice" data-choice="${i}" aria-pressed="${selectedChoice===i}"><span class="keycap">${i+1}</span><span>${escapeHTML(choice)}</span>${r&&r.correct===i?icon('check'):''}</button>`).join('')}</div>${r?`<div class="quiz-answer ${r.success?'':'wrong'}"><strong>${r.success?'Correct.':'Not quite.'}</strong>${r.tip?escapeHTML(r.tip)+'<br>':''}${escapeHTML(r.explanation)}</div>`:''}<div class="quiz-bottom"><span class="subtle">Keys 1–4 to select · Enter to check</span>${r?.success?btn(`Next activity ${icon('arrow')}`,'lesson','primary',`data-id="${nextFor(current.id).id}"`):r?btn('Try it again','quiz-retry','primary'):btn(`Check answer ${icon('arrow')}`,'quiz-submit','primary',selectedChoice===null?'disabled':'')}</div></div></div>`;
}
function discussionView(){
 if(phase===1)return `<div class="answer-layout"><section class="card"><div class="section-head" style="margin-top:0"><h3 style="margin:0">Your answer</h3>${timerButton()}</div><textarea id="discussion-answer" class="answer-editor" placeholder="Describe your design, assumptions, trade-offs and failure handling." aria-label="Your discussion answer"></textarea><div class="answer-meta"><span id="answer-length">0 words</span><span id="save-state" class="save-state">${icon('check')} ${boot.hosted?'Saved to your private instance':'Saved on this computer'}</span></div>${btn(`Review this answer ${icon('arrow')}`,'discussion-submit','primary')}</section><aside class="card"><div class="card-title">${icon('mic')} ARCHITECTURE DISCUSSION</div><p style="font-size:14px">${escapeHTML(current.question)}</p><p class="subtle">The automatic checks look for structure cues only. They cannot judge the correctness of your design.</p><div id="followups">${followupHTML()}</div>${btn('Give me a follow-up','followup','secondary small',followupCount>=current.followups.length?'disabled':'')}<div class="source-note">Follow-ups help you explore decisions, trade-offs and alternatives.</div></aside></div>`;
 return discussionFeedbackView();
}
function followupHTML(){return current.followups.slice(0,followupCount).map((q,i)=>`<div class="followup"><small>Follow-up ${i+1}</small>${escapeHTML(q)}</div>`).join('');}
function mountAnswer(){const area=$('#discussion-answer');area.value=localAnswer;updateAnswerLength();area.addEventListener('input',()=>{noteDraft(area.value);updateAnswerLength();});}
function updateAnswerLength(){const count=(localAnswer.trim().match(/\S+/g)||[]).length;if($('#answer-length'))$('#answer-length').textContent=`${count} words · ~${Math.round(count/135*60)}s at 135 words/min` ;}
function discussionFeedbackView(){
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
async function submitDiscussion(){
 if(busy)return;busy=true;clearTimeout(savingTimeout);
 try{const data=await api('/api/discussion',{id:current.id,text:localAnswer});state=data.state;feedback=data.result;phase=2;renderLesson();}catch(e){toast(e.message);}finally{busy=false;}
}
function modal(title,subtitle,body,footer='',narrow=false){
 $('#modal-root').innerHTML=`<div class="modal-backdrop"><section class="modal ${narrow?'narrow':''}" role="dialog" aria-modal="true" aria-labelledby="modal-title"><header class="modal-head"><div><h2 id="modal-title">${escapeHTML(title)}</h2><p>${escapeHTML(subtitle)}</p></div><button data-action="close-modal" aria-label="Close dialog">${icon('close')}</button></header><div class="modal-body">${body}</div>${footer?`<footer class="modal-footer">${footer}</footer>`:''}</section></div>`;
 document.body.style.overflow='hidden';setTimeout(()=>$('#modal-root button')?.focus(),0);
}
function closeModal(){ $('#modal-root').innerHTML='';document.body.style.overflow=''; }
function showSafety(runAfter=false){
 modal(boot.hosted?'Your code runs on your private instance.':'Your code runs on your computer.','A real interpreter, not a pretend test result.',`<p>When you press Run tests, JudgeLab copies the exercise into a fresh temporary folder and executes it using the Python interpreter that started this app.</p><div class="info-strip warning">${icon('info')}<div><strong>This is not a security sandbox.</strong> ${escapeHTML(boot.execution_warning)}</div></div><p>${boot.hosted?'The hosted instance requires a login and checks request origin/session tokens. It runs one learner’s trusted code; it is not suitable for sharing with untrusted users.':'The app binds only to 127.0.0.1, checks request origin/session tokens, limits output, and stops long-running test processes. These safeguards do not make arbitrary code safe.'}</p><p>No model API is called. Discussion answers receive transparent structure cues and a self-review rubric, not semantic AI grading.</p>`,btn('Not now','close-modal','secondary')+btn('I understand · continue','consent','primary',`data-run="${runAfter}"`),true);
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
async function navigate(route){if(busy){toast('Let the current submission finish before leaving.');return;}await flushDraft();location.hash=route;}
async function handleRoute(){
 if(busy){return;}
 await flushDraft();current=null;editor=null;clearInterval(timerInterval);focusMode=false;
 const route=decodeURIComponent(location.hash.replace(/^#\/?/,''))||'home';const [type,id]=route.split('/');
 if(type==='lesson')await openLesson(id);else if(type==='track')renderList('track',id);else if(type==='code')renderList(type);else if(type==='review')renderReview();else if(type==='settings')renderSettings();else renderHome();
 window.scrollTo(0,0);
}
// One delegated handler keeps the interface free of inline scripts and unsafe HTML events.
document.addEventListener('click',async event=>{
 const target=event.target.closest('[data-action]');if(!target||target.disabled)return;
 // Keep browser handling for Cmd/Ctrl/Shift clicks and non-primary clicks.
 // Context menus and middle-clicks use the anchor's href without this handler.
 if(target.matches('a[href]')){
  if(event.button!==0||event.metaKey||event.ctrlKey||event.shiftKey||event.altKey)return;
  event.preventDefault();
 }
 const a=target.dataset.action;
 if(busy && !['close-modal','menu'].includes(a)){toast(current?.kind==='code'?'Tests are running. One moment.':'Your answer is being checked. One moment.');return;}
 try{
  switch(a){
   case 'navigate':listFilter='all';await navigate(target.dataset.route);break;
   case 'lesson':await navigate('lesson/'+target.dataset.id);break;
   case 'menu':document.body.classList.toggle('menu-open');break;
   case 'phase':await flushDraft();phase=Number(target.dataset.phase);renderLesson();$('#lesson-tab-'+phase)?.focus();$('.activity-nav')?.scrollIntoView({block:'start'});break;
   case 'list-filter':listFilter=target.dataset.value;{const [type,id]=location.hash.replace('#','').split('/');renderList(type,id);}break;
   case 'test-filter':testFilter=target.dataset.value;renderLesson();break;
   case 'run':await submitCode();break;
   case 'jump':jumpToTarget();break;
   case 'focus':focusMode=!focusMode;document.body.classList.toggle('focus-mode',focusMode);setTimeout(()=>editor?.refresh(),40);break;
   case 'hint':hintCount=Math.min(hintCount+1,current.hints.length);$('#hints').innerHTML=hintHTML();target.disabled=hintCount>=current.hints.length;target.innerHTML=icon('help')+' Another hint';break;
   case 'models':{const panel=$('#model-reference');panel.hidden=!panel.hidden;document.querySelector('[data-action="models"]').setAttribute('aria-expanded',String(!panel.hidden));editor?.refresh();break;}
   case 'complete':if(editor){editor.focus();completeExercise(editor);}break;
   case 'references':showReferences();break;
   case 'reveal':await reveal();break;
   case 'copy-reference':{const text=$('#reference-answer').textContent;try{await navigator.clipboard.writeText(text);toast('Reference copied. Compare it with your code before running again.');}catch(e){toast('Clipboard unavailable. Select the reference text and copy it manually.');}break;}
   case 'download-code':download(current.file.split('/').pop(),localCode,'text/x-python');break;
   case 'reset':if(confirm('Reset the ENTIRE shared file to its starter? This also removes your other functions in that file. Export your .py first to keep a copy.')){localCode=current.starter;localBackup(current.workspace,localCode);editor?.setValue(localCode);await saveDraft(current.id,localCode);toast('File reset. Past completion badges remain historical achievements.');}break;
   case 'timer':timer.running=!timer.running;renderLesson();break;
   case 'quiz-choice':if(!quizResult){selectedChoice=Number(target.dataset.choice);renderLesson();}break;
   case 'quiz-submit':await submitQuiz();break;
   case 'quiz-retry':quizResult=null;selectedChoice=null;renderLesson();break;
   case 'discussion-submit':await submitDiscussion();break;
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
 const lessonTab=event.target.closest?.('.activity-nav [role="tab"]');
 if(lessonTab&&['ArrowLeft','ArrowRight','Home','End'].includes(event.key)){
  event.preventDefault();
  const tabs=$$('.activity-nav [role="tab"]'),index=tabs.indexOf(lessonTab);
  const next=event.key==='Home'?0:event.key==='End'?tabs.length-1:(index+(event.key==='ArrowRight'?1:-1)+tabs.length)%tabs.length;
  tabs[next].click();return;
 }
 if(event.key==='Escape'){if($('#modal-root').firstChild)closeModal();document.body.classList.remove('menu-open');}
 if($('#modal-root').firstChild&&event.key==='Tab'){
  const focusable=$$('#modal-root button, #modal-root select, #modal-root textarea, #modal-root a[href]').filter(x=>!x.disabled);
  if(focusable.length){const first=focusable[0],last=focusable[focusable.length-1];if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus();}else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus();}}
 }
 if(current?.kind==='quiz'&&phase===1&&!document.activeElement.closest('[role="tablist"]')&&!$('#modal-root').firstChild&&!['INPUT','TEXTAREA'].includes(document.activeElement.tagName)){
  if(/^[1-4]$/.test(event.key)&&!quizResult){selectedChoice=Number(event.key)-1;renderLesson();}
  if(event.key==='Enter'&&selectedChoice!==null&&!quizResult){event.preventDefault();submitQuiz();}
 }
});
window.addEventListener('hashchange',handleRoute);
window.addEventListener('beforeunload',()=>{if(current&&current.kind!=='quiz')localBackup(current.kind==='code'?current.workspace:current.id,current.kind==='code'?localCode:localAnswer);});
(async()=>{try{boot=await api('/api/bootstrap');catalog=boot.catalog;state=boot.state;token=boot.token;await handleRoute();}catch(e){$('#shell').innerHTML=`<div class="boot"><h1>The lab could not connect.</h1><p>${escapeHTML(e.message)}</p><p>Reload after the server is ready. For local practice, start python run.py.</p></div>`;}})();
