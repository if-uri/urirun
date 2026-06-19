import { check, run } from './urihandler-v6.js';

const registry = {
  version: 'urihandler.registry.v4',
  routes: { cli: { echo: { say: { kind: 'cli', adapter: 'spawn', config: { command: ['echo'] } } } } },
};

// Default deny: no policy means execute is blocked.
console.log('blocked:', check('cli://local/echo/say/hi', registry).decision.allowed);

// With an allow rule the command actually runs through the gate.
const result = await run('cli://local/echo/say/hello', registry, null, {
  mode: 'execute',
  policy: { execute: { allow: ['cli://local/echo/*'] } },
});
console.log('ok:', result.ok, 'stdout:', result.result.stdout.trim());
