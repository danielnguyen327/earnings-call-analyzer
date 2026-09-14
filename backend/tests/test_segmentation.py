from app.segmentation import segment_transcript, segment_text, flatten_turns


def test_segment_transcript_splits_on_analyst_turns(sample_turns):
    segments = segment_transcript(sample_turns)

    assert [t["title"] for t in segments["prepared_remarks"]] == [
        "Director of Investor Relations", "CEO", "CFO", "Operator",
    ]
    assert [t["speaker"] for t in segments["qa"]] == [
        "Analyst A", "CEO Name", "Analyst B", "CFO Name",
    ]
    assert [t["title"] for t in segments["closing"]] == [
        "Director of Investor Relations",
    ]


def test_segment_transcript_empty():
    assert segment_transcript([]) == {
        "prepared_remarks": [], "qa": [], "closing": [],
    }


def test_segment_transcript_falls_back_to_thirds_without_analyst_turns():
    turns = [{"speaker": f"S{i}", "title": "Executive", "content": str(i)} for i in range(9)]
    segments = segment_transcript(turns)

    assert sum(len(v) for v in segments.values()) == 9
    assert len(segments["qa"]) > 0


def test_flatten_turns():
    turns = [{"speaker": "A", "content": "hello"}, {"speaker": "B", "content": "world"}]
    assert flatten_turns(turns) == "A: hello\n\nB: world"


def test_segment_text(sample_turns):
    segments = segment_transcript(sample_turns)
    text = segment_text(segments)

    assert set(text.keys()) == {"prepared_remarks", "qa", "closing"}
    assert "Strong quarter overall." in text["prepared_remarks"]
    assert "Can you comment on margins?" in text["qa"]
    assert "concludes the call" in text["closing"]