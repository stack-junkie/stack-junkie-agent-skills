import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';

export const sha256 = value => crypto.createHash('sha256').update(value).digest('hex');
export const stable = value => JSON.stringify(value, (_, v) => v && typeof v === 'object' && !Array.isArray(v) ? Object.fromEntries(Object.keys(v).sort().map(k => [k, v[k]])) : v);
export const fingerprint = value => sha256(stable(value));
export function inventoryIdentity(value) {
  const { contentFingerprint, capturedAt, ...content } = value;
  const actual = fingerprint(content);
  if (contentFingerprint !== undefined && contentFingerprint !== actual) throw new Error('Inventory contentFingerprint does not match canonical inventory data; rebuild the inventory');
  return actual;
}
export function isoTimestamp(value) {
  const m = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,3}))?(Z|([+-])(\d{2}):(\d{2}))$/.exec(value);
  if (!m) throw new Error('Expected ISO timestamp YYYY-MM-DDTHH:mm:ss[.SSS]Z or an explicit +/-HH:mm offset');
  const [, year, month, day, hour, minute, second] = m;
  const date = new Date(0);
  date.setUTCFullYear(Number(year), Number(month) - 1, Number(day));
  date.setUTCHours(0, 0, 0, 0);
  if (date.getUTCFullYear() !== Number(year) || date.getUTCMonth() !== Number(month) - 1 || date.getUTCDate() !== Number(day) ||
      Number(hour) > 23 || Number(minute) > 59 || Number(second) > 59 || (m[8] !== 'Z' && (Number(m[10]) > 23 || Number(m[11]) > 59)) || !Number.isFinite(Date.parse(value))) {
    throw new Error(`Invalid ISO calendar date, time or offset: ${value}`);
  }
  return value;
}
export function args(argv = process.argv.slice(2)) {
  const result = {};
  for (let i = 0; i < argv.length; i++) {
    const key = argv[i];
    if (!key.startsWith('--') || !argv[i + 1] || argv[i + 1].startsWith('--')) throw new Error(`Expected --option value, got ${key}`);
    if (Object.hasOwn(result, key.slice(2))) throw new Error(`Duplicate option ${key}`);
    result[key.slice(2)] = argv[++i];
  }
  return result;
}
export function need(options, name) {
  if (!options[name]) throw new Error(`Missing --${name}`);
  return options[name];
}
export function only(options, allowed) {
  for (const key of Object.keys(options)) if (!allowed.includes(key)) throw new Error(`Unknown option --${key}`);
}
export const readJson = async file => JSON.parse((await fs.readFile(file, 'utf8')).replace(/^\uFEFF/, ''));
export async function writeJson(file, value, protectedPaths = []) {
  const target = path.resolve(file);
  if (protectedPaths.some(p => path.resolve(p) === target)) throw new Error(`Output would overwrite an input: ${target}`);
  await fs.mkdir(path.dirname(target), { recursive: true });
  await fs.writeFile(target, `${JSON.stringify(value, null, 2)}\n`, { flag: 'wx' });
}
export async function fileHash(file) {
  try { return sha256(await fs.readFile(file)); }
  catch (error) { if (error.code === 'ENOENT') return null; throw error; }
}
export async function isFile(file) {
  try { return (await fs.stat(file)).isFile(); }
  catch (error) { if (['ENOENT', 'ENOTDIR'].includes(error.code)) return false; throw error; }
}
export function within(root, relative) {
  const target = path.resolve(root, relative);
  const rel = path.relative(path.resolve(root), target);
  if (rel === '..' || rel.startsWith(`..${path.sep}`) || path.isAbsolute(rel)) throw new Error(`Path escapes root: ${relative}`);
  return target;
}
export async function checkLocalFile(root, relative) {
  const target = within(root, relative);
  if (!await isFile(target)) return false;
  const actual = await fs.realpath(target);
  within(await fs.realpath(root), path.relative(await fs.realpath(root), actual));
  return true;
}
export function urlKey(value, base) {
  const u = new URL(value, base);
  u.search = ''; u.hash = '';
  u.pathname = u.pathname.replace(/%[0-9a-f]{2}/gi, escape => {
    const character = String.fromCharCode(parseInt(escape.slice(1), 16));
    return /^[A-Za-z0-9._~-]$/.test(character) ? character : escape.toUpperCase();
  });
  if (u.pathname !== '/') u.pathname = u.pathname.replace(/\/$/, '');
  return u.href;
}
export function validateInventory(value) {
  if (value.schemaVersion !== 1 || !Array.isArray(value.articles) || !Array.isArray(value.routes) || !Array.isArray(value.origins)) throw new Error('Expected inventory schemaVersion 1 with articles, routes and origins arrays');
  if (!path.isAbsolute(value.root ?? '')) throw new Error('Inventory root must be absolute');
  if (value.asOf !== undefined) isoTimestamp(value.asOf);
  if (!value.origins.length || value.origins.some(origin => { const u = new URL(origin); return !['http:', 'https:'].includes(u.protocol) || u.origin !== origin; })) throw new Error('Inventory origins must be HTTP(S) origins without paths');
  for (const route of value.routes) {
    urlKey(route.url);
    if (route.anchors !== null && (!Array.isArray(route.anchors) || route.anchors.some(a => typeof a !== 'string'))) throw new Error('Route anchors must be an array of IDs or null for unknown');
  }
  const ids = new Set(), urls = new Set();
  for (const record of value.articles) {
    if (!record.id || ids.has(record.id)) throw new Error(`Missing or duplicate article id: ${record.id}`);
    ids.add(record.id);
    const key = urlKey(record.url);
    if (urls.has(key)) throw new Error(`Duplicate article URL: ${key}`);
    urls.add(key);
    if (typeof record.body !== 'string' || typeof record.searchText !== 'string' || typeof record.sourceText !== 'string') throw new Error(`${record.id}: full sourceText, body and searchText are required`);
    if (!Array.isArray(record.headings) || !Array.isArray(record.anchors) || !Array.isArray(record.references)) throw new Error(`${record.id}: headings, anchors, references must be arrays`);
    if (record.anchors.some(a => typeof a !== 'string') || record.references.some(r => !['link', 'asset'].includes(r.kind) || !(typeof r.url === 'string' || r.url === null))) throw new Error(`${record.id}: anchors must be strings; references need kind link/asset and string/null url`);
    if (!record.source?.path || !/^[a-f0-9]{64}$/.test(record.source.sha256 ?? '')) throw new Error(`${record.id}: source path and SHA256 required`);
    if (sha256(record.sourceText) !== record.source.sha256) throw new Error(`${record.id}: sourceText does not match source SHA256`);
    if (!['eligible', 'ineligible', 'invalid', 'unknown'].includes(record.localPublication?.status)) throw new Error(`${record.id}: explicit localPublication status required`);
    if (record.localPublication.asOf !== undefined) isoTimestamp(record.localPublication.asOf);
    if (record.livePublication !== 'unverified') throw new Error(`${record.id}: helpers do not verify live publication; use livePublication: unverified`);
  }
  return value;
}
export async function freshness(inventory) {
  const changed = [];
  if (inventory.sourceSet) {
    const names = (await fs.readdir(within(inventory.root, inventory.sourceSet.directory))).filter(n => n.endsWith(inventory.sourceSet.extension)).sort();
    if (stable(names) !== stable(inventory.sourceSet.names)) changed.push({ sourceSet: inventory.sourceSet.directory, expected: inventory.sourceSet.names, actual: names });
  }
  for (const record of inventory.articles) {
    const actual = await fileHash(within(inventory.root, record.source.path));
    if (actual !== record.source.sha256) changed.push({ id: record.id, path: record.source.path, expected: record.source.sha256, actual });
  }
  for (const dependency of inventory.dependencies ?? []) {
    const actual = await fileHash(within(inventory.root, dependency.path));
    if (actual !== dependency.sha256) changed.push({ dependency: dependency.path, expected: dependency.sha256, actual });
  }
  return changed;
}
export async function main(run) {
  try { await run(); }
  catch (error) { console.error(JSON.stringify({ error: error.message })); process.exitCode = 1; }
}
