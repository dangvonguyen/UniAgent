from .models import Rule

RULES: list[Rule] = [
    Rule(
        id="advance_approval",
        check=(
            "Check whether the business trip application was submitted at the time "
            "the policy on approving business trips requires "
            "(application date relative to the trip start)."
        ),
        queries=[
            "Dienstreise Genehmigung vor Antritt der Reise",
            "Dienstreise vorher angeordnet oder genehmigt Reisekostenabrechnung",
            "business trip approval before travel",
        ],
    ),
    Rule(
        id="overnight_rate_cap",
        check=(
            "Compare the case's accommodation costs per night against the policy's "
            "reimbursement rule for overnight costs on business trips."
        ),
        queries=[
            "Übernachtungskosten Dienstreise erstattungsfähig je Nacht",
            "Übernachtungsgeld Reisekostengesetz Hessen",
            "business trip accommodation costs reimbursement per night",
        ],
    ),
]
