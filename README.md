# Crewboard

A development-agent command center with you as the approval authority.

**PM → plan approval → database → full stack → QA → deployment approval → ShipIt → your review.**

The board persists projects, artifacts, approval digests, worker receipts and activity in SQLite. Boss and worker credentials are separate. The optional dedicated worker invokes model roles, executes generated Python tests in Docker, pushes a tested commit and deploys that exact commit to Render after approval.

```sh
python -m unittest discover -s tests -v
python dev.py
```

No third-party Python packages are required for the board or worker. [Connection and deployment guide](docs/SETUP.md) includes account links, credential placement, limitations and recovery steps. [Portfolio roadmap and research method](docs/PORTFOLIO.md) explains which projects to build and what each teaches. [Custom agent skills](skills/) contain the role instructions consumed by the worker.

Local control-plane behavior is testable without paid accounts. Model calls, Git pushes, Docker execution and Render releases require a configured external worker and are not established by local tests. The reference portfolio research remains blocked by network access; no project-by-project findings have been invented.
