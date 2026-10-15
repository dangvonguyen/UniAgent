from src.models import Rule

EXPENSE_REIMBURSEMENT_RULES: list[Rule] = [
    Rule(
        id="cost_purpose",
        check=(
            "Subject: the work-related purpose of each claimed cost: was it incurred for the institution's work rather than privately?\n"
            "Policy: the provisions that let employees pay costs themselves and have them reimbursed, given whole with their conditions and exceptions, including what they say or imply about whom and for what such costs must be incurred, and what the policy requires the claim or its receipts to state or show about that purpose.\n"
            "Compare: what each claimed cost was incurred for, against what these provisions require of the purpose of reimbursable costs, whether they state it or it follows from whom and for whom they let costs be advanced. Where the provisions say how the purpose must be stated or shown, apply that requirement as written. Where they say nothing about it, judge from the case documents as a whole: a fact they neither show nor contradict decides nothing by itself, and the verdict rests on what they do show.\n"
            "Out of scope, never a reason to fail this rule even where the provisions regulate it: how the purchase should have been ordered and whether it was eligible to be paid privately; which categories of costs are excluded from reimbursement or restricted to certain occasions or beneficiaries; whether the receipt is a final invoice; whether the same order was claimed more than once; the cost amounts; the submission procedure (forms, systems, deadlines)."
        ),
        queries={
            "de": [
                "privat verauslagte Kosten Erstattung",
                "Auslagen Beschäftigte Anschaffung selbst bezahlt Erstattung",
                "Kostenerstattung Auslagen Quittung Erstattungsformular",
                "Erstattung verauslagter Kosten dienstlicher Zweck",
                "Erstattungsantrag Auslagen Begründung Verwendungszweck",
            ],
            "en": [
                "reimbursement of privately advanced costs",
                "employees paid purchases themselves reimbursement receipt",
                "out-of-pocket expenses refund work-related purpose",
                "expense claim purpose of expenditure statement",
            ],
        },
        questions={
            "de": [
                "Unter welchen Voraussetzungen können Beschäftigte selbst bezahlte Kosten erstattet bekommen?",
                "Welchen dienstlichen Zweck müssen von Beschäftigten verauslagte Kosten haben, damit sie erstattet werden?",
                "Wie muss der Zweck einer Auslage auf dem Beleg oder im Antrag angegeben werden?",
            ],
            "en": [
                "Under what conditions can employees be reimbursed for costs they paid themselves?",
                "What work-related purpose must costs advanced by employees have to be reimbursed?",
                "How must the purpose of an expense be stated on the receipt or in the claim?",
            ],
        },
    ),
]
