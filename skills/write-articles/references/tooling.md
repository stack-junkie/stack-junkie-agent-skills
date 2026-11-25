# Deterministic article helpers

These helpers handle local inventory, candidate retrieval, mechanical validation and stale-review detection. They do not write article text, verify factual claims, decide whether two articles are related, approve wording or prove that a URL is live. They never execute article MDX. Keep human and model judgment in the writing workflow.

Use Node 22.18 or newer. The portable commands use Node standard libraries only. The Stack Junkie adapter additionally imports the trusted site's existing `lib/content-schema.mjs`, publication predicate, MDX parser, remark-gfm and github-slugger from the site's installed dependencies. It does not install packages. Run it against a trusted checkout. Importing the adapter evaluates those trusted library modules, never the article source.

All output paths must be new files. Helpers refuse to overwrite existing files, including inputs. Use a fresh revision suffix for reruns. JSON reports are the deliverables; stdout only summarizes them. Exit 0 means the command completed with no reported mechanical/state concerns, exit 2 means a report was written with findings or missing/stale state, and exit 1 means bad input or execution failure. Inventory can contain invalid articles while exiting 0; inspect each article's `localPublication` status.

## 1. Capture full local articles

```powershell
node scripts/inventory.mjs --adapter stack-junkie --root 'C:\path\to\stack-junkie.com' --as-of '2026-10-04T12:00:00Z' --out 'C:\article-work\inventory-v1.json'
```

Omit `--as-of` to evaluate local publication eligibility at execution time. Use a real ISO calendar timestamp with seconds and timezone, such as `2026-10-04T05:00:00-07:00`. Invalid dates, times and offsets are rejected rather than normalized. Existing filenames determine Stack Junkie article URLs. The helper reads every `content/blog/*.mdx` file, including dirty edits, and retains full raw source and body text. It uses the live schema's frontmatter parser and search-text extractor. Headings, duplicate heading anchors, static JSX IDs, images, links, reference definitions and static JSX src/href attributes come from a parsed syntax tree. Code fences are not treated as actual links or headings. Invalid articles stay in inventory with their error messages and `invalid` eligibility.

Local `eligible` means the current schema and asset checks passed, `draft` is false and the article's date has arrived under the site's publication predicate. It does not mean deployed, indexed, approved, or safe to publish. `livePublication` always remains `unverified`.

The inventory captures source SHA256, trusted schema/dependency hashes and article filename membership. Retrieval rejects stale sources, changed schema dependencies and added/deleted article files. Static route files are inventoried without claiming knowledge of generated dynamic routes or rendered anchors. After adding other routes or changing helper behavior, rebuild the inventory. Capture image files separately in article state when image review depends on them.

`contentFingerprint` hashes canonical JSON of every inventory field except `contentFingerprint` itself and `capturedAt`. Import, retrieval and validation recompute it and reject a supplied mismatch. Exports without that optional field get a newly computed identity. Older helper snapshots using a different fingerprint contract must be rebuilt; do not copy their identity into a new inventory.

## 2. Retrieve by the reader's task

```powershell
node scripts/retrieve.mjs --inventory 'C:\article-work\inventory-v1.json' --task 'Recover context after compaction and restore saved agent progress' --limit 8 --out 'C:\article-work\candidates-v1.json'
```

The deterministic BM25 score uses full extracted article content, including headings and code. There is no title or metadata boost. It is lexical retrieval, not embeddings or a semantic judgment. Default candidates must be locally eligible. Use `--include-ineligible true` only to examine unpublished overlap, and keep those candidates out of publication link recommendations until verified.

The result contains matched terms, matching full text lines, and the **complete source/body of every returned candidate**. Read those bodies before selecting links. Decide which section actually helps the current reader, what precise destination/anchor serves that need, and how to introduce the link naturally in prose. Shared product names or high scores alone do not establish relevance. If the first task wording misses a concept, reformulate it, expand the limit, or inspect the inventory. A zero-match result is not proof that nothing relevant exists.

## 3. Check local mechanics

```powershell
node scripts/validate.mjs --inventory 'C:\article-work\inventory-v1.json' --article 'C:\article-work\draft.mdx' --published-file 'proposed-filename.mdx' --url 'https://www.stack-junkie.com/blog/proposed-filename' --out 'C:\article-work\validation-v1.json'
```

For an existing inventoried source, `--url` may be omitted. `--published-file` supplies the intended published basename when a private file is named `draft.mdx`; otherwise the actual basename is used. The intended URL must match it. The adapter reuses the site's authoritative `parseArticle` filename/slug/canonical checks on an in-memory validation view, omitting the image field only for that call because actual image syntax and private/local existence are checked separately. It never changes the draft or moves private assets into the website. A draft can change without rebuilding its own inventory entry, but changed destination articles and schema dependencies are reported as stale. Checks cover frontmatter schema, static files and assets, local article destinations, fragment IDs, local publication eligibility of linked articles, undefined/dynamic references, and unresolved draft markers. The helper does not fetch external URLs, infer redirects, test commands, compile the site, inspect pixels or verify whether a source supports a claim. Generated dynamic routes not supplied in the inventory remain explicitly unresolved.

Undefined full/collapsed Markdown references such as `[Text][missing]`, `![Alt][missing]` and `[Text][]` receive conservative `needs-review` findings when the parser leaves them as plain prose. Fenced/inline code, escaped syntax, HTML/MDX code or pre elements, and blockquoted examples are excluded. Ambiguous shortcut `[Text]` syntax is not treated as a broken link. Review candidates in context; do not automatically rewrite intentional literal prose. URL lookup normalizes only percent-encoded unreserved path characters, preserving reserved separators and traversal protections.

For images still in the private article folder, supply an explicit URL-to-file map rather than copying them into a website:

```json
{
  "/static/images/blog/proposed-filename/hero.webp": "C:/article-work/images/hero.webp"
}
```

Add `--asset-map 'C:\article-work\asset-map.json'`. Values must be absolute local file paths. Without a map, local asset URLs resolve under the inventory root's `public` directory. Traversal and symlinks escaping that directory are rejected. File existence does not establish visual correctness. Marker findings inside intentional quotations/examples can be false positives; document the review decision instead of deleting the example automatically.

## Portable inventory interface for other sites

Other sites provide a JSON inventory from their own trusted content parser. There is no fallback parser that pretends to know arbitrary MDX or site routing. Use the same fields below, with full actual content and hashes. `source.sha256` is lowercase SHA256 of UTF-8 source bytes. `sourceText` must match it exactly, including line endings and frontmatter. `searchText` must contain all displayable article text and relevant code, not a title/summary surrogate. `anchors` must be the site's actual generated/static anchor IDs. Unknown publication state is `unknown`, not eligible.

```json
{
  "schemaVersion": 1,
  "adapter": "your-site-parser",
  "root": "C:/site",
  "capturedAt": "2026-10-04T12:00:00Z",
  "asOf": "2026-10-04T12:00:00Z",
  "origins": ["https://example.test"],
  "articles": [{
    "id": "restore-progress",
    "url": "https://example.test/articles/restore-progress",
    "title": "Restore saved progress",
    "source": {"path": "content/restore-progress.md", "sha256": "REPLACE_WITH_ACTUAL_64_CHARACTER_LOWERCASE_SHA256"},
    "sourceText": "## Restore progress\nUse the saved checkpoint.\n",
    "body": "## Restore progress\nUse the saved checkpoint.\n",
    "searchText": "Restore progress\nUse the saved checkpoint.",
    "metadata": {},
    "headings": [{"depth": 2, "text": "Restore progress", "anchor": "restore-progress", "line": 1}],
    "anchors": ["restore-progress"],
    "references": [],
    "localPublication": {"status": "unknown", "asOf": "2026-10-04T12:00:00Z", "reason": "Parser has not established eligibility", "issues": []},
    "livePublication": "unverified"
  }],
  "routes": [{"url": "https://example.test/about", "anchors": null, "evidence": "local-route-file", "source": "app/about/page.tsx"}],
  "dependencies": [],
  "sourceSet": {"directory": "content", "extension": ".md", "names": ["restore-progress.md"]}
}
```

The SHA string above is intentionally a schema placeholder and fails validation until replaced with the real hash. Each `reference` is `{ "url": "/articles/other#steps", "kind": "link", "line": 12 }` or `{ "url": "/assets/image.webp", "kind": "asset", "line": 15 }`. A dynamic/unresolved reference uses `url: null`, with `dynamic: true` or `unresolvedReference: true`. Routes with known static anchors use an array; `null` means unknown. Supply dependency entries as `{ "path": "site-parser-config.json", "sha256": "actual hash" }`. `sourceSet` is optional and supports one flat directory; omit it only when the external adapter independently checks membership and rebuilds after additions/deletions.

Validate and fingerprint a generic inventory:

```powershell
node scripts/inventory.mjs --input 'C:\article-work\site-export.json' --out 'C:\article-work\inventory-v1.json'
```

For a new/changed article on another site, the site parser exports a single article record using the same article shape. Pass it to validation using `--record 'C:\article-work\draft-record.json'` along with `--article`; the helper checks its source hash against the actual file. A parser's `localPublication.status: invalid` always produces a finding, with its `localPublication.issues` retained. Draft/scheduled `ineligible` status alone does not make a private draft invalid. The helper trusts that site's parser for syntax, anchors and extracted references. It never infers equivalent semantics from a different site's schema. Stack Junkie validation always uses its live parser and rejects `--record` overrides.

## 4. Track lightweight article state

Create one manifest in the private article folder. Paths are relative to that manifest unless absolute. List each artifact and image file that matters to a review, not a directory. Required artifacts default to `true`.

```json
{
  "schemaVersion": 1,
  "articleId": "proposed-filename",
  "artifacts": [
    {"id": "draft", "path": "draft.mdx"},
    {"id": "research", "path": "research.md"},
    {"id": "claims", "path": "claims.json"},
    {"id": "links", "path": "link-decisions.md"},
    {"id": "inventory", "path": "inventory-v1.json"},
    {"id": "hero", "path": "images/hero.webp", "required": false}
  ],
  "findings": [{"id": "source-1", "status": "open", "description": "Confirm the timeout default in official docs"}],
  "reviews": [{"id": "editorial", "report": "editorial-review.md", "dependsOn": ["draft", "research", "claims", "links", "inventory"]}]
}
```

```powershell
node scripts/state.mjs --manifest 'C:\article-work\state-input.json' --out 'C:\article-work\state-v1.json'
```

It reports missing artifacts, unresolved findings, per-file hashes, per-review `currentInputFingerprint`, and the review report's `reportSha256`. Initially a review is `unrecorded`, `missing-report`, or `missing-input`. Add `hero` to a visual review's `dependsOn` when the image exists and was inspected. Any listed review dependency must exist, even when that artifact is otherwise optional. After the reviewer actually completes a review, record the returned current dependency fingerprint as `inputFingerprint` and the reviewed report hash as `reportSha256` in that manifest review entry. These record what was reviewed; they are not a generated approval.

Rerun with `--previous 'C:\article-work\state-v1.json' --out 'C:\article-work\state-v2.json'`. Prior attestations can carry forward, but a changed/missing dependency or changed report makes the review stale. The script preserves the attested report hash across repeated stale snapshots, so running it again cannot make a changed report current. It shows `changedArtifacts` against the prior snapshot.

Finding statuses are `open`, `owner-needed`, or `resolved`. A resolved finding requires a `resolution` explanation. No numeric score can clear an open finding. A `current` review means only that its recorded inputs and report match; inspect the report verdict and exact findings yourself. Add the skill/rules files to dependencies when their changes require a new review. Unlisted inputs cannot invalidate anything automatically. This is a small state summary, not a publication controller.
