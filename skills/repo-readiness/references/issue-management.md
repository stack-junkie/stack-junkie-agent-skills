# Issue management

Use this policy to document repository bugs and improvements without turning issue creation into paperwork.

## Core rule

Capture the minimum information needed to understand, reproduce, and resolve the issue. Add no section that would remain empty or repeat another section.

Keep one independently fixable problem or desired outcome per issue. Use the title as the summary. Describe observable behavior before theories about its cause.

## Bug format

```markdown
## Actual behavior

What happened?

## Expected behavior

What should happen instead?

## Reproduction

How can we make it happen again?
```

Use a specific behavioral title such as `Workspace dirty indicator disappears after renaming a tab`. Do not prefix the title with `Bug` when the issue already has a `bug` label.

## Improvement format

```markdown
## Problem

What is difficult or missing today?

## Desired outcome

What should become possible or easier?
```

Describe the outcome before proposing an implementation. Put implementation choices in later discussion unless the constraint itself is part of the request.

## Add detail only when useful

Add screenshots, recordings, logs, sample files, version, operating system, hardware, data source, impact, constraints, or acceptance checks only when they materially help someone understand, reproduce, prioritize, fix, or verify the issue.

Add acceptance checks during triage when the completion boundary is not already obvious. Make them observable behavior, not an implementation task list.

Never attach credentials, private customer data, or proprietary data that is not approved for the repository.

## Create and triage

Before creating an issue:

1. Confirm the target repository and search open and closed issues for a duplicate.
2. Preserve what the reporter observed. Do not silently rewrite it into a different problem.
3. Draft the shortest title and body that retain the useful facts.
4. Ask only for missing information that blocks useful documentation or materially changes the issue.
5. Create the issue only when the user authorized the GitHub write.

After creation:

- Keep the opening body as the current canonical description.
- Put investigation findings and chronological evidence in comments.
- Update the body when confirmed reproduction or completion conditions become clearer.
- Use the repository's existing type labels. Add workflow or priority labels only when they support a real decision.
- Assign the person actively responsible for the next implementation step, not automatically the reporter.
- Use a milestone only for a real release commitment.

## Resolve and close

Link implementation with `Fixes #<number>` or `Closes #<number>` when the change should close the issue after merging.

Do not treat code, a commit, or a pull request as proof that the issue is resolved. Exercise the reported workflow, record the result, and request reporter confirmation when practical. Close as completed after verification; otherwise retain or reopen the issue with the failed condition.

Issue existence is backlog evidence, not proof of repository readiness or product completion.

## Reusable templates

The skill includes:

- `assets/github/ISSUE_TEMPLATE/bug.md`
- `assets/github/ISSUE_TEMPLATE/improvement.md`

Copy or adapt them into `.github/ISSUE_TEMPLATE/` only when the user requests repository templates. Preserve established labels and conventions. Do not add project boards, issue forms, extra fields, or lifecycle machinery merely because GitHub supports them.
