import fs from 'node:fs/promises';
import path from 'node:path';
import { args, only, need, readJson, writeJson, validateInventory, freshness, sha256, checkLocalFile, isFile, urlKey, inventoryIdentity, main } from './lib.mjs';
import { adapter } from './stack-junkie.mjs';

await main(async () => {
  const o = args(); only(o, ['inventory', 'article', 'url', 'published-file', 'record', 'asset-map', 'out']);
  const inventoryFile = need(o, 'inventory'), inventory = validateInventory(await readJson(inventoryFile));
  const inventoryFingerprint = inventoryIdentity(inventory);
  const articleFile = path.resolve(need(o, 'article'));
  const sourceText = await fs.readFile(articleFile, 'utf8');
  const existing = inventory.articles.find(a => path.resolve(inventory.root, a.source.path) === articleFile);
  let subject;
  if (o.record) {
    if (inventory.adapter === 'stack-junkie') throw new Error('Stack Junkie drafts use the live site parser; --record is only for other-site adapters');
    subject = await readJson(o.record);
    validateInventory({ ...inventory, articles: [subject] });
    if (subject.source.sha256 !== sha256(sourceText)) throw new Error('Generic article record is stale for --article');
  } else if (inventory.adapter === 'stack-junkie') {
    const parsed = await (await adapter(inventory.root)).analyze(sourceText, articleFile, { publishedFile: o['published-file'] ?? path.basename(articleFile) });
    subject = { ...parsed, sourceText, url: o.url ?? existing?.url, source: { sha256: sha256(sourceText) } };
  } else {
    if (!existing || existing.source.sha256 !== sha256(sourceText)) throw new Error('Other sites need a matching full --record for a new or changed article');
    subject = existing;
  }
  if (!subject.url && !o.url) throw new Error('New draft requires --url with intended article URL');
  const subjectUrl = new URL(o.url ?? subject.url);
  const findings = [];
  const add = (code, detail, reference, severity = 'error') => findings.push({ code, severity, detail, ...(reference ? { reference } : {}) });
  const changed = (await freshness(inventory)).filter(c => !c.path || path.resolve(inventory.root, c.path) !== articleFile);
  for (const entry of changed) add('stale-inventory', entry);
  for (const issue of subject.schemaIssues ?? []) add('schema', issue);
  if (subject.localPublication?.status === 'invalid') {
    const issues = subject.localPublication.issues;
    for (const issue of Array.isArray(issues) && issues.length ? issues : ['The site parser marks this article invalid']) add('parser-invalid', issue);
  }
  if (inventory.adapter === 'stack-junkie' && !o.record) {
    const intended = o['published-file'] ?? path.basename(articleFile);
    if (urlKey(subjectUrl.href) !== urlKey(`https://www.stack-junkie.com/blog/${intended.replace(/\.mdx$/, '')}`) && urlKey(subjectUrl.href) !== urlKey(`https://stack-junkie.com/blog/${intended.replace(/\.mdx$/, '')}`)) add('publication-path', 'Intended URL must match the published filename. For a private draft.mdx, pass --published-file actual-article-slug.mdx.');
    if (subjectUrl.search || subjectUrl.hash) add('publication-path', 'Intended article URL must not include a query or fragment');
  }
  const origins = new Set(inventory.origins);
  if (!origins.has(subjectUrl.origin)) throw new Error('Article URL must belong to an inventory origin');
  const canonical = value => {
    const u = new URL(value, subjectUrl);
    if (origins.has(u.origin)) { const origin = new URL(inventory.origins[0]); u.protocol = origin.protocol; u.host = origin.host; }
    return urlKey(u.href);
  };
  const byUrl = new Map(inventory.articles.map(r => [canonical(r.url), r]));
  byUrl.set(canonical(subjectUrl.href), subject);
  const routes = new Map(inventory.routes.map(r => [canonical(r.url), r]));
  const assetMap = o['asset-map'] ? await readJson(o['asset-map']) : {};
  for (const [url, file] of Object.entries(assetMap)) {
    if (!url.startsWith('/') || typeof file !== 'string' || !path.isAbsolute(file)) throw new Error('Asset map must map root-relative URLs to absolute local file paths');
  }
  const examined = [];
  for (const ref of subject.references) {
    if (!ref.url) { add('unresolved-reference', 'Dynamic MDX URL or missing Markdown reference definition needs manual resolution', ref, ref.undefinedReferenceCandidate ? 'needs-review' : 'error'); continue; }
    let u;
    try { u = new URL(ref.url, subjectUrl); }
    catch { add('invalid-url', 'URL could not be parsed', ref); continue; }
    if (!['http:', 'https:', 'mailto:', 'tel:'].includes(u.protocol)) { add('unsupported-url-scheme', u.protocol, ref); continue; }
    if (!['http:', 'https:'].includes(u.protocol)) { examined.push({ ...ref, result: 'non-http-not-checked' }); continue; }
    if (!origins.has(u.origin)) { examined.push({ ...ref, result: 'external-not-fetched' }); continue; }
    let pathname, fragment;
    try { pathname = decodeURIComponent(u.pathname); fragment = decodeURIComponent(u.hash.slice(1)); }
    catch { add('invalid-url-encoding', 'Bad percent-encoding', ref); continue; }
    const destination = byUrl.get(canonical(u.href));
    if (destination && ref.kind !== 'asset') {
      if (destination !== subject && destination.localPublication.status !== 'eligible') add('ineligible-article-target', `${destination.id}: ${destination.localPublication.status}`, ref);
      if (fragment && !destination.anchors.includes(fragment)) add('missing-anchor', fragment, ref);
      examined.push({ ...ref, result: 'local-article-checked', livePublication: 'unverified' }); continue;
    }
    if (ref.kind === 'asset' || /\.[a-z0-9]{1,10}$/i.test(pathname)) {
      try {
        if (pathname.includes('\\')) throw new Error('Backslashes are not valid local asset URLs');
        let exists;
        if (Object.hasOwn(assetMap, pathname)) exists = await isFile(assetMap[pathname]);
        else exists = await checkLocalFile(path.join(inventory.root, 'public'), `.${pathname}`);
        if (!exists) add('missing-asset', pathname, ref);
        examined.push({ ...ref, result: exists ? 'local-asset-exists' : 'missing-asset' });
      } catch (error) { add('unsafe-asset-path', error.message, ref); }
      continue;
    }
    const route = routes.get(canonical(u.href));
    if (route) {
      if (fragment && route.anchors === null) add('unverified-route-anchor', 'Route exists locally but rendered anchors are unknown', ref, 'needs-review');
      else if (fragment && !route.anchors.includes(fragment)) add('missing-anchor', fragment, ref);
      examined.push({ ...ref, result: 'local-route-only', evidence: route.evidence });
    } else add('unresolved-internal-destination', 'No inventoried article, known route or asset; verify redirect/dynamic route before approval', ref, 'needs-review');
  }
  const marker = /\[(?:NEEDS[_ ]VERIFICATION|NEEDS CHRIS|SCREENSHOT|IMAGE|TODO|TBD|PLACEHOLDER)(?::[^\]\r\n]*)?\]|\b(?:TODO|TBD)\b|\{\{[^}\r\n]+\}\}/gi;
  for (const [index, line] of sourceText.split(/\r\n|\n|\r/).entries()) {
    const matches = [...line.matchAll(marker)].map(m => m[0]);
    if (matches.length) add('draft-marker', { line: index + 1, markers: [...new Set(matches)], context: line }, null, 'needs-review');
  }
  const result = { schemaVersion: 1, article: articleFile, url: subjectUrl.href, sourceSha256: sha256(sourceText),
    inventoryFingerprint, mechanicallyClear: findings.length === 0, findings, examined,
    limitations: ['Does not assess claim truth, citation entailment, voice or natural link placement.', 'External URLs are listed but not fetched. No live publication or redirect verification.', 'Markers in quoted examples may be intentional; findings need an actual reviewer.', 'Dynamic MDX attributes and unlisted generated routes remain unresolved rather than assumed valid.'] };
  await writeJson(need(o, 'out'), result, [articleFile, inventoryFile, o.record, o['asset-map']].filter(Boolean));
  console.log(JSON.stringify({ out: path.resolve(o.out), mechanicallyClear: result.mechanicallyClear, findings: findings.length }));
  if (findings.length) process.exitCode = 2;
});
