import {
  buildRegistryDocument,
  defaultAdapter,
  dispatchGenerated,
} from '../../../v4/examples/js/urihandler-v4.js';

export const BINDINGS_VERSION = 'urihandler.bindings.v5';

export function slugify(value, fallback = 'item') {
  return String(value).replace(/[^a-zA-Z0-9_.-]+/g, '-').replace(/^[-._]+|[-._]+$/g, '').toLowerCase() || fallback;
}

export function inferKind(binding) {
  if (binding.kind) return binding.kind;
  if (binding.command || binding.adapter === 'spawn') return 'cli';
  if (binding.template || binding.adapter === 'shell-template') return 'shell';
  if (binding.url || binding.method || binding.adapter === 'fetch') return 'http';
  if (binding.topicPrefix || binding.adapter === 'mqtt-publish') return 'mqtt';
  if (binding.ref) return 'function';
  return 'function';
}

export function binding(uri, options = {}) {
  const kind = inferKind(options);
  const config = { ...(options.config || {}) };
  for (const key of ['command', 'template', 'method', 'url', 'topicPrefix']) {
    if (options[key] !== undefined) config[key] = options[key];
  }
  const normalized = {
    uri,
    kind,
    adapter: options.adapter || defaultAdapter(kind),
    config,
    source: { ...(options.source || {}) },
  };
  for (const key of ['ref', 'policy', 'meta']) {
    if (options[key] !== undefined) normalized[key] = options[key];
  }
  return normalized;
}

export function routeSourceFromBinding(item) {
  const routeEntry = {
    kind: item.kind,
    adapter: item.adapter,
    config: item.config || {},
  };
  for (const key of ['ref', 'policy', 'meta']) {
    if (item[key] !== undefined) routeEntry[key] = item[key];
  }
  return { uri: item.uri, routeEntry, source: item.source || {} };
}

export function buildBindingDocument(bindings, { generatedAt = new Date().toISOString() } = {}) {
  return {
    version: BINDINGS_VERSION,
    generatedAt,
    bindingCount: bindings.length,
    bindings: [...bindings].sort((left, right) => left.uri.localeCompare(right.uri)),
  };
}

export function compileRegistryDocument(bindingDocumentOrBindings, options = {}) {
  const bindings = Array.isArray(bindingDocumentOrBindings)
    ? bindingDocumentOrBindings
    : bindingDocumentOrBindings.bindings || [];
  return buildRegistryDocument(bindings.map(routeSourceFromBinding), {
    generatedAt: options.generatedAt,
    onConflict: options.onConflict || 'keep',
  });
}

export function scanPackageJson(packageJson, source = { type: 'package-json' }) {
  const bindings = [];
  for (const script of Object.keys(packageJson.scripts || {}).sort()) {
    bindings.push(binding(`cli://local/npm/${slugify(script)}`, {
      kind: 'cli',
      adapter: 'spawn',
      command: ['start', 'stop', 'restart', 'test'].includes(script) ? ['npm', script] : ['npm', 'run', script],
      meta: { script: packageJson.scripts[script] },
      source: { ...source, script },
    }));
  }
  for (const section of ['dependencies', 'devDependencies', 'optionalDependencies', 'peerDependencies']) {
    for (const [name, spec] of Object.entries(packageJson[section] || {})) {
      if (!String(spec).includes('github.com') && !String(spec).startsWith('github:')) continue;
      bindings.push(binding(`package://github/${slugify(name)}/install`, {
        kind: 'process',
        adapter: 'spawn',
        command: ['npm', 'install', `${name}@${spec}`],
        source: { ...source, type: 'npm-github-dependency', section, dependency: name },
      }));
    }
  }
  return bindings;
}

export { dispatchGenerated };
