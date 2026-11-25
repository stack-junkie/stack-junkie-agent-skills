import path from 'node:path';
import { args, only, need, readJson, writeJson, fileHash, fingerprint, main } from './lib.mjs';

await main(async () => {
  const o = args(); only(o, ['manifest', 'previous', 'out']);
  const manifestFile = path.resolve(need(o, 'manifest')), manifest = await readJson(manifestFile);
  if (manifest.schemaVersion !== 1 || !manifest.articleId || !Array.isArray(manifest.artifacts) || !Array.isArray(manifest.findings ?? [])) throw new Error('Expected manifest schemaVersion 1, articleId, artifacts and findings');
  const base = path.dirname(manifestFile), resolve = p => path.resolve(base, p);
  const seen = new Set(), artifacts = [];
  for (const input of manifest.artifacts) {
    if (!input.id || seen.has(input.id) || typeof input.path !== 'string') throw new Error('Each artifact needs unique id and path');
    seen.add(input.id);
    artifacts.push({ id: input.id, path: resolve(input.path), required: input.required !== false, sha256: await fileHash(resolve(input.path)) });
  }
  const findings = manifest.findings ?? [], ids = new Set();
  for (const finding of findings) {
    if (!finding.id || ids.has(finding.id) || !['open', 'resolved', 'owner-needed'].includes(finding.status) || !finding.description) throw new Error('Findings need unique id, description and status open/resolved/owner-needed');
    ids.add(finding.id);
    if (finding.status === 'resolved' && !finding.resolution) throw new Error(`Resolved finding ${finding.id} needs a resolution explanation`);
  }
  const previous = o.previous ? await readJson(o.previous) : null;
  if (previous && previous.articleId !== manifest.articleId) throw new Error('Previous state belongs to another article');
  const reviews = [], reviewIds = new Set();
  for (const review of manifest.reviews ?? []) {
    if (!review.id || reviewIds.has(review.id) || !Array.isArray(review.dependsOn) || !review.dependsOn.length || !review.report) throw new Error('Review needs unique id, nonempty dependsOn artifact IDs, and report path');
    reviewIds.add(review.id);
    const inputs = review.dependsOn.map(id => { const a = artifacts.find(a => a.id === id); if (!a) throw new Error(`Unknown review dependency ${id}`); return { id, sha256: a.sha256 }; }).sort((a, b) => a.id.localeCompare(b.id, 'en'));
    const currentInputFingerprint = fingerprint(inputs);
    const old = previous?.reviews?.find(r => r.id === review.id);
    const attestedFingerprint = review.inputFingerprint ?? old?.attestedFingerprint ?? null;
    const reportPath = resolve(review.report), reportSha256 = await fileHash(reportPath);
    const expectedReportSha256 = review.reportSha256 ?? old?.attestedReportSha256 ?? null;
    const status = !reportSha256 ? 'missing-report' : inputs.some(i => i.sha256 === null) ? 'missing-input' :
      !attestedFingerprint || !expectedReportSha256 ? 'unrecorded' :
        attestedFingerprint !== currentInputFingerprint || expectedReportSha256 !== reportSha256 ? 'stale' : 'current';
    reviews.push({ id: review.id, dependsOn: review.dependsOn, report: reportPath, reportSha256, attestedReportSha256: expectedReportSha256, currentInputFingerprint, attestedFingerprint, status });
  }
  const missingArtifacts = artifacts.filter(a => a.required && a.sha256 === null).map(a => a.id);
  const unresolvedFindings = findings.filter(f => f.status !== 'resolved');
  const changedArtifacts = previous ? artifacts.filter(a => previous.artifacts?.find(p => p.id === a.id)?.sha256 !== a.sha256).map(a => a.id) : [];
  const output = { schemaVersion: 1, articleId: manifest.articleId, artifacts, findings, reviews,
    missingArtifacts, unresolvedFindings, changedArtifacts,
    inputFingerprint: fingerprint(artifacts.map(a => ({ id: a.id, sha256: a.sha256 })).sort((a, b) => a.id.localeCompare(b.id, 'en'))),
    needsAttention: !!(missingArtifacts.length || unresolvedFindings.length || reviews.some(r => r.status !== 'current')),
    limitations: ['A current review means recorded report and dependencies have not changed. It does not mean the review passed or was truthful.', 'Findings and review attestations are entered by the actual reviewer. This helper never approves publication.', 'List all relevant inputs, including draft, sources, assets, inventory, rules and claim ledger; unlisted changes cannot invalidate a review.'] };
  await writeJson(need(o, 'out'), output, [manifestFile, o.previous, ...artifacts.map(a => a.path), ...reviews.map(r => r.report)].filter(Boolean));
  console.log(JSON.stringify({ out: path.resolve(o.out), needsAttention: output.needsAttention, missingArtifacts, unresolvedFindings: unresolvedFindings.length, reviews: reviews.map(r => ({ id: r.id, status: r.status })) }));
  if (output.needsAttention) process.exitCode = 2;
});
