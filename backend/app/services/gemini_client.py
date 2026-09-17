import json
import time

from google import genai
from google.genai import types
from google.genai import errors as genai_errors
from pydantic import BaseModel, Field, ValidationError

from app.config import settings

MODEL_NAME = "gemini-3.6-flash"
MAX_ATTEMPTS = 2

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
    overall_sentiment: str
    sentiment_score: float
    management_confidence: float
    key_themes: list[str]
    forward_guidance: str
    guidance_tone: str
    risk_factors: list[str]
    summary: str
    segment_sentiments: list[float] = Field(min_length=3, max_length=3)


class GeminiAnalysisError(Exception):
    pass


class GeminiAnalysisClient:
    def __init__(self, model_name: str = MODEL_NAME):
        self.model_name = model_name
        self.client = genai.Client(api_key=settings.google_gemini_api_key)

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
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(response_mime_type="application/json"),
                )
                data = json.loads(response.text)
                return AnalysisResult.model_validate(data)
            except (json.JSONDecodeError, ValidationError, genai_errors.APIError) as e:
                last_error = e
                if attempt < MAX_ATTEMPTS - 1:
                    time.sleep(2)
                continue

        raise GeminiAnalysisError(
            f"Gemini failed to produce a valid analysis after {MAX_ATTEMPTS} attempts: {last_error}"
        ) from last_error
