import {
  binding,
  buildBindingDocument,
  compileRegistryDocument,
  dispatchGenerated,
  scanPackageJson,
} from './urihandler-v5.js';

const bindings = [
  ...scanPackageJson({
    scripts: { test: 'node --test', build: 'vite build' },
    dependencies: { 'tellmesh-demo': 'github:tellmesh/demo-package' },
  }),
  binding('device://device-01/led/set/on', {
    kind: 'function',
    adapter: 'local-function',
    ref: 'devices.ledSet',
    source: { type: 'manual-js-binding' },
  }),
];

const bindingDocument = buildBindingDocument(bindings);
const registry = compileRegistryDocument(bindingDocument);

console.log(bindingDocument.version, bindingDocument.bindingCount);
console.log(await dispatchGenerated('cli://local/npm/test', registry));
