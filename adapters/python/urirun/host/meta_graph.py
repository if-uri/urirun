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


_TOPICS = ("signal", "email", "cron", "kvm", "calendar", "system")


def _ticket_list(project: str) -> list[dict]:
    pf = _planfile()
    if not pf:
        return []
    try:
        cp = subprocess.run([pf, "ticket", "list", "--format", "json"], capture_output=True,
                            text=True, timeout=15, cwd=project or str(Path("~/github/if-uri").expanduser()))
        return json.loads(cp.stdout[cp.stdout.index("["):cp.stdout.rindex("]") + 1])
    except Exception:  # noqa: BLE001
        return []


def _ticket_topic(t: dict, labs: list) -> str:
    return next((h for h in _TOPICS if any(h in l.lower() for l in labs) or h in t.get("name", "").lower()), "")


def _label_edges(tid: str, labs: list, ids: set) -> list[dict]:
    out = []
    for lab in labs:
        for pref, rel in _LABEL_EDGE.items():
            if lab.startswith(pref) and lab[len(pref):] in ids:
                out.append({"from": tid, "to": lab[len(pref):], "rel": rel})
    return out


def _note_edges(t: dict, tid: str, ids: set) -> list[dict]:
    out = []
    for note in ((t.get("outputs") or {}).get("notes") or []):
        s = str(note)
        out += [{"from": tid, "to": ref, "rel": "blocked_by"}
                for ref in set(re.findall(r"blocked_by\s+([A-Z]+-\d+)", s)) if ref in ids and ref != tid]
        m = re.search(r"spięte w rabbithole:\S+ \(([A-Z]+-\d+)\)", s)
        if m and m.group(1) in ids:
            out.append({"from": tid, "to": m.group(1), "rel": "clustered_in"})
    return out


def ticket_relations(project: str = "") -> dict[str, Any]:
    """Węzły=tickety, krawędzie z labeli + not (blocked_by / nora / diagnoza / retry)."""
    data = _ticket_list(project)
    ids = {t["id"] for t in data}
    nodes, edges = [], []
    for t in data:
        labs = [str(x) for x in (t.get("labels") or [])]
        nodes.append({"id": t["id"], "name": t.get("name", "")[:50], "status": t.get("status"),
                      "topic": _ticket_topic(t, labs), "source": t.get("source")})
        edges += _label_edges(t["id"], labs, ids) + _note_edges(t, t["id"], ids)
    done = {t["id"] for t in data if t.get("status") in ("done", "closed")}
    edges += [{"from": e["to"], "to": e["from"], "rel": "enables"}
              for e in list(edges) if e["rel"] == "blocked_by" and e["to"] in done]
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


_PREDICATE_LEGEND = {
    "blocked_by": "czeka aż tamten będzie done", "enables": "done → odblokowuje tamten",
    "generates_for": "wytwarza zdolność dla", "retries": "ponawia", "diagnoses": "diagnozuje pętlę w",
    "fixes": "naprawia anomalię", "clustered_in": "należy do nory", "escalation_of": "eskalacja nory",
    "relates": "powiązany wniosek (przyczyna/wzmocnienie)", "learned_from": "wniosek narodził się z tematu",
}


def to_llm(g: dict[str, Any]) -> str:
    """Serializacja DLA LLM: triple podmiot-predykat-obiekt (fakt-na-linię, encje z typem inline,
    legenda predykatów). Najczytelniejsze dla modelu — atomowa jednostka wiedzy, kompaktowe,
    filtrowalne, czyta się jak zdania. NIE surowy JSON (rekonstrukcja grafu = koszt tokenów)."""
    tg, cg = g["ticket_graph"], g["conclusion_graph"]
    tstat = {n["id"]: n.get("status", "?") for n in tg["nodes"]}
    ctype = {n["id"]: n.get("type", "?") for n in cg["nodes"]}
    out = ["# META-GRAF (triple: PODMIOT predykat OBIEKT). Encja ticketu = ID[status], wniosku = nazwa:typ.",
           "# LEGENDA predykatów:"]
    out += [f"#   {p} = {d}" for p, d in _PREDICATE_LEGEND.items()]
    out.append("\n# RELACJE TICKETÓW:")
    for e in tg["edges"]:
        out.append(f"{e['from']}[{tstat.get(e['from'], '?')}] {e['rel']} {e['to']}[{tstat.get(e['to'], '?')}]")
    out.append("\n# RELACJE WNIOSKÓW (łańcuchy wiedzy):")
    for e in cg["edges"]:
        out.append(f"{e['from']}:{ctype.get(e['from'], '?')} {e['rel']} {e['to']}:{ctype.get(e['to'], '?')}")
    out.append("\n# CROSS (zdarzenia → mądrość):")
    for x in g["cross"]:
        out.append(f"{x['conclusion']} learned_from topic:{x['topic']}")
    return "\n".join(out)


def _focus_ids(tg: dict, focus: set) -> set:
    """ID ticketów w fokusie (po ID albo temacie) + ich bezpośredni sąsiedzi z krawędzi."""
    rel = {n["id"] for n in tg["nodes"] if n["id"] in focus or (n.get("topic") and n["topic"] in focus)}
    rel |= {e["to"] for e in tg["edges"] if e["from"] in rel} | {e["from"] for e in tg["edges"] if e["to"] in rel}
    return rel


def grounding_for(topic_or_ids, project: str = "") -> str:
    """GROUNDING DLA LLM-PLANERA: zawężony triple-widok wokół tematu/ticketów bieżącej decyzji.
    Nie cały graf — tylko okolica fokusu + legenda predykatów, by model decydował na RELACJACH."""
    g = graph(project)
    focus = {topic_or_ids} if isinstance(topic_or_ids, str) else set(topic_or_ids or [])
    tg = g["ticket_graph"]
    tstat = {n["id"]: n.get("status", "?") for n in tg["nodes"]}
    rel_ids = _focus_ids(tg, focus)
    out = ["# GROUNDING (triple: PODMIOT predykat OBIEKT) — relacje istotne dla tej decyzji:"]
    out += [f"#   {p} = {d}" for p, d in _PREDICATE_LEGEND.items() if any(e["rel"] == p for e in tg["edges"])]
    out += [f"{e['from']}[{tstat.get(e['from'], '?')}] {e['rel']} {e['to']}[{tstat.get(e['to'], '?')}]"
            for e in tg["edges"] if e["from"] in rel_ids or e["to"] in rel_ids]
    out += [f"{x['conclusion']} learned_from topic:{x['topic']}  (znany wniosek/antywzorzec)"
            for x in g["cross"] if x["topic"] in focus]
    return "\n".join(out) if len(out) > 1 else "# GROUNDING: brak relacji dla tego fokusu"


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
