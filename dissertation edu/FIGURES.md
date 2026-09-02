# Figures — what each one is, and where it goes

All figures are in `figures/` as **PNG (200 dpi) and PDF**, with bare kebab-case
filenames so they drop straight into `investigation/05_report/figures/`.

Use the PDF in LaTeX — it is vector and scales cleanly.

```bash
cp "dissertation edu/figures/"*.pdf investigation/05_report/figures/
```

Every figure regenerates from source. Nothing is hand-drawn, so none of them can
drift from the code or the data.

```bash
cd "dissertation edu/tools"
../../debugger-platforn/venv/bin/python render_langgraph.py
../../debugger-platforn/venv/bin/python render_chapter3_figures.py
```

---

## 1. `langgraph-state-machine`

**Goes in §3.1**, as the new Figure 3.1 — the reader should meet the agent's
actual structure before Chapter 5 discusses what Phase A recovered from it.
Also worth referencing from §7.5, where you claim the sandbox preserves this
graph.

Parsed directly from
`tech_repair-live-agent/server-mirror/services/agents/whatsapp/graph/builder.ts`
by `tools/render_langgraph.py`. It reads `.addNode`, `.addEdge` and
`.addConditionalEdges` inside `buildGraph()` only, strips comments first, and
recovers the routing predicates from the `switch (state.intent)` in
`routeByIntent`. Add a node in the code and the figure changes; it cannot go
stale.

Shows: 12 nodes, 21 edges, 2 conditional routers, entry at `event_detector`,
single terminal edge `response → END`, and the eight router branches labelled
with the intents that trigger them.

`human_taken_over` is drawn dashed and grey because it is **unreachable in this
build** — `state.humanTakenOver` is only ever set true by the node itself, and
every invocation seeds it false.

The extraction is also written to `langgraph-state-machine.json`, so you can
quote node and edge counts in the text and cite the same artefact.

> Suggested caption:
> *"The LangGraph state machine of the deployed WhatsApp support agent, rendered
> directly from `graph/builder.ts`. Twelve nodes converge on a single response
> node. The router applies two guard clauses before dispatching on intent; the
> `human_taken_over` branch is present in the graph but unreachable in this
> build, since nothing outside the node itself sets the flag it tests."*

⚠️ **This figure replaces the claim that the guardrails are English.** See
`CORRECTIONS.md` §2 — that finding was a bug in the rule-language detector,
which is now fixed.

---

## 2. `production-corpus-signals`

**Goes in §3.2**, beside the bulleted list of structural signals.

Recomputed from the anonymised corpus with the project's own scorer, so the
figure and the prose cannot disagree. It plots the six operational signals with
counts and percentages, distinguishing conversation-level from message-level
units — which matters, because the message-level one is exactly where the 376
error came from.

**Two numbers in the figure differ from the current §3.2 text**, and the figure
is right: explicit human requests are **221**, not 219, and verbatim repeaters
are **163 conversations**, not 376. See `CORRECTIONS.md` §3.

> Suggested caption:
> *"Operational signals in the production corpus before any scoring. All six are
> produced by business processes and messaging infrastructure rather than by any
> language model, which is what allows the resulting ground truth to be
> independent of the testing tool it is used to assess."*

---

## 3. `production-failure-taxonomy`

**Goes in §3.4**, either replacing or complementing the prose list of category
counts. It also pairs naturally with Table 3.1.

All eight categories with counts and percentage-of-failures, sorted by
magnitude. Every value reproduces the dissertation exactly — §3.4 is the section
that survived the audit intact, and the figure says so at a glance: loops and
stalls dominate at 68.1%, unresolved requests follow at 58.8%, comprehension at
40.7%.

The subtitle states the scoring criterion (score ≥ 3 and ≥ 1 category) and that
labels are multi-label, which pre-empts the obvious question about why the
percentages exceed 100.

> Suggested caption:
> *"The eight production failure categories after rule-based scoring: 376
> failures among 1,299 conversations. Categories are multi-label, so a
> conversation failing in more than one way is counted under each."*

---

## 4. `failure-signal-overlap`

**Goes in §3.2**, directly replacing the parenthetical about the numerical
coincidence — or in §9.2, supporting the comprehension argument.

This figure exists because of the audit. §3.2 currently defends itself against a
coincidence that does not exist: there is only one 376 in the data. What the
figure shows instead is the genuinely interesting relationship — verbatim
repetition is **neither necessary nor sufficient** for failure.

- 116 conversations both repeat and fail
- 47 repeat without failing (a lone repeat scores 1.0, below the threshold of 3)
- 260 fail without any repetition (the modal failure is a bare `resolution` from
  an explicit request for a human)
- Jaccard index 0.274

That is a stronger and more defensible claim than the coincidence hedge, and it
makes the §9.2 argument sharper: repetition is one weighted input among several,
and it is the input the simulator never produces.

> Suggested caption:
> *"Verbatim customer repetition against scored failure. The two sets overlap
> only partially (Jaccard 0.274): repetition is one weighted signal among
> several, neither necessary nor sufficient for a conversation to be scored as a
> failure. It is, however, the only comprehension signal that a simulated
> conversation could exhibit at all."*

---

## Also generated

`chapter3-recomputed-numbers.json` — every §3.2 and §3.4 quantity as recomputed
from the corpus. Not a figure; useful as the single source you check the prose
against, and as an appendix artefact for the reproducibility statement.

---

## Figures I did not regenerate, and why

| Existing figure | Verdict |
|---|---|
| Fig 4.1 anonymisation pipeline | The TikZ version in `report.tex` is accurate and matches `backend/pipeline.py`. Keep it. |
| Fig 5.2 platform pipeline | Accurate. Keep. |
| Fig 7.1 Phase C architecture | Accurate against `src/execution/`. Keep. |
| Fig 8.1 scorer parity design | Accurate against `compare_real_vs_sim.py`. Keep. |
| Fig 8.2 / 8.4 category comparison | Already generated from data by `compare_real_vs_sim.py` and `reached_only_charts.py`. Keep. |
| Fig 8.3 scale curves | Already generated by `scale_curves.py`. Keep. |
| Fig 5.1 / 5.4 / 6.1 / 7.2 UI screenshots | Cannot be generated from source. The platform runs, so they can be re-captured if you want fresher ones — see `HOW_TO_RUN.md`. |
| Fig 5.3 agent map graph | Keep, but read `CORRECTIONS.md` §6 first: the "55 tools" are static-analysis function entries, not a runtime tool registry, and the caption should say so. |

No Chapter 2 figure is included. Chapter 2 is a literature review whose argument
is already carried by the seven-cluster prose structure, and a synthesised
"research gap matrix" would be a drawing of your own claims rather than anything
generated from source — which is the opposite of what these figures are for. If
you want one, the honest version is a table, not a figure.
