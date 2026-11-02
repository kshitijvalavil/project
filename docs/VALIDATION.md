# Validation evidence

Verified in this instance:

- 18 existing-in-this-change workflow and HTTP tests passed, zero skips. Checks include Boss/worker authorization separation, stale approval digests, stale receipts, exclusive task claims, rejection/retry behavior, artifact confinement, nonzero-test release gating, exact deployment commit matching, SQLite restart persistence and Render target checks.
- The same 18 tests passed inside an official Python image with verified digest, network disabled, read-only source, a non-root user, dropped capabilities, constrained CPU/memory/PIDs and writable temporary storage only. This validated the test-container configuration, not an AI-generated application.
- Chromium browser automation passed: unlock, six role cards, project brief submission, a clearly labeled PM fixture, Boss plan approval, skills navigation, lock and a mobile-width overflow check. No page JavaScript errors occurred. Screenshot: `/tmp/crewboard-overview.png`. Test data used a temporary database and was deleted.
- Python compilation and JavaScript syntax checks passed. Read-only Git remote access and Docker daemon health passed with approved socket access.

Not verified: live model responses, real agent-generated project correctness, Git write authorization, Render API schema/credentials, live deployment, rollback execution, browser/accessibility coverage of generated projects, fresh-task snapshot restoration, or reference portfolio research. API contract compatibility must be confirmed on the first connected staging run. The Render blueprint has not been applied.

Initial HTTP tests failed because the command sandbox forbade sockets. They passed after using approved loopback access. The first Docker check exposed a restrictive umask; the worker now makes source readable by the non-root container user and the sandbox test run passed. Chromium was available as the system binary rather than Playwright's default cached executable; the optional browser check handles that.

The server trusts its configured worker to report genuine test results and exact source commits. A compromised worker credential can forge worker evidence; it still cannot perform Boss approvals. This is a single-owner prototype, not a multi-tenant attestation system. Generated test quality still requires acceptance review. Test pass counts alone do not establish product quality.
