# A portfolio that shows engineering depth

These recommendations are independent of Hrudvi Bandla's work. The provided URL is https://www.hrudvibandla.com/projects. Fetching it with approved network access received HTTP 403 at the proxy CONNECT tunnel; the domain is not in the active allowlist. The needed domains are saved in the environment draft, not yet applied. No project names, features, stacks, metrics, repos or demos on that site have been verified. There is no completed project-by-project review yet.

## Recommended sequence

| Project | First useful release | Skills to learn | Evidence worth showing |
| --- | --- | --- | --- |
| Crewboard agent studio | Human plan/release gates, durable jobs, role artifacts, isolated test runner | State machines, APIs, SQLite transactions, job leases, agent tool boundaries, CI/CD | A denied unauthorized approval, restart-safe audit history, executed test report, approved commit matching deployment |
| Support triage workspace | Import sample tickets, label and route them, review suggested responses | Async jobs, retrieval/search, structured model outputs, privacy, evaluation | A held-out labeled dataset, routing accuracy and confusion matrix, latency/cost measurements, failure examples |
| Data quality monitor | CSV import, schema inference with review, validation rules and quality history | SQL, streaming imports, constraints, query performance, visualizations | Messy public fixtures, explained violations, reproducible import benchmarks, query plans |
| Application tracker | Private applications board, reminders, interview notes, funnel and CSV export | Authentication, authorization, CRUD, scheduling, accessibility, deletion/export | Two-user isolation tests, accessible keyboard flow, export/delete tests, useful product walkthrough |

Start with one strong product and its case study. Add a second project to demonstrate data engineering or AI evaluation, rather than three variations of a chat interface. Original requirements, clear tradeoffs and measured results matter more than copying a feature list.

## Suggested learning sprints

1. Product and data foundation: define users and success criteria; write a small API contract; diagram entities; learn SQL constraints and migrations. Outcome: a PM packet and a tested data layer.
2. Working vertical slice: implement a single complete user flow, including validation and error states; connect accessible UI to API. Outcome: a repeatable local demonstration.
3. Trust and automation: add permissions, meaningful regression tests, job failure/retry handling and logs. Outcome: evidence that failure paths work.
4. Release and explain: stage on Render, run checks, write rollback notes and a case study. Outcome: demo, architecture diagram, test evidence and measured limitations.

## Public-reference research method

Once access works, inventory **every** project listed on the portfolio, follow its public details/demo/repository links, and record each source and observation date. For each project prepare:

- Problem, intended user, feature inventory, user journey and observed UI behavior.
- Actual public stack evidence (README, package manifests, deployment metadata) versus architectural hypotheses.
- Data model and API contracts inferred from visible behavior, with confidence labels.
- Background processing, integrations, access control, tests, deployment and likely failure modes.
- What cannot be known without source access, and how to test each hypothesis.
- A clean-room implementation plan with original branding, code and a meaningful differentiator.

Public behavior supports a reconstruction hypothesis; it cannot establish private source code, exact database schema or proprietary algorithms. Do not copy private code or pretend guesses are findings. If the site remains inaccessible, the project list plus public repository/demo links or a saved page can unblock the inventory.
