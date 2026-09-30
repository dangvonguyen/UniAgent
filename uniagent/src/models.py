"""Data shapes exchanged between pipeline stages."""

from typing import Literal

from pydantic import BaseModel

Verdict = Literal["pass", "fail", "not_applicable", "unknown"]


class Rule(BaseModel):
    id: str
    check: str  # topic and what to compare; never a value, never the rule's logic
    queries: dict[str, list[str]]  # language code -> queries


class PolicyQuote(BaseModel):
    corpus: str
    doc_id: str
    quote: str  # verified verbatim against the retrieved document


class ResolvedRule(BaseModel):
    rule: Rule
    quotes: list[PolicyQuote]  # [] = looked up, nothing found


class CaseDocument(BaseModel):
    name: str
    text: str


class Case(BaseModel):
    case_id: str
    documents: list[CaseDocument]


class CaseQuote(BaseModel):
    document: str
    quote: str


class RuleVerdict(BaseModel):
    rule_id: str
    verdict: Verdict
    reason: str
    case_quotes: list[CaseQuote] = []
    policy_quotes: list[PolicyQuote] = []


class Decision(BaseModel):
    case_id: str
    result: Literal["angenommen", "abgelehnt"]
    verdicts: list[RuleVerdict]
