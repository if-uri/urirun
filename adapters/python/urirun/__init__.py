import re
from urllib.parse import parse_qsl, unquote

URI_RE = re.compile(r'^(?P<scheme>[a-z][a-z0-9+.-]*)://(?P<target>[^/?#]+)(?P<path>/[^?#]*)?(?:\?(?P<query>[^#]*))?(?:#(?P<fragment>.*))?$', re.I)

def parse_uri(uri: str):
    m = URI_RE.match(str(uri))
    if not m:
        raise ValueError(f"Invalid URI: {uri}")
    path = m.group('path') or '/'
    segments = [unquote(s) for s in path.split('/') if s]
    return {
        'package': m.group('scheme'),
        'target': unquote(m.group('target')),
        'segments': segments,
        'query': dict(parse_qsl(m.group('query') or '')),
        'fragment': m.group('fragment') or None,
        'raw': uri,
    }

def build_invocation(descriptor: dict):
    function_name = '_'.join(descriptor['segments'][:2])
    args = [descriptor['target'], *descriptor['segments'][2:]]
    descriptor = dict(descriptor)
    descriptor['functionName'] = function_name
    descriptor['args'] = args
    return descriptor

def dispatch(uri: str, registry: dict, payload=None):
    descriptor = parse_uri(uri)
    invocation = build_invocation(descriptor)
    mod = registry.get(invocation['package'])
    if mod is None:
        raise KeyError(f"Unknown package: {invocation['package']}")
    fn = getattr(mod, invocation['functionName'], None) if not isinstance(mod, dict) else mod.get(invocation['functionName'])
    if not callable(fn):
        raise KeyError(f"Unknown function: {invocation['package']}.{invocation['functionName']}")
    return fn(*invocation['args'], payload, invocation)


def command(uri: str, **options):
    """Declare a v2 URI command with the public top-level decorator API.

    This is the preferred spelling for connector authors:

        import urirun

        @urirun.command("demo://host/http/query/status")
        def status(url: str):
            return ["demo", "{url}"]

    ``urirun.v2.uri_command`` remains supported for existing code.
    """
    from urirun.v2 import uri_command

    return uri_command(uri, **options)


def shell(uri: str, **options):
    """Declare a v2 shell-template URI route with the top-level API."""
    from urirun.v2 import uri_shell

    return uri_shell(uri, **options)


def connector_bindings(*, routes=None, connector=None):
    """Export v2 bindings generated from ``@urirun.command`` decorators."""
    from urirun.v2 import connector_bindings as _connector_bindings

    return _connector_bindings(routes=routes, connector=connector)
