#!/usr/bin/env python3
"""Generate the Chapter 3 figures from the anonymised production corpus.

Every number is recomputed from the corpus using the project's own scorer
(``src/production/scoring.py`` + ``ground_truth.build_ground_truth``), so the
figures cannot disagree with the data or with each other.

Figures produced (kebab-case, bare filenames, PNG + PDF):
    production-corpus-signals        structural signals before scoring (§3.2)
    production-failure-taxonomy      the eight categories after scoring (§3.4)
    failure-signal-overlap           repeaters vs failures set relationship (§3.2)

Run from anywhere; paths resolve relative to the repository root.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

REPO = Path(__file__).resolve().parents[2]
PLATFORM = REPO / "debugger-platforn"
CORPUS = REPO / "investigation/02_data/real/tech_repair-conversations-anonymized.json"
OUTDIR = Path(__file__).resolve().parents[1] / "figures"

sys.path.insert(0, str(PLATFORM))
from src.production import ground_truth as _gt_mod  # noqa: E402
from src.production import scoring as _scoring_mod  # noqa: E402
from src.production.ground_truth import build_ground_truth  # noqa: E402

# build_ground_truth re-scores every conversation internally, so a naive
# compute() traverses the 20 MB corpus twice. Memoise by conversation id for
# the lifetime of this script; scoring is pure over a conversation dict.
_score_cache: dict = {}
_raw_score = _scoring_mod.score_conversation


def score_conversation(conv):  # noqa: D103
    key = conv.get("id") or id(conv)
    if key not in _score_cache:
        _score_cache[key] = _raw_score(conv)
    return _score_cache[key]


_gt_mod.score_conversation = score_conversation

INK = "#263238"
ACCENT = "#1565C0"
WARN = "#C62828"


def load() -> list[dict]:
    with open(CORPUS, encoding="utf-8") as f:
        return json.load(f)["conversations"]


def compute(convs: list[dict]) -> dict:
    """Recompute every §3.2 and §3.4 quantity from the corpus."""
    n_conv = len(convs)
    n_msg = sum(len(c.get("messages") or []) for c in convs)

    escalated = repeaters = long_conv = 0
    failed_deliveries = 0
    unknown_intent = requested_human = 0

    repeat_ids, escalated_ids = set(), set()

    for c in convs:
        sig = score_conversation(c)
        cid = c.get("id")

        if getattr(sig, "escalated", False):
            escalated += 1
            escalated_ids.add(cid)
        if getattr(sig, "requested_human", False):
            requested_human += 1
        if getattr(sig, "unknown_intent_count", 0) >= 1:
            unknown_intent += 1
        if (c.get("message_count") or 0) > 40:
            long_conv += 1
        if getattr(sig, "customer_repeat_count", 0) > 0:
            repeaters += 1
            repeat_ids.add(cid)
        failed_deliveries += sum(
            1 for m in (c.get("messages") or []) if m.get("status") == "failed"
        )

    gt = build_ground_truth(convs, min_score=3.0)
    failures = gt.failures if hasattr(gt, "failures") else gt
    failure_ids = {f.conversation_id for f in failures}
    n_fail = len(failure_ids)

    # production_categories keeps the eight-category vocabulary of Table 3.1;
    # shared_categories is its projection onto the frozen taxonomy.
    cats: dict[str, int] = {}
    for f in failures:
        for cat in f.production_categories:
            key = cat.value if hasattr(cat, "value") else str(cat)
            cats[key] = cats.get(key, 0) + 1

    return {
        "n_conv": n_conv,
        "n_msg": n_msg,
        "escalated": escalated,
        "requested_human": requested_human,
        "unknown_intent": unknown_intent,
        "long_conv": long_conv,
        "failed_deliveries": failed_deliveries,
        "repeaters": repeaters,
        "n_fail": n_fail,
        "categories": cats,
        "repeat_ids": repeat_ids,
        "failure_ids": failure_ids,
    }


# ---------------------------------------------------------------------------
# Figure 1 — structural signals (§3.2)
# ---------------------------------------------------------------------------

def fig_signals(d: dict) -> None:
    rows = [
        ("Escalated to a human agent", d["escalated"], "conversations"),
        ("Explicit request for a human", d["requested_human"], "conversations"),
        ("Unknown-intent telemetry", d["unknown_intent"], "conversations"),
        ("Stored message_count > 40", d["long_conv"], "conversations"),
        ("Customer repeats verbatim", d["repeaters"], "conversations"),
        ("Failed WhatsApp deliveries", d["failed_deliveries"], "messages"),
    ]
    rows.sort(key=lambda r: r[1])

    fig, ax = plt.subplots(figsize=(10.4, 5.0))
    ys = range(len(rows))
    colours = [ACCENT if r[2] == "conversations" else "#78909C" for r in rows]
    ax.barh(list(ys), [r[1] for r in rows], color=colours, height=0.62,
            edgecolor=INK, linewidth=0.7)

    for y, (label, v, unit) in zip(ys, rows):
        pct = f"  ({v / d['n_conv']:.1%} of conversations)" if unit == "conversations" else "  (messages)"
        ax.text(v + max(r[1] for r in rows) * 0.012, y, f"{v:,}{pct}",
                va="center", fontsize=9.4, color=INK)

    ax.set_yticks(list(ys))
    ax.set_yticklabels([r[0] for r in rows], fontsize=10)
    ax.set_xlabel("count", fontsize=10)
    ax.set_xlim(0, max(r[1] for r in rows) * 1.34)
    ax.set_title(
        "Operational signals in the production corpus, before any scoring\n"
        f"{d['n_conv']:,} conversations · {d['n_msg']:,} messages · "
        "no language model in the loop",
        fontsize=12, fontweight="bold", pad=12,
    )
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="x", alpha=0.25, linestyle=":")
    ax.set_axisbelow(True)
    fig.tight_layout()
    save(fig, "production-corpus-signals")


# ---------------------------------------------------------------------------
# Figure 2 — failure taxonomy (§3.4)
# ---------------------------------------------------------------------------

def fig_taxonomy(d: dict) -> None:
    order = [
        "loop_stall", "resolution", "comprehension", "data_gap",
        "delivery_infra", "hallucination", "missed_escalation",
        "silent_abandonment",
    ]
    cats = d["categories"]
    # `order` is a display preference, not a filter: any category the scorer
    # emits that is not listed still appears, so a renamed or added label can
    # never vanish from the figure while still counting toward n_fail.
    items = [(k, cats[k]) for k in order if cats.get(k)]
    items += [(k, v) for k, v in sorted(cats.items()) if k not in order and v]
    items.sort(key=lambda kv: kv[1])
    if not items:
        raise SystemExit("No failure categories found — nothing to plot.")

    n_fail = d["n_fail"]
    fig, ax = plt.subplots(figsize=(10.4, 5.4))
    ys = range(len(items))
    vals = [v for _, v in items]
    ax.barh(list(ys), vals, color="#455A64", height=0.62,
            edgecolor=INK, linewidth=0.7)

    for y, (k, v) in zip(ys, items):
        ax.text(v + max(vals) * 0.012, y, f"{v}  ({v / n_fail:.1%} of failures)",
                va="center", fontsize=9.4, color=INK)

    ax.set_yticks(list(ys))
    ax.set_yticklabels([k for k, _ in items], fontsize=10, family="DejaVu Sans Mono")
    ax.set_xlabel("conversations carrying the label", fontsize=10)
    ax.set_xlim(0, max(vals) * 1.36)
    ax.set_title(
        "Production failure taxonomy after rule-based scoring\n"
        f"{n_fail} failures among {d['n_conv']:,} conversations "
        f"({n_fail / d['n_conv']:.1%}) · score ≥ 3 and ≥ 1 category · labels are multi-label",
        fontsize=12, fontweight="bold", pad=12,
    )
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="x", alpha=0.25, linestyle=":")
    ax.set_axisbelow(True)
    fig.tight_layout()
    save(fig, "production-failure-taxonomy")


# ---------------------------------------------------------------------------
# Figure 3 — repeaters vs failures (§3.2 correction)
# ---------------------------------------------------------------------------

def fig_overlap(d: dict) -> None:
    R, F = d["repeat_ids"], d["failure_ids"]
    both = len(R & F)
    only_r = len(R - F)
    only_f = len(F - R)
    jac = both / len(R | F) if (R | F) else 0.0

    fig, ax = plt.subplots(figsize=(9.2, 5.4))

    ax.add_patch(Circle((-0.62, 0), 1.30, facecolor=ACCENT, alpha=0.30,
                        edgecolor=ACCENT, linewidth=1.8))
    ax.add_patch(Circle((0.62, 0), 1.55, facecolor=WARN, alpha=0.26,
                        edgecolor=WARN, linewidth=1.8))

    ax.text(-1.42, 0.10, f"{only_r}", ha="center", fontsize=17, fontweight="bold", color=INK)
    ax.text(-1.42, -0.24, "repeat only", ha="center", fontsize=9, color=INK)

    ax.text(0.02, 0.10, f"{both}", ha="center", fontsize=17, fontweight="bold", color=INK)
    ax.text(0.02, -0.24, "both", ha="center", fontsize=9, color=INK)

    ax.text(1.42, 0.10, f"{only_f}", ha="center", fontsize=17, fontweight="bold", color=INK)
    ax.text(1.42, -0.24, "failure only", ha="center", fontsize=9, color=INK)

    ax.text(-1.30, 1.62, f"verbatim repeaters\nn = {len(R)}", ha="center",
            fontsize=10.5, fontweight="bold", color=ACCENT)
    ax.text(1.45, 1.86, f"scored failures\nn = {len(F)}", ha="center",
            fontsize=10.5, fontweight="bold", color=WARN)

    ax.set_title(
        "Verbatim customer repetition is neither necessary nor sufficient for failure\n"
        f"Jaccard index = {jac:.3f} — the two sets are distinct",
        fontsize=12, fontweight="bold", pad=14,
    )
    ax.set_xlim(-3.0, 3.2)
    ax.set_ylim(-1.9, 2.35)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.tight_layout()
    save(fig, "failure-signal-overlap")


def save(fig, stem: str) -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(OUTDIR / f"{stem}.{ext}", dpi=200,
                    bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  -> {stem}.png / .pdf")


def main() -> None:
    convs = load()
    d = compute(convs)

    print("Recomputed from corpus:")
    print(f"  conversations          {d['n_conv']:,}")
    print(f"  messages               {d['n_msg']:,}")
    print(f"  escalated              {d['escalated']}  ({d['escalated']/d['n_conv']:.1%})")
    print(f"  requested a human      {d['requested_human']}")
    print(f"  unknown intent         {d['unknown_intent']}")
    print(f"  message_count > 40     {d['long_conv']}")
    print(f"  failed deliveries      {d['failed_deliveries']} messages")
    print(f"  verbatim repeaters     {d['repeaters']} conversations")
    print(f"  scored failures        {d['n_fail']}  ({d['n_fail']/d['n_conv']:.1%})")
    print(f"  categories             {d['categories']}")
    print()

    fig_signals(d)
    fig_taxonomy(d)
    fig_overlap(d)

    (OUTDIR / "chapter3-recomputed-numbers.json").write_text(
        json.dumps(
            {k: v for k, v in d.items() if k not in ("repeat_ids", "failure_ids")},
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
