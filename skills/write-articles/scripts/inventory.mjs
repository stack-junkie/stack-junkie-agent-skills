import path from 'node:path';
import { args, only, need, readJson, writeJson, validateInventory, freshness, inventoryIdentity, isoTimestamp, main } from './lib.mjs';
import { adapter } from './stack-junkie.mjs';

await main(async () => {
  const o = args(); only(o, ['adapter', 'root', 'out', 'as-of', 'input']);
  let inventory;
  if (o.input) {
    if (o.adapter || o.root || o['as-of']) throw new Error('--input imports an existing generic inventory; do not combine with adapter/root/as-of');
    inventory = validateInventory(await readJson(o.input));
    const changed = await freshness(inventory);
    if (changed.length) throw new Error(`Imported inventory does not match local sources: ${JSON.stringify(changed)}`);
  } else {
    if (need(o, 'adapter') !== 'stack-junkie') throw new Error('Built-in adapter is stack-junkie; other sites supply --input inventory.json');
    const root = path.resolve(need(o, 'root'));
    const asOf = o['as-of'] ?? new Date().toISOString();
    isoTimestamp(asOf);
    inventory = await (await adapter(root)).inventory(asOf);
    validateInventory(inventory);
  }
  inventory.contentFingerprint = inventoryIdentity(inventory);
  await writeJson(need(o, 'out'), inventory, [o.input, ...inventory.articles.map(r => path.resolve(inventory.root, r.source.path))].filter(Boolean));
  console.log(JSON.stringify({ out: path.resolve(o.out), articles: inventory.articles.length,
    eligible: inventory.articles.filter(r => r.localPublication.status === 'eligible').length,
    invalid: inventory.articles.filter(r => r.localPublication.status === 'invalid').length, fingerprint: inventory.contentFingerprint }));
});
