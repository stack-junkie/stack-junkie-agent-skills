# GitHub Issues

The tracker is [stack-junkie/stack-junkie-agent-skills](https://github.com/stack-junkie/stack-junkie-agent-skills/issues). Run `gh` in this checkout and use `--repo stack-junkie/stack-junkie-agent-skills` for issue commands. For multiline issue bodies and comments, pass a file with `--body-file`.

PRs as a request surface: no.

## Wayfinding operations

1. Create the map as an issue labelled `wayfinder:map`. Give each decision its own issue with the appropriate label: `wayfinder:research`, `wayfinder:prototype`, `wayfinder:grilling`, or `wayfinder:task`.
2. Attach each decision to the map as a native GitHub sub-issue. Add native blocking relationships between decisions that depend on one another. Use the commands below with the current GitHub CLI.
3. To find the next decision, list the map's children and choose an open, unassigned child with zero open blockers. Claim it with `gh issue edit NUMBER --add-assignee "@me"`.
4. On resolution, post the answer and rationale as an issue comment, close the decision, then add its linked title and one-line outcome to the parent map. Keep supporting details in the decision issue.

## GitHub CLI operations

Read an issue and its discussion with `gh issue view NUMBER --json title,body,state,labels,comments,assignees`. Use `gh issue create`, `gh issue edit`, and `gh issue list` for specs, build tickets, and triage. Use `gh issue comment` before `gh issue close` when recording a resolution.

For sub-issues and blockers, the REST commands below work with the installed GitHub CLI 2.93. Replace uppercase placeholders with integers. The path takes the visible issue number. The form fields take numeric database IDs from the first command.

```powershell
gh api repos/stack-junkie/stack-junkie-agent-skills/issues/NUMBER --jq .id
gh api --method POST repos/stack-junkie/stack-junkie-agent-skills/issues/PARENT_NUMBER/sub_issues -F sub_issue_id=CHILD_DATABASE_ID
gh api --method POST repos/stack-junkie/stack-junkie-agent-skills/issues/DEPENDENT_NUMBER/dependencies/blocked_by -F issue_id=BLOCKER_DATABASE_ID
gh api --paginate repos/stack-junkie/stack-junkie-agent-skills/issues/PARENT_NUMBER/sub_issues --jq '.[] | {number,title,state,assignees,blockers:.issue_dependencies_summary.blocked_by}'
```

Wayfinder child issues hold planning decisions. After planning, link the spec to the map and attach each approved implementation ticket to the spec. Use the same native blocking relationships for implementation dependencies.
