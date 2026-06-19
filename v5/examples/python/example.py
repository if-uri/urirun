from pathlib import Path

from urihandler.v5 import build_binding_document, compile_registry_document, scan_path
from urihandler.v4 import dispatch_generated


project = Path(__file__).resolve().parents[1] / "project"
bindings = build_binding_document(scan_path(project))
registry = compile_registry_document(bindings)

print(bindings["version"], bindings["bindingCount"])
print(dispatch_generated("cli://local/npm/test", registry))
