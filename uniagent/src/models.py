"""Data shapes exchanged between pipeline stages."""

from typing import Literal

from pydantic import BaseModel

Verdict = Literal["pass", "fail", "not_applicable", "unknown"]


class Rule(BaseModel):
    """What one rule checks; never a value or the rule's logic."""

    id: str
    subject: str = ""
    """
    The one question this rule answers: shared by every stage, so the digest and the
    check agree on it, and is named in a way that other rules within the same domain
    understand they should not interfere with it.
    """
    policy: str = ""
    """
    Which provisions to find, one bullet per kind. The digest prompt already keeps
    their conditions and exceptions, so the bullets need not ask for them.
    """
    compare: str = ""
    """
    Which case facts to collect and set against the policy, one instruction per bullet.
    Leave out what the check prompt already says, such as applying exceptions.
    """
    check: str = ""  # legacy
    queries: dict[str, list[str]]  # language code -> BM25 keyword queries
    questions: dict[str, list[str]]  # language code -> natural-language questions

    def policy_text(self) -> str:
        """The rule as the digest sees it: which policy text to find."""
        if self.check:
            return self.check
        return f"<subject>{self.subject}</subject>\n<policy>\n{self.policy}\n</policy>"

    def check_text(self) -> str:
        """The rule as the case check sees it: what to compare in the case."""
        if self.check:
            return self.check
        return (
            f"<subject>{self.subject}</subject>\n<compare>\n{self.compare}\n</compare>"
        )


class PolicyQuote(BaseModel):
    corpus: str
    doc_id: str
    quote: str  # verified verbatim against the retrieved document
    title: str = ""  # the law or page the quote comes from


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
