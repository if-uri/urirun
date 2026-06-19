import assert from 'node:assert/strict';
import test from 'node:test';
import {
  dispatch,
  executors,
  hashUri,
  parseUri,
  resolveRoute,
  translate,
} from './urihandler-v3.js';

const registry = {
  artifact: {
    build: {
      frontend: {
        adapter: 'spawn',
        config: { command: ['npm', 'run', 'build'] },
        kind: 'process',
      },
    },
  },
  cli: {
    git: {
      status: {
        adapter: 'spawn',
        config: { command: ['git', 'status'] },
        kind: 'cli',
      },
    },
  },
  device: {
    led: {
      set: {
        adapter: 'local-function',
        kind: 'function',
        ref: (target, args, payload, descriptor) => ({ descriptor, ok: true, payload, state: args[0], target }),
      },
    },
  },
  log: {
    info: {
      'user-created': {
        adapter: 'local-function',
        kind: 'function',
        ref: (target, args, payload, descriptor) => ({ args, descriptor, event: 'user-created', ok: true, payload, sink: target }),
      },
    },
  },
  mqtt: {
    publish: {
      home: {
        adapter: 'mqtt-publish',
        config: { topicPrefix: 'home' },
        kind: 'mqtt',
      },
    },
  },
  service: {
    user: {
      create: {
        adapter: 'fetch',
        config: { method: 'POST', url: 'http://user-service.local/api/users' },
        kind: 'http',
      },
    },
  },
  shell: {
    system: {
      restart: {
        adapter: 'shell-template',
        config: { template: 'systemctl restart {0}' },
        kind: 'shell',
      },
    },
  },
};

test('parses and translates v3 route entry model', () => {
  const descriptor = parseUri('service://api/user/create/basic?trace=1#ops');
  assert.deepEqual(translate(descriptor), {
    args: ['basic'],
    descriptor,
    operation: 'create',
    package: 'service',
    resource: 'user',
    route: ['service', 'user', 'create'],
    target: 'api',
  });
});

test('dispatches function, http, cli, shell, mqtt, and artifact adapters', async () => {
  assert.equal((await dispatch('device://device-01/led/set/on', registry, { source: 'test' })).state, 'on');
  assert.equal((await dispatch('service://api/user/create/basic', registry, { name: 'Ada' })).type, 'http');
  assert.deepEqual((await dispatch('cli://local/git/status', registry)).command, ['git', 'status']);
  assert.equal((await dispatch('shell://local/system/restart/nginx', registry)).command, 'systemctl restart nginx');
  assert.equal((await dispatch('mqtt://broker/publish/home/kitchen/light/on', registry, { on: true })).topic, 'home/broker/kitchen/light/on');
  assert.deepEqual((await dispatch('artifact://runner/build/frontend/release', registry)).command, ['npm', 'run', 'build', 'release']);
});

test('uses runtime route cache and custom executor registry', async () => {
  const runtimeCache = new Map();
  assert.equal((await dispatch('service://api/user/create/basic', registry, {}, runtimeCache)).type, 'http');
  assert.equal(runtimeCache.size, 1);
  const routeEntry = resolveRoute(translate(parseUri('service://api/user/create/basic')), registry);
  assert.equal([...runtimeCache.values()][0], routeEntry);

  const customExecutors = {
    ...executors,
    fetch: ({ routeEntry, target, args, payload }) => ({ adapter: 'custom-fetch', args, payload, target, url: routeEntry.config.url }),
  };
  assert.equal((await dispatch('service://api/user/create/basic', registry, {}, new Map(), customExecutors)).adapter, 'custom-fetch');
});

test('rejects invalid routes and executors', async () => {
  assert.throws(() => translate(parseUri('cli://local/git')), /resource and operation/);
  await assert.rejects(() => dispatch('device://device-01/motor/set/on', registry), /Route not found/);
  await assert.rejects(() => dispatch('device://device-01/led/set/on', registry, {}, new Map(), {}), /Executor not found/);
});

test('hashes normalized URI with sha256 hex', () => {
  assert.match(hashUri('device://device-01/led/set/on'), /^[a-f0-9]{64}$/);
});
