const URI_RE = /^(?<scheme>[a-z][a-z0-9+.-]*):\/\/(?<target>[^/?#]+)(?<path>\/[^?#]*)?(?:\?(?<query>[^#]*))?(?:#(?<fragment>.*))?$/i;
const CONFIG_KEYS = ['command', 'template', 'method', 'url', 'topicPrefix', 'steps'];

export function parseUri(uri) {
  const match = String(uri).match(URI_RE);
  if (!match) throw new Error(`Invalid URI: ${uri}`);
  const segments = (match.groups.path || '/').split('/').filter(Boolean).map(decodeURIComponent);
  return {
    package: match.groups.scheme,
    target: decodeURIComponent(match.groups.target),
    segments,
    query: Object.fromEntries(new URLSearchParams(match.groups.query || '')),
    fragment: match.groups.fragment || null,
    raw: uri,
  };
}

export function translate(descriptor) {
  if (descriptor.segments.length < 2) {
    throw new Error(`URI must include resource and operation: ${descriptor.raw}`);
  }
  const [resource, operation, ...args] = descriptor.segments;
  return {
    package: descriptor.package,
    target: descriptor.target,
    resource,
    operation,
    args,
    route: [descriptor.package, resource, operation],
    descriptor,
  };
}

export function routeKey(uri) {
  return translate(parseUri(uri)).route.join('.');
}

export function normalizeBinding(binding = {}) {
  const config = { ...(binding.config || {}) };
  for (const key of CONFIG_KEYS) {
    if (binding[key] !== undefined) config[key] = binding[key];
  }
  return {
    kind: binding.kind || 'function',
    adapter: binding.adapter || binding.kind || 'local-function',
    config,
    ref: binding.ref,
    meta: binding.meta || {},
  };
}

export function compileBindings(bindingMap) {
  const entries = bindingMap.bindings || bindingMap;
  const routes = {};
  for (const [uri, binding] of Object.entries(entries)) {
    const key = routeKey(uri);
    if (routes[key]) throw new Error(`Duplicate route: ${key}`);
    routes[key] = { uri, ...normalizeBinding(binding) };
  }
  return routes;
}

export function createUriRuntime({ bindings, adapters, refs = {}, state = {} }) {
  const routes = compileBindings(bindings);

  async function dispatch(uri, payload = {}) {
    const descriptor = parseUri(uri);
    const translation = translate(descriptor);
    const route = translation.route.join('.');
    const entry = routes[route];
    if (!entry) throw new Error(`Route not found: ${route}`);
    const adapter = adapters[entry.adapter] || adapters[entry.kind];
    if (!adapter) throw new Error(`Adapter not found: ${entry.adapter || entry.kind}`);
    return adapter({ entry, descriptor, translation, payload, refs, state, dispatch });
  }

  return { dispatch, routes, state };
}
