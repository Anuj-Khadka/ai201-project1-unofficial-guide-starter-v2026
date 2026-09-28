"""
Stage 2 of the pipeline: splitting documents into chunks.

⚠️ THIS IS THE FILE YOU CHANGE IN MILESTONE 3.

`split_documents` below is deliberately plain. It cuts every document into
fixed-size pieces with a fixed overlap and pays no attention to where sentences
or paragraphs end. It works, and it is not good.

On a corpus of short posts it may not cut anything at all: `campus_life` comes
out as 88 documents and 88 chunks, because almost nothing in it reaches 800
characters. That is the baseline, not a bug — Milestone 3 is where you decide
whether one post should stay one chunk.

Your job in Milestone 3 is to replace the *body* of `split_documents` with a
strategy that fits the documents you actually read in Milestone 1. Keep the
name and the shape of what it returns — the rest of the pipeline calls it, and
your README has to name the function that produced your chunks.

If you get stuck for 30 minutes, `fallback_split` is the original. Switch back
to it, write down what you saw, and move on. That's a real observation about
your pipeline, not giving up.
"""

import re
from dataclasses import dataclass

import config
from ingest import Document


@dataclass
class Chunk:
    """One piece of one document."""

    text: str
    source: str        # which file it came from
    index: int         # which chunk within that file, starting at 0
    produced_by: str   # the function that made it — cite this in your README

    @property
    def label(self) -> str:
        return f"{self.source}#{self.index}"


def fallback_split(
    documents: list[Document],
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[Chunk]:
    """
    The starter's original chunker. Fixed-size character windows with overlap.

    Keep this function. Milestone 3's stop rule points back at it, and having
    something to compare your own strategy against is useful in unit 2.
    """
    chunk_size = chunk_size or config.CHUNK_SIZE
    overlap = overlap or config.CHUNK_OVERLAP

    if overlap >= chunk_size:
        raise ValueError("overlap has to be smaller than chunk_size")

    chunks: list[Chunk] = []
    for doc in documents:
        start = 0
        index = 0
        while start < len(doc.text):
            piece = doc.text[start : start + chunk_size].strip()
            if piece:
                chunks.append(
                    Chunk(
                        text=piece,
                        source=doc.source,
                        index=index,
                        produced_by="chunker.py::fallback_split",
                    )
                )
                index += 1
            start += chunk_size - overlap

    return chunks


_PARAGRAPH_BREAK = re.compile(r"\n\s*\n")
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def _paragraphs(text: str) -> list[str]:
    """
    Blank-line separated blocks, with CRLF line endings normalised first.

    The corpus files end their lines with \r\n. Splitting on "\n\n" without
    normalising finds nothing, and every document comes back as one block.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return [block.strip() for block in _PARAGRAPH_BREAK.split(text) if block.strip()]


def _title_and_body(blocks: list[str]) -> tuple[str, list[str]]:
    """
    Peel the heading off the top of a document.

    Every campus_life document opens with a bare title line — "Laundry in Old
    Brewhouse", "CS 340 Databases" — on its own, with no sentence punctuation.
    It matters because it is the only place the building or course name
    appears: the laundry paragraph of housing_old_brewhouse.txt never says
    "Old Brewhouse" anywhere in it.
    """
    if len(blocks) > 1:
        first = blocks[0]
        if "\n" not in first and len(first) <= 90 and not first.endswith((".", "!", "?")):
            return first, blocks[1:]
    return "", blocks


def _pack(paragraphs: list[str], limit: int) -> list[str]:
    """
    Group consecutive paragraphs into bodies no longer than `limit` characters.

    Never cuts inside a paragraph, so no sentence is ever split in half. The
    limit only decides whether two neighbours travel together: 62 of the 183
    body paragraphs in this corpus are under 100 characters, and on their own
    those are fragments rather than answers.
    """
    bodies: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if not current:
            current = paragraph
        elif len(current) + 2 + len(paragraph) <= limit:
            current = f"{current}\n\n{paragraph}"
        else:
            bodies.append(current)
            current = paragraph
    if current:
        bodies.append(current)
    return bodies


def _carried_sentence(previous: str, budget: int) -> str:
    """The last sentence of `previous`, when overlap is switched on."""
    if budget <= 0:
        return ""
    sentences = [s.strip() for s in _SENTENCE_END.split(previous) if s.strip()]
    if not sentences or len(sentences[-1]) > budget:
        return ""
    return sentences[-1]


def split_documents(documents: list[Document]) -> list[Chunk]:
    """
    Split only the documents that hold more than one thought, and prefix the
    title line to every piece.

    Why not fixed character windows: every document in campus_life is under
    550 characters, so the starter's 800-character window never cut anything.
    88 documents came out as 88 chunks and CHUNK_OVERLAP was dead code. Size
    is not what is wrong with these documents.

    What is wrong is that the longer ones cover several unrelated topics at
    once. housing_old_brewhouse.txt runs to 549 characters and covers the
    building's history, heating, laundry prices and noise, so a question about
    laundry retrieves four topics' worth of text to get one clause.

    So: documents with fewer than MIN_PARAGRAPHS_TO_SPLIT body paragraphs stay
    whole, and longer ones are cut on paragraph boundaries. The rule counts
    paragraphs rather than characters because length alone says nothing here —
    admin_housing_lottery.txt is 398 characters of a single unbroken paragraph
    that a character rule would flag as long and then fail to split.

    Every chunk from a split document carries the title line, so a chunk about
    laundry costs still says "Old Brewhouse" and can be retrieved by a question
    that names the building.
    """
    limit = config.CHUNK_SIZE
    overlap_budget = config.CHUNK_OVERLAP
    split_at = config.MIN_PARAGRAPHS_TO_SPLIT

    chunks: list[Chunk] = []

    for doc in documents:
        blocks = _paragraphs(doc.text)
        if not blocks:
            continue

        title, body = _title_and_body(blocks)

        if len(body) < split_at:
            # One thought, one chunk. Keep the document exactly as it is.
            bodies = ["\n\n".join(body)]
        else:
            bodies = _pack(body, limit)

        for index, text in enumerate(bodies):
            if index > 0:
                carried = _carried_sentence(bodies[index - 1], overlap_budget)
                if carried:
                    text = f"{carried}\n\n{text}"

            chunks.append(
                Chunk(
                    text=f"{title}\n\n{text}" if title else text,
                    source=doc.source,
                    index=index,
                    produced_by="chunker.py::split_documents",
                )
            )

    return chunks


def describe(chunks: list[Chunk]) -> str:
    """A one-line summary, printed after indexing."""
    if not chunks:
        return "0 chunks"
    lengths = [len(c.text) for c in chunks]
    return (
        f"{len(chunks)} chunks, "
        f"{sum(lengths) // len(lengths)} characters on average "
        f"(shortest {min(lengths)}, longest {max(lengths)}), "
        f"produced by {chunks[0].produced_by}"
    )


if __name__ == "__main__":
    from ingest import load_documents

    chunks = split_documents(load_documents())
    print(describe(chunks))
