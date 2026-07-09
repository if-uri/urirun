<!--
This file contains realistic prompt examples and the expected `urirun:processes`
output that an LLM should produce when asked to solve specific tasks using the
markpact/marksync + urirun runtime contract.
-->

# markpact / marksync — LLM process examples

## Example 1: Build and deploy a Flask blog app with Docker

Prompt:

"""
You are an assistant that generates executable URI process plans for the
`urirun` runtime. The target environment supports `markpact` for contract-based
project generation and `marksync` for syncing projects into a live orchestration
server. Produce only a single JSON array inside a fenced code block labeled
`urirun:processes`.

Task: Generate a Flask blog application, package it with Docker support,
validate the generated contract, sync it to the marksync server, and run the
build in a Docker-enabled runtime.

Constraints:
- Use `work://` for project generation and review orchestration.
- Use `markpact://` for validation and runtime execution.
- Use `marksync://` for syncing contract state.
- Include clear dependencies and human approval where deployment risk exists.
"""

Result:

```urirun:processes
[
  {
    "id": "generate-flask-blog",
    "name": "Generate Flask blog markpact contract",
    "actor": "llm",
    "uri": "work://llm/generate/markpact-contract",
    "payload": {
      "prompt": "Create a markpact README for a Flask blog application with Docker support, SQLite storage, and a simple admin editor. Include dependencies, Dockerfile, and a runtime command."
    },
    "depends_on": [],
    "human_approval": false,
    "timeout_seconds": 420,
    "retries": 1
  },
  {
    "id": "validate-flask-blog",
    "name": "Validate generated Flask blog contract",
    "actor": "script",
    "uri": "markpact://local/validate",
    "payload": {
      "contract_path": "generated/flask-blog/README.md"
    },
    "depends_on": ["generate-flask-blog"],
    "human_approval": false,
    "timeout_seconds": 180,
    "retries": 1
  },
  {
    "id": "sync-flask-blog",
    "name": "Sync Flask blog contract to marksync server",
    "actor": "script",
    "uri": "marksync://sync-server/push",
    "payload": {
      "contract_path": "generated/flask-blog/README.md",
      "server_uri": "ws://localhost:8765"
    },
    "depends_on": ["validate-flask-blog"],
    "human_approval": false,
    "timeout_seconds": 120,
    "retries": 1
  },
  {
    "id": "run-flask-blog-docker",
    "name": "Run Flask blog contract in Docker runtime",
    "actor": "script",
    "uri": "markpact://local/run",
    "payload": {
      "contract_path": "generated/flask-blog/README.md",
      "docker": true
    },
    "depends_on": ["sync-flask-blog"],
    "human_approval": false,
    "timeout_seconds": 600,
    "retries": 2
  },
  {
    "id": "approve-production-blog",
    "name": "Human review and approve production deployment",
    "actor": "human",
    "uri": "work://human/review/approve",
    "payload": {
      "summary": "Review the Flask blog project and approve the Docker deployment to production."
    },
    "depends_on": ["run-flask-blog-docker"],
    "human_approval": true,
    "timeout_seconds": 3600,
    "retries": 0
  }
]
```

## Example 2: Signal Desktop via KVM (lenovo bare-metal)

**Adresowanie:** na węźle lenovo segment to `host` (`URIRUN_KVM_URI_HOST=host`), nie `laptop`.
Dispatch: `POST http://192.168.188.201:8765/run`. Przed keyboard: `router://host/plan/query/diagnose`.

Prompt:

"""
You are an LLM tasked with producing a process plan in `urirun:processes` format.
Send a text message via Signal Desktop on lenovo using ONLY registered kvm://host/... URIs.
Output one fenced ```urirun:processes``` block.
"""

Result:

```urirun:processes
[
  {
    "id": "kvm-doctor",
    "name": "KVM capability report (Wayland/display)",
    "actor": "script",
    "uri": "kvm://host/doctor/query/report",
    "payload": {},
    "depends_on": [],
    "human_approval": false,
    "timeout_seconds": 60,
    "retries": 1
  },
  {
    "id": "list-windows",
    "name": "Enumerate desktop windows",
    "actor": "script",
    "uri": "kvm://host/window/query/list",
    "payload": {},
    "depends_on": ["kvm-doctor"],
    "human_approval": false,
    "timeout_seconds": 30,
    "retries": 1
  },
  {
    "id": "focus-signal",
    "name": "Focus Signal window",
    "actor": "script",
    "uri": "kvm://host/window/command/focus",
    "payload": {"title": "Signal"},
    "depends_on": ["list-windows"],
    "human_approval": false,
    "timeout_seconds": 90,
    "retries": 2
  },
  {
    "id": "probe-composer",
    "name": "Defensive 3-char probe in composer",
    "actor": "script",
    "uri": "kvm://host/input/command/type",
    "payload": {"text": "TST"},
    "depends_on": ["focus-signal"],
    "human_approval": false,
    "timeout_seconds": 60,
    "retries": 1
  },
  {
    "id": "verify-probe",
    "name": "Verify probe visible in UI",
    "actor": "script",
    "uri": "kvm://host/ui/query/verify",
    "payload": {"text": "TST"},
    "depends_on": ["probe-composer"],
    "human_approval": false,
    "timeout_seconds": 30,
    "retries": 1
  },
  {
    "id": "type-message",
    "name": "Type full message",
    "actor": "script",
    "uri": "kvm://host/input/command/type",
    "payload": {"text": "Hello from urirun KVM flow"},
    "depends_on": ["verify-probe"],
    "human_approval": false,
    "timeout_seconds": 60,
    "retries": 1
  },
  {
    "id": "send-return",
    "name": "Send with Return key",
    "actor": "script",
    "uri": "kvm://host/input/command/key",
    "payload": {"keys": "Return"},
    "depends_on": ["type-message"],
    "human_approval": false,
    "timeout_seconds": 30,
    "retries": 1
  },
  {
    "id": "verify-sent",
    "name": "Post-send verification",
    "actor": "script",
    "uri": "kvm://host/ui/query/verify",
    "payload": {"text": "Hello from urirun"},
    "depends_on": ["send-return"],
    "human_approval": false,
    "timeout_seconds": 30,
    "retries": 1
  },
  {
    "id": "final-capture",
    "name": "Evidence screenshot",
    "actor": "script",
    "uri": "kvm://host/screen/query/capture",
    "payload": {"max_width": 480},
    "depends_on": ["verify-sent"],
    "human_approval": false,
    "timeout_seconds": 30,
    "retries": 0
  }
]
```

## Example 3: Sync a repo and execute a maintenance workflow

Prompt:

"""
Generate a URI process plan for a maintenance workflow that syncs a repository
contract into marksync, validates it with markpact, and runs a maintenance script.
The plan should be explicit about dependencies and include a human approval
step before the final maintenance execution.
"""

Result:

```urirun:processes
[
  {
    "id": "sync-repo-contract",
    "name": "Sync repository README contract to marksync",
    "actor": "script",
    "uri": "marksync://sync-server/push",
    "payload": {
      "contract_path": "repos/maintenance/README.md",
      "server_uri": "ws://localhost:8765"
    },
    "depends_on": [],
    "human_approval": false,
    "timeout_seconds": 120,
    "retries": 1
  },
  {
    "id": "validate-maintenance-contract",
    "name": "Validate maintenance contract with markpact",
    "actor": "script",
    "uri": "markpact://local/validate",
    "payload": {
      "contract_path": "repos/maintenance/README.md"
    },
    "depends_on": ["sync-repo-contract"],
    "human_approval": false,
    "timeout_seconds": 180,
    "retries": 1
  },
  {
    "id": "review-maintenance-plan",
    "name": "Human review maintenance workflow",
    "actor": "human",
    "uri": "work://human/review/maintenance-plan",
    "payload": {
      "summary": "Review the maintenance workflow and approve execution."
    },
    "depends_on": ["validate-maintenance-contract"],
    "human_approval": true,
    "timeout_seconds": 3600,
    "retries": 0
  },
  {
    "id": "execute-maintenance-script",
    "name": "Run maintenance script through the runtime",
    "actor": "script",
    "uri": "shell://maintenance-host/command/run",
    "payload": {
      "command": "./scripts/maintenance.sh",
      "cwd": "/workspace/repos/maintenance"
    },
    "depends_on": ["review-maintenance-plan"],
    "human_approval": false,
    "timeout_seconds": 600,
    "retries": 2
  }
]
```
