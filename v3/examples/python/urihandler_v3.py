import hashlib
import re
from urllib.parse import parse_qsl, unquote, quote

URI_RE = re.compile(r'^(?P<scheme>[a-z][a-z0-9+.-]*)://(?P<target>[^/?#]+)(?P<path>/[^?#]*)?(?:\?(?P<query>[^#]*))?(?:#(?P<fragment>.*))?$', re.I)

def parse_uri(uri: str):
    m = URI_RE.match(str(uri))
    if not m:
        raise ValueError(f'Invalid URI: {uri}')
    segments = [unquote(s) for s in (m.group('path') or '/').split('/') if s]
    return {
        'package': m.group('scheme'),
        'target': unquote(m.group('target')),
        'segments': segments,
        'query': dict(parse_qsl(m.group('query') or '')),
        'fragment': m.group('fragment') or None,
        'raw': uri,
        'normalized': f"{m.group('scheme')}://{unquote(m.group('target'))}/{'/'.join(quote(s, safe='') for s in segments)}",
    }

def translate(d: dict):
    if len(d['segments']) < 2:
        raise ValueError('URI must include resource and operation segments')
    resource, operation, *args = d['segments']
    return {'route': [d['package'], resource, operation], 'package': d['package'], 'target': d['target'], 'resource': resource, 'operation': operation, 'args': args, 'descriptor': d}

def hash_uri(normalized: str):
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

def resolve_route(t: dict, registry: dict):
    route_entry = registry.get(t['package'], {}).get(t['resource'], {}).get(t['operation'])
    if not route_entry:
        raise KeyError(f"Route not found: {'.'.join(t['route'])}")
    return route_entry

def exec_local_function(ctx):
    fn = ctx['routeEntry'].get('ref')
    if not callable(fn):
        raise ValueError('Missing function ref')
    return fn(ctx['target'], ctx['args'], ctx['payload'], ctx['descriptor'])

def exec_fetch(ctx):
    return {
        'ok': True,
        'simulated': True,
        'type': 'http',
        'method': ctx['routeEntry'].get('config', {}).get('method', 'POST'),
        'url': ctx['routeEntry'].get('config', {}).get('url'),
        'body': {
            'target': ctx['target'],
            'args': ctx['args'],
            'payload': ctx['payload'],
            'descriptor': ctx['descriptor'],
        }
    }

def exec_spawn(ctx):
    return {
        'ok': True,
        'simulated': True,
        'type': 'cli',
        'command': [*(ctx['routeEntry'].get('config', {}).get('command') or []), *ctx['args']]
    }

def exec_shell_template(ctx):
    template = ctx['routeEntry'].get('config', {}).get('template', '')
    command = template
    for idx, value in enumerate(ctx['args']):
        command = command.replace(f'{{{idx}}}', value)
    return {'ok': True, 'simulated': True, 'type': 'shell', 'command': command}

def exec_mqtt_publish(ctx):
    topic_prefix = ctx['routeEntry'].get('config', {}).get('topicPrefix', '')
    topic = '/'.join([x for x in [topic_prefix, ctx['target'], *ctx['args']] if x])
    return {'ok': True, 'simulated': True, 'type': 'mqtt', 'topic': topic, 'payload': ctx['payload']}

EXECUTORS = {
    'local-function': exec_local_function,
    'fetch': exec_fetch,
    'spawn': exec_spawn,
    'shell-template': exec_shell_template,
    'mqtt-publish': exec_mqtt_publish,
}

def dispatch(uri: str, registry: dict, payload=None, runtime_cache: dict | None = None, executors: dict | None = None):
    runtime_cache = runtime_cache if runtime_cache is not None else {}
    executor_registry = EXECUTORS if executors is None else executors
    descriptor = parse_uri(uri)
    translation = translate(descriptor)
    key = hash_uri(descriptor['normalized'])
    route_entry = runtime_cache.get(key) or resolve_route(translation, registry)
    runtime_cache[key] = route_entry
    executor = executor_registry.get(route_entry.get('adapter')) or executor_registry.get(route_entry.get('kind'))
    if executor is None:
        raise ValueError(f"Executor not found: {route_entry.get('adapter') or route_entry.get('kind')}")
    return executor({'routeEntry': route_entry, 'descriptor': descriptor, 'translation': translation, 'target': translation['target'], 'args': translation['args'], 'payload': payload})
