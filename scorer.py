from gate import REFUSAL


def judge(question: str, expects: str, answer: str, results) -> bool:
    """
    Did this answer state the fact?

    `question` and `results` are unused — they are part of the signature
    run_eval.py expects, and keeping them makes it easy to score on retrieval
    instead later without changing the call.
    """
    if not expects or not expects.strip():
        return False

    if not answer or answer.strip() == REFUSAL:
        # The gate refused an in-corpus question. That is a failure here:
        # OUT_OF_SCOPE questions are measured separately by run_eval.py.
        return False

    return expects.strip().lower() in answer.lower()
