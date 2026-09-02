# Prompt for the Overleaf agent

Copy everything below the line into Overleaf.

---

I am adding four figures to my MSc dissertation. They are already uploaded to
the `figures/` folder. Please place them as specified below and make the
accompanying text edits.

**Filenames (do not rename):**

```
figures/langgraph-state-machine.pdf
figures/production-corpus-signals.pdf
figures/production-failure-taxonomy.pdf
figures/failure-signal-overlap.pdf
```

All four are single-page vector PDFs. `.png` versions of each also exist in
`figures/` — use the `.pdf` versions, they scale without pixelation.

**Before you start:**

- Make sure `\usepackage{graphicx}` is in the preamble (add it if missing).
- Figure 1 needs `\usepackage{rotating}` — add it if it is not already there.
- Do not modify, move, or renumber any figure that is already in the document.
- Match the surrounding code style. If the document already uses a particular
  float placement convention (`[H]`, `[htbp]`, etc.), follow it rather than
  copying mine verbatim.
- Let LaTeX number the figures. Do not hardcode numbers in the captions.

---

## Figure 1 — `langgraph-state-machine.pdf`

**Where:** Chapter 3, in section **3.1 "The deployed WhatsApp support agent"**.
Place it immediately after the paragraph that begins *"Internally it is a
LangGraph application: a graph of nodes around a large language model core..."*

**Important — this figure is very wide (aspect ratio roughly 1.9:1).** At
`\textwidth` on a portrait page its node labels become unreadable. Please place
it as a full-page sideways figure:

```latex
\begin{sidewaysfigure}[p]
\centering
\includegraphics[width=0.95\textheight]{figures/langgraph-state-machine.pdf}
\caption{The LangGraph state machine of the deployed WhatsApp support agent,
rendered directly from \texttt{graph/builder.ts}. Twelve nodes converge on a
single response node. The router applies two guard clauses before dispatching
on intent; the \texttt{human\_taken\_over} branch is present in the graph but
unreachable in this build, since nothing outside the node itself sets the flag
it tests.}
\label{fig:langgraph}
\end{sidewaysfigure}
```

If `sidewaysfigure` causes problems, the fallback is a rotated full-page float:

```latex
\begin{figure}[p]
\centering
\includegraphics[angle=90,height=0.92\textheight]{figures/langgraph-state-machine.pdf}
\caption{...same caption...}
\label{fig:langgraph}
\end{figure}
```

Add a reference to it in the body text, e.g. change *"Internally it is a
LangGraph application"* to *"Internally it is a LangGraph application
(Figure~\ref{fig:langgraph})"*.

---

## Figure 2 — `production-corpus-signals.pdf`

**Where:** Chapter 3, section **3.2 "The production corpus"**, immediately
after the bulleted list of structural signals (the list containing "291
conversations escalated to a human agent", "297 conversations carry unknown
intent telemetry", and so on).

```latex
\begin{figure}[htbp]
\centering
\includegraphics[width=0.95\textwidth]{figures/production-corpus-signals.pdf}
\caption{Operational signals in the production corpus before any scoring. All
six are produced by business processes and messaging infrastructure rather than
by any language model, which is what allows the resulting ground truth to be
independent of the testing tool it is used to assess.}
\label{fig:corpus-signals}
\end{figure}
```

---

## Figure 3 — `production-failure-taxonomy.pdf`

**Where:** Chapter 3, section **3.4 "Rule based failure scoring"**, after the
paragraph that reports the category counts (*"...the dominant categories are
loops and stalls (256 conversations, 68.1 per cent of failures)..."*).

```latex
\begin{figure}[htbp]
\centering
\includegraphics[width=0.95\textwidth]{figures/production-failure-taxonomy.pdf}
\caption{The eight production failure categories after rule-based scoring: 376
failures among 1,299 conversations. Categories are multi-label, so a
conversation failing in more than one way is counted under each.}
\label{fig:failure-taxonomy}
\end{figure}
```

---

## Figure 4 — `failure-signal-overlap.pdf`

**Where:** Chapter 3, section **3.2**, directly after the bullet about
customers repeating themselves verbatim (see the text edit below, which
replaces that bullet's parenthetical).

```latex
\begin{figure}[htbp]
\centering
\includegraphics[width=0.75\textwidth]{figures/failure-signal-overlap.pdf}
\caption{Verbatim customer repetition against scored failure. The two sets
overlap only partially (Jaccard 0.274): repetition is one weighted signal among
several, neither necessary nor sufficient for a conversation to be scored as a
failure. It is, however, the only comprehension signal a simulated conversation
could exhibit at all.}
\label{fig:signal-overlap}
\end{figure}
```

---

## Required text edits

Two figures report numbers that differ from the current text. **The figures are
correct** — they are computed directly from the corpus. Please make these edits
so the prose and the figures agree, otherwise the document will contradict
itself.

### Edit 1 — Section 3.2, the "explicit request for a human" bullet

Find the bullet reading:

> 219 conversations contain an explicit customer request for a human, roughly
> three quarters of all escalations;

Change **219** to **221**. Leave the rest of the sentence as it is (221/291 is
75.9 per cent, so "roughly three quarters" still holds).

### Edit 2 — Section 3.2, the verbatim-repetition bullet

Find the bullet that currently reads (approximately):

> 376 conversations contain a customer repeating themselves verbatim. (This
> count coincides, and it is purely a numerical coincidence, with the scorer's
> total failure set in Section 3.4. The two sets are not the same set.
> Repetition is one weighted input among several: a conversation with repeats
> becomes a failure only if its overall score reaches the threshold, and the
> comprehension label has its own trigger conditions, which is why only 153 of
> the 376 failures carry that label.)

Replace the **entire bullet, including the whole parenthetical**, with:

> 163 conversations contain a customer repeating themselves verbatim, which is
> the scorer's reachable comprehension signal. Repetition is one weighted input
> among several rather than a failure criterion in itself: a conversation with
> repeats becomes a failure only if its overall score reaches the threshold, and
> the comprehension label has its own trigger conditions, which is why only 153
> of the 376 failures carry that label
> (Figure~\ref{fig:signal-overlap}).

The parenthetical about a "numerical coincidence" must be deleted rather than
reworded: the 376 figure was a units error (it was an *occurrence* count read
as a *conversation* count), so there is no second 376 for the failure count to
coincide with, and the hedge no longer describes anything real.

### Edit 3 — Chapter 9, section 9.2 "Why comprehension failures never appear"

Find the sentence:

> Real customers repeat themselves. 376 real conversations contain verbatim
> repeats

Change **376** to **163**. The surrounding argument is unaffected and in fact
gets stronger: 163 out of 1,299 is 12.6 per cent, against zero verbatim
self-repetitions in 2,950 simulated conversations.

---

## One thing to check, not to change

Section 5.3 currently states that the agent map detects *"conversations in
Spanish while the guardrails are written in English"*, and section 6.3.3 builds
on that supposed mismatch. That claim is being revised separately and the new
Figure~\ref{fig:langgraph} is consistent with the revision. Please **do not**
try to reconcile section 5.3 yourself — just leave it alone, and flag it in
your summary so I know it is still outstanding.

---

When you are done, please report back with:

1. The section each figure was placed in, and its assigned float placement.
2. Confirmation that the three text edits were applied.
3. Any LaTeX warnings, especially float-placement or `Overfull \hbox` warnings
   on the sideways figure.
