import { createHash } from 'node:crypto';
import { spawn } from 'node:child_process';

export function parseUri(uri) {
  const match = String(uri).match(/^(?<scheme>[a-z][a-z0-9+.-]*):\/\/(?<target>[^/?#]+)(?<path>\/[^?#]*)?(?:\?(?<query>[^#]*))?(?:#(?<fragment>.*))?$/i);
  if (!match) throw new Error(`Invalid URI: ${uri}`);
  const segments = (match.groups.path || '/').split('/').filter(Boolean).map(decodeURIComponent);
  return {
    package: match.groups.scheme,
    target: decodeURIComponent(match.groups.target),
    segments,
    query: Object.fromEntries(new URLSearchParams(match.groups.query || '')),
    fragment: match.groups.fragment || null,
    raw: uri,
    normalized: `${match.groups.scheme}://${decodeURIComponent(match.groups.target)}/${segments.map(encodeURIComponent).join('/')}`,
  };
}

export function translate(d) {
  if (d.segments.length < 2) {
    throw new Error('URI must include resource and operation segments');
  }
  const [resource, operation, ...args] = d.segments;
  return { route: [d.package, resource, operation], package: d.package, target: d.target, resource, operation, args, descriptor: d };
}

export function hashUri(normalized) {
  return createHash('sha256').update(normalized).digest('hex');
}

export function resolveRoute(t, registry) {
  const routeEntry = registry?.[t.package]?.[t.resource]?.[t.operation];
  if (!routeEntry) throw new Error(`Route not found: ${t.route.join('.')}`);
  return routeEntry;
}

export const executors = {
  'local-function': async ({ routeEntry, target, args, payload, descriptor }) => {
    if (typeof routeEntry.ref !== 'function') throw new Error('Missing function ref');
    return await routeEntry.ref(target, args, payload, descriptor);
  },
  fetch: async ({ routeEntry, target, args, payload, descriptor }) => {
    return {
      ok: true,
      simulated: true,
      type: 'http',
      method: routeEntry.config.method || 'POST',
      url: routeEntry.config.url,
      body: { target, args, payload, descriptor }
    };
  },
  spawn: async ({ routeEntry, args }) => {
    return { ok: true, simulated: true, type: 'cli', command: [...(routeEntry.config.command || []), ...args] };
  },
  'shell-template': async ({ routeEntry, args }) => {
    const template = routeEntry.config.template || '';
    const command = template.replace(/\{(\d+)\}/g, (_, i) => args[Number(i)] || '');
    return { ok: true, simulated: true, type: 'shell', command };
  },
  'mqtt-publish': async ({ routeEntry, target, args, payload }) => {
    return { ok: true, simulated: true, type: 'mqtt', topic: [routeEntry.config.topicPrefix, target, ...args].filter(Boolean).join('/'), payload };
  }
};

export async function dispatch(uri, registry, payload, runtimeCache = new Map(), executorRegistry = executors) {
  const descriptor = parseUri(uri);
  const translation = translate(descriptor);
  const key = hashUri(descriptor.normalized);
  const cached = runtimeCache.get(key);
  const routeEntry = cached || resolveRoute(translation, registry);
  runtimeCache.set(key, routeEntry);
  const executor = executorRegistry[routeEntry.adapter] || executorRegistry[routeEntry.kind];
  if (!executor) throw new Error(`Executor not found: ${routeEntry.adapter || routeEntry.kind}`);
  return await executor({ routeEntry, descriptor, translation, target: translation.target, args: translation.args, payload });
}
