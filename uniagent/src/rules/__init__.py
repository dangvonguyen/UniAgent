from typing import Literal

from src.models import Rule

from .business_trip import BUSINESS_TRIP_RULES
from .expense_reimbursement import EXPENSE_REIMBURSEMENT_RULES
from .procurement import PROCUREMENT_RULES

CaseType = Literal["business_trip", "expense_reimbursement", "procurement"]

RULES: dict[CaseType, list[Rule]] = {
    "business_trip": BUSINESS_TRIP_RULES,
    "expense_reimbursement": EXPENSE_REIMBURSEMENT_RULES,
    "procurement": PROCUREMENT_RULES,
}

TOPICS: dict[CaseType, str] = {
    "business_trip": (
        "Business trip: an employee's request concerning an official trip, such as "
        "its approval or the reimbursement of its costs."
    ),
    "expense_reimbursement": (
        "Reimbursement of privately advanced costs: an employee paid costs on the "
        "institution's behalf and asks to be paid back."
    ),
    "procurement": (
        "Internal procurement: a request to the institution's procurement office to "
        "buy goods or services."
    ),
}

# Case directory name prefix -> case type, e.g. "auslagenerstattung-03".
CASE_TYPE_PREFIXES: dict[str, CaseType] = {
    "dienstreiseantrag": "business_trip",
    "auslagenerstattung": "expense_reimbursement",
    "beschaffungsantrag": "procurement",
}


def case_type_for(case_id: str) -> CaseType:
    for prefix, case_type in CASE_TYPE_PREFIXES.items():
        if case_id == prefix or case_id.startswith(f"{prefix}-"):
            return case_type
    raise ValueError(
        f"Unknown case type for {case_id!r}; expected a directory name starting "
        f"with one of {sorted(CASE_TYPE_PREFIXES)}."
    )
