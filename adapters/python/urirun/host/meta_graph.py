# Author: Tom Sapletta · Part of the ifURI solution.
"""meta_graph — WYŻSZA WARSTWA dla wnioskowania: graf RELACJI całości.

Nad pojedynczymi ticketami i wnioskami buduje metadane-relacje:
  * graf ticketów  — węzły=tickety, krawędzie=blocked_by / generates / retries / diagnoses /
    clustered_in (nora) / escalates / enables (done→odblokowuje);
  * graf wniosków  — węzły=trwałe wnioski (pamięci), krawędzie z [[linków]] + typ (feedback/project);
  * cross          — który wniosek NARODZIŁ SIĘ z którego ticketu/nory (uczenie ze zdarzeń).

To pozwala wnioskować o STRUKTURZE (nie pojedynczych elementach): „co wynika z tej nory",
„jaki łańcuch przyczynowy wniosków", „które tickety dzielą root".
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

_MEMDIR = Path("~/.claude/projects/-home-tom-github-if-uri/memory").expanduser()
_LABEL_EDGE = {  # label-prefix → (typ krawędzi, kierunek do referowanego ticketu)
    "capgen:": "generates_for", "capretry:": "retries", "loop-diag:": "diagnoses",
    "sysfix:": "fixes", "rabbithole:": "escalation_of",
}


def _planfile() -> str | None:
    for c in ("~/github/if-uri/venv/bin/planfile",):
        p = Path(c).expanduser()
        if p.is_file():
            return str(p)
    import shutil
    return shutil.which("planfile")


def ticket_relations(project: str = "") -> dict[str, Any]:
    """Węzły=tickety, krawędzie z labeli + not (blocked_by / nora / diagnoza / retry)."""
    pf = _planfile()
    proj = project or str(Path("~/github/if-uri").expanduser())
    if not pf:
        return {"nodes": [], "edges": []}
    try:
        cp = subprocess.run([pf, "ticket", "list", "--format", "json"], capture_output=True,
                            text=True, timeout=15, cwd=proj)
        data = json.loads(cp.stdout[cp.stdout.index("["):cp.stdout.rindex("]") + 1])
    except Exception:  # noqa: BLE001
        return {"nodes": [], "edges": []}
    ids = {t["id"] for t in data}
    nodes, edges = [], []
    for t in data:
        tid = t["id"]
        labs = [str(x) for x in (t.get("labels") or [])]
        topic = next((h for h in ("signal", "email", "cron", "kvm", "calendar", "system")
                      if any(h in l.lower() for l in labs) or h in t.get("name", "").lower()), "")
        nodes.append({"id": tid, "name": t.get("name", "")[:50], "status": t.get("status"),
                      "topic": topic, "source": t.get("source")})
        for lab in labs:
            for pref, rel in _LABEL_EDGE.items():
                if lab.startswith(pref):
                    tgt = lab[len(pref):]
                    if tgt in ids:
                        edges.append({"from": tid, "to": tgt, "rel": rel})
        for note in ((t.get("outputs") or {}).get("notes") or []):
            s = str(note)
            for ref in set(re.findall(r"blocked_by\s+([A-Z]+-\d+)", s)):
                if ref in ids and ref != tid:
                    edges.append({"from": tid, "to": ref, "rel": "blocked_by"})
            m = re.search(r"spięte w rabbithole:\S+ \(([A-Z]+-\d+)\)", s)
            if m and m.group(1) in ids:
                edges.append({"from": tid, "to": m.group(1), "rel": "clustered_in"})
    # enables: done ticket → tickety które go blokowały (odwrotność blocked_by)
    done = {t["id"] for t in data if t.get("status") in ("done", "closed")}
    for e in list(edges):
        if e["rel"] == "blocked_by" and e["to"] in done:
            edges.append({"from": e["to"], "to": e["from"], "rel": "enables"})
    return {"nodes": nodes, "edges": edges}


def conclusion_relations() -> dict[str, Any]:
    """Węzły=wnioski (pamięci), krawędzie z [[linków]] między nimi. Graf wiedzy."""
    nodes, edges = [], []
    if not _MEMDIR.is_dir():
        return {"nodes": [], "edges": []}
    for f in sorted(_MEMDIR.glob("*.md")):
        if f.name == "MEMORY.md":
            continue
        txt = f.read_text(errors="replace")
        name = (re.search(r"^name:\s*(.+)$", txt, re.M) or [None, f.stem])[1].strip()
        desc = (re.search(r"^description:\s*(.+)$", txt, re.M) or [None, ""])[1].strip().strip('"')
        typ = (re.search(r"type:\s*(\w+)", txt) or [None, "?"])[1]
        nodes.append({"id": name, "desc": desc[:70], "type": typ})
        body = txt.split("---", 2)[-1]
        for link in set(re.findall(r"\[\[([^\]]+)\]\]", body)):
            edges.append({"from": name, "to": link, "rel": "relates"})
    return {"nodes": nodes, "edges": edges}


def graph(project: str = "") -> dict[str, Any]:
    """Pełny meta-graf: relacje ticketów + relacje wniosków + cross (wniosek←nora/ticket)."""
    tg = ticket_relations(project)
    cg = conclusion_relations()
    # cross: wnioski o nory/tickety (heurystyka po temacie w opisie wniosku)
    cross = []
    hole_topics = {n["topic"] for n in tg["nodes"] if n.get("topic")}
    for c in cg["nodes"]:
        for topic in hole_topics:
            if topic and topic in (c["desc"] + c["id"]).lower():
                cross.append({"conclusion": c["id"], "topic": topic, "rel": "learned_from"})
    return {"ticket_graph": tg, "conclusion_graph": cg, "cross": cross,
            "stats": {"tickets": len(tg["nodes"]), "ticket_edges": len(tg["edges"]),
                      "conclusions": len(cg["nodes"]), "conclusion_edges": len(cg["edges"]),
                      "cross_links": len(cross)}}
