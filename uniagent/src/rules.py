from .models import Rule

RULES: list[Rule] = [
    Rule(
        id="application_approval_timing",
        check=(
            "Determine the relationship between the timing of a business-trip "
            "application or approval and the timing of the trip."
        ),
        queries=[
            (
                "Dienstreise Dienstreiseantrag Antragstellung Genehmigung "
                "Zeitpunkt Frist Reisebeginn Reiseantritt"
            ),
            (
                "business trip application approval timing deadline "
                "trip start travel commencement"
            ),
        ],
    ),
    Rule(
        id="reimbursement_claim_timing",
        check=(
            "Determine the timing rules that apply to claiming, submitting, "
            "or settling business-trip expenses."
        ),
        queries=[
            (
                "Dienstreise Reisekosten Reisekostenabrechnung "
                "Reisekostenvergütung Erstattung Antrag Abrechnung "
                "Frist Ausschlussfrist"
            ),
            (
                "business trip travel expenses reimbursement claim "
                "submission settlement application deadline time limit"
            ),
        ],
    ),
    Rule(
        id="domestic_accommodation_reimbursement",
        check=(
            "Determine how accommodation costs for domestic business trips "
            "are reimbursed, including whether any limits or justification "
            "conditions apply."
        ),
        queries=[
            (
                "Dienstreise Inland Reisekosten Übernachtung "
                "Übernachtungskosten Hotelkosten Erstattung "
                "Höchstbetrag Höchstgrenze Nachweis Begründung"
            ),
            (
                "domestic business trip accommodation hotel overnight "
                "cost reimbursement limit maximum justification evidence"
            ),
        ],
    ),
    Rule(
        id="foreign_accommodation_reimbursement",
        check=(
            "Determine how accommodation costs for business trips abroad "
            "are reimbursed and what conditions apply."
        ),
        queries=[
            (
                "Auslandsdienstreise Ausland Reisekosten Übernachtung "
                "Übernachtungskosten Hotelkosten Erstattung "
                "Auslandsreisekosten"
            ),
            (
                "foreign business trip abroad accommodation hotel "
                "overnight expenses travel cost reimbursement"
            ),
        ],
    ),
    Rule(
        id="business_private_trip_combination",
        check=(
            "Determine how combining a business trip with private travel "
            "or a private stay affects travel-expense reimbursement."
        ),
        queries=[
            (
                "Dienstreise Privatreise Privataufenthalt private Verlängerung "
                "Verbindung Reisekosten Fahrtkosten Erstattung"
            ),
            (
                "business trip private travel private stay extension "
                "combined journey travel expenses reimbursement"
            ),
        ],
    ),
    Rule(
        id="a1_certificate_requirements",
        check=(
            "Determine what rules, if any, apply to an A1 certificate for "
            "business travel or work abroad, including relevant timing."
        ),
        queries=[
            (
                "A1 Bescheinigung A1-Bescheinigung Auslandsdienstreise "
                "Entsendung Ausland Antrag Frist Vorlauf Sozialversicherung"
            ),
            (
                "A1 certificate foreign business trip posting abroad "
                "application timing deadline social security"
            ),
        ],
    ),
    Rule(
        id="transport_mode_selection",
        check=(
            "Determine how the choice of transport mode for a business trip "
            "is assessed, including relevant cost or economic considerations."
        ),
        queries=[
            (
                "Dienstreise Reisekosten Beförderungsmittel Verkehrsmittel "
                "Flug Bahn Zug Flugkosten Fahrtkosten Wirtschaftlichkeit "
                "wirtschaftlich notwendig"
            ),
            (
                "business trip travel transport mode flight train rail "
                "travel costs economic economical necessity reimbursement"
            ),
        ],
    ),
    Rule(
        id="invoice_billing_requirements",
        check=(
            "Determine what rules apply to invoice addressee and billing "
            "information for expenses connected with business trips."
        ),
        queries=[
            (
                "Dienstreise Reisekosten Rechnung Rechnungsempfänger "
                "Rechnungsadresse Universität Kassel Abrechnung Beleg"
            ),
            (
                "business trip travel expenses invoice addressee "
                "billing address university reimbursement receipt"
            ),
        ],
    ),
    Rule(
        id="event_side_program_costs",
        check=(
            "Determine how costs for side programmes, accompanying programmes, "
            "or evening activities connected with an event are treated."
        ),
        queries=[
            (
                "Rahmenprogramm Rahmenprogramme Begleitprogramm Abendprogramm "
                "Veranstaltung Aufwendungen Kosten Bewirtungskosten "
                "Teilnahmegebühren Finanzierung Erstattung"
            ),
            (
                "event side programme accompanying programme evening programme "
                "expenses costs participation fees financing reimbursement"
            ),
        ],
    ),
    Rule(
        id="third_party_reimbursement",
        check=(
            "Determine how business-trip expenses are treated when costs "
            "may also be financed, paid, or reimbursed by another source."
        ),
        queries=[
            (
                "Dienstreise Reisekosten Drittmittel Dritte dritte Seite "
                "Erstattung Finanzierung Zahlung Anrechnung Kostenübernahme"
            ),
            (
                "business trip travel expenses third party funding "
                "reimbursement payment financing cost coverage credit"
            ),
        ],
    ),
]
