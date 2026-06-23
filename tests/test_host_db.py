from __future__ import annotations

from urirun.host import host_db


def test_delete_logs_filters_stream_and_event(tmp_path):
    db = str(tmp_path / "host.db")
    chat_message = host_db.add_log(db, "chat", "message", {"role": "system"})
    chat_audit = host_db.add_log(db, "chat", "ask", {"prompt": "keep"})
    service_message = host_db.add_log(db, "service", "message", {"event": "keep"})

    deleted = host_db.delete_logs(
        db,
        [chat_message["id"], chat_audit["id"], service_message["id"]],
        stream="chat",
        event="message",
    )

    assert deleted == 1
    remaining = {item["id"] for item in host_db.recent_logs(db, limit=10)}
    assert chat_message["id"] not in remaining
    assert chat_audit["id"] in remaining
    assert service_message["id"] in remaining
