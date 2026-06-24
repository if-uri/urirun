from urirun.host import scanner_bridge


class BridgeRecorder:
    def __init__(self) -> None:
        self.artifacts = []
        self.messages = []
        self.logs = []

    def deps(self) -> scanner_bridge.ScannerBridgeDeps:
        return scanner_bridge.ScannerBridgeDeps(
            preview_url=lambda path, project: f"/preview?path={path}",
            register_artifact=self.register_artifact,
            chat_message=self.chat_message,
            add_chat_message=self.add_chat_message,
            add_log=self.add_log,
        )

    def register_artifact(self, db, kind, uri, path, meta):
        row = {"kind": kind, "uri": uri, "path": path, "meta": meta}
        self.artifacts.append(row)
        return row

    def chat_message(self, role, content, *, detail=None, attachments=None):
        return {
            "role": role,
            "content": content,
            "detail": detail or {},
            "attachments": attachments or [],
        }

    def add_chat_message(self, db, message):
        self.messages.append(message)
        return message

    def add_log(self, db, stream, event, detail):
        self.logs.append({"db": db, "stream": stream, "event": event, "detail": detail})
        return self.logs[-1]


def test_register_scanner_result_uses_document_pdf_as_canonical_artifact(tmp_path) -> None:
    recorder = BridgeRecorder()
    original = tmp_path / "raw.jpg"
    original.write_bytes(b"raw")
    missing_crop = tmp_path / "missing-crop.jpg"
    pdf = tmp_path / "document.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")

    result = scanner_bridge.register_scanner_result(
        recorder.deps(),
        str(tmp_path),
        ":memory:",
        uri="scanner://host/capture/duplicate",
        display_path=missing_crop,
        original_path=original,
        meta={"source": "phone"},
        crop={"ok": True, "path": str(missing_crop)},
        ocr={"ok": True, "text": "PARAGON", "chars": 7},
        document={
            "ok": True,
            "duplicate": True,
            "docId": "DOC-RESCAN",
            "duplicateOf": "DOC-DUP",
            "path": str(pdf),
        },
        content_prefix="Phone scan saved",
    )

    assert result["scanArtifact"]["skipped"] is True
    assert result["documentArtifact"]["kind"] == "document-pdf"
    assert result["documentArtifact"]["uri"] == "document://host/DOC-DUP"
    assert recorder.artifacts == [result["documentArtifact"]]
    assert recorder.messages[-1]["attachments"][0]["kind"] == "document-pdf"


def test_register_scanner_result_registers_camera_scan_without_document(tmp_path) -> None:
    recorder = BridgeRecorder()
    original = tmp_path / "raw.jpg"
    original.write_bytes(b"raw")
    crop = tmp_path / "crop.jpg"
    crop.write_bytes(b"crop")

    result = scanner_bridge.register_scanner_result(
        recorder.deps(),
        str(tmp_path),
        ":memory:",
        uri="scanner://host/capture/raw",
        display_path=crop,
        original_path=original,
        meta={"source": "phone"},
        crop={"ok": True, "path": str(crop)},
        ocr={"ok": False, "error": "no text"},
        document={"ok": False, "reason": "analysis-only"},
        content_prefix="Phone scan saved",
    )

    assert result["scanArtifact"]["kind"] == "camera-scan"
    assert result["documentArtifact"] is None
    assert recorder.artifacts == [result["scanArtifact"]]
    assert recorder.messages[-1]["attachments"] == []


def test_scanner_session_logs_and_adds_chat_message() -> None:
    recorder = BridgeRecorder()

    result = scanner_bridge.scanner_session(recorder.deps(), ":memory:", {
        "event": "open",
        "href": "https://host/scanner",
        "width": 390,
        "height": 844,
        "userAgent": "phone",
    })

    assert result["ok"] is True
    assert result["uri"].startswith("scanner://host/session/")
    assert recorder.logs[-1]["stream"] == "scanner-session"
    assert recorder.logs[-1]["event"] == "open"
    assert recorder.messages[-1]["content"] == "Phone scanner opened"
    assert recorder.messages[-1]["detail"]["href"] == "https://host/scanner"


def test_uri_event_logs_js_event() -> None:
    events = []
    deps = scanner_bridge.ScannerBridgeDeps(
        preview_url=lambda path, project: None,
        register_artifact=lambda db, kind, uri, path, meta: {},
        chat_message=lambda *a, **k: {},
        add_chat_message=lambda db, message: None,
        add_log=lambda db, stream, event, detail: events.append((stream, event, detail)),
    )

    result = scanner_bridge.uri_event(deps, ":memory:", {
        "s": ["scanner"],
        "e": ["scanner_actions_ready"],
        "p": ["/scanner"],
        "l": ["ready"],
    })

    assert result == {"ok": True, "event": "scanner_actions_ready"}
    assert events[-1][0] == "uri-js"
    assert events[-1][1] == "scanner_actions_ready"
    assert events[-1][2]["path"] == "/scanner"


def test_page_action_queue_round_trip() -> None:
    recorder = BridgeRecorder()
    scanner_bridge.PAGE_ACTION_QUEUES.clear()

    queued = scanner_bridge.page_action_enqueue(
        recorder.deps(),
        ":memory:",
        target="scanner",
        uri="scanner://page/camera/command/start",
        payload={"x": 1},
        uri_mode=lambda mode: "execute",
        utc_now=lambda: "2026-06-24T00:00:00Z",
    )
    polled = scanner_bridge.page_action_poll("scanner")

    assert queued["queued"] is True
    assert polled["count"] == 1
    assert polled["actions"][0]["payload"] == {"x": 1}
    assert scanner_bridge.page_action_poll("scanner")["count"] == 0
