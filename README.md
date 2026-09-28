# The Unofficial Guide

<!-- Replace this line with your name and which corpus you picked. -->

> **This file is your submission.** Fill it in as you go — most sections get
> written during the milestone that produces them, not at the end.
>
> How the starter works, and every command you'll need, is in `RUNNING.md`.
> Leave that file alone.
>
> **Paste everything as text.** No screenshots, no video. A typed table gets
> full credit; a picture of the same table gets none.
>
> Delete these instruction blocks as you replace them. The `<!-- -->` comments
> are notes to you and don't show up when the page renders — you can leave them
> or remove them.

---

# Unit 1

## What This Does

<!-- Three or four sentences. Which corpus you picked, and the kinds of
     questions your system answers. Write it for someone who has never seen
     this repo.

     Milestone 5. -->

## Chunking Strategy

**Chunk size:** 240 characters (a packing limit — paragraphs are grouped up to this size and never cut open)
**Overlap:** 0 characters
**Split rule:** a document is only split if it has 3 or more body paragraphs

Function: `chunker.py::split_documents`

The starter cut every document into fixed 800-character windows. On this corpus
that did nothing at all: `campus_life` is 88 documents, the longest is 549
characters, and not one reaches 800. `python app.py index` reported 88 documents
and 88 chunks, and `CHUNK_OVERLAP = 120` never executed. Size is not what is
wrong with these documents.

What is wrong is that the longer ones hold several unrelated thoughts.
`housing_old_brewhouse.txt` is 549 characters covering the building's history,
its heating, its laundry prices and its noise. A question about laundry costs
had to retrieve four topics' worth of text to reach one clause.

So the rule counts **paragraphs, not characters**. I started out planning a
character threshold and changed my mind: `admin_housing_lottery.txt` is 398
characters of a single unbroken paragraph, so any character cutoff low enough
to catch the housing files would also flag that one as long and then find
nothing in it to split. Paragraph count maps onto what I actually care about —
whether the document covers more than one thing. 16 of the 88 documents have
three or more body paragraphs, and those 16 are exactly the templated housing
and course files.

The second half of the strategy matters more than the split. Every one of these
documents opens with a bare title line, and **that title is the only place the
building or course name appears**. The laundry paragraph inside
`housing_old_brewhouse.txt` never says "Old Brewhouse" anywhere in it. Split on
paragraphs naively and you produce a chunk reading "Laundry costs $1.50 wash,
$1.50 dry, coin only" that no question naming the building could ever find. So
`split_documents` peels the title off and prefixes it to every chunk that
document produces. Chunk 4 below is the result.

**Overlap is 0 on purpose.** These paragraphs are independent labelled sections
— `The good:`, `The bad:`, laundry, noise. Carrying the tail of one into the
next would import an unrelated topic into every chunk, which is the exact
problem the split is meant to fix. Because I cut on paragraph boundaries, no
sentence is ever split in half, so there is no broken thought for an overlap to
repair. `config.CHUNK_OVERLAP` still drives sentence-level overlap if raised
above 0.

**Results of the change:**

| | Before (`fallback_split`) | After (`split_documents`) |
|---|---|---|
| Chunks | 88 | 106 |
| Average length | 317 chars | 268 chars |
| Longest chunk | 549 chars | 421 chars |
| Documents split | 0 | 16 |
| Best distance, "cost to wash clothes in Old Brewhouse?" | — | 0.173 |

**One thing it does not fix.** The laundry and noise facts share a single
paragraph in every housing file: *"Laundry costs $1.50 wash, $1.50 dry, coin
only, and the machines are old. On noise: sound carries strangely..."*. A
paragraph-level split cannot separate those two. Chunk 4 below still carries
both. It went from 549 characters to 216, which is enough for retrieval to work,
but splitting on the `On noise:` sentence is the obvious next move if criterion
1 misses on a noise question in unit 2.

## Sample Chunks

All five produced by `chunker.py::split_documents`. Chunks 1 and 5 come from
documents left whole (fewer than 3 body paragraphs); chunks 2, 3 and 4 come from
documents that were split, and show the title prefix doing its job.

**Chunk 1** — source: `admin_add_drop_deadline.txt#0` — produced by: `chunker.py::split_documents`

```
On the add/drop deadline

You can add a course through the end of the second week. Dropping is a longer window — through the end of week six — but a drop after week two shows as a W on your transcript. Nothing anywhere on the registrar's site says this plainly, and students find out from each other.
```

Left whole — one body paragraph, one topic, and it names its own subject.

**Chunk 2** — source: `course_biol_160.txt#1` — produced by: `chunker.py::split_documents`

```
BIOL 160 Cell Biology

The one piece of advice: the unit tests come fast, roughly every three weeks; falling behind once is very hard to recover from.
```

The shortest kind of chunk this produces, at 24 words. Without the prefixed
title it would be advice about "the unit tests" with no course attached.

**Chunk 3** — source: `housing_old_brewhouse.txt#0` — produced by: `chunker.py::split_documents`

```
Old Brewhouse — what it's actually like

Took this last spring. Built 1902 as a brewery, converted to housing in 1998. Rooms are doubles and triples with unusual floor plans, no two alike.

The good: the most characterful building on campus and people get attached to it.
```

Two short paragraphs packed together because they fit inside the 240-character
limit. On its own, "The good: the most characterful building on campus" is not
an answer to anything.

**Chunk 4** — source: `housing_old_brewhouse.txt#2` — produced by: `chunker.py::split_documents`

```
Old Brewhouse — what it's actually like

Laundry costs $1.50 wash, $1.50 dry, coin only, and the machines are old. On noise: sound carries strangely because of the original brick; a room two floors up can be louder than next door.
```

The chunk the whole strategy was built for. Before the change this material was
buried in a 549-character chunk alongside the building's history and heating.
It is also the clearest example of the title prefix earning its place: the
paragraph itself never says "Old Brewhouse".

**Chunk 5** — source: `housing_old_brewhouse_laundry.txt#0` — produced by: `chunker.py::split_documents`

```
Laundry in Old Brewhouse

Machines take $1.50 wash, $1.50 dry, coin only, and the machines are old. There are eight washers and six dryers for the building, which is the wrong ratio and means the dryers back up on Sunday evenings.

Best time to do laundry here is Tuesday or Wednesday morning. Sunday after 6pm you will wait.
```

Left whole, and worth including because it states the same $1.50 price as
chunk 4. My laundry test question has two valid sources, and both now come back
in the top two results.

## Sample Answer

<!-- One complete question and answer, pasted as text, with the source line
     visible. Milestone 4. -->

**Question:**


**Answer:**

```
```

**My relevance cutoff:**

<!-- The number you set in config.py, and how you got there.

     You ran five questions your corpus covers and the five in OUT_OF_SCOPE
     that it clearly doesn't, and wrote down the best distance for each. What
     did those two groups look like? Where was the gap? Put the actual numbers
     here — the table below wants all ten rows.

     Milestone 4. -->

| Question | In corpus? | Best distance |
|---|---|---|
|  |  |  |

## How I Used AI

<!-- Two specific moments. For each: what you asked for, what came back, and
     what you changed about it.

     "I asked Claude to write the chunking function from my notes. It ignored
     the overlap, so I added that myself" is the level of detail we're after.
     "I used AI to help me code" is not.

     Milestone 5. -->

**1.**

**2.**

<!-- ── Stretch features ─────────────────────────────────────────────────────
     Doing one? Say so here BEFORE you start. A feature this README never
     claims earns nothing.
     ───────────────────────────────────────────────────────────────────────── -->

---

# Unit 2

<!-- These sections get ADDED to what's already above. Don't delete or rewrite
     unit 1 — the point is that someone can see what you said before you knew
     how it went. -->

## Run Log — Before

<!-- Your five criteria, three runs each. `python run_eval.py --label before`
     runs the questions, puts the OUT_OF_SCOPE ones through the gate, and
     writes it all into results/ for you. Targets come from criteria.md; the
     verdict column is your call.

     Criterion 3 is measured in one deterministic pass rather than three, so
     the same number goes in all three run columns. That's correct, not lazy.

     Milestone 1. -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 |  |  |  |  |
| 2. Every answer names a source | 5 of 5 |  |  |  |  |
| 3. Gate stops out-of-corpus questions | 4 of 5 |  |  |  |  |
| 4. | | | | | |
| 5. | | | | | |

<!-- Underneath, paste the REAL output for each criterion from one of your
     runs — the actual text your system produced, not a description of it.
     Name the file and function that produced it. -->

## Verdicts

<!-- MET or MISSED for each of the five, against the target you wrote last
     unit — not a new one. Plus a sentence on how you decided. That sentence
     matters most where it was close.

     If your target said 4 of 5 and your runs came out 4, 3, 4, that's a MISS.
     The target has to hold, not show up occasionally.

     Milestone 2. -->

| # | Criterion | Verdict | How I decided |
|---|---|---|---|
| 1 |  |  |  |
| 2 |  |  |  |
| 3 |  |  |  |
| 4 |  |  |  |
| 5 |  |  |  |

## Diagnoses

<!-- For each miss: which stage caused it, and how. The stage alone isn't
     enough — you need the mechanism.

     Not a diagnosis: "Question 3 didn't work."
     A diagnosis:     "Question 3 asks about laundry costs. The answer is in
                       one sentence that got split across two chunks, so
                       neither chunk on its own contains it."

     The five stages: loading → chunking → embedding → retrieval → generation.

     Look for a pattern. If three misses all ask about numbers, that's one
     problem, not three.

     Missed nothing? Say so, then say honestly whether your targets were set
     low, and which one you'd tighten and to what.

     Milestone 3. -->

## The Improvement

**What I changed:**

**Why I picked it:**

<!-- Connect it to a specific diagnosis above in one sentence. If you can't,
     you picked a fix because it sounded impressive. -->

### Run Log — After

<!-- Same format, same five criteria, three runs each.
     `python run_eval.py --label after` -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 |  |  |  |  |
| 2. Every answer names a source | 5 of 5 |  |  |  |  |
| 3. Gate stops out-of-corpus questions | 4 of 5 |  |  |  |  |
| 4. | | | | | |
| 5. | | | | | |

**Did it help?**

<!-- Say plainly whether it did, and how you know. If it made things worse,
     say that — a change that backfired, honestly reported, earns full credit
     and is more interesting than one that worked. What matters is that you can
     tell.

     Milestone 4. -->

## What's Still Broken

<!-- For each criterion still missed after your fix: what you'd do about it,
     and why you stopped where you did.

     "I ran out of time" is fine if it's true. Pretending nothing is left is
     not.

     Milestone 5. -->

## What I'd Do Differently

<!-- Knowing what you know now — which of your five criteria would you write
     differently, and why?

     Milestone 5. -->
