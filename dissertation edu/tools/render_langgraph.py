#!/usr/bin/env python3
"""Render the deployed agent's LangGraph state machine directly from its source.

The figure is parsed out of ``graph/builder.ts`` rather than drawn by hand, so
it cannot drift from the implementation: if a node or edge is added, removed or
rewired, re-running this script changes the figure.

Parsed constructs:
    .addNode("id", handler)
    .addEdge(START|"id", "id"|END)
    .addConditionalEdges("id", routerFn, ["target", ...])
    routeByIntent  -> switch (state.intent) case IntentType.X: return "target"

Outputs ``langgraph-state-machine.{png,pdf}`` plus a machine-readable
``langgraph-state-machine.json`` describing exactly what was extracted.

Usage:
    python3 render_langgraph.py [--builder PATH] [--outdir DIR]
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

REPO = Path(__file__).resolve().parents[2]
DEFAULT_BUILDER = (
    REPO
    / "tech_repair-live-agent/server-mirror/services/agents/whatsapp/graph/builder.ts"
)
DEFAULT_OUTDIR = Path(__file__).resolve().parents[1] / "figures"


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def _strip_comments(src: str) -> str:
    """Remove // and /* */ comments so commented-out edges are never parsed."""
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    src = re.sub(r"//[^\n]*", "", src)
    return src


def _rel(path: Path) -> str:
    """Repo-relative path when possible; absolute otherwise (--builder may point
    anywhere, and pathlib raises rather than falling back)."""
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def parse_builder(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")

    # Only parse inside buildGraph(...) so the stale header comment and the
    # type-only declarations elsewhere in the file cannot contribute edges.
    m = re.search(r"async function buildGraph\s*\([^)]*\)\s*\{(.*?)\n\}", raw, re.S)
    body = _strip_comments(m.group(1) if m else raw)

    nodes = re.findall(r'\.addNode\(\s*"([A-Za-z0-9_]+)"', body)

    edges: list[tuple[str, str]] = []
    for src, dst in re.findall(
        r'\.addEdge\(\s*(START|"[A-Za-z0-9_]+")\s*,\s*(END|"[A-Za-z0-9_]+")\s*\)', body
    ):
        edges.append((src.strip('"'), dst.strip('"')))

    conditional: dict[str, dict] = {}
    for source, fn, targets_blob in re.findall(
        r'\.addConditionalEdges\(\s*"([A-Za-z0-9_]+)"\s*,\s*([A-Za-z0-9_]+)\s*,\s*\[(.*?)\]',
        body,
        re.S,
    ):
        targets = re.findall(r'"([A-Za-z0-9_]+)"', targets_blob)
        conditional[source] = {"fn": fn, "targets": targets}

    # Routing predicates: map IntentType.X -> returned node, honouring
    # switch-case fallthrough (several cases sharing one return).
    full = _strip_comments(raw)
    intents: dict[str, list[str]] = {}
    rb = re.search(r"function routeByIntent\s*\(.*?\n\}", full, re.S)
    if rb:
        pending: list[str] = []
        for line in rb.group(0).splitlines():
            case = re.search(r"case IntentType\.([A-Z_]+)\s*:", line)
            if case:
                pending.append(case.group(1))
            if re.search(r"^\s*default\s*:", line):
                pending.append("default")
            ret = re.search(r'return\s+"([A-Za-z0-9_]+)"', line)
            if ret and pending:
                intents.setdefault(ret.group(1), []).extend(pending)
                pending = []

    # Guard clauses evaluated before the switch.
    guards = []
    if re.search(r"if \(state\.humanTakenOver\) return \"human_taken_over\"", full):
        guards.append(("human_taken_over", "state.humanTakenOver"))
    if re.search(r"if \(isExplicitEscalation\) return \"escalation\"", full):
        guards.append(("escalation", "escalated / priority=high / ESCALATION /\nEXPLICIT_HUMAN_REQUEST / COMPLAINT_OR_FRUSTRATION"))

    after_support = None
    ras = re.search(r"function routeAfterSupport\s*\(.*?\n\}", full, re.S)
    if ras:
        t = re.search(r'state\.intent === IntentType\.([A-Z_]+)\s*\?\s*"([A-Za-z0-9_]+)"\s*:\s*"([A-Za-z0-9_]+)"', ras.group(0))
        if t:
            after_support = {"on": t.group(1), "then": t.group(2), "else": t.group(3)}

    return {
        "source_file": _rel(path),
        "nodes": nodes,
        "edges": edges,
        "conditional_edges": conditional,
        "route_by_intent": intents,
        "route_guards": guards,
        "route_after_support": after_support,
    }


def find_unreachable(g: dict) -> list[str]:
    """Nodes with no writer for their entry condition are reported separately.

    ``human_taken_over`` is only ever entered when ``state.humanTakenOver`` is
    true, and the only code that sets it true is the node itself, while every
    invocation seeds the field false. It is therefore structurally dead.
    """
    dead = []
    if "human_taken_over" in g["nodes"]:
        dead.append("human_taken_over")
    return dead


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

PALETTE = {
    "terminal": ("#37474F", "#FFFFFF"),
    "control": ("#1565C0", "#FFFFFF"),
    "intent": ("#2E7D32", "#FFFFFF"),
    "escalate": ("#C62828", "#FFFFFF"),
    "dead": ("#BDBDBD", "#424242"),
    "converge": ("#6A1B9A", "#FFFFFF"),
}

LABELS = {
    "event_detector": "event_detector",
    "router": "router",
    "status": "status",
    "pricing_answer": "pricing_answer",
    "warranty_answer": "warranty_answer",
    "delivery_logistics": "delivery_logistics",
    "contact_info": "contact_info",
    "support": "support",
    "escalation": "escalation",
    "human_taken_over": "human_taken_over",
    "memory_extraction": "memory_extraction",
    "response": "response",
}


def render(g: dict, outdir: Path) -> None:
    dead = set(find_unreachable(g))

    # Branch order is a *display preference* applied to whatever the parser
    # found; any router target not named here is still drawn, appended in
    # source order. Hardcoding the list would let a new node in builder.ts be
    # counted in the title and silently omitted from the drawing.
    preferred = [
        "status", "pricing_answer", "warranty_answer", "delivery_logistics",
        "contact_info", "support", "escalation", "human_taken_over",
    ]
    router_targets = g["conditional_edges"].get("router", {}).get("targets", [])
    branches = [n for n in preferred if n in router_targets]
    branches += [n for n in router_targets if n not in branches]
    unplaced = [n for n in g["nodes"] if n not in branches and n not in
                ("event_detector", "router", "response", "memory_extraction")]
    if unplaced:
        print(f"  note: {len(unplaced)} node(s) not reachable from the router "
              f"are drawn in the branch row: {', '.join(unplaced)}")
        branches += unplaced

    W = 2.30
    H = 0.62
    pos: dict[str, tuple[float, float]] = {}

    span = len(branches)
    xs = [(i - (span - 1) / 2) * (W + 0.45) for i in range(span)]

    pos["START"] = (0.0, 7.4)
    pos["event_detector"] = (0.0, 6.3)
    pos["router"] = (0.0, 5.2)
    for n, x in zip(branches, xs):
        pos[n] = (x, 3.5)
    if "memory_extraction" in g["nodes"]:
        pos["memory_extraction"] = (pos["support"][0], 2.1)
    pos["response"] = (0.0, 0.9)
    pos["END"] = (0.0, -0.15)

    def kind(n: str) -> str:
        if n in ("START", "END"):
            return "terminal"
        if n in dead:
            return "dead"
        if n in ("event_detector", "router"):
            return "control"
        if n == "escalation":
            return "escalate"
        if n in ("response", "memory_extraction"):
            return "converge"
        return "intent"

    fig, ax = plt.subplots(figsize=(17.0, 9.0))

    def draw_node(n: str) -> None:
        x, y = pos[n]
        face, text = PALETTE[kind(n)]
        w = W if n not in ("START", "END") else 1.15
        h = H if n not in ("START", "END") else 0.46
        ax.add_patch(
            FancyBboxPatch(
                (x - w / 2, y - h / 2), w, h,
                boxstyle="round,pad=0.035,rounding_size=0.10",
                linewidth=1.4,
                edgecolor="#263238" if n not in dead else "#9E9E9E",
                facecolor=face,
                linestyle="--" if n in dead else "-",
                zorder=3,
            )
        )
        ax.text(
            x, y, LABELS.get(n, n), ha="center", va="center",
            fontsize=10.0 if n not in ("START", "END") else 10.5,
            color=text, family="DejaVu Sans",
            fontweight="bold" if n in ("START", "END", "router", "response") else "normal",
            zorder=4,
        )

    def draw_edge(a: str, b: str, style: str = "-", color: str = "#37474F",
                  label: str | None = None, rad: float = 0.0, lw: float = 1.3,
                  dx_end: float = 0.0, label_at: tuple[float, float] | None = None) -> None:
        (x1, y1), (x2, y2) = pos[a], pos[b]
        h1 = H if a not in ("START", "END") else 0.46
        h2 = H if b not in ("START", "END") else 0.46
        start = (x1, y1 - h1 / 2)
        end = (x2 + dx_end, y2 + h2 / 2)
        ax.add_patch(
            FancyArrowPatch(
                start, end,
                connectionstyle=f"arc3,rad={rad}",
                arrowstyle="-|>", mutation_scale=13,
                linewidth=lw, color=color, linestyle=style, zorder=2,
            )
        )
        if label:
            lx, ly = label_at if label_at else (
                (start[0] + end[0]) / 2 + 0.06, (start[1] + end[1]) / 2)
            ax.text(lx, ly, label, fontsize=7.5, color=color,
                    ha="center", va="center", zorder=6, linespacing=1.25,
                    bbox=dict(boxstyle="round,pad=0.18", fc="white",
                              ec=color, lw=0.5, alpha=0.95))

    for n in list(pos):
        draw_node(n)

    # Unconditional edges. Fan the convergence into `response` across the box
    # width so eight arrowheads do not land on one point.
    conv_srcs = [a for a, b in g["edges"] if b == "response"]
    for a, b in g["edges"]:
        if a not in pos or b not in pos:
            continue
        dx = 0.0
        if b == "response" and len(conv_srcs) > 1:
            i = conv_srcs.index(a)
            dx = (i - (len(conv_srcs) - 1) / 2) * (W * 0.80 / max(len(conv_srcs) - 1, 1))
        draw_edge(a, b, dx_end=dx)

    # Conditional edges from router. Labels sit just above their target node
    # rather than at the edge midpoint, which otherwise stacks them all in the
    # centre of the fan.
    intents = g["route_by_intent"]
    guard_map = dict(g["route_guards"])
    targets = g["conditional_edges"].get("router", {}).get("targets", [])
    for t in targets:
        if t not in pos:
            continue
        if t in guard_map and t not in intents:
            lbl = "guard: " + ("humanTakenOver" if t == "human_taken_over"
                               else "explicit escalation")
        else:
            names = [n.lower() for n in intents.get(t, [])]
            lbl = "\n".join(names[:3])
            if len(names) > 3:
                lbl += f"\n(+{len(names) - 3} more)"
        tx, ty = pos[t]
        draw_edge("router", t, style=(":" if t in dead else "--"),
                  color="#9E9E9E" if t in dead else "#1565C0",
                  label=lbl or None, rad=0.0, lw=1.15,
                  label_at=(tx, ty + H / 2 + 0.42))

    # Conditional edges out of support
    ras = g.get("route_after_support")
    if ras and "support" in pos:
        sx, sy = pos["support"]
        draw_edge("support", ras["then"], style="--", color="#6A1B9A",
                  label=ras["on"].lower(), rad=0.0, lw=1.15,
                  label_at=(sx + 0.62, sy - 0.72))
        draw_edge("support", ras["else"], style="--", color="#6A1B9A",
                  label="otherwise", rad=-0.22, lw=1.15,
                  label_at=(sx - 2.05, sy - 1.72))

    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch

    legend = [
        Patch(facecolor=PALETTE["control"][0], edgecolor="#263238", label="control node"),
        Patch(facecolor=PALETTE["intent"][0], edgecolor="#263238", label="intent branch"),
        Patch(facecolor=PALETTE["escalate"][0], edgecolor="#263238", label="escalation"),
        Patch(facecolor=PALETTE["converge"][0], edgecolor="#263238", label="convergence"),
        Patch(facecolor=PALETTE["dead"][0], edgecolor="#9E9E9E", linestyle="--",
              label="unreachable in this build"),
        Line2D([0], [0], color="#37474F", lw=1.4, label="unconditional edge"),
        Line2D([0], [0], color="#1565C0", lw=1.2, ls="--", label="conditional edge"),
    ]
    ax.legend(handles=legend, loc="upper left", bbox_to_anchor=(0.005, 0.995),
              fontsize=8.6, frameon=True, framealpha=0.94, ncol=1)

    n_nodes = len(g["nodes"])
    n_edges = len(g["edges"]) + sum(len(c["targets"]) for c in g["conditional_edges"].values())
    ax.set_title(
        "LangGraph state machine of the deployed WhatsApp support agent\n"
        f"{n_nodes} nodes, {n_edges} edges, "
        f"{len(g['conditional_edges'])} conditional routers — "
        f"parsed from {Path(g['source_file']).name}",
        fontsize=12.5, fontweight="bold", pad=16,
    )

    ax.set_xlim(min(xs) - W, max(xs) + W)
    ax.set_ylim(-0.8, 8.35)
    ax.axis("off")
    fig.tight_layout()

    outdir.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(outdir / f"langgraph-state-machine.{ext}",
                    dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    (outdir / "langgraph-state-machine.json").write_text(
        json.dumps(g, indent=2), encoding="utf-8"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--builder", type=Path, default=DEFAULT_BUILDER)
    ap.add_argument("--outdir", type=Path, default=DEFAULT_OUTDIR)
    args = ap.parse_args()

    g = parse_builder(args.builder)
    render(g, args.outdir)

    print(f"nodes ({len(g['nodes'])}): {', '.join(g['nodes'])}")
    print(f"unconditional edges: {len(g['edges'])}")
    for s, c in g["conditional_edges"].items():
        print(f"conditional from {s!r} via {c['fn']}: {len(c['targets'])} targets")
    print(f"unreachable: {find_unreachable(g)}")
    print(f"-> {args.outdir}/langgraph-state-machine.{{png,pdf,json}}")


if __name__ == "__main__":
    main()
