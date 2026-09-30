from .models import Rule

RULES: list[Rule] = [
    Rule(
        id="trip_approval",
        check=(
            "Determine the relationship between the timing of a business-trip "
            "application or approval and the timing of the trip."
        ),
        queries={
            "de": [
                "Dienstreise Dienstreiseantrag Antragstellung Genehmigung Zeitpunkt Frist Reisebeginn Reiseantritt"
            ],
            "en": [
                "business trip application approval timing deadline trip start travel commencement"
            ],
        },
    ),
    Rule(
        id="expense_claim_submission",
        check=(
            "Determine the timing rules that apply to claiming, submitting, "
            "or settling business-trip expenses."
        ),
        queries={
            "de": [
                "Dienstreise Reisekosten Reisekostenabrechnung Reisekostenvergütung Erstattung Antrag Abrechnung Frist Ausschlussfrist"
            ],
            "en": [
                "business trip travel expenses reimbursement claim submission settlement application deadline time limit"
            ],
        },
    ),
    Rule(
        id="accommodation_costs_domestic",
        check=(
            "Determine how accommodation costs for domestic business trips "
            "are reimbursed, including whether any limits or justification "
            "conditions apply."
        ),
        queries={
            "de": [
                "Dienstreise Inland Reisekosten Übernachtung Übernachtungskosten Hotelkosten Erstattung Höchstbetrag Höchstgrenze Nachweis Begründung"
            ],
            "en": [
                "domestic business trip accommodation hotel overnight cost reimbursement limit maximum justification evidence"
            ],
        },
    ),
    Rule(
        id="accommodation_costs_abroad",
        check=(
            "Determine how accommodation costs for business trips abroad "
            "are reimbursed and what conditions apply."
        ),
        queries={
            "de": [
                "Auslandsdienstreise Ausland Reisekosten Übernachtung Übernachtungskosten Hotelkosten Erstattung Auslandsreisekosten"
            ],
            "en": [
                "foreign business trip abroad accommodation hotel overnight expenses travel cost reimbursement"
            ],
        },
    ),
    Rule(
        id="business_private_trip_combination",
        check=(
            "Determine how combining a business trip with private travel "
            "or a private stay affects travel-expense reimbursement."
        ),
        queries={
            "de": [
                "Dienstreise Privatreise Privataufenthalt private Verlängerung Verbindung Reisekosten Fahrtkosten Erstattung"
            ],
            "en": [
                "business trip private travel private stay extension combined journey travel expenses reimbursement"
            ],
        },
    ),
    Rule(
        id="cross_border_social_security_coverage",
        check=(
            "Determine what rules, if any, apply to an A1 certificate for "
            "business travel or work abroad, including relevant timing."
        ),
        queries={
            "de": [
                "A1 Bescheinigung A1-Bescheinigung Auslandsdienstreise Entsendung Ausland Antrag Frist Vorlauf Sozialversicherung"
            ],
            "en": [
                "A1 certificate foreign business trip posting abroad application timing deadline social security"
            ],
        },
    ),
    Rule(
        id="transport_costs",
        check=(
            "Determine how the choice of transport mode for a business trip "
            "is assessed, including relevant cost or economic considerations."
        ),
        queries={
            "de": [
                "Dienstreise Reisekosten Beförderungsmittel Verkehrsmittel Flug Bahn Zug Flugkosten Fahrtkosten Wirtschaftlichkeit wirtschaftlich notwendig"
            ],
            "en": [
                "business trip travel transport mode flight train rail travel costs economic economical necessity reimbursement"
            ],
        },
    ),
    Rule(
        id="invoice_formalities",
        check=(
            "Determine what rules apply to invoice addressee and billing "
            "information for expenses connected with business trips."
        ),
        queries={
            "de": [
                "Dienstreise Reisekosten Rechnung Rechnungsempfänger Rechnungsadresse Universität Kassel Abrechnung Beleg"
            ],
            "en": [
                "business trip travel expenses invoice addressee billing address university reimbursement receipt"
            ],
        },
    ),
    Rule(
        id="event_side_program_costs",
        check=(
            "Determine how costs for side programmes, accompanying programmes, "
            "or evening activities connected with an event are treated."
        ),
        queries={
            "de": [
                "Rahmenprogramm Rahmenprogramme Begleitprogramm Abendprogramm Veranstaltung Aufwendungen Kosten Bewirtungskosten Teilnahmegebühren Finanzierung Erstattung"
            ],
            "en": [
                "event side programme accompanying programme evening programme expenses costs participation fees financing reimbursement"
            ],
        },
    ),
    Rule(
        id="third_party_funding",
        check=(
            "Determine how business-trip expenses are treated when costs "
            "may also be financed, paid, or reimbursed by another source."
        ),
        queries={
            "de": [
                "Dienstreise Reisekosten Drittmittel Dritte dritte Seite Erstattung Finanzierung Zahlung Anrechnung Kostenübernahme"
            ],
            "en": [
                "business trip travel expenses third party funding reimbursement payment financing cost coverage credit"
            ],
        },
    ),
]
