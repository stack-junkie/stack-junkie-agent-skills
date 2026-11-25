> Instructional reference example, created October 4, 2026. Not attributed to the owner. Git's git-status documentation was opened on that date. Output examples are constructed illustrations, not a capture of someone's repository.

# Read the two columns in Git's short status

For ordinary tracked files outside an unresolved merge, `git status --short` reports two status positions. The first describes the index, and the second describes the working tree. [Git's short-format documentation](https://git-scm.com/docs/git-status#_short_format).

Run this inside the repository you want to inspect:

```sh
git status --short
```

## Common entries

Here, `.` represents a blank to make the positions easier to compare. Git prints a space there. These ordinary-file meanings follow [Git's status table](https://git-scm.com/docs/git-status#_short_format).

| Illustrated pair | Meaning |
| --- | --- |
| `M.` | Modified in the index; no further working-tree change |
| `.M` | Modified in the working tree relative to the index |
| `MM` | Modified in the index and changed again in the working tree |
| `A.` | Added to the index |
| `.D` | Deleted in the working tree |
| `??` | Untracked |
| `UU` | Unresolved conflict with both sides modified |

## Read one line without losing the blank

This constructed line has a blank before `M`:

```text
 M notes.md
```

For an ordinary tracked file, the modification is in the working tree. Moving the letter left changes the meaning:

```text
M  notes.md
```

Now the modification is represented in the index. Preserve the spacing when sharing status output. These interpretations follow the documented `X` and `Y` positions. [Git's format definition](https://git-scm.com/docs/git-status#_short_format).

An issue report that says only "the file shows M" leaves out the detail needed to distinguish these cases. Include the full line and whether a merge is in progress. That makes a follow-up investigation more specific without changing the repository.

## Where this shortcut stops

For unresolved merges, the positions describe states introduced by the two merge heads. Do not interpret `UU` as an ordinary staged/unstaged pair. Submodules have additional conventions. [Git's merge and submodule notes](https://git-scm.com/docs/git-status#_short_format).

For scripts, use a machine-oriented format such as `--porcelain=v1`; Git documents stability across versions and user configuration. [Git's porcelain format](https://git-scm.com/docs/git-status#_porcelain_format_version_1).

For a human check, read both positions before choosing what to inspect next. A letter without its position is an incomplete description.
