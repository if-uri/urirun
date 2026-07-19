from __future__ import annotations

import json
import subprocess
import sys


def test_add_openapi_loads_extracted_cli_bridge_in_fresh_process(tmp_path):
    spec = tmp_path / "openapi.json"
    spec.write_text(
        json.dumps(
            {
                "openapi": "3.0.3",
                "info": {"title": "pets", "version": "1"},
                "servers": [{"url": "https://example.test"}],
                "paths": {
                    "/pets": {
                        "get": {
                            "operationId": "listPets",
                            "responses": {"200": {"description": "ok"}},
                        }
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    process = subprocess.run(
        [
            sys.executable,
            "-c",
            "from urirun.runtime.v2 import main; raise SystemExit(main())",
            "add-openapi",
            str(spec),
            "--scheme",
            "pet",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert process.returncode == 0, process.stderr or process.stdout
    generated = json.loads(process.stdout)
    assert "pet://api/pets/query/get" in generated["bindings"]
