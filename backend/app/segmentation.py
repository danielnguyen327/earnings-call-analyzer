SEGMENT_NAMES = ("prepared_remarks", "qa", "closing")

def segment_transcript(turns: list[dict]) -> dict[str, list[dict]]:
    if not turns:
        return {name: [] for name in SEGMENT_NAMES}

    def norm(title):
        return (title or "").strip().lower()

    analyst_indices = [
        i for i, t in enumerate(turns) if norm(t.get("title")) == "analyst"
    ]

    if analyst_indices:
        qa_start, qa_end = analyst_indices[0], analyst_indices[-1]
        moderator_title = norm(turns[0].get("title"))
        # Include the answer(s) to the last question, stopping once the
        # moderator/operator hands off into closing remarks.
        while (
            qa_end + 1 < len(turns)
            and norm(turns[qa_end + 1].get("title")) not in {moderator_title, "operator"}
        ):
            qa_end += 1
    else:
        # No analyst detected - fall back to thirds
        n = len(turns)
        qa_start, qa_end = n // 3, (2 * n) // 3 - 1

    return {
        "prepared_remarks": turns[:qa_start],
        "qa": turns[qa_start:qa_end + 1],
        "closing": turns[qa_end + 1:],
    }

def flatten_turns(turns: list[dict]) -> str:
    return "\n\n".join(
        f"{t.get("speaker", "Unknown")}: {t.get("content", "")}"
        for t in turns
    )

def segment_text(segments: dict[str, list[dict]]) -> dict[str, str]:
    return {name: flatten_turns(turns) for name, turns in segments.items()}