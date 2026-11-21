"""Sends a letter to Google Gemini and gets back a LetterAnalysis.

Flow:  letter (photo, PDF or text)  ->  Gemini  ->  JSON  ->  LetterAnalysis
The API key is read on the server from .env, so it never reaches the browser.
"""

import os

from dotenv import load_dotenv

from .schema import LetterAnalysis, QuestionAnswer

load_dotenv()

# Models we try in order. If Google retires one, the next one is used.
DEFAULT_MODELS = ["gemini-3.8-flash", "gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-flash-latest"]

SYSTEM_PROMPT = """You are PlainSpeak, a careful assistant that helps people understand official letters
(housing, medical, benefits, school, immigration, utilities, legal).

Rules:
- Write every explanation for a 5th-grade reading level: short sentences, common words, no jargon.
  If you must use a term like "eviction", explain it in the same sentence.
- Write all explanations in the reader's chosen language. Keep `original_text` and every `source_quote`
  in the letter's ORIGINAL language, copied word for word.
- Every deadline, action and money item MUST include a `source_quote` copied exactly from the letter.
  Never invent dates, amounts, phone numbers or names. If something is not in the letter, leave it empty
  and mention it in `unclear_points`.
- Do not give legal or medical advice. Explain what the letter says and who can help.
- Set `needs_human_help` to true for eviction, court, immigration, debt collection, losing benefits,
  or anything with serious consequences.
- If the image is blurry or the text is cut off, say so in `unclear_points` and lower `confidence`.
"""


class AnalyzerError(Exception):
    """A friendly error we can show to the user."""


def has_api_key() -> bool:
    return bool(os.getenv("GEMINI_API_KEY"))


def _models_to_try() -> list[str]:
    preferred = os.getenv("GEMINI_MODEL")
    models = [preferred] if preferred else []
    return models + [m for m in DEFAULT_MODELS if m != preferred]


def _ask_gemini(system_prompt: str, contents: list, answer_shape):
    """Send `contents` to Gemini and return an object of type `answer_shape` (a Pydantic class).

    Tries each model in turn, and turns technical errors into friendly messages.
    """
    # Imported here so the app (and tests) still load without the library configured.
    from google import genai
    from google.genai import errors, types

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        response_mime_type="application/json",
        response_schema=answer_shape,   # the AI must fill in exactly these fields
        temperature=0.2,                # low = more careful, less creative
    )

    last_error = None
    for model in _models_to_try():
        try:
            response = client.models.generate_content(model=model, contents=contents, config=config)
        except errors.ClientError as e:
            last_error = e
            if e.code == 404:  # model not found -> try the next one
                continue
            if e.code == 429:
                raise AnalyzerError("The free AI limit was reached. Wait a minute and try again.") from e
            if e.code in (400, 401, 403):
                raise AnalyzerError(f"The AI service rejected the request ({e.code}). Check your API key.") from e
            raise AnalyzerError(f"The AI service returned an error ({e.code}).") from e
        except errors.ServerError as e:
            last_error = e
            continue  # Google had a hiccup -> try the next model
        try:
            if isinstance(response.parsed, answer_shape):
                return response.parsed
            return answer_shape.model_validate_json(response.text)
        except Exception as e:
            raise AnalyzerError("The AI gave an answer we couldn't read. Please try again.") from e

    raise AnalyzerError(f"No AI model was available right now. Last error: {last_error}")


def analyze_letter(language: str, text: str = "", files: list[tuple[bytes, str]] | None = None) -> LetterAnalysis:
    """Analyze a letter given as pasted text and/or photos/PDFs.

    `files` is a list of (file_bytes, mime_type), one per page, in order.
    """
    files = files or []
    if not has_api_key():
        raise AnalyzerError("No API key found. Add GEMINI_API_KEY to your .env file, or try a sample letter.")
    if not text.strip() and not files:
        raise AnalyzerError("Please upload a photo of your letter or paste its text.")

    from google.genai import types

    contents: list = [f"Explain this letter. The reader's language is: {language}."]
    for page, (data, mime) in enumerate(files, start=1):
        if len(files) > 1:
            contents.append(f"Page {page}:")
        contents.append(types.Part.from_bytes(data=data, mime_type=mime))
    if text.strip():
        contents.append("Letter text:\n" + text)
    return _ask_gemini(SYSTEM_PROMPT, contents, LetterAnalysis)


QUESTION_PROMPT = """You answer a reader's question about ONE official letter.
- Answer ONLY from what the letter says. Quote the exact words you used in `source_quotes`.
- If the letter does not answer the question, say so plainly, set `answered_from_letter` to false,
  and say who could answer it in `who_to_ask` (use a contact from the letter if there is one).
- Never invent facts, dates, amounts, laws or phone numbers. No legal or medical advice.
- Use short sentences and common words. Write the answer in the reader's language;
  keep quotes in the letter's original language.
"""


def ask_question(letter_text: str, question: str, language: str) -> QuestionAnswer:
    """Answer a follow-up question using only the letter."""
    if not has_api_key():
        raise AnalyzerError("Asking your own questions needs an AI key. Try one of the suggested questions.")
    if not question.strip():
        raise AnalyzerError("Type a question first.")
    if len(question) > 500:
        raise AnalyzerError("Please keep your question shorter (under 500 characters).")
    contents = [f"The reader's language is: {language}.", "The letter:\n" + letter_text, "Question: " + question]
    return _ask_gemini(QUESTION_PROMPT, contents, QuestionAnswer)
