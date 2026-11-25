import path from 'node:path';
import { args, only, need, readJson, writeJson, validateInventory, freshness, inventoryIdentity, main } from './lib.mjs';
const stop = new Set('a an the and or to of for in on with is are be by how what why when where from that this my i me it'.split(' '));
const tokens = text => (text.normalize('NFKC').toLowerCase().match(/[\p{L}\p{N}_-]+/gu) ?? []).filter(t => t.length > 1 && !stop.has(t));
await main(async () => {
  const o = args(); only(o, ['inventory', 'task', 'out', 'limit', 'include-ineligible']);
  const file = need(o, 'inventory'), inventory = validateInventory(await readJson(file));
  const inventoryFingerprint = inventoryIdentity(inventory);
  const changed = await freshness(inventory);
  if (changed.length) throw new Error(`Stale inventory; rebuild before retrieval: ${JSON.stringify(changed)}`);
  const query = [...new Set(tokens(need(o, 'task')))];
  if (!query.length) throw new Error('Reader task has no searchable terms');
  const limit = Number(o.limit ?? 8);
  if (!Number.isInteger(limit) || limit < 1 || limit > 100) throw new Error('--limit must be 1..100');
  if (o['include-ineligible'] && o['include-ineligible'] !== 'true') throw new Error('--include-ineligible accepts true only');
  const all = inventory.articles.filter(a => o['include-ineligible'] || a.localPublication.status === 'eligible');
  const docs = all.map(article => { const words = tokens(article.searchText); const counts = new Map(); for (const word of words) counts.set(word, (counts.get(word) ?? 0) + 1); return { article, counts, length: words.length }; });
  const avgLength = docs.reduce((s, d) => s + d.length, 0) / Math.max(docs.length, 1);
  const df = new Map(query.map(q => [q, docs.filter(d => d.counts.has(q)).length]));
  const ranked = docs.map(d => {
    let score = 0;
    const matchedTerms = [];
    for (const q of query) {
      const tf = d.counts.get(q) ?? 0; if (!tf) continue;
      matchedTerms.push(q);
      const idf = Math.log(1 + (docs.length - df.get(q) + 0.5) / (df.get(q) + 0.5));
      score += idf * (tf * 2.2) / (tf + 1.2 * (0.25 + 0.75 * d.length / (avgLength || 1)));
    }
    const matchingLines = d.article.searchText.split('\n').map((text, index) => ({ searchLine: index + 1, text })).filter(line => query.some(q => tokens(line.text).includes(q)));
    return { score, matchedTerms, matchingLines, article: d.article };
  }).filter(d => d.score > 0).sort((a, b) => b.score - a.score || a.article.id.localeCompare(b.article.id, 'en'));
  const result = { schemaVersion: 1, readerTask: o.task, inventoryFingerprint,
    method: 'BM25 over full extracted article content, including headings and code; no title or summary boost; exact token matching',
    searchedArticles: docs.length, matchedArticles: ranked.length, queryTerms: query, limit,
    candidates: ranked.slice(0, limit),
    limitations: ['Lexical retrieval is a candidate filter, not a semantic relatedness decision.', 'Every candidate includes complete body and source. Read full candidates and judge actual reader-task usefulness and natural link introduction.', 'No match does not prove no relevant article. Reformulate the reader task, inspect broader inventory or increase limit.', 'Only local publication eligibility is known. Live publication remains unverified.'] };
  await writeJson(need(o, 'out'), result, [file, ...inventory.articles.map(r => path.resolve(inventory.root, r.source.path))]);
  console.log(JSON.stringify({ out: path.resolve(o.out), candidates: result.candidates.map(c => ({ id: c.article.id, score: c.score, matchedTerms: c.matchedTerms })) }));
});
