"""Optional UI check; requires Playwright + installed Chromium, not board dependencies."""
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from playwright.sync_api import sync_playwright

root=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as directory:
    admin,worker=secrets.token_urlsafe(36),secrets.token_urlsafe(36)
    port='18764'
    origin='http://127.0.0.1:'+port
    process=subprocess.Popen([sys.executable,'app.py'],cwd=root,stdout=subprocess.DEVNULL,
        env={**os.environ,'PORT':port,'BOARD_DB':directory+'/board.db','BOARD_ADMIN_TOKEN':admin,'BOARD_WORKER_TOKEN':worker})
    try:
        for _ in range(50):
            try:
                urllib.request.urlopen(origin+'/health',timeout=1).close();break
            except OSError:time.sleep(.1)
        else:raise RuntimeError('Server failed to become healthy')
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True,executable_path=shutil.which('chromium') or pw.chromium.executable_path,args=['--no-sandbox'])
            page=browser.new_page(viewport={'width':1440,'height':1100})
            errors=[]
            page.on('pageerror',lambda error:errors.append(str(error)))
            page.goto(origin)
            page.get_by_placeholder('Boss access token').fill(admin)
            page.get_by_role('button',name='Unlock →').click()
            page.locator('#unlock').wait_for(state='hidden')
            assert page.locator('.agent').count()==6
            page.get_by_role('button',name='＋ New project').click()
            page.locator('[name=title]').fill('UI integration fixture')
            page.locator('[name=brief]').fill('A small support ticket workspace with search and meaningful tests.')
            page.locator('[name=repository]').fill('example/ui-fixture')
            page.locator('[name=render_service]').fill('srv-fixture')
            page.get_by_role('button',name='Send to Product Manager →').click()
            page.get_by_text('Brief saved.',exact=False).wait_for()
            def post(action,data):
                req=urllib.request.Request(origin+'/api/worker/'+action,data=json.dumps(data).encode(),
                    headers={'Authorization':'Bearer '+worker,'Content-Type':'application/json'})
                return json.load(urllib.request.urlopen(req))['result']
            p=post('claim',{})
            post('complete',dict(id=p['id'],receipt=p['lease']['receipt'],result={'report':'FIXTURE — not live research. Sprint: implement a ticket workflow and test persistence.','files':{}}))
            page.get_by_role('button',name='Review decision →').wait_for(timeout=10000)
            page.get_by_role('button',name='Review decision →').click()
            page.get_by_role('button',name='Approve plan & start build').click()
            page.get_by_text('Decision saved to the audit log.').wait_for()
            page.get_by_role('button',name='⌘ Skills & connections').click()
            assert page.get_by_text('Probe · QA Engineer').is_visible()
            page.get_by_role('button',name='◫ Command center').click()
            page.screenshot(path='/tmp/crewboard-overview.png',full_page=True)
            page.set_viewport_size({'width':390,'height':844})
            assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), 'Mobile overflow'
            page.get_by_role('button',name='Lock workspace').click()
            assert page.locator('#unlock').is_visible()
            assert not errors,errors
            browser.close()
        print('Browser checks passed: unlock, six roles, brief submission, PM fixture, plan approval, skills, lock, mobile layout. Screenshot: /tmp/crewboard-overview.png')
    finally:
        process.terminate();process.wait(timeout=10)
