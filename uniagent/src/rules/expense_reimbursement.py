from src.models import Rule

EXPENSE_REIMBURSEMENT_RULES: list[Rule] = [
    Rule(
        id="cost_purpose",
        subject="Was each claimed cost incurred for the institution's work, as opposed to the applicant's private use?",
        policy=(
            "- provisions on whose costs employees may pay themselves and have reimbursed, and what they state or imply about the work or purpose such costs must serve\n"
            "- provisions on what the claim or its receipts must state or show about the purpose of a cost"
        ),
        compare=(
            "- Establish what each claimed cost was incurred for from what the case documents show: the items, the addressee, the delivery address, any note of the applicant, and whether anything in them links the cost to the institution or its work. That the applicant paid from their own account is common to every such claim and says nothing about purpose.\n"
            "- Compare it with what the policy requires of the purpose of reimbursable costs: what it states, or what follows from whose costs it has employees advance and have reimbursed.\n"
            "- Conditions on when a cost may be advanced at all are other subjects. A cost that misses them can still have been incurred for the institution's work, and one that meets them can still be private."
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
