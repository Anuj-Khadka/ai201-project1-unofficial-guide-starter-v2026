# The Unofficial Guide

<!-- Replace this line with your name and which corpus you picked. -->

**Anuj Khadka (corpus: `campus_life`)**

---

# Unit 1

## What This Does

This answers questions about one university using `campus_life`, a corpus of 88 
short posts written by students: which dorm has uneven heating, how long the
queue at a dining hall runs at noon, what a course's assessment actually looks
like, how the add/drop deadline really works. You ask a plain question —
"How much does it cost to wash clothes in Old Brewhouse?" — and it answers from
those posts and names the file the answer came from.

Under the hood it splits each post into paragraph-sized chunks, embeds them
locally into a Chroma vector store, and retrieves the five nearest to your
question. A relevance gate checks the closest match against a 0.6 cutoff before
the model is called at all, so a question the corpus doesn't cover gets
"I don't have enough information about that" instead of a confident guess, and
costs no API quota.

Run it with `python app.py ask "your question here"`.

<!-- Three or four sentences. Which corpus you picked, and the kinds of
     questions your system answers. Write it for someone who has never seen
     this repo.

     Milestone 5. -->

## Chunking Strategy

**Chunk size:** 240 characters (a packing limit — paragraphs are grouped up to this size and never cut open)
**Overlap:** 0 characters
**Split rule:** a document is split if it has 2 or more body paragraphs

Function: `chunker.py::split_documents`

The starter cut every document into fixed 800-character windows. On this corpus
that did nothing at all: `campus_life` is 88 documents, the longest is 549
characters, and not one reaches 800. `python app.py index` reported 88 documents
and 88 chunks, and `CHUNK_OVERLAP = 120` never executed. Size is not what is
wrong with these documents.

What is wrong is that they bundle unrelated facts together.
`housing_old_brewhouse.txt` is 549 characters covering the building's history,
its heating, its laundry prices and its noise, so a question about laundry costs
had to retrieve four topics' worth of text to reach one clause.

So the rule counts **paragraphs, not characters**. A character threshold doesn't
work here: `admin_housing_lottery.txt` is 398 characters of a single unbroken
paragraph, so any cutoff low enough to catch the housing files would flag that
one as long and then find nothing in it to split. Paragraph count maps onto what
I actually care about — whether the document covers more than one thing.

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

### I changed the split rule partway through, and here is why

I first set the rule at **3 or more body paragraphs**. That was the conservative
choice: it split only the 16 templated housing and course files, the ones I
could see were obviously multi-topic, and left everything else alone.

Milestone 4 showed me it was wrong. Running my five test questions through
retrieval, "What is the maximum working hours during the terms?" came back with
`course_stat_150_workload.txt` at rank 1 — **the wrong document** — at a distance
of 0.5313, beating the correct `money_jobs.txt` at 0.5339 by 0.0026. Four of the
five results were course workload files, because "working hours" embeds close to
"Workload for X… hours a week".

The cause was my own rule. `money_jobs.txt` has a title and exactly two body
paragraphs:

```
On-campus work
  para 1   Library and dining jobs post in the first week of each semester…
  para 2   Maximum is 20 hours a week during term. Most people find 10 to 12…
```

At a 3-paragraph rule it stays whole, so the one sentence that answers the
question is diluted by a paragraph about job postings. Dropping the rule to 2
isolates it, and the distance goes from 0.5339 to **0.3483** at rank 1. The same
thing happened to `transit_shuttle.txt` — also two paragraphs, schedule then
student-ID trivia — which went from 0.4093 to **0.2071**.

A 0.0026 margin is noise, not a result, and my relevance gate only inspects the
*best* distance. At the 3-paragraph rule the gate would have passed that question
on the strength of a chunk about STAT 150's reading load — the right decision for
the wrong reason. So I lowered the rule to 2.

The usual objection to smaller chunks is that they lose the context that made the
sentence mean anything. That doesn't apply here, because the title prefix keeps
every chunk naming its own subject: `On-campus work / Maximum is 20 hours a week
during term` stands alone perfectly well.

**Results of the change:**

| | Starter (`fallback_split`) | Rule = 3 paragraphs | Rule = 2 (final) |
|---|---|---|---|
| Chunks | 88 | 106 | **142** |
| Average length | 317 chars | 268 chars | **206 chars** |
| Longest chunk | 549 chars | 421 chars | **397 chars** |
| Documents split | 0 | 16 | **52** |
| Smallest chunk | — | 24 words | **15 words** |
| Worst in-corpus distance | — | 0.5313 (wrong doc) | **0.3483** |
| Gap to out-of-scope group | — | 0.29 | **0.48** |

The smallest chunk at 15 words still clears criterion 4's 8-word floor, which is
what the packing limit is for: 62 of the 183 body paragraphs in this corpus are
under 100 characters, and on their own those would be fragments rather than
answers. Packing folds them into a neighbour instead.

**One thing it does not fix.** The laundry and noise facts share a single
paragraph in every housing file: *"Laundry costs $1.50 wash, $1.50 dry, coin
only, and the machines are old. On noise: sound carries strangely…"*. A
paragraph-level split cannot separate those two. Chunk 4 below still carries
both. It went from 549 characters to 230, which is enough for retrieval to work,
but splitting on the `On noise:` sentence is the obvious next move if a noise
question misses in unit 2.

## Sample Chunks

All five produced by `chunker.py::split_documents`. Chunk 1 comes from a
document left whole (one body paragraph); the rest come from documents that were
split, and show the title prefix doing its job.

**Chunk 1** — source: `admin_add_drop_deadline.txt#0` — produced by: `chunker.py::split_documents`

```
On the add/drop deadline

You can add a course through the end of the second week. Dropping is a longer window — through the end of week six — but a drop after week two shows as a W on your transcript. Nothing anywhere on the registrar's site says this plainly, and students find out from each other.
```

Left whole — one body paragraph, one topic, and it names its own subject. 58 words.

**Chunk 2** — source: `course_biol_160.txt#1` — produced by: `chunker.py::split_documents`

```
BIOL 160 Cell Biology

The one piece of advice: the unit tests come fast, roughly every three weeks; falling behind once is very hard to recover from.
```

Near the short end at 27 words. Without the prefixed title this would be advice
about "the unit tests" with no course attached to it.

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
paragraph itself never says "Old Brewhouse". It retrieves at 0.1726, the best
distance of any of my five questions.

**Chunk 5** — source: `housing_old_brewhouse_laundry.txt#0` — produced by: `chunker.py::split_documents`

```
Laundry in Old Brewhouse

Machines take $1.50 wash, $1.50 dry, coin only, and the machines are old. There are eight washers and six dryers for the building, which is the wrong ratio and means the dryers back up on Sunday evenings.
```

Worth including because it states the same $1.50 price as chunk 4, from a
different file. My laundry question has two valid sources and both come back in
the top two results. This file also split under the 2-paragraph rule — the "best
time to do laundry is Tuesday or Wednesday morning" advice is now chunk `#1`,
separate from the price.

## Sample Answer

**Question:** What is the maximum working hours during the terms?

**Answer:**

```
  (best distance 0.348, cutoff 0.6)

The maximum on-campus working hours during the term is 20 hours a week (money_jobs.txt).

Sources retrieved: course_econ_101_workload.txt, course_engl_205_workload.txt, course_phys_130_workload.txt, course_stat_150_workload.txt, money_jobs.txt

1 model calls this session, 518 tokens (494 in, 24 out)
```

This is the question that drove my chunking change, so it is the one worth
showing. It also exposes something I have not fixed: **four of the five
retrieved sources are irrelevant course workload files.** The model used only
`money_jobs.txt`, which is the grounding instruction in `generate.py` working
correctly on top of noisy retrieval — but `TOP_K = 5` is still feeding the model
four chunks it should not have been sent.

And the refusal case, which is criterion 3:

```
> python app.py ask "What is the capital of Mongolia?"
  (best distance 0.825, cutoff 0.6)

I don't have enough information about that.

0 model calls this session
```

Note `0 model calls` — the gate stopped it before the model was ever reached, so
a refused question costs no quota.

**My relevance cutoff: 0.6**

This is the number the starter ships with, but I verified it rather than
inheriting it. I ran all five of my test questions and all five of the
`OUT_OF_SCOPE` ones and recorded the best distance for each:

| Question | In corpus? | Best distance | Top source |
|---|---|---|---|
| How much does it cost to wash clothes in Old Brewhouse? | yes | 0.1726 | `housing_old_brewhouse.txt` |
| What time does the campus shuttle run on the weekdays? | yes | 0.2071 | `transit_shuttle.txt` |
| When does application open for study abroad? | yes | 0.2523 | `admin_study_abroad.txt` |
| What is the assessment pattern for STAT 150 Applied Statistics? | yes | 0.2732 | `course_stat_150_exams.txt` |
| What is the maximum working hours during the terms? | yes | 0.3483 | `money_jobs.txt` |
| What is the capital of Mongolia? | no | 0.8246 | `course_hist_118_exams.txt` |
| What is the recommended dosage of ibuprofen for a headache? | no | 0.8477 | `course_hist_118.txt` |
| How do I write a for loop in Rust? | no | 0.8768 | `course_engl_205.txt` |
| Who won the 1994 World Cup? | no | 0.8859 | `course_hist_118_exams.txt` |
| How do I change the oil in a diesel engine? | no | 0.9231 | `dining_verrill_street_grill.txt` |

**The two groups:** in-corpus questions land between **0.17 and 0.35**.
Out-of-scope questions land between **0.82 and 0.93**. There is no overlap at
all — the gap runs from 0.3483 to 0.8246, which is 0.48 wide, wider than either
group. The midpoint is 0.586, so 0.6 sits almost exactly in the middle with
roughly 0.25 of margin on each side.

I left it at 0.6 rather than moving it to the exact midpoint because a round
number is easier to reason about and the extra 0.014 buys nothing. I would only
move it if a real question started landing above 0.4, which would mean the
in-corpus group had grown a tail I need to cover.

**What a wrong cutoff would cost me.** At 0.3 the system would refuse the work
hours question, the shuttle question and the study abroad question — three of my
five — all of which it can answer. At 0.9 it would accept four of the five
out-of-scope questions and hand the model chunks about history exams to answer a
question about Mongolia.

**Top-k is still 5.** I tested 8 on the STAT 150 question and the correct chunk
was already at rank 1, so a larger k only added noise. The real problem is in
the other direction, visible in the sample answer above: the gate only inspects
the single best distance, so once one chunk passes, all five go to the model
including ones further away than the cutoff I just set. On the study abroad
question, results 3, 4 and 5 sit at 0.656, 0.685 and 0.700 — all worse than 0.6,
all sent anyway. Filtering every retrieved chunk against the threshold, rather
than just the closest one, is the first thing I would change.

## How I Used AI


<!-- Two specific moments. For each: what you asked for, what came back, and
     what you changed about it.

     "I asked Claude to write the chunking function from my notes. It ignored
     the overlap, so I added that myself" is the level of detail we're after.
     "I used AI to help me code" is not.

     Milestone 5. -->

**1. The chunker that didn't chunk.** I described my corpus to Claude — 88 short
posts, a title line then two to five paragraphs, the longest 549 characters —
and asked for a chunking strategy. Before that I had tried the change myself,
and what I actually changed was the `produced_by` string inside
`fallback_split` from `"chunker.py::fallback_split"` to
`"chunker.py::split_documents"`. That made my README cite the right function
name while the splitting logic stayed exactly as the starter shipped it.
`python app.py index` gave me 88 chunks at 317 characters average, shortest 178,
longest 549 — byte-identical to the run before it. That identical summary line
is how it got caught. What I took from it: the index summary is the test. If the
numbers don't move, nothing happened, no matter what the label says.

**2. Not taking the recommendation.** Claude proposed splitting only documents
with 3 or more body paragraphs, and I used it. Milestone 4 showed it was wrong —
on "What is the maximum working hours during the terms?", the wrong document
(`course_stat_150_workload.txt`, 0.5313) beat the right one (`money_jobs.txt`,
0.5339) by 0.0026, because `money_jobs.txt` has exactly two paragraphs and never
got split. Rather than accept a second recommendation, I asked for both rules
measured across all ten of my questions. The data decided it: at a 2-paragraph
rule that question went to 0.3483 at rank 1, the shuttle question went from
0.4093 to 0.2071, nothing regressed, and the gap between my in-corpus and
out-of-scope groups went from 0.29 to 0.48. I changed the rule I'd been given,
on evidence I asked for rather than on the advice itself.


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

Five questions, three runs each, caching off. The raw per-question output is
committed in `results/run_2026-10-04_1940_before.md`, produced by
`run_eval.py::main`. The table below aggregates those rows into one row per
criterion.

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunks contain the answer | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 2. Every answer names a source | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 3. Gate stops out-of-corpus questions | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 4. Every chunk is at least 8 words and a complete sentence | every chunk | 142/142 | 142/142 | 142/142 | MET |
| 5. The named source contains the fact | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |

Criteria 3 and 4 carry the same number in all three columns because both are
measured in one deterministic pass — the gate is a comparison against a fixed
cutoff, and chunking never involves the model. Criteria 1, 2 and 5 could have
moved and didn't: I read all fifteen answers, and while the wording varied
between runs, what each answer asserted and cited did not.

### Criterion 1 — retrieved chunks contain the answer

Target 4 of 5. Result 5 of 5 on every run.
Produced by `store.py::search`, over chunks from `chunker.py::split_documents`.

```
### How much does it cost to wash clothes in Old Brewhouse? — run 1

- Best distance: 0.1726 (passed the gate)
- Sources retrieved: housing_calder_annexe.txt, housing_fenwick_court_laundry.txt, housing_innisfree_hall_laundry.txt, housing_old_brewhouse.txt, housing_old_brewhouse_laundry.txt
```

```
### What is the maximum working hours during the terms? — run 1

- Best distance: 0.3483 (passed the gate)
- Sources retrieved: course_econ_101_workload.txt, course_engl_205_workload.txt, course_phys_130_workload.txt, course_stat_150_workload.txt, money_jobs.txt
```

The answer-bearing file is present in both — `housing_old_brewhouse.txt` in the
first, `money_jobs.txt` in the second — and the same held for the other three
questions (`admin_study_abroad.txt`, `course_stat_150_exams.txt`,
`transit_shuttle.txt`). I kept the second block even though it passed, because
four of its five retrieved files are course workload documents with nothing to
do with on-campus jobs. The criterion is met and the retrieval around it is
still noisy.

### Criterion 2 — every answer names a source

Target 5 of 5. Result 5 of 5 on every run, so 15 of 15 answers overall.
Produced by `generate.py::answer_from_chunks`, under the system instruction in
`generate.py::GROUNDING_INSTRUCTION`.

```
The maximum is 20 hours a week during the term (money_jobs.txt).
```

```
The campus shuttle runs from 7am to 11pm on weekdays. 

Source: transit_shuttle.txt
```

The citation format drifted between runs — inline parentheses, `(from X)`, or a
`Source:` line of its own — but a filename appeared every time.

### Criterion 3 — the gate stops out-of-corpus questions

Target 4 of 5. Result 5 of 5 refused.
Produced by `run_eval.py::check_out_of_scope`, deciding with `gate.py::check`
against the 0.6 cutoff in `config.py`.

```
| Out-of-scope question | Best distance | Gate |
|---|---|---|
| What is the capital of Mongolia? | 0.825 | refused |
| How do I change the oil in a diesel engine? | 0.923 | refused |
| Who won the 1994 World Cup? | 0.886 | refused |
| What is the recommended dosage of ibuprofen for a headache? | 0.848 | refused |
| How do I write a for loop in Rust? | 0.877 | refused |

-> gate refused 5 of 5
```

The closest of the five sat at 0.825, well clear of the 0.6 cutoff, and none
reached the model — a refused question costs no API quota.

### Criterion 4 — every chunk is at least 8 words and a complete sentence

Target: every chunk. Result 142 of 142, smallest 15 words, none under 8.
Produced by `chunker.py::split_documents`, summarised by `chunker.py::describe`.

```
> python app.py index
  loaded   88 documents, 27,908 characters, ~317 characters per document
  chunked  142 chunks, 206 characters on average (shortest 90, longest 397), produced by chunker.py::split_documents
```

```
> python app.py chunks -n 1

======================================================================
Chunk 1  |  source: admin_add_drop_deadline.txt#0  |  produced by: chunker.py::split_documents
======================================================================
On the add/drop deadline

You can add a course through the end of the second week. Dropping is a longer window — through the end of week six — but a drop after week two shows as a W on your transcript. Nothing anywhere on the registrar's site says this plainly, and students find out from each other.
```

`shortest 90` in the summary line is the evidence: 90 characters is 15 words,
comfortably over the 8-word floor. This criterion never involves the model, so
it is identical on every run by construction.

### Criterion 5 — the source an answer names is the one the fact came from

Target 4 of 5. Result 5 of 5 on every run.
Produced by `generate.py::answer_from_chunks`.

Checking this one means putting the answer next to the file it named, because
neither piece demonstrates anything alone.

The answer:

```
The maximum is 20 hours a week during the term (money_jobs.txt).
```

What `corpora/campus_life/documents/money_jobs.txt` actually says:

```
On-campus work

Library and dining jobs post in the first week of each semester and go fast. Pay is the same across departments — the difference is whether you can study during the shift. Library desk: usually yes. Dining: no.

Maximum is 20 hours a week during term. Most people find 10 to 12 is the point where it stops affecting coursework.
```

The fact is in the file that was named. The same check passed on the other four.
The one that needed care was STAT 150, where the answer named two files:

```
(Sources: `course_stat_150_exams.txt` and `course_stat_150.txt`)
```

`course_stat_150.txt` is not only the course overview — it contains the line
"Assessment: three equally weighted midterms, no final. No curve, but the lowest
midterm is dropped," so both named files genuinely carry the fact. Had it held
only workload information, that would have been a miscitation and this criterion
would have come out 4 of 5.

## Verdicts

<!-- MET or MISSED for each of the five, against the target you wrote last
     unit — not a new one. Plus a sentence on how you decided. That sentence
     matters most where it was close.

     If your target said 4 of 5 and your runs came out 4, 3, 4, that's a MISS.
     The target has to hold, not show up occasionally.

     Milestone 2. -->

All five criteria were met. Nothing was close, so the "how I decided" column below 
is about *how I measured* rather than how I weighed a borderline call.

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
