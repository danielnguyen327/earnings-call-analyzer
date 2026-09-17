import json
import time

import anthropic
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.config import settings

MODEL_NAME = "claude-haiku-4-5-20251001"
MAX_TOKENS = 2048
MAX_ATTEMPTS = 2
TIMEOUT_S = 90.0

PROMPT_TEMPLATE = """You are analyzing an earnings call transcript for {company_name} ({quarter}).

The call is split into three parts: prepared remarks, Q&A, and closing remarks.

--- PREPARED REMARKS ---
{prepared_remarks}

--- Q&A ---
{qa}

--- CLOSING ---
{closing}

Analyze this transcript and respond with a single JSON object with exactly these fields:
- overall_sentiment: one of "positive", "cautious", "negative"
- sentiment_score: float from 0.0 (very negative) to 1.0 (very positive)
- management_confidence: float from 0.0 (low confidence) to 1.0 (high confidence)
- key_themes: array of 3-6 short strings naming the main topics discussed
- forward_guidance: a paragraph summarizing forward-looking guidance mentioned
- guidance_tone: one of "optimistic", "neutral", "cautious"
- risk_factors: array of short strings naming risks or concerns raised
- summary: a 2-4 sentence summary of the call
- segment_sentiments: array of exactly 3 floats (0.0-1.0), one each for prepared remarks, Q&A, and closing, in that order
"""


class AnalysisResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    overall_sentiment: str
    sentiment_score: float
    management_confidence: float
    key_themes: list[str]
    forward_guidance: str
    guidance_tone: str
    risk_factors: list[str]
    summary: str
    segment_sentiments: list[float] = Field(min_length=3, max_length=3)


class ClaudeAnalysisError(Exception):
    pass


def _api_schema() -> dict:
    """Claude's structured-output schema only supports minItems of 0 or 1,
    so strip array length constraints here — AnalysisResult still enforces
    them when we validate the parsed response below.
    """
    schema = AnalysisResult.model_json_schema()
    for prop in schema.get("properties", {}).values():
        prop.pop("minItems", None)
        prop.pop("maxItems", None)
    return schema


class ClaudeAnalysisClient:
    def __init__(self, model_name: str = MODEL_NAME):
        self.model_name = model_name
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key, timeout=TIMEOUT_S)

    def analyze(self, company_name: str, quarter: str, segments_text: dict[str, str]) -> AnalysisResult:
        prompt = PROMPT_TEMPLATE.format(
            company_name=company_name,
            quarter=quarter,
            prepared_remarks=segments_text.get("prepared_remarks", ""),
            qa=segments_text.get("qa", ""),
            closing=segments_text.get("closing", ""),
        )

        last_error: Exception | None = None
        for attempt in range(MAX_ATTEMPTS):
            try:
                response = self.client.messages.create(
                    model=self.model_name,
                    max_tokens=MAX_TOKENS,
                    messages=[{"role": "user", "content": prompt}],
                    output_config={
                        "format": {
                            "type": "json_schema",
                            "schema": _api_schema(),
                        }
                    },
                )
                text = response.content[0].text
                data = json.loads(text)
                return AnalysisResult.model_validate(data)
            except (json.JSONDecodeError, ValidationError, anthropic.APIError) as e:
                last_error = e
                if attempt < MAX_ATTEMPTS - 1:
                    time.sleep(2)
                continue

        raise ClaudeAnalysisError(
            f"Claude failed to produce a valid analysis after {MAX_ATTEMPTS} attempts: {last_error}"
        ) from last_error
