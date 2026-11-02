'use strict';
let token = '', state = {projects:[],events:[],roles:[]}, view = 'overview';
const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const labels = {planning:'PM queued',plan_review:'Plan approval',database:'Database queued',building:'Engineering queued',testing:'QA queued',deploy_review:'Release approval',deploying:'Deployment queued',deployed:'Deployed · review ready',rejected:'Rejected'};
const roles = [{id:'boss',name:'You',title:'Boss / approval authority',symbol:'B'}, {id:'pm',name:'Atlas',title:'Product Manager',symbol:'A'}, {id:'database',name:'Schema',title:'Database Engineer',symbol:'S'}, {id:'engineer',name:'Forge',title:'Full-stack Engineer',symbol:'F'}, {id:'tester',name:'Probe',title:'QA Engineer',symbol:'P'}, {id:'shipit',name:'ShipIt',title:'Release Engineer',symbol:'↑'}];
const stageRole = {planning:'pm',database:'database',building:'engineer',testing:'tester',deploying:'shipit'};
const recommendations = [
 ['Agent development studio','Build this first. Show approval gates, durable jobs, test evidence, and a shipped product. Your workflow becomes your first case study.',['Agent orchestration','Full stack','Deployment']],
 ['Support triage workspace','Turn incoming support requests into searchable tickets with suggested categories, human review, and response drafts. Measure routing accuracy against a labeled evaluation set.',['LLM evaluation','Search','Background jobs']],
 ['Data quality monitor','Import a CSV, validate its schema, flag missing or duplicate records, and track quality over time. Start with explainable rules before adding AI.',['SQL','Data pipelines','Charts']],
 ['Application & interview tracker','Manage applications, reminders, interview notes, and an outcomes funnel. Use a private data model and export/delete controls.',['CRUD','Privacy','Analytics']]
];
function notice(message, error=false) { $('#notice').className=error?'error':'success'; $('#notice').textContent=message; }
async function api(path, data) {
 const response = await fetch(path,{method:data===undefined?'GET':'POST',headers:{'Authorization':'Bearer '+token,'Content-Type':'application/json'},...(data===undefined?{}:{body:JSON.stringify(data)})});
 const body=await response.json(); if(!response.ok) throw Error(body.error || 'Request failed'); return body;
}
async function refresh() {
 if(!token) return;
 try { state=await api('/api/state'); $('#unlock').hidden=true; render(); }
 catch(e) { notice(e.message,true); }
}
function team() {
 return `<div class="section-heading"><h2>Meet your crew <span> / 6 roles, one shared mission</span></h2><span>Worker receipts show actual activity</span></div><div class="team-grid">${(state.roles.length?state.roles:roles).map(r=>{
 const tasks=state.projects.filter(p=>stageRole[p.stage]===r.id);
 const active=tasks.some(p=>p.lease && p.lease.expires*1000>Date.now()&&!p.error);
 const status=r.id==='boss'?'Decision maker':active?'Task claimed':tasks.length?'Queued / needs worker':'No active task';
 return `<article class="agent"><div class="agent-head"><div class="avatar ${r.id==='boss'?'boss':''}">${esc(r.symbol)}</div><span class="pill ${active?'live':''}">${status}</span></div><h3>${esc(r.name)}</h3><p class="title">${esc(r.title)}</p><div class="agent-bottom">${r.id==='boss'?'Final say on <b>plans & releases</b>':active?'<b>Claimed task</b> · result pending':`<b>${tasks.length} queued</b> · execution requires worker`}</div></article>`;
 }).join('')}</div>`;
}
function projectCard(p) {
 return `<article class="project"><span class="pill ${p.stage.endsWith('review')?'wait':''}">${esc(labels[p.stage]||p.stage)}</span><h3>${esc(p.title)}</h3><p>${esc(p.brief.slice(0,160))}</p>${p.error?`<p class="error">${esc(p.error)}</p>`:''}<div class="actions"><button class="quiet" data-report="${p.id}">Open research & artifacts ↗</button>${p.error?`<button class="quiet" data-retry="${p.id}">Retry blocked task</button>`:''}${p.stage.endsWith('review')?`<button class="primary" data-report="${p.id}">Review decision →</button>`:''}</div></article>`;
}
function library() {
 const items=[
 ['Atlas · Product Manager','Custom playbook: evidence log, user journeys, MVP scope, acceptance criteria, sprint estimates, risk register. Never treats an inaccessible source as researched.','Linear for sprint tracking; Notion for specifications; Playwright for inspecting public demos.',['https://linear.app/integrations','https://www.notion.com/integrations','https://playwright.dev/']],
 ['Forge · Full-stack Engineer','Custom playbook: API contracts, accessible UI, error states, tests, and readable implementation. First runner supports dependency-free Python + SQLite + vanilla web.','Official model APIs and SDKs; GitHub Apps with access to a dedicated repository.',['https://platform.openai.com/docs','https://docs.github.com/en/apps']],
 ['Schema · Database Engineer','Custom playbook: entity relationships, indexes, constraints, migrations, privacy, and rollback notes. No production SQL execution.','SQLite documentation now; managed PostgreSQL on Render when the data model needs it.',['https://www.sqlite.org/docs.html','https://render.com/docs/postgresql']],
 ['Probe · QA Engineer','Custom playbook: acceptance-to-test mapping, boundary cases, regression risks. Worker executes tests separately in a network-isolated Docker container.','unittest is integrated; Playwright and axe-core are recommended next for browser and accessibility tests.',['https://docs.python.org/3/library/unittest.html','https://playwright.dev/','https://github.com/dequelabs/axe-core']],
 ['ShipIt · Release Engineer','Custom playbook: exact-commit deployment, disabled automatic deploys, health verification, release notes, rollback plan.','Render REST API is wired in the optional worker; needs your service and key.',['https://render.com/docs/api','https://dashboard.render.com/u/settings#api-keys']],
 ['Boss · You','Approve the research and plan before building; approve the exact tested commit before release. Agents cannot call approval endpoints.','Two distinct credentials separate Boss access from worker access. Optional integrations above are recommendations, not installed plugins.',['https://dashboard.render.com/','https://platform.openai.com/api-keys']]
 ];
 return `<div class="section-heading"><h2>Skills with a job to do.</h2><span>Custom playbooks included · external connections optional</span></div><div class="library-grid">${items.map(([name,custom,external,links])=>`<article class="panel"><h3>${name}</h3><p>${custom}</p><p>${external}</p>${links.map((url,i)=>`<a href="${url}" target="_blank" rel="noopener noreferrer">Official source ${i+1} ↗</a>`).join('')}</article>`).join('')}</div><div class="research"><strong>Choose skills by provenance, not popularity.</strong><p>Start with vendor documentation and official GitHub organizations. Pin package versions, inspect permissions and source, and trial a skill in a disposable repository. A marketplace listing alone does not establish trust. Crewboard’s custom playbooks are in skills/.</p></div>`;
}
function render() {
 const pending=state.projects.filter(p=>['plan_review','deploy_review'].includes(p.stage));
 $('#approval-count').textContent=pending.length;
 $('#breadcrumb').textContent={overview:'Command center',projects:'Projects & sprints',approvals:'Approvals',library:'Skills & connections'}[view];
 document.querySelectorAll('.nav').forEach(n=>n.classList.toggle('active',n.dataset.view===view));
 let html='';
 if(view==='overview') {
 html=`<div class="stats"><div class="stat"><small>Projects in motion</small><strong>${state.projects.filter(p=>!['deployed','rejected'].includes(p.stage)).length}</strong><span>Your next portfolio starts here</span></div><div class="stat"><small>Waiting on you</small><strong>${pending.length.toString().padStart(2,'0')}</strong><span>Plan and release decisions</span></div><div class="stat"><small>Agent roles</small><strong>05 <span>+ you</span></strong><span>Separate roles · shared context</span></div><div class="stat"><small>Verified deployments</small><strong>${state.projects.filter(p=>p.stage==='deployed').length.toString().padStart(2,'0')}</strong><span>Exact commit + smoke check</span></div></div>${team()}<div class="split"><section><div class="section-heading"><h2>On your desk</h2><span>Approval queue</span></div><div class="panel">${pending.length?pending.map(projectCard).join(''):'<div class="empty"><strong>A clear desk. A fresh start.</strong>When a plan or release is ready, it lands here for your review.</div>'}</div></section><section><div class="section-heading"><h2>Team activity</h2><span>Live · refreshes every 5s</span></div><div class="panel">${state.events.length?state.events.slice(0,5).map(e=>`<div class="event">${esc(e.message)}<time>${esc(new Date(e.at).toLocaleString())}</time></div>`).join(''):'<div class="empty"><strong>No activity yet</strong>Submit a brief and connect a worker to begin.</div>'}</div></section></div><div class="research"><strong>↗ Reference research · awaiting source access</strong><p>The setup environment could not reach <a href="https://www.hrudvibandla.com/projects" target="_blank" rel="noopener noreferrer">hrudvibandla.com/projects</a>. Its project inventory and technical breakdowns are pending. Recommendations below are independent ideas, not claims about that portfolio.</p></div><div class="section-heading"><h2>Your portfolio shortlist</h2><span>Build depth before breadth</span></div><div class="panel">${recommendations.map(([title,description,tags],i)=>`<div class="recommendation"><span class="number">0${i+1}</span><div><h3>${title}</h3><p>${description}</p>${tags.map(t=>`<span class="tag">${t}</span>`).join('')}</div></div>`).join('')}</div>`;
 } else if(view==='library') html=library();
 else if(view==='approvals') html=`<div class="section-heading"><h2>Your approval is the gate.</h2></div>${pending.length?pending.map(projectCard).join(''):'<div class="panel empty"><strong>No decisions waiting</strong>Read the PM plan before build approval. Read test evidence before deployment approval.</div>'}`;
 else html=`<div class="section-heading"><h2>From brief to shipped.</h2><span>Projects persist in SQLite</span></div><div class="board-columns">${[['Plan',['planning','plan_review']],['Build & test',['database','building','testing']],['Release',['deploy_review','deploying','deployed','rejected']]].map(([title,stages])=>`<section class="column"><h3>${title.toUpperCase()}</h3>${state.projects.filter(p=>stages.includes(p.stage)).map(projectCard).join('')||'<div class="empty">No projects here yet.</div>'}</section>`).join('')}</div>`;
 $('#content').innerHTML=html;
}
function review(id) {
 const p=state.projects.find(p=>p.id===id); if(!p) return;
 $('#review-content').innerHTML=`<div class="eyebrow">${esc(labels[p.stage])}</div><h2>${esc(p.title)}</h2><p>${esc(p.brief)}</p><p>Repository: ${esc(p.repository)} · Render: ${esc(p.render_service)}</p>${Object.entries(p.results).map(([stage,r])=>`<h3>${esc(stage)}</h3><pre>${esc(r.report)}</pre>${r.commit?`<p>Commit: <code>${esc(r.commit)}</code> · ${esc(r.test_count ?? 'Deployment')} tests / verification</p>`:''}`).join('')}${Object.entries(p.files).map(([name,content])=>`<details><summary>${esc(name)}</summary><pre>${esc(content)}</pre></details>`).join('')}${p.stage.endsWith('review')?`<p class="hint">Decision is bound to review digest ${esc(p.review_digest)}. Approval starts ${p.stage==='plan_review'?'implementation':'deployment of the tested commit'}.</p><div class="dialog-actions"><button class="quiet" data-decision="reject" data-id="${p.id}" data-digest="${p.review_digest}">Reject</button><button class="primary" data-decision="approve" data-id="${p.id}" data-digest="${p.review_digest}">${p.stage==='plan_review'?'Approve plan & start build':'Approve deployment'}</button></div>`:''}`;
 $('#review-dialog').showModal();
}
$('#login').addEventListener('submit',async e=>{e.preventDefault();token=$('#token').value;$('#token').value='';await refresh();});
$('#lock').addEventListener('click',()=>{token='';state={projects:[],events:[],roles:[]};$('#unlock').hidden=false;$('#review-dialog').close();$('#project-dialog').close();$('#review-content').textContent='';$('#notice').textContent='';render();});
$('#new-project').addEventListener('click',()=>{if(!token) return notice('Unlock the workspace first.',true);$('#project-dialog').showModal();});
$('#cancel').addEventListener('click',()=>$('#project-dialog').close());
$('#close-review').addEventListener('click',()=>$('#review-dialog').close());
$('#project-form').addEventListener('submit',async e=>{e.preventDefault();const button=e.submitter;button.disabled=true;try{await api('/api/create',Object.fromEntries(new FormData(e.target)));$('#project-dialog').close();e.target.reset();notice('Brief saved. The PM task is queued; a connected worker must claim it.');await refresh();}catch(e){notice(e.message,true);}finally{button.disabled=false;}});
document.addEventListener('click',async e=>{
 const target=e.target.closest('button');if(!target)return;
 if(target.dataset.view){view=target.dataset.view;render();}
 if(target.dataset.report)review(target.dataset.report);
 if(target.dataset.retry){try{await api('/api/retry',{id:target.dataset.retry});await refresh();}catch(e){notice(e.message,true);}}
 if(target.dataset.decision){target.disabled=true;try{await api('/api/'+target.dataset.decision,{id:target.dataset.id,digest:target.dataset.digest});$('#review-dialog').close();notice('Decision saved to the audit log.');await refresh();}catch(e){notice(e.message,true);}finally{target.disabled=false;}}
});
setInterval(refresh,5000);render();
