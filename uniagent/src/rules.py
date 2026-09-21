from .models import Rule


RULES: list[Rule] = [
    Rule(
        id="advance_approval",
        check=(
            "Determine the relationship between the timing of a business-trip "
            "application or approval and the start of the trip."
        ),
        queries=[
            "Dienstreiseantrag Genehmigung Zeitpunkt Reisebeginn",
            "Dienstreise Antragstellung Genehmigung Frist",
            "Dienstreisegenehmigung Reiseantritt",
        ],
    ),

    Rule(
        id="six_month_deadline",
        check=(
            "Determine the applicable time limits for claiming, submitting, "
            "or settling business-trip expenses after a trip."
        ),
        queries=[
            "Reisekostenabrechnung Frist",
            "Reisekostenvergütung Antrag Frist",
            "Reisekostenerstattung Ausschlussfrist",
            "Dienstreise Abrechnung Frist",
        ],
    ),

    Rule(
        id="domestic_hotel_limit",
        check=(
            "Determine how accommodation costs for domestic business trips "
            "are reimbursed, including any applicable limits or justification conditions."
        ),
        queries=[
            "Übernachtungskosten Dienstreise Inland Erstattung",
            "Hotelkosten Dienstreise Höchstbetrag",
            "Übernachtungskosten Reisekosten Höchstgrenze",
            "notwendige Übernachtungskosten Dienstreise",
        ],
    ),

    Rule(
        id="foreign_hotel",
        check=(
            "Determine how accommodation costs are handled for business trips abroad."
        ),
        queries=[
            "Auslandsdienstreise Übernachtungskosten",
            "Ausland Reisekosten Übernachtung Erstattung",
            "Hotelkosten Auslandsdienstreise",
            "Auslandsreisekosten Übernachtung",
        ],
    ),

    Rule(
        id="private_extension",
        check=(
            "Determine how combining a business trip with private travel or "
            "a private stay affects reimbursable travel costs."
        ),
        queries=[
            "Dienstreise Privatreise Reisekosten",
            "Dienstreise private Verlängerung Erstattung",
            "Dienstreise Privataufenthalt Kosten",
            "Verbindung Dienstreise private Reise",
        ],
    ),

    Rule(
        id="a1_certificate",
        check=(
            "Determine the requirements and timing related to an A1 certificate "
            "for business travel or work abroad."
        ),
        queries=[
            "A1-Bescheinigung Auslandsdienstreise",
            "A1 Dienstreise Ausland Antrag",
            "Entsendebescheinigung Dienstreise Ausland",
            "A1-Bescheinigung Frist Vorlauf",
        ],
    ),

    Rule(
        id="flight_train_comparison",
        check=(
            "Determine how the choice between air, rail, or other transport "
            "modes is assessed for business travel, including economic considerations."
        ),
        queries=[
            "Dienstreise Flug Bahn Wirtschaftlichkeit",
            "Reisekosten Wahl Beförderungsmittel",
            "Flugkosten Bahnkosten Dienstreise",
            "wirtschaftliches Beförderungsmittel Dienstreise",
        ],
    ),

    Rule(
        id="invoice_addressee",
        check=(
            "Determine what requirements apply to the addressee or billing "
            "information on invoices for business-trip expenses."
        ),
        queries=[
            "Dienstreise Rechnungsempfänger Universität",
            "Reisekosten Rechnungsadresse",
            "Dienstreise Rechnung Universität Kassel",
            "Reisekostenabrechnung Rechnungsempfänger",
        ],
    ),

    Rule(
        id="evening_program",
        check=(
            "Determine how costs for supporting programmes, side programmes, "
            "or evening activities connected with an event are treated."
        ),
        queries=[
            "Rahmenprogramme Aufwendungen Finanzierung Teilnahmegebühren",
            "Rahmenprogramm Kosten Erstattung Veranstaltung",
            "Rahmenprogramm Bewirtungskosten Finanzierung",
            "Begleitprogramm Abendprogramm Aufwendungen Kosten",
        ],
    ),

    Rule(
        id="double_funding",
        check=(
            "Determine how business-trip expenses are treated when the same "
            "trip or expense may be financed or reimbursed from another source."
        ),
        queries=[
            "Reisekosten Doppelfinanzierung",
            "Reisekosten Drittmittel Erstattung",
            "Dienstreise andere Erstattung Anrechnung",
            "Reisekosten Finanzierung durch Dritte",
        ],
    ),
]