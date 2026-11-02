# Connect the crew

## What is built and what is not verified

The board is a working Python/SQLite control plane. The optional worker contains real model, Docker-test, Git-push and Render API code. All 18 workflow/HTTP tests passed locally and in the offline Docker sandbox, and browser checks passed. Read-only Git access works with approved socket access. Model calls, Git pushes and Render releases have not been live-tested; no model/Render keys are configured. Passing local fixture tests does not establish a live autonomous run. Browser automation for generated projects, revision loops after QA failure, team login, per-agent scoped worker tokens and spend metering are future work. Failed tasks stop for diagnosis; they are not automatically repaired.

The first worker intentionally supports small **Python standard-library + SQLite + vanilla-web** projects. Broader stacks need a reviewed test image and runner; changing a prompt alone is insufficient. Five agents are separate role invocations sharing explicit artifacts, not five independently authenticated services. Boss access is separate. The model cannot approve plans or releases.

## Run locally

Python 3.12+ is the only board dependency. From the repository root:

```sh
python -m unittest discover -s tests -v
python dev.py
```

`dev.py` creates two random access tokens in ignored `.data/local-tokens.json` on first run, reuses them on restart, binds loopback, and starts the board. Retrieve only the admin token privately from that file to unlock the browser; never commit or share it. The worker token goes only to a trusted worker. In cloud onboarding, local URLs are internal checks, not supported public previews.

## Host the board on Render

1. Push this repository to your GitHub account using your normal authenticated Git workflow. No push or paid deployment has been performed in this session.
2. Open [Render Blueprints](https://dashboard.render.com/select-repo?type=blueprint), connect the repository and review `render.yaml`. It specifies a paid Starter service and a persistent 1 GB disk; confirm current pricing at [Render pricing](https://render.com/pricing) before applying. The disk is required for SQLite durability. Do not remove it to use an ephemeral free service for real projects.
3. Deploy the board, then use its Render service **Environment** page to retrieve `BOARD_ADMIN_TOKEN` privately and unlock it. Keep `BOARD_WORKER_TOKEN` separate. Do not paste secrets into chat. Render creates the values automatically.

The board uses a single process/service with SQLite. Do not scale to multiple independent disks. The board's `/health` confirms process health, not model or worker readiness.

## Connect a dedicated worker (one-time setup)

Use a dedicated VM or development machine with Python 3.12, Git and a working Docker daemon. **Do not expose the Docker socket on the public board host.** The worker is highly trusted and must have access only to dedicated generated-project repositories and Render services. Docker is defense in depth, not a guarantee against hostile code; do not run untrusted multi-tenant jobs on your personal computer.

Create a separate GitHub repository and a separate target Render service for the application the agents will build. Configure its build/start commands for Python (`python app.py`), and disable automatic deploys. The board's host service is not this target. Provision the repo with an initial README commit. Avoid credentials or personal data in target checkouts.

Put these values into the worker machine's secret/environment manager:

| Variable | Where to obtain / meaning |
| --- | --- |
| `BOARD_URL` | The HTTPS URL of the deployed board |
| `BOARD_WORKER_TOKEN` | Board Render service → Environment; never use the Boss token |
| `OPENAI_API_KEY` | [OpenAI API keys](https://platform.openai.com/api-keys); API billing is separate from a ChatGPT subscription |
| `AGENT_MODEL` | Optional model supporting Chat Completions JSON mode; default `gpt-4.1`; confirm account availability and pricing |
| `RENDER_API_KEY` | [Render account settings](https://dashboard.render.com/u/settings#api-keys) |
| `ALLOWED_REPOSITORIES` | Comma-separated dedicated `owner/repository` targets, no spaces |
| `WORKER_DIR` | Optional private local working directory, outside the source checkout |
| `TEST_IMAGE` | Optional reviewed Python image; default is the official Python 3.12 slim digest verified during setup |

Authenticate Git for read/write access to only the target repositories using [GitHub CLI](https://cli.github.com/) or a narrowly scoped [GitHub App](https://docs.github.com/en/apps). The worker uses normal Git HTTPS authentication; it never extracts or writes a token. Use an account-level Render key only on the trusted worker; fine-grained credential isolation is a future improvement.

Pull the verified test image once and confirm Docker health, then start the worker from this repository:

```sh
docker info
docker pull python:3.12-slim
python worker.py
```

Use a service manager for unattended operation. Only one worker should process a project at a time. Leases expire after 30 minutes and use unique receipts. A worker crash during an external side effect still needs reconciliation: inspect the existing Git branch or Render deployment before retrying. The first runner does not provide exactly-once external side effects.

Submit a brief in the board. The PM invokes the model, then stops. Read its evidence, unknowns and sprint plan before approving. DB and full-stack roles generate files. QA reviews them and the worker runs real tests in an offline Docker container. The tested source is committed to `crewboard/<project-id>` and pushed only when Render automatic deployment is disabled. Review the test report and immutable commit; approve deployment. ShipIt requests that exact commit, checks Render's result, then makes an HTTP smoke request. Perform your own product acceptance review after deployment.

API calls incur model costs. One successful sprint uses four model calls (PM, database, engineering, QA); deployment uses deterministic API calls. Output limits bound each call but are not a dollar budget. Set provider project spending limits/alerts before connecting the worker. Research is restricted to supplied material in this runner: it has no web-search tool. Read blocked-source warnings before approving a plan.

## Legitimate skills and plugins

Custom role skills are readable files under `skills/`. Their narrow responsibilities and output formats are already consumed by the worker. They are prompts, not trained models or proof of expertise.

Recommended optional integrations: [Linear integrations](https://linear.app/integrations) for PM issue tracking, [Notion integrations](https://www.notion.com/integrations) for research specs, [Figma developer tools](https://developers.figma.com/) for design context, [Playwright](https://playwright.dev/) for browser QA, [axe-core](https://github.com/dequelabs/axe-core) for accessibility, [SQLite documentation](https://www.sqlite.org/docs.html) and [Render PostgreSQL](https://render.com/docs/postgresql) for data work, and [Render API documentation](https://render.com/docs/api) for releases. These are official sources, not a claim that marketplace plugins are installed. Verify compatibility and permissions before connecting. There is no verified one-click Render plugin available in this session.

## Current external blockers

- Review and save the environment network draft, then publish the environment. The saved additions are `www.hrudvibandla.com`, `hrudvibandla.com`, `api.openai.com`, and `api.render.com`; the package-manager preset is preserved. The portfolio request currently receives an HTTP 403 from the proxy CONNECT tunnel. Saving a draft does not apply its policy to the running machine.
- Use approved socket access for local HTTP, Git and Docker checks. The restricted command sandbox blocks sockets; these checks succeeded outside that restriction. No daemon recovery or TLS bypass is necessary.
- The selected generated application's Render hostname must also be allowed for smoke requests when running the worker under this cloud policy. A worker on a separately configured machine uses that machine's policy.
- Supply keys securely to the worker, connect target GitHub repository access, and provision the Render services. Those account authorizations and any charges require your action.

Until these are resolved, the board is locally tested; autonomous external execution and live deployment are **not verified**.
