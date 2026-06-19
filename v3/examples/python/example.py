from urihandler_v3 import dispatch

runtime_cache = {}
registry = {
    'device': {
        'led': {
            'set': {
                'kind': 'function',
                'adapter': 'local-function',
                'ref': lambda target, args, payload, descriptor: {'ok': True, 'type': 'function', 'target': target, 'state': args[0] if args else None, 'payload': payload, 'descriptor': descriptor}
            }
        }
    },
    'service': {
        'user': {
            'create': {
                'kind': 'http',
                'adapter': 'fetch',
                'config': {'method': 'POST', 'url': 'http://user-service.local/api/users'}
            }
        }
    },
    'cli': {
        'git': {
            'status': {
                'kind': 'cli',
                'adapter': 'spawn',
                'config': {'command': ['git', 'status']}
            }
        }
    },
    'shell': {
        'system': {
            'restart': {
                'kind': 'shell',
                'adapter': 'shell-template',
                'config': {'template': 'systemctl restart {0}'}
            }
        }
    },
    'log': {
        'info': {
            'user-created': {
                'kind': 'function',
                'adapter': 'local-function',
                'ref': lambda target, args, payload, descriptor: {'ok': True, 'type': 'log', 'sink': target, 'event': 'user-created', 'args': args, 'payload': payload, 'descriptor': descriptor}
            }
        }
    }
}

print(dispatch('device://device-01/led/set/on', registry, {'source': 'frontend'}, runtime_cache))
print(dispatch('service://api/user/create/basic', registry, {'name': 'Ada'}, runtime_cache))
print(dispatch('cli://local/git/status', registry, None, runtime_cache))
print(dispatch('shell://local/system/restart/nginx', registry, None, runtime_cache))
print(dispatch('log://app/info/user-created', registry, {'userId': 42}, runtime_cache))
