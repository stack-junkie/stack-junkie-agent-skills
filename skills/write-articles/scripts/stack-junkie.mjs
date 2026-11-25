import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { createRequire } from 'node:module';
import { sha256, fileHash } from './lib.mjs';

export async function adapter(root) {
  const require = createRequire(path.join(root, 'package.json'));
  const load = async name => import(pathToFileURL(require.resolve(name)).href);
  const [schema, publication, mdx, gfm, slugger] = await Promise.all([
    import(pathToFileURL(path.join(root, 'lib/content-schema.mjs')).href),
    import(pathToFileURL(path.join(root, 'lib/publication.ts')).href),
    load('@mdx-js/mdx'), load('remark-gfm'), load('github-slugger'),
  ]);
  const processor = mdx.createProcessor({ remarkPlugins: [gfm.default] });
  function bodyDetails(content, offset = 0) {
    const headings = [], anchors = [], references = [], definitions = new Map();
    const tree = processor.parse(content); // Parse only. Never compile, import or evaluate article MDX.
    const s = new slugger.default();
    const text = node => node.value ?? (node.children ?? []).map(text).join('');
    const pending = [], plainText = [];
    function visit(node, inExample = false) {
      const example = inExample || node.type === 'blockquote' || ['pre', 'code'].includes(node.name?.toLowerCase());
      const line = (node.position?.start?.line ?? 1) + offset;
      if (node.type === 'text' && !example) plainText.push(node);
      if (node.type === 'heading') {
        const label = text(node), anchor = s.slug(label);
        headings.push({ depth: node.depth, text: label, anchor, line }); anchors.push(anchor);
      }
      if (node.type === 'definition') definitions.set(node.identifier, node.url);
      if (['mdxFlowExpression', 'mdxTextExpression'].includes(node.type)) references.push({ url: null, kind: 'link', line, dynamic: true, reason: 'Expression-generated content is not evaluated' });
      if (['link', 'image', 'linkReference', 'imageReference'].includes(node.type)) pending.push({ node, line });
      for (const attr of node.attributes ?? []) {
        if (attr.type === 'mdxJsxExpressionAttribute') references.push({ url: null, kind: 'link', line, dynamic: true, reason: 'Spread attributes cannot be resolved statically' });
        if (attr.name === 'id' && typeof attr.value === 'string') anchors.push(attr.value);
        if (['src', 'href', 'poster'].includes(attr.name)) references.push({ url: typeof attr.value === 'string' ? attr.value : null, kind: attr.name === 'href' ? 'link' : 'asset', line, dynamic: typeof attr.value !== 'string' });
      }
      for (const child of node.children ?? []) visit(child, example);
    }
    visit(tree);
    for (const { node, line } of pending) references.push({ url: node.url ?? definitions.get(node.identifier) ?? null, kind: node.type.startsWith('image') ? 'asset' : 'link', line, unresolvedReference: !node.url && !definitions.has(node.identifier) });
    for (const node of plainText) {
      const raw = content.slice(node.position.start.offset, node.position.end.offset);
      for (const match of raw.matchAll(/!?\[([^\]\r\n]+)\]\s*\[([^\]\r\n]*)\]/g)) {
        if (match.index > 0 && raw[match.index - 1] === '\\') continue;
        const label = (match[2] || match[1]).trim().replace(/\s+/g, ' ').toLowerCase();
        if (definitions.has(label)) continue;
        references.push({ url: null, kind: match[0].startsWith('!') ? 'asset' : 'link',
          line: node.position.start.line + offset + raw.slice(0, match.index).split(/\r\n|\n|\r/).length - 1,
          unresolvedReference: true, undefinedReferenceCandidate: true, label, syntax: match[0] });
      }
    }
    return { headings, anchors: [...new Set(anchors)], references, ...schema.extractSearchContent(content) };
  }
  function analyze(sourceText, file, options = {}) {
    const { data, content } = schema.parseFrontmatter(sourceText, file);
    const offset = sourceText.slice(0, sourceText.length - content.length).split(/\r\n|\n|\r/).length - 1;
    const result = schema.frontmatterSchema.safeParse(data);
    const schemaIssues = result.success ? [] : result.error.issues.map(i => `${i.path.join('.')}: ${i.message}`);
    if (options.publishedFile !== undefined) {
      const publishedFile = options.publishedFile;
      if (!/^[a-z0-9]+(?:-[a-z0-9]+)*\.mdx$/.test(publishedFile)) schemaIssues.push('publishedFile: Use the intended lowercase article filename, ending .mdx');
      else {
        // Reuse the authoritative filename/canonical contract. Asset existence is checked
        // separately against public/ or the explicit private asset map, without moving files.
        const { image, ...validationData } = data;
        if (image !== undefined && (typeof image !== 'string' || !image.startsWith('/') || image.startsWith('//') || /[?#\\]/.test(image))) schemaIssues.push('image: Use a public root-relative asset path');
        try { schema.parseArticle(`---\n${JSON.stringify(validationData)}\n---\n${content}`, `content/blog/${publishedFile}`, root); }
        catch (error) { schemaIssues.push(error.message); }
      }
    }
    const details = bodyDetails(content, offset);
    if (typeof data.image === 'string') details.references.unshift({ url: data.image, kind: 'asset', line: 1, frontmatter: true });
    for (const target of [...(Array.isArray(data.related) ? data.related : []), ...(typeof data.clusterHub === 'string' ? [data.clusterHub] : [])]) {
      if (typeof target === 'string') details.references.push({ url: `/blog/${target}`, kind: 'link', line: 1, frontmatter: true });
    }
    return { metadata: data, body: content, ...details, schemaIssues };
  }
  async function inventory(asOf) {
    const directory = path.join(root, 'content/blog');
    const files = (await fs.readdir(directory)).filter(f => f.endsWith('.mdx')).sort();
    const articles = [];
    for (const name of files) {
      const file = `content/blog/${name}`, sourceText = await fs.readFile(path.join(root, file), 'utf8');
      const id = name.slice(0, -4), issues = [];
      let parsed;
      try {
        parsed = analyze(sourceText, file); issues.push(...parsed.schemaIssues);
        try { schema.parseArticle(sourceText, file, root); } catch (error) { issues.push(error.message); }
      } catch (error) {
        issues.push(error.message);
        parsed = { metadata: {}, body: sourceText, searchText: sourceText, headings: [], anchors: [], references: [] };
      }
      const eligible = !issues.length && publication.isPublishedPost(parsed.metadata, Date.parse(asOf));
      articles.push({ id, url: `https://www.stack-junkie.com/blog/${id}`, title: parsed.metadata.title ?? id,
        source: { path: file, sha256: sha256(sourceText) }, sourceText, body: parsed.body,
        searchText: parsed.searchText, metadata: parsed.metadata, headings: parsed.headings, anchors: parsed.anchors, references: parsed.references,
        localPublication: { status: issues.length ? 'invalid' : eligible ? 'eligible' : 'ineligible', asOf, reason: issues.length ? 'Local schema or asset errors' : eligible ? 'Current local schema passes; draft false and date reached' : 'Draft or scheduled date', issues },
        livePublication: 'unverified' });
    }
    const dependencies = [];
    for (const file of ['lib/content-schema.mjs', 'lib/publication.ts', 'lib/tags.ts', 'lib/hub-defs.ts', 'lib/authors.ts', 'package-lock.json']) dependencies.push({ path: file, sha256: await fileHash(path.join(root, file)) });
    const routes = [];
    async function walk(dir, segments = []) {
      for (const entry of await fs.readdir(dir, { withFileTypes: true })) {
        if (entry.isDirectory()) {
          if (entry.name.startsWith('_') || entry.name.startsWith('@')) continue;
          const next = /^\(.+\)$/.test(entry.name) ? segments : [...segments, entry.name];
          await walk(path.join(dir, entry.name), next);
        } else if (/^page\.(tsx|ts|jsx|js|mdx)$/.test(entry.name) && !segments.some(s => s.includes('['))) {
          const file = path.join(dir, entry.name);
          routes.push({ url: `https://www.stack-junkie.com/${segments.join('/')}`, anchors: null, evidence: 'local-static-route-file', source: path.relative(root, file).replaceAll('\\', '/') });
          dependencies.push({ path: path.relative(root, file).replaceAll('\\', '/'), sha256: await fileHash(file) });
        }
      }
    }
    await walk(path.join(root, 'app'));
    return { schemaVersion: 1, adapter: 'stack-junkie', root, capturedAt: new Date().toISOString(), asOf,
      origins: ['https://www.stack-junkie.com', 'https://stack-junkie.com'], articles, routes, dependencies,
      sourceSet: { directory: 'content/blog', extension: '.mdx', names: files },
      limitations: ['Local working-tree snapshot, including dirty files; no live deployment verification.', 'Static MDX is parsed, never executed. Dynamic MDX references are unresolved.', 'Static route files do not establish redirects, generated dynamic routes or rendered anchors.'] };
  }
  return { analyze, inventory };
}
