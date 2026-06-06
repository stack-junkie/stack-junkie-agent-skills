# GitHub Publish

Create the remote only after confirming the owner/name to use.

Recommended repository name:

```text
repo-readiness
```

Local publish flow:

```powershell
git status --short
git remote add origin https://github.com/<owner>/repo-readiness.git
git push -u origin main
```

Do not claim the GitHub remote exists until `git remote -v` and the first push both succeed.
