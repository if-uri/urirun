import { dispatch } from './urihandler-v3.js';

const runtimeCache = new Map();
const registry = {
  device: {
    led: {
      set: {
        kind: 'function',
        adapter: 'local-function',
        ref: (target, args, payload, descriptor) => ({ ok: true, type: 'function', target, state: args[0], payload, descriptor })
      }
    }
  },
  log: {
    info: {
      'user-created': {
        kind: 'function',
        adapter: 'local-function',
        ref: (target, args, payload, descriptor) => ({ ok: true, type: 'log', sink: target, event: 'user-created', args, payload, descriptor })
      }
    }
  },
  service: {
    user: {
      create: {
        kind: 'http',
        adapter: 'fetch',
        config: { method: 'POST', url: 'http://user-service.local/api/users' }
      }
    }
  },
  cli: {
    git: {
      status: {
        kind: 'cli',
        adapter: 'spawn',
        config: { command: ['git', 'status'] }
      }
    }
  },
  shell: {
    system: {
      restart: {
        kind: 'shell',
        adapter: 'shell-template',
        config: { template: 'systemctl restart {0}' }
      }
    }
  }
};

console.log(await dispatch('device://device-01/led/set/on', registry, { source: 'frontend' }, runtimeCache));
console.log(await dispatch('log://app/info/user-created', registry, { userId: 42 }, runtimeCache));
console.log(await dispatch('service://api/user/create/basic', registry, { name: 'Ada' }, runtimeCache));
console.log(await dispatch('cli://local/git/status', registry, null, runtimeCache));
console.log(await dispatch('shell://local/system/restart/nginx', registry, null, runtimeCache));
