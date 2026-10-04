# Acceptance criteria — The Unofficial Guide

Five criteria that say what "working" means for this system, written in unit 1
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"Retrieval works"* is an opinion. *"For at
least 4 of my 5 test questions, the top results include a chunk containing the
answer"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter or looser one. A reason that says something about your corpus or your
pipeline earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

---

## 1. Retrieved chunks contain the answer

For at least 4 of my 5 test questions, the retrieved chunks include one that
contains the answer.

**Why this target:**
<!-- e.g. "One of my questions is about a topic only two documents mention, so
     I expect that one to be hard." -->

I picked 4 of 5 rather than 5 of 5 because one of my questions is about a topic only one documents mention, and the chunk that covers it is short enough that it may not embed close to the question. I didn't go looser than 4 because a retriever that misses two of five questions isn't one I'd trust to build answers on.


---

## 2. Every answer names a source

Every answer the system produces names at least one source document.

**Why this target:**
<!-- Why all five and not four? What about your setup makes that achievable —
     or what would have to go wrong for it not to be? -->

This is 5 of 5 because naming a source isn't something retrieval has to get right. It's a formatting behavior I control through the prompt and the citation step, so there's no good reason it should ever fail. If it did fail, that would mean the prompt or the output parsing broke, not that the question was hard.

---

## 3. The relevance gate stops out-of-corpus questions

When I ask a question my documents clearly don't cover, the relevance gate
stops it and the system returns "I don't have enough information about that" —
in at least 4 of 5 tries.

<!-- The five questions are the ones in `OUT_OF_SCOPE` at the bottom of
     `questions.py`, and `run_eval.py` puts them through the gate and writes
     what happened into your run log. Swap them for your own if you'd rather —
     just keep five of them, or the "4 of 5" above has nothing to be 4 of. -->

**Why this target:**
<!-- What did your distances look like when you set the cutoff in Milestone 4?
     Was there a clean gap, or did the two groups overlap? -->
I picked 4 of 5 because one of my out-of-scope questions uses words that also appear in my documents, so I expect it to score close enough to sneak past the gate. The other four are about topics nowhere in the corpus and should be easy to stop.
---

## 4. Size of the chunk

Every chunk should be at least 8 words and read as at least one complete sentence.

**Why this target:**

I made this "every chunk" rather than a sample because the chunks most likely to
fail are title lines and one-line fragments, and those cluster in a few
documents where a random sample of five could miss them entirely. Eight words is
the threshold because my chunker packs any paragraph under 100 characters into
its neighbour rather than emitting it alone, and 62 of the 183 body paragraphs
in `campus_life` are that short — so if the packing step ever fails to fire, a
bare heading is exactly what I would get, and a bare heading in this corpus is
three to six words.

---

## 5. The source an answer names is the one the fact came from

For at least 4 of my 5 test questions, the fact in the answer can be found in
the document the answer names. Where two documents both contain the fact,
naming either one counts.

**Why this target:**

Criterion 2 only checks that a filename appears, so an answer could cite the
wrong file and still pass all four of my other criteria. I picked 4 of 5 rather
than 5 of 5 because the model is handed 5 chunks, not 1, and on "maximum working
hours" four of those five are course workload files that have nothing to do with
on-campus jobs — that is the question I expect to be miscited if any of them is.
I didn't go looser than 4 because a system that attaches the wrong filename to
one answer in three is worse than one that cites nothing at all: a wrong source
looks exactly like a right one until you go and check it.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 2 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 1. Retrieved chunks contain the answer

         For at least 4 of my 5 test questions, the retrieved chunks include
         one that contains the answer.

         **Why this target:** ...

         > **Revised in unit 2:** For at least 4 of 5 questions, the top three
         > results contain the answer.
         >
         > **Why revised:** I couldn't judge "the chunks include one that
         > contains the answer" the same way twice — I scored two questions
         > differently on Monday than on Wednesday. The new version is
         > something I can actually check.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said 4 of 5 but got 2 of 5, so 2 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.

     The whole reason the originals stay visible is so someone can see what you
     said before you knew the answer.
     ───────────────────────────────────────────────────────────────────────── -->
