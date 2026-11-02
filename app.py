"""Crewboard: a small approval control plane. Python standard library only."""
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from datetime import datetime, timezone

ROOT = Path(__file__).parent
DB_PATH = Path(os.environ.get('BOARD_DB', str(ROOT / '.data/board.sqlite3')))
ROLES = [
    dict(id='boss', name='You', title='Boss / approval authority', symbol='B', skills=['Plan review', 'Release approval'], tools=['Approval queue']),
    dict(id='pm', name='Atlas', title='Product Manager', symbol='A', skills=['Research & evidence', 'Sprint planning', 'Acceptance criteria'], tools=['Research playbook', 'Model API']),
    dict(id='database', name='Schema', title='Database Engineer', symbol='S', skills=['Data modeling', 'Migrations', 'Query design'], tools=['SQL playbook', 'Model API']),
    dict(id='engineer', name='Forge', title='Full-stack Engineer', symbol='F', skills=['Frontend & backend', 'Accessibility', 'API contracts'], tools=['Engineering playbook', 'Model API', 'Git']),
    dict(id='tester', name='Probe', title='QA Engineer', symbol='P', skills=['Regression tests', 'Failure analysis', 'Release evidence'], tools=['QA playbook', 'Docker sandbox', 'unittest']),
    dict(id='shipit', name='ShipIt', title='Release Engineer', symbol='↑', skills=['Render deployments', 'Smoke checks', 'Release reports'], tools=['Render API', 'Git commit pinning']),
]
STAGES = {'planning': 'pm', 'database': 'database', 'building': 'engineer', 'testing': 'tester', 'deploying': 'shipit'}

def now():
    return datetime.now(timezone.utc).isoformat()

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH, timeout=15)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    with connect() as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY, data TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY, project_id TEXT, at TEXT, message TEXT);
        ''')

def save(db, p, message):
    p['updated_at'] = now()
    db.execute('INSERT OR REPLACE INTO projects VALUES (?,?)', (p['id'], json.dumps(p)))
    db.execute('INSERT INTO events(project_id,at,message) VALUES (?,?,?)', (p['id'], now(), message))

def load(db, pid):
    row = db.execute('SELECT data FROM projects WHERE id=?', (pid,)).fetchone()
    if not row:
        raise ValueError('Project not found')
    return json.loads(row['data'])

def snapshot():
    with connect() as db:
        projects = [json.loads(r[0]) for r in db.execute('SELECT data FROM projects ORDER BY rowid DESC')]
        events = [dict(r) for r in db.execute('SELECT * FROM events ORDER BY id DESC LIMIT 60')]
    return dict(projects=projects, events=events, roles=ROLES,
                mode='Live control plane · external worker required',
                research=dict(status='blocked', url='https://www.hrudvibandla.com/projects',
                              note='Site could not be fetched from the setup environment. No projects have been reviewed.'))

def text(data, key, limit=30000):
    value = data.get(key, '')
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(f'{key} must be nonempty text (max {limit} characters)')
    return value.strip()

def validate_files(files):
    if not isinstance(files, dict) or len(files) > 40:
        raise ValueError('files must be an object with at most 40 files')
    for name, content in files.items():
        path = Path(name)
        if (not name or '\\' in name or path.is_absolute() or '..' in path.parts
            or any(part.startswith('.') for part in path.parts)
            or len(name) > 180 or not isinstance(content, str) or len(content) > 60000):
            raise ValueError('Unsafe artifact path or oversized file')
        if path.suffix not in {'.py', '.html', '.css', '.js', '.sql', '.md', '.json', '.txt', '.yaml', '.yml'}:
            raise ValueError('Unsupported artifact type')

def mutate(action, data, actor):
    """All workflow transitions are checked under a SQLite write transaction."""
    with connect() as db:
        db.execute('BEGIN IMMEDIATE')
        if action == 'create' and actor == 'boss':
            import re
            repo = text(data, 'repository', 150)
            if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repo):
                raise ValueError('Repository must be owner/repository on GitHub')
            service = text(data, 'render_service', 100)
            if not re.fullmatch(r'srv-[a-z0-9]+', service):
                raise ValueError('Use the Render service ID beginning srv-')
            p = dict(id=secrets.token_hex(8), title=text(data, 'title', 150), brief=text(data, 'brief'),
                     repository=repo, render_service=service, stage='planning', results={}, approvals=[],
                     files={}, lease=None, error=None, created_at=now())
            save(db, p, 'Boss submitted a brief. Product Manager queued.')
            return p
        if action == 'claim' and actor == 'worker':
            # One worker per project; expired work is reclaimed with a new receipt.
            import time
            for row in db.execute('SELECT data FROM projects ORDER BY rowid'):
                p = json.loads(row[0])
                lease = p.get('lease')
                if p['stage'] in STAGES and not p.get('error') and (not lease or lease['expires'] < time.time()):
                    p['lease'] = dict(receipt=secrets.token_hex(24), expires=time.time()+1800)
                    save(db, p, f"{STAGES[p['stage']]} worker claimed task")
                    return p
            return None
        p = load(db, text(data, 'id', 40))
        stage = p['stage']
        if action in ('approve', 'reject') and actor == 'boss':
            if stage not in ('plan_review', 'deploy_review'):
                raise ValueError('No approval is pending')
            if not hmac.compare_digest(str(data.get('digest', '')), p['review_digest']):
                raise ValueError('Review changed. Refresh and read the latest artifact.')
            p['approvals'].append(dict(gate=stage, decision=action, digest=p['review_digest'], at=now()))
            p['stage'] = ('database' if stage == 'plan_review' else 'deploying') if action == 'approve' else 'rejected'
            p['lease'] = None
            save(db, p, f'Boss {action}d {stage.replace("_", " ")}')
            return p
        if action in ('complete', 'fail') and actor == 'worker':
            import time
            lease = p.get('lease')
            if (stage not in STAGES or not lease or lease['expires'] < time.time()
                or not hmac.compare_digest(str(data.get('receipt', '')), lease['receipt'])):
                raise ValueError('Worker receipt missing, stale, or expired')
            if action == 'fail':
                p['error'] = text(data, 'error', 4000)
                p['lease'] = None
                save(db, p, 'Worker blocked. See project error; no automatic retry or deployment.')
                return p
            result = data.get('result')
            if not isinstance(result, dict):
                raise ValueError('result must be an object')
            text(result, 'report', 60000)
            files = result.get('files', {})
            validate_files(files)
            if stage in ('planning', 'deploying') and files:
                raise ValueError('This role cannot change implementation files')
            if stage == 'testing':
                if files:
                    raise ValueError('QA cannot change the tested artifact in its final result')
                import re
                if result.get('passed') is not True or type(result.get('test_count')) is not int or result['test_count'] < 1:
                    raise ValueError('Passing executed tests with a nonzero count are required')
                if not re.fullmatch(r'[0-9a-f]{40}', str(result.get('commit', ''))):
                    raise ValueError('QA must supply the exact tested Git commit')
                if result.get('artifact_digest') != digest(p['files']):
                    raise ValueError('QA tested a different artifact')
            if stage == 'deploying':
                qa = p['results']['testing']
                if result.get('commit') != qa['commit'] or result.get('verified') is not True:
                    raise ValueError('Deployment must verify the approved commit')
            p['results'][stage] = result
            p['files'].update(files)
            p['stage'] = {'planning':'plan_review', 'database':'building', 'building':'testing', 'testing':'deploy_review', 'deploying':'deployed'}[stage]
            p['lease'] = None
            if p['stage'] in ('plan_review', 'deploy_review'):
                p['review_digest'] = digest(dict(brief=p['brief'], repository=p['repository'], render_service=p['render_service'], results=p['results'], files=p['files']))
            save(db, p, f'{stage} complete → {p["stage"]}')
            return p
        if action == 'retry' and actor == 'boss' and p.get('error'):
            p['error'] = None
            p['lease'] = None
            save(db, p, 'Boss requeued the blocked task')
            return p
        raise ValueError('Action not allowed for this role or workflow stage')

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass  # Never log authorization headers or request bodies.

    def send(self, status, body, mime='application/json'):
        encoded = json.dumps(body).encode() if mime == 'application/json' else body
        self.send_response(status)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(encoded)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")
        self.end_headers()
        self.wfile.write(encoded)

    def actor(self):
        token = self.headers.get('Authorization', '').removeprefix('Bearer ')
        for role, name in [('boss', 'BOARD_ADMIN_TOKEN'), ('worker', 'BOARD_WORKER_TOKEN')]:
            expected = os.environ.get(name, '')
            if expected and hmac.compare_digest(expected, token):
                return role
        return None

    def do_GET(self):
        if self.path == '/health':
            self.send(200, {'status':'ok'})
        elif self.path == '/api/state':
            if not self.actor():
                return self.send(401, {'error':'Unlock with your Boss access token'})
            self.send(200, snapshot())
        elif self.path in ('/', '/app.js', '/style.css'):
            name, mime = {'/':('index.html','text/html; charset=utf-8'), '/app.js':('app.js','text/javascript'), '/style.css':('style.css','text/css')}[self.path]
            self.send(200, (ROOT/'static'/name).read_bytes(), mime)
        else:
            self.send(404, {'error':'Not found'})

    def do_POST(self):
        actor = self.actor()
        if not actor:
            return self.send(401, {'error':'Authentication required'})
        actions = {'/api/create':'create', '/api/approve':'approve', '/api/reject':'reject', '/api/retry':'retry',
                   '/api/worker/claim':'claim', '/api/worker/complete':'complete', '/api/worker/fail':'fail'}
        action = actions.get(self.path)
        if not action:
            return self.send(404, {'error':'Not found'})
        if (action in ('claim','complete','fail')) != (actor == 'worker'):
            return self.send(403, {'error':'This credential cannot perform that action'})
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if size < 0 or size > 1500000:
                return self.send(413, {'error':'Request too large'})
            data = json.loads(self.rfile.read(size))
            if not isinstance(data, dict):
                raise ValueError('JSON object required')
            result = mutate(action, data, actor)
            self.send(200, {'result':result})
        except (ValueError, TypeError) as exc:
            self.send(400, {'error':str(exc)})
        except Exception:
            self.send(500, {'error':'Internal error; inspect server configuration'})

def main():
    admin, worker = os.environ.get('BOARD_ADMIN_TOKEN', ''), os.environ.get('BOARD_WORKER_TOKEN', '')
    if len(admin) < 32 or len(worker) < 32 or admin == worker:
        raise SystemExit('Set distinct BOARD_ADMIN_TOKEN and BOARD_WORKER_TOKEN values, each at least 32 characters.')
    init_db()
    server = ThreadingHTTPServer((os.environ.get('HOST','127.0.0.1'), int(os.environ.get('PORT','8000'))), Handler)
    print('Crewboard listening; no model or deployment runs without a connected worker.', flush=True)
    server.serve_forever()

if __name__ == '__main__':
    main()
