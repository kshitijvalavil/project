import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
import urllib.request
import urllib.error
from http.server import ThreadingHTTPServer
import app
import worker

class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = patch.object(app, 'DB_PATH', Path(self.temp.name)/'test.sqlite3')
        self.db.start()
        app.init_db()

    def tearDown(self):
        self.db.stop()
        self.temp.cleanup()

    def create(self):
        return app.mutate('create', dict(title='Help desk', brief='Private support tickets with search.',
            repository='example/helpdesk', render_service='srv-example123'), 'boss')

    def claim(self):
        return app.mutate('claim', {}, 'worker')

    def complete(self, project, **extra):
        return app.mutate('complete', dict(id=project['id'], receipt=project['lease']['receipt'],
            result=dict(report='Actual role report', files={}, **extra)), 'worker')

    def decide(self, p, decision='approve'):
        return app.mutate(decision, dict(id=p['id'], digest=p['review_digest']), 'boss')

    def release_review(self):
        self.create()
        p=self.complete(self.claim())
        self.decide(p)
        self.complete(self.claim())
        self.complete(self.claim())
        p=self.claim()
        return self.complete(p, passed=True, test_count=3, commit='a'*40, artifact_digest=app.digest(p['files']))

    def test_plan_gate_stops_claims_until_boss_approves(self):
        self.create()
        p=self.complete(self.claim())
        self.assertEqual(p['stage'],'plan_review')
        self.assertIsNone(self.claim())
        with self.assertRaises(ValueError):
            app.mutate('approve',dict(id=p['id'],digest=p['review_digest']),'worker')
        self.decide(p)
        self.assertEqual(self.claim()['stage'],'database')

    def test_stale_review_digest_is_denied(self):
        self.create(); p=self.complete(self.claim())
        with self.assertRaises(ValueError):
            app.mutate('approve',dict(id=p['id'],digest='old'),'boss')
        self.assertIsNone(self.claim())

    def test_only_one_live_lease(self):
        self.create(); self.claim()
        self.assertIsNone(self.claim())

    def test_stale_receipt_cannot_complete(self):
        self.create(); p=self.claim(); p['lease']['receipt']='forged'
        with self.assertRaises(ValueError): self.complete(p)

    def test_failed_task_requires_explicit_retry(self):
        self.create(); p=self.claim()
        app.mutate('fail',dict(id=p['id'],receipt=p['lease']['receipt'],error='Docker unavailable'),'worker')
        self.assertIsNone(self.claim())
        app.mutate('retry',dict(id=p['id']),'boss')
        self.assertIsNotNone(self.claim())

    def test_zero_tests_cannot_reach_deploy_review(self):
        self.create(); self.decide(self.complete(self.claim()))
        self.complete(self.claim());self.complete(self.claim());p=self.claim()
        for count in (0, -1, True):
            with self.assertRaises(ValueError):
                self.complete(p,passed=True,test_count=count,commit='a'*40,artifact_digest=app.digest(p['files']))

    def test_different_artifact_digest_is_denied(self):
        self.create();self.decide(self.complete(self.claim()))
        self.complete(self.claim());self.complete(self.claim());p=self.claim()
        with self.assertRaises(ValueError):
            self.complete(p,passed=True,test_count=2,commit='a'*40,artifact_digest='wrong')

    def test_release_gate_binds_exact_commit(self):
        p=self.release_review()
        self.assertEqual(p['stage'],'deploy_review')
        self.assertIsNone(self.claim())
        self.decide(p);p=self.claim()
        with self.assertRaises(ValueError):self.complete(p,verified=True,commit='b'*40)
        p=self.complete(p,verified=True,commit='a'*40)
        self.assertEqual(p['stage'],'deployed')
        self.assertEqual(len(p['approvals']),2)

    def test_rejection_stops_pipeline(self):
        self.create();p=self.complete(self.claim());self.decide(p,'reject')
        self.assertIsNone(self.claim())

    def test_duplicate_approval_is_denied(self):
        self.create();p=self.complete(self.claim());self.decide(p)
        with self.assertRaises(ValueError):self.decide(p)

    def test_artifact_paths_are_confined(self):
        for path in ('../secret.py','/tmp/secret.py','.git/config','a/../../app.py','a\\b.py','env.sh'):
            with self.subTest(path=path),self.assertRaises(ValueError):app.validate_files({path:'bad'})
        app.validate_files({'tests/test_app.py':'valid'})

    def test_restart_retains_state_and_events(self):
        p=self.create();app.init_db();state=app.snapshot()
        self.assertEqual(state['projects'][0]['id'],p['id'])
        self.assertEqual(len(state['events']),1)

    def test_qa_blocking_review_does_not_run_or_publish(self):
        with patch.object(worker,'model',return_value={'report':'Missing auth','blocking':True}), patch.object(worker,'test_and_publish') as publish:
            with self.assertRaises(ValueError): worker.execute({'stage':'testing'})
            publish.assert_not_called()

    def test_render_must_match_repo_and_disable_auto_deploy(self):
        p={'repository':'example/app'}
        for service in ({'repo':'https://github.com/other/app','autoDeploy':'no'}, {'repo':'https://github.com/example/app','autoDeploy':'yes'}):
            with self.assertRaises(ValueError):worker.check_service(p,service)
        worker.check_service(p,{'repo':'https://github.com/example/app','autoDeploy':'no'})

class HttpTests(unittest.TestCase):
    def setUp(self):
        WorkflowTests.setUp(self)
        self.env=patch.dict(os.environ,{'BOARD_ADMIN_TOKEN':'boss-test-token','BOARD_WORKER_TOKEN':'worker-test-token'})
        self.env.start()
        self.server=ThreadingHTTPServer(('127.0.0.1',0),app.Handler)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.url=f'http://127.0.0.1:{self.server.server_port}'

    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join();self.env.stop();WorkflowTests.tearDown(self)

    def http(self,path,token='',data=None):
        req=urllib.request.Request(self.url+path, data=None if data is None else json.dumps(data).encode(),
            headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(req) as res:return res.status,json.load(res)
        except urllib.error.HTTPError as exc:return exc.code,json.load(exc)

    def test_http_read_requires_auth(self):
        self.assertEqual(self.http('/api/state')[0],401)
        self.assertEqual(self.http('/api/state','boss-test-token')[0],200)
        self.assertEqual(self.http('/health')[0],200)

    def test_http_worker_cannot_approve_or_create(self):
        for path in ('/api/approve','/api/create','/api/reject','/api/retry'):
            self.assertEqual(self.http(path,'worker-test-token',{})[0],403)

    def test_http_boss_cannot_impersonate_worker(self):
        self.assertEqual(self.http('/api/worker/claim','boss-test-token',{})[0],403)

    def test_http_create_claim_complete_and_approve(self):
        status,body=self.http('/api/create','boss-test-token',dict(title='Test',brief='A useful test app',repository='example/repo',render_service='srv-example'))
        self.assertEqual(status,200)
        _,body=self.http('/api/worker/claim','worker-test-token',{})
        p=body['result']
        status,body=self.http('/api/worker/complete','worker-test-token',dict(id=p['id'],receipt=p['lease']['receipt'],result={'report':'Sprint plan: one useful flow with tests','files':{}}))
        self.assertEqual(status,200);p=body['result']
        status,body=self.http('/api/approve','boss-test-token',dict(id=p['id'],digest=p['review_digest']))
        self.assertEqual(status,200);self.assertEqual(body['result']['stage'],'database')

if __name__=='__main__':unittest.main()
