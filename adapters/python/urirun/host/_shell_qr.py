# Author: Tom Sapletta · Part of the ifURI solution.
"""Periodic QR panel in the host-dashboard shell.

When the dashboard runs in a terminal, print — at startup and every interval — a scannable QR
for the LAN URL (so a phone can open the dashboard) plus the clickable local URL (most terminals
hyperlink an http:// URL). The QR is for mobile; the local line is for the desktop you're on.

QR rendering uses the optional ``qrcode`` package; without it, the panel still prints the URLs
and a one-line install hint — never a hard dependency.
"""
from __future__ import annotations

import os
import socket
import sys
import threading
import time


def _lan_ip() -> str:
    """Best-effort LAN IP a phone on the same network can reach (not 127.0.0.1)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("192.168.255.255", 1))   # no packets sent; just picks the egress iface
            ip = s.getsockname()[0]
        finally:
            s.close()
        if ip and not ip.startswith("127."):
            return ip
    except OSError:
        pass
    try:
        return socket.gethostbyname(socket.gethostname())
    except OSError:
        return "127.0.0.1"


def terminal_qr(url: str) -> str | None:
    """A compact, scannable QR as text (unicode half-blocks: two matrix rows per line). None
    when the ``qrcode`` package isn't installed."""
    try:
        import qrcode
    except Exception:  # noqa: BLE001
        return None
    qr = qrcode.QRCode(border=2, error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(url)
    qr.make(fit=True)
    m = qr.get_matrix()
    # A "dark" module must render as the LIGHT terminal cell to scan on a dark background, so we
    # invert: dark module -> space (light), light module -> block. Half-blocks pack two rows.
    out = []
    for y in range(0, len(m), 2):
        row = []
        for x in range(len(m[0])):
            top = m[y][x]
            bot = m[y + 1][x] if y + 1 < len(m) else False
            row.append(" " if (top and bot) else "▄" if top else "▀" if bot else "█")
        out.append("".join(row))
    return "\n".join(out)


def _hyperlink(url: str, label: str | None = None) -> str:
    """OSC 8 terminal hyperlink so the local URL is clickable; falls back to plain text."""
    return f"\033]8;;{url}\033\\{label or url}\033]8;;\033\\"


def print_qr_panel(scheme: str, port: int, *, local_host: str = "127.0.0.1") -> None:
    lan = f"{scheme}://{_lan_ip()}:{port}/"
    local = f"{scheme}://{local_host}:{port}/"
    lines = ["", "\033[36m── ifURI dashboard ──────────────────────────────\033[0m"]
    qr = terminal_qr(lan)
    if qr:
        lines.append("\033[2m📱 Scan on your phone (same network):\033[0m")
        lines.append(qr)
    else:
        lines.append("\033[2m📱 phone URL (pip install qrcode for a scannable code):\033[0m")
    lines.append(f"   📱 mobile:  {lan}")
    lines.append(f"   🖱  local:   {_hyperlink(local)}")
    lines.append("\033[36m──────────────────────────────────────────────────\033[0m")
    sys.stderr.write("\n".join(lines) + "\n")
    sys.stderr.flush()


def start_qr_panel(scheme: str, port: int, *, local_host: str = "127.0.0.1") -> None:
    """Print the QR panel once now, then every URIRUN_QR_INTERVAL seconds (default 300; 0 = once)
    on a daemon thread. Enabled by the caller (startup_qr / URIRUN_QR_SHELL)."""
    interval = 0
    try:
        interval = int(os.environ.get("URIRUN_QR_INTERVAL", "300"))
    except ValueError:
        interval = 300
    print_qr_panel(scheme, port, local_host=local_host)
    if interval <= 0:
        return

    def _loop() -> None:
        while True:
            time.sleep(interval)
            try:
                print_qr_panel(scheme, port, local_host=local_host)
            except Exception:  # noqa: BLE001 - a print must never take the server down
                return
    threading.Thread(target=_loop, name="urirun-qr-panel", daemon=True).start()
