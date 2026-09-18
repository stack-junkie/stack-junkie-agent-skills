# Owner-facing delivery reports

Use when the owner requests a dashboard, executive report or visual project-management artifacts. Reports serve decisions and product review, not a new reporting platform.

## Reuse the supplied artifact

The offline template is assets/delivery-dashboard.html. Its input is one JSON snapshot with project, updated, runs and footer. Each run contains identity/status, executive outcome, observed metrics, work items with dependency IDs and forecast windows, acceptance, team, deputy decisions, standups, risks, review criteria, evidence and launch prompt.

The initial Life Explosion example and full JSON shape live in the source repo's pilots/life-explosion-delivery-review.html and pilots/life-explosion-report-data.json. They are prepared assignments, not completed runs. In another project, supply its real work and references; do not reuse Life Explosion's gameplay scope.

Render from the single report-data.json snapshot:

    python scripts/render_report.py --data <run-folder>/report-data.json --output <run-folder>/report.html

The renderer uses only Python's standard library. The report works offline without a server, CDN, installation or subscription. Use relative evidence paths within the bundle for portability. The buttons switch runs, filter Kanban, copy the launch prompt, export the same data and print the visible run. This is a timestamped snapshot, not a live controller or editable project database.

If a board already exists, derive this JSON from its current items and cite the canonical record IDs; do not maintain two independent work lists. If no board exists, use this one JSON as the pilot work-item source and avoid a parallel Markdown board.

## What the owner must be able to see

- What changed for the player/user, what can be used now, and the exact unfinished boundary.
- Actual elapsed time and available usage, with measurement scope, unknowns and estimates explicit.
- Ready/In progress/Review/Blocked/Done items, actual owners and dependencies.
- A relative Gantt view whose forecast windows are labeled as estimates. Do not imply bars represent measured activity; summarize actual timing separately.
- Behavior acceptance, evidence links and remaining defects.
- Team roster and actual contributions, brief standups, deputy verdicts and PM dispositions.
- Risks and decisions requiring the owner.
- Actual runtime images or muted clips and the runnable artifact/launch instructions.
- A compact next-manager handoff and distinct product/workflow verdict.

Report dates and source/build freshness. Keep prepared fixtures, ordinary user interaction, automated tests and owner acceptance separate. Use words such as Unverified and Unknown when evidence is missing; never substitute zero or fabricated progress.

## Cadence and scope

Render at kickoff, significant outcome or blocker changes, and final closure. Reuse the template without redesigning it during the pilot. Reserve reporting time within the existing resource ceiling, including media inspection and handoff. If the ceiling arrives, deliver an honest partial report.

Keep raw logs with the worker evidence. A short failed attempt with its diagnosis matters more than a long manifest in the executive summary. Do not copy secrets, personal account data, raw private transcripts or unrelated work into a shareable report.

## Inspect before delivery

Open the actual generated HTML in an isolated browser. Exercise run switching and filters if multiple runs are present, verify evidence links/media and check a narrow viewport. Avoid claiming visual validation solely from successful rendering or HTML parsing. Any new preview capture belongs in chat with its absolute path and what it proves.

The renderer and template are conveniences, not proof that report claims are correct. Independent review must still inspect the underlying product.
