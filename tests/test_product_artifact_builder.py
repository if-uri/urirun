from __future__ import annotations

from scripts import build_product_artifacts as builder


def test_product_artifact_builder_creates_manifest_and_checksums(tmp_path):
    manifest = builder.build(tmp_path, skip_python_build=True)

    assert manifest["product"] == "urirun"
    assert manifest["promotion"]["production_deploys"] is False
    platforms = {item["platform"] for item in manifest["artifacts"]}
    assert {"windows", "linux", "macos"} <= platforms
    for item in manifest["artifacts"]:
        artifact = tmp_path / item["file_name"]
        assert artifact.exists()
        assert item["sha256"] == builder._sha256(artifact)
        assert item["size"] == artifact.stat().st_size
    assert (tmp_path / "manifest.json").exists()
    assert (tmp_path / "SHA256SUMS").exists()
