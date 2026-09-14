import pytest


@pytest.fixture
def sample_turns():
    """A minimal but representative Alpha Vantage transcript payload:
    IR intro, CEO, CFO prepared remarks, then two analyst Q&A rounds,
    then closing remarks — mirrors the real AAPL response shape.
    """
    return [
        {"speaker": "IR Person", "title": "Director of Investor Relations",
         "content": "Welcome to the call.", "sentiment": "0.2"},
        {"speaker": "CEO Name", "title": "CEO",
         "content": "Strong quarter overall.", "sentiment": "0.6"},
        {"speaker": "CFO Name", "title": "CFO",
         "content": "Revenue grew year over year.", "sentiment": "0.5"},
        {"speaker": "Operator", "title": "Operator",
         "content": "We will now begin Q&A.", "sentiment": "0.0"},
        {"speaker": "Analyst A", "title": "Analyst",
         "content": "Can you comment on margins?", "sentiment": "0.1"},
        {"speaker": "CEO Name", "title": "CEO",
         "content": "Margins improved this quarter.", "sentiment": "0.4"},
        {"speaker": "Analyst B", "title": "Analyst",
         "content": "Any update on guidance?", "sentiment": "-0.1"},
        {"speaker": "CFO Name", "title": "CFO",
         "content": "We are cautiously optimistic.", "sentiment": "0.2"},
        {"speaker": "IR Person", "title": "Director of Investor Relations",
         "content": "Thanks everyone, that concludes the call.", "sentiment": "0.3"},
    ]