import assert from 'node:assert/strict';
import test from 'node:test';
import {
  binding,
  buildBindingDocument,
  compileRegistryDocument,
  dispatchGenerated,
  scanPackageJson,
} from './urihandler-v5.js';

test('builds v5 bindings and compiles them to registry', async () => {
  const bindings = [
    ...scanPackageJson({
      scripts: { test: 'node --test', build: 'vite build' },
      dependencies: { 'tellmesh-demo': 'github:tellmesh/demo-package' },
    }),
    binding('device://device-01/led/set/on', {
      kind: 'function',
      adapter: 'local-function',
      ref: 'devices.ledSet',
      source: { type: 'js-code-uri' },
    }),
  ];
  const document = buildBindingDocument(bindings, { generatedAt: '2026-06-19T00:00:00.000Z' });
  const registry = compileRegistryDocument(document, { generatedAt: '2026-06-19T00:00:00.000Z' });

  assert.equal(document.version, 'urihandler.bindings.v5');
  assert.equal(registry.version, 'urihandler.registry.v4');
  assert.deepEqual(registry.routes.cli.npm.test.config.command, ['npm', 'test']);
  assert.deepEqual(registry.routes.package['tellmesh-demo'].install.config.command, [
    'npm',
    'install',
    'tellmesh-demo@github:tellmesh/demo-package',
  ]);
  assert.equal(registry.routes.device.led.set.ref, 'devices.ledSet');
  assert.deepEqual(await dispatchGenerated('cli://local/npm/test', registry), {
    ok: true,
    simulated: true,
    type: 'cli',
    command: ['npm', 'test'],
  });
});
