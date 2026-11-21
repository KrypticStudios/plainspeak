"""The shape of PlainSpeak's answer.

We ask the AI to fill in exactly these fields (this is called "structured
output"). Because the shape is fixed, our code can trust that `summary`,
`deadlines`, etc. always exist, and Pydantic checks the AI's reply for us.
"""

from typing import Literal

from pydantic import BaseModel, Field


class Deadline(BaseModel):
    date: str = Field(description="Date in YYYY-MM-DD format. Empty string if the letter gives no exact date.")
    what: str = Field(description="What must happen by this date, in plain words.")
    source_quote: str = Field(description="The exact words copied from the letter that mention this deadline.")


class ActionStep(BaseModel):
    step: str = Field(description="One simple thing the reader should do, starting with a verb.")
    source_quote: str = Field(description="The exact words copied from the letter that this step is based on.")


class Contact(BaseModel):
    name: str = Field(description="Person or office to contact.")
    phone: str = Field(default="", description="Phone number exactly as written, or empty.")
    email: str = Field(default="", description="Email exactly as written, or empty.")
    address: str = Field(default="", description="Street address exactly as written, or empty.")
    why: str = Field(description="Why the reader would contact them, in plain words.")


class MoneyItem(BaseModel):
    amount: str = Field(description="Amount exactly as written, e.g. $1,250.00.")
    what: str = Field(description="What the money is for, in plain words.")
    source_quote: str = Field(description="The exact words copied from the letter that mention this amount.")


class LetterAnalysis(BaseModel):
    original_text: str = Field(description="The full text of the letter, transcribed exactly in its original language.")
    document_type: str = Field(description="What kind of letter this is, e.g. 'Eviction notice', 'Medical bill'.")
    sender: str = Field(description="Who sent the letter.")
    summary: str = Field(description="2-4 short sentences explaining the letter at a 5th-grade reading level.")
    urgency: Literal["low", "medium", "high"]
    urgency_reason: str = Field(description="One sentence on why it has this urgency.")
    deadlines: list[Deadline]
    actions: list[ActionStep]
    money: list[MoneyItem]
    contacts: list[Contact]
    rights: list[str] = Field(description="Rights or protections the letter itself mentions, in plain words. Empty if none.")
    unclear_points: list[str] = Field(description="Anything that is unclear, missing, or that you are unsure about.")
    needs_human_help: bool = Field(description="True if the reader should talk to a real person (lawyer, caseworker, etc.).")
    help_reason: str = Field(description="Why they should, or should not, get human help.")
    confidence: Literal["high", "medium", "low"] = Field(description="How confident you are in this reading of the letter.")


class QuestionAnswer(BaseModel):
    """The answer to a follow-up question about the letter."""
    answer: str = Field(description="A short answer in plain words (5th-grade level), in the reader's language.")
    answered_from_letter: bool = Field(description="True only if the letter itself answers the question.")
    source_quotes: list[str] = Field(description="Exact words copied from the letter that support the answer. "
                                                 "Empty if the letter doesn't say.")
    who_to_ask: str = Field(default="", description="If the letter doesn't fully answer it, who could (from the "
                                                    "letter's contacts if possible). Empty otherwise.")
