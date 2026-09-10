from __future__ import annotations

from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, unquote
import argparse
import copy
import importlib.metadata
import importlib.util
import json
import mimetypes
import os
import secrets
import sys
import threading
import webbrowser

from .engine import (ROOT, CATALOG, LESSONS, MAX_CODE, fingerprint, run_code,
                     reference_text, discussion_feedback)


def now():
    return datetime.now(timezone.utc).isoformat()


def empty_state():
    return {'version':1, 'drafts':{}, 'answers':{}, 'completed':{}, 'attempts':{},
            'results':{}, 'reviews':{}, 'revealed':[], 'bookmarks':[], 'activity':[], 'consent':False}


class Store:
    def __init__(self, path):
        self.path = path
        self.lock = threading.RLock()
        self.state = empty_state()
        if path.exists():
            try:
                self.state.update(json.loads(path.read_text(encoding='utf-8')))
            except (OSError, ValueError):
                backup = path.with_suffix('.unreadable.json')
                path.rename(backup)
                print(f'Unreadable progress backed up to {backup}')

    def persist(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        tmp = self.path.with_suffix('.tmp')
        tmp.write_text(json.dumps(self.state,ensure_ascii=False,indent=2), encoding='utf-8')
        tmp.replace(self.path)

    def snapshot(self):
        with self.lock:
            return copy.deepcopy(self.state)

    def record(self, lesson, success, method):
        id = lesson['id']
        self.state['attempts'][id] = self.state['attempts'].get(id,0)+1
        if success and id not in self.state['completed']:
            self.state['completed'][id] = {'at':now(),'method':method,'xp':lesson['xp']}
        self.state['activity'].append({'id':id,'at':now(),'success':success,'method':method})
        self.state['activity'] = self.state['activity'][-500:]


def public_catalog():
    value = copy.deepcopy(CATALOG)
    for lesson in value['lessons']:
        for key in ('correct','wrong','explanation','guide','cues'):
            lesson.pop(key,None)
    return value


def lesson_payload(lesson, store):
    value = copy.deepcopy(lesson)
    for key in ('correct','wrong','explanation','guide','cues'):
        value.pop(key,None)
    if lesson['kind']=='code':
        directory = ROOT/'packs'/lesson['pack']
        refs=[]
        if lesson['pack']=='guided':
            names=['models.py','text_tools.py','examples.py','README.md']
        elif lesson['pack']=='v2':
            names=['practice/models.py','practice/text.py','practice/sample_data.py',
                   'ARCHITECTURE_FOLLOWUPS.md','HINTS.md']
            number=lesson['file'].split('round')[1][:2]
            names += [str(path.relative_to(directory)) for path in (directory/'prompts').glob(number+'*.md')]
        elif lesson['pack']=='indexed':
            names=['README.md','models.py','storage.py','text_tools.py','demo.py']
        else:
            names=['README.md']
        for name in names:
            p=directory/name
            if p.exists(): refs.append({'name':name,'text':p.read_text(encoding='utf-8')})
        for name in lesson['tests']:
            refs.append({'name':name,'text':(directory/name).read_text(encoding='utf-8')})
        value['references']=refs
    return value


class LabHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


class Handler(BaseHTTPRequestHandler):
    server_version = 'JudgeLab/1.0'

    def log_message(self, format, *args):
        # Do not write submissions or personal answers to a log.
        if args and str(args[0]).startswith('POST /api/run'):
            print('Practice submission evaluated.')

    def allowed_hosts(self):
        return {f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'}

    def guard(self, write=False):
        if self.headers.get('Host','') not in self.allowed_hosts():
            self.respond({'error':'Only local host access is permitted.'},403)
            return False
        if write:
            origin=self.headers.get('Origin')
            if origin and origin not in {f'http://{host}' for host in self.allowed_hosts()}:
                self.respond({'error':'Cross-origin requests are rejected.'},403)
                return False
            if self.headers.get('X-Lab-Token') != self.server.token:
                self.respond({'error':'Session token missing or expired. Reload the app.'},403)
                return False
            if not self.headers.get('Content-Type','').startswith('application/json'):
                self.respond({'error':'JSON content is required.'},415)
                return False
        return True

    def security_headers(self):
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('X-Frame-Options','DENY')
        self.send_header('Referrer-Policy','no-referrer')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; font-src 'self'; object-src 'none'; frame-ancestors 'none'")

    def respond(self, value, status=200):
        data=json.dumps(value,ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.security_headers()
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length',str(len(data)))
        self.end_headers()
        try:self.wfile.write(data)
        except (BrokenPipeError,ConnectionResetError):pass

    def do_GET(self):
        if not self.guard():return
        path=unquote(urlsplit(self.path).path)
        if path=='/api/bootstrap':
            return self.respond({'catalog':public_catalog(),'state':self.server.store.snapshot(),
                                 'token':self.server.token,'python':sys.version.split()[0],
                                 'pytest':importlib.metadata.version('pytest'),'runner':'Local CPython + pytest',
                                 'execution_warning':'Your submitted Python runs with your user permissions. This is not a security sandbox. Run only your own trusted practice code; never expose this server to a network.'})
        if path.startswith('/api/lesson/'):
            id=path.rsplit('/',1)[-1]
            if id not in LESSONS:return self.respond({'error':'Unknown lesson'},404)
            return self.respond(lesson_payload(LESSONS[id],self.server.store))
        if path=='/api/export':
            return self.respond(self.server.store.snapshot())
        web=ROOT/'web'
        if path=='/':path='/index.html'
        file=(web/path.lstrip('/')).resolve()
        if not file.is_relative_to(web.resolve()) or not file.is_file():
            return self.respond({'error':'Not found'},404)
        data=file.read_bytes()
        self.send_response(200); self.security_headers()
        ctype=mimetypes.guess_type(file.name)[0] or 'application/octet-stream'
        if ctype in ('text/html','text/css','text/javascript','application/javascript'):ctype+='; charset=utf-8'
        self.send_header('Content-Type',ctype)
        self.send_header('Content-Length',str(len(data)));self.end_headers()
        try:self.wfile.write(data)
        except (BrokenPipeError,ConnectionResetError):pass

    def body(self):
        try:size=int(self.headers.get('Content-Length','0'))
        except ValueError:raise ValueError('Invalid body size')
        if not 0<size<=8_000_000:raise ValueError('Request must be between 1 byte and 8 MB.')
        value=json.loads(self.rfile.read(size))
        if not isinstance(value,dict):raise ValueError('Expected a JSON object.')
        return value

    def do_POST(self):
        if not self.guard(write=True):return
        path=urlsplit(self.path).path
        try:
            body=self.body()
            store=self.server.store
            if path=='/api/consent':
                with store.lock:
                    store.state['consent']=body.get('accepted') is True;store.persist()
                return self.respond({'ok':True})
            if path=='/api/import':
                incoming=body.get('state')
                if not isinstance(incoming,dict) or incoming.get('version')!=1:
                    raise ValueError('Not a JudgeLab version 1 backup.')
                fresh=empty_state()
                for id,answer in incoming.get('answers',{}).items():
                    if id in LESSONS and isinstance(answer,str) and len(answer)<=30000:fresh['answers'][id]=answer
                workspaces={x.get('workspace') for x in LESSONS.values() if x['kind']=='code'}
                for key,draft in incoming.get('drafts',{}).items():
                    if key in workspaces and isinstance(draft,dict) and isinstance(draft.get('text'),str) and len(draft['text'])<=MAX_CODE:
                        fresh['drafts'][key]={'text':draft['text'],'at':now()}
                for id,entry in incoming.get('completed',{}).items():
                    if id in LESSONS and isinstance(entry,dict):
                        fresh['completed'][id]={'at':str(entry.get('at',now())), 'method':str(entry.get('method','imported')),'xp':LESSONS[id]['xp']}
                for key in ['bookmarks','revealed']:
                    fresh[key]=[x for x in incoming.get(key,[]) if x in LESSONS]
                for id,count in incoming.get('attempts',{}).items():
                    if id in LESSONS and isinstance(count,int) and 0<=count<=100000:fresh['attempts'][id]=count
                with store.lock:
                    fresh['consent']=store.state['consent'];store.state=fresh;store.persist()
                return self.respond({'state':store.snapshot(),'message':'Drafts and achievements imported. Run tests again to validate the imported code.'})
            if path=='/api/bookmark':
                id=body.get('id')
                if id not in LESSONS:raise ValueError('Unknown activity')
                with store.lock:
                    marks=store.state['bookmarks']
                    if id in marks:marks.remove(id)
                    else:marks.append(id)
                    store.persist()
                return self.respond({'bookmarks':marks})
            id=body.get('id')
            if id not in LESSONS:raise ValueError('Unknown activity')
            lesson=LESSONS[id]
            if path=='/api/save':
                text=body.get('text')
                if not isinstance(text,str) or len(text)>MAX_CODE:raise ValueError('Draft is too large or not text')
                with store.lock:
                    at=now()
                    if lesson['kind']=='code':store.state['drafts'][lesson['workspace']]={'text':text,'at':at}
                    else:store.state['answers'][id]=text
                    store.persist()
                return self.respond({'ok':True,'at':at})
            if path=='/api/reveal':
                if store.state['attempts'].get(id,0)<1:raise ValueError('Make one attempt before opening the reference approach.')
                with store.lock:
                    if id not in store.state['revealed']:store.state['revealed'].append(id);store.persist()
                if lesson['kind']=='code':
                    return self.respond({'text':reference_text(lesson),'explanation':lesson['explanation'],
                                         'label':'One reference approach, newly added for practice. Not an official company solution.'})
                return self.respond({'text':lesson.get('guide',lesson.get('explanation','')),
                                     'label':'Discussion guidance for self-review. Not a verdict on your answer.'})
            if path=='/api/quiz':
                if lesson['kind']!='quiz':raise ValueError('This is not a quick check')
                choice=body.get('choice')
                if not isinstance(choice,int) or not 0<=choice<len(lesson['choices']):raise ValueError('Choose an answer first')
                success=choice==lesson['correct']
                result={'success':success,'choice':choice,'correct':lesson['correct'],'explanation':lesson['explanation'],
                        'tip':'' if success else lesson['wrong'][choice]}
                with store.lock:
                    store.record(lesson,success,'quiz');store.state['results'][id]=result;store.persist()
                return self.respond({'result':result,'state':store.snapshot()})
            if path=='/api/discussion':
                if lesson['kind']!='discussion':raise ValueError('This is not a discussion prompt')
                text=body.get('text','')
                result=discussion_feedback(lesson,text)
                with store.lock:
                    store.state['answers'][id]=text;store.record(lesson,False,'structure cues')
                    store.state['results'][id]=result;store.persist()
                return self.respond({'result':result,'state':store.snapshot()})
            if path=='/api/review':
                if lesson['kind']!='discussion':raise ValueError('Only discussion prompts use a self-review rubric')
                checks=body.get('checks',[])
                if not isinstance(checks,list) or len(checks)!=len(lesson['criteria']) or any(x not in ('yes','revise') for x in checks):
                    raise ValueError('Review every rubric point as met or needs work.')
                if not discussion_feedback(lesson,store.state['answers'].get(id,''))['can_review']:
                    raise ValueError('Write at least 25 words before marking a rehearsal reviewed.')
                with store.lock:
                    store.state['reviews'][id]={'checks':checks,'at':now()}
                    store.record(lesson,True,'self-reviewed rehearsal');store.persist()
                return self.respond({'state':store.snapshot(),'needs_work':checks.count('revise')})
            if path=='/api/run':
                if lesson['kind']!='code':raise ValueError('Only coding exercises run pytest')
                if not store.state['consent']:raise ValueError('Read and accept the local-code execution warning first.')
                if not self.server.run_lock.acquire(blocking=False):return self.respond({'error':'Another test run is active. Wait for it to finish.'},409)
                try:
                    code=body.get('text','')
                    result=run_code(lesson,code)
                    with store.lock:
                        store.state['drafts'][lesson['workspace']]={'text':code,'at':now()}
                        store.state['results'][id]=result;store.record(lesson,result['success'],'pytest');store.persist()
                    return self.respond({'result':result,'state':store.snapshot()})
                finally:self.server.run_lock.release()
            return self.respond({'error':'Unknown operation'},404)
        except (ValueError,TypeError,KeyError,json.JSONDecodeError) as error:
            return self.respond({'error':str(error)},400)
        except Exception as error:
            print(f'Local server error: {type(error).__name__}: {error}')
            return self.respond({'error':f'Local server error: {type(error).__name__}. See the terminal.'},500)


def check_environment():
    if sys.version_info<(3,13):
        raise SystemExit('Python 3.13 or newer is required. Create the venv using python3.13 (Windows: py -3.13).')
    missing=[name for name in ['pytest','pytest_asyncio','fastapi','httpx'] if importlib.util.find_spec(name) is None]
    if missing:
        raise SystemExit('Missing dependencies: '+', '.join(missing)+'\nRun: python -m pip install -r requirements.txt')
    return {'python':sys.version.split()[0], **{name:importlib.metadata.version(name) for name in ['pytest','pytest-asyncio','fastapi','httpx']}}


def main():
    parser=argparse.ArgumentParser(description='JudgeLab: local, single-user coding practice. Never expose to a network.')
    parser.add_argument('--port',type=int,default=8765)
    parser.add_argument('--no-browser',action='store_true')
    parser.add_argument('--check',action='store_true')
    parser.add_argument('--state-dir',type=Path,default=ROOT/'.judgelab')
    args=parser.parse_args()
    environment=check_environment()
    if args.check:
        print(json.dumps(environment,indent=2));return
    if not 1024<=args.port<=65535:raise SystemExit('Use a port between 1024 and 65535.')
    try:server=LabHTTPServer(('127.0.0.1',args.port),Handler)
    except OSError as error:raise SystemExit(f'Cannot start local server: {error}\nTry: python run.py --port 8766')
    server.store=Store(args.state_dir/'progress.json')
    server.token=secrets.token_urlsafe(32)
    server.run_lock=threading.Lock()
    url=f'http://127.0.0.1:{server.server_port}'
    print(f'\n  JudgeLab is ready → {url}\n  Python {environment["python"]} · real pytest · no API keys\n  Progress: {server.store.path}\n\n  Only submit your own trusted code. This runner is NOT a security sandbox.\n  Ctrl+C stops the app.\n',flush=True)
    if not args.no_browser:threading.Timer(0.5,lambda:webbrowser.open(url)).start()
    try:server.serve_forever()
    except KeyboardInterrupt:print('\nJudgeLab stopped. Your saved work is on disk.')
    finally:server.server_close()
