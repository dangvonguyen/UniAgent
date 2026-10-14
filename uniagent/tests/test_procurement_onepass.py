"""Source-gate and mutation checks, using synthetic documents only."""

import unittest

from src.check import CheckAnswer, CheckQuote, DecisionEvidence, _answer_errors, _to_verdict
from src.models import CaseDocument, PolicyQuote
from src.procurement_audit import (
    Source, _declared_offer_count, _form_arithmetic, audit_coverage,
)
from src.procurement_consistency import audit_texts as consistency_audit
from src.procurement_evidence import decision_evidence_errors
from src.procurement_scope_gate import stage_errors
from src.quotes import match_case_parts
from src.rules.procurement import PROCUREMENT_RULES


class ProcurementOnePassTests(unittest.TestCase):
    def test_nine_rules_are_registered_once(self):
        ids = [r.id for r in PROCUREMENT_RULES]
        self.assertEqual(ids[:5], [
            "framework_contract_sourcing", "comparison_offers",
            "amount_calculation", "document_consistency", "award_selection",
        ])
        self.assertEqual(ids[5:], [
            "request_and_order_authority", "asset_classification",
            "special_research_equipment_procedure", "non_eu_import_procurement",
        ])
        self.assertEqual(len(set(ids)), 9)

    def test_arithmetic_mutations_and_partial_table(self):
        table = ("3. Positionen\nPos Bezeichnung Menge EP netto GP netto\n"
                 "1 Waage 2 10,00 € 20,00 €\n"
                 "2 Lampe 1 5,00 € 5,00 €\n"
                 "Summe netto 25,00 €\n4. Begründung\n")
        self.assertEqual(_form_arithmetic("request.pdf", table), [])
        bad = table.replace("Summe netto 25,00 €", "Summe netto 30,00 €")
        self.assertEqual([f.kind for f in _form_arithmetic("request.pdf", bad)],
                         ["form_total"])
        partial = table.replace("1 5,00 € 5,00 €", "1 unreadable 5,00 €")
        self.assertEqual(_form_arithmetic("request.pdf", partial), [])
        self.assertTrue(audit_coverage(
            "synthetic", {"beschaffungsantrag.pdf": partial}
        )["amount_calculation"])

    def test_amount_decision_needs_verified_duty_and_fact(self):
        policy = {"E1": PolicyQuote(corpus="test", doc_id="a",
                   quote="Die Preise im Beschaffungsantrag müssen rechnerisch richtig angegeben werden.")}
        documents = {"C1": CaseDocument(name="request.pdf",
                     text="Summe netto 30,00 €")}
        link = DecisionEvidence(policy_ref="E1", policy_obligation=policy["E1"].quote,
                                case_source="C1", case_fact="Summe netto 30,00 €",
                                stage="before ordering")
        self.assertEqual(decision_evidence_errors(
            "amount_calculation", [link], ["E1"], policy, documents), [])
        answer = CheckAnswer(verdict="pass", reason="the stated sum is correct",
                             case_quotes=[{"source": "C1", "quote": link.case_fact}],
                             policy_refs=["E1"], decision_evidence=[link])
        self.assertEqual(_answer_errors("amount_calculation", answer, policy, documents), [])
        self.assertEqual(_to_verdict("amount_calculation", answer, policy, documents).verdict,
                         "pass")
        answer.case_quotes = []
        self.assertIn("missing-verified-policy-or-case-source",
                      _answer_errors("amount_calculation", answer, policy, documents))
        answer.case_quotes = [CheckQuote(source="C1", quote="Summe netto 30,00 €")]
        answer.decision_evidence = []
        self.assertIn("missing-decision-evidence-link",
                      _answer_errors("amount_calculation", answer, policy, documents))

    def test_award_disclosure_is_not_award_decision(self):
        quote = "Die Zuschlagskriterien sind vor Angebotsabgabe bekannt zu geben."
        link = DecisionEvidence(policy_ref="E1", policy_obligation=quote,
                                case_source="C1", case_fact="Zuschlag an Firma A",
                                stage="before order")
        errors = decision_evidence_errors(
            "award_selection", [link], ["E1"],
            {"E1": PolicyQuote(corpus="test", doc_id="a", quote=quote)},
            {"C1": CaseDocument(name="award.pdf", text="Zuschlag an Firma A")},
        )
        self.assertIn("evidence-only-requires-disclosure:E1", errors)

    def test_subject_and_stage_are_checked_before_verdict(self):
        answer = CheckAnswer(verdict="not_applicable")
        self.assertIn("amount-subject-present-not-applicable-unfounded",
            _answer_errors("amount_calculation", answer, {},
                {"C1": CaseDocument(name="request.pdf", text="Summe netto 30,00 €")}))
        self.assertIn("ordering-duty-not-shown-due-at-request-stage",
            stage_errors("framework_contract_sourcing", "fail", ["E1"],
                {"E1": PolicyQuote(corpus="test", doc_id="a",
                    quote="Bestellungen müssen über das System erfolgen.")},
                {"C1": CaseDocument(name="request.pdf", text="Bitte bestellen.")}))

    def test_intended_order_duty_applies_to_proposal_stage(self):
        policy = {"E1": PolicyQuote(corpus="test", doc_id="a",
            quote="Sollte man ein Produkt bestellen wollen, zu dem ein Rahmenvertrag "
                  "besteht, muss man es beim Rahmenvertragspartner bestellen.")}
        request = {"C1": CaseDocument(name="request.pdf",
            text="Bitte kaufen Sie das Produkt bei einem anderen Anbieter.")}
        self.assertEqual(stage_errors(
            "framework_contract_sourcing", "fail", ["E1"], policy, request), [])
        # Timing alone does not prove a violation or resolve an exception; the
        # other evidence gates must still check the item and cited obligation.
        policy["E1"] = PolicyQuote(corpus="test", doc_id="b",
            quote="Nach erfolgter Bestellung muss die Buchung im System erfolgen.")
        self.assertIn("ordering-duty-not-shown-due-at-request-stage",
            stage_errors("framework_contract_sourcing", "fail", ["E1"], policy, request))

    def test_third_offer_and_exception_mutations(self):
        form = ("Rahmenvertragsprodukt [ ] ja [X] nein\n"
                "Vergabeart Preisvergleich\nEingeholte Angebote 2\n")
        duty = Source("test/DOC", "Grundsätzlich müssen drei Angebote eingeholt "
                      "werden. Ausnahme bei Rahmenvertrag.")
        docs = {"beschaffungsantrag.pdf": form,
                "angebot-a.pdf": "Angebot Nr. A-1\nSumme netto 10,00 €",
                "angebot-b.pdf": "Angebot Nr. B-2\nSumme netto 11,00 €"}
        self.assertEqual(len(_declared_offer_count(
            "beschaffungsantrag.pdf", form, docs, 3, duty)), 1)
        repaired = dict(docs)
        repaired["angebot-c.pdf"] = "Angebot Nr. C-3\nSumme netto 12,00 €"
        self.assertEqual(_declared_offer_count(
            "beschaffungsantrag.pdf", form, repaired, 3, duty), [])
        exception = form.replace("[ ] ja [X] nein", "[X] ja [ ] nein")
        self.assertEqual(_declared_offer_count(
            "beschaffungsantrag.pdf", exception, docs, 3, duty), [])

    def test_award_price_mutation_uses_original_offer(self):
        docs = {
            "angebot-a.pdf": "Angebot Nr. X-100\nSumme netto 2.350,00 €",
            "beschaffungsantrag.pdf": (
                "Vorgesehener Lieferant Firma A (Angebot X-100)\n"
                "Summe netto 2.350,00 €"),
            "vergabevermerk.pdf": "Firma A X-100 2.350,00 € 2.796,50 € 1\n",
        }
        self.assertEqual(consistency_audit("synthetic", docs)["discrepancies"], [])
        changed = dict(docs)
        changed["vergabevermerk.pdf"] = changed["vergabevermerk.pdf"].replace(
            "2.350,00 € 2.796,50 €", "3.243,00 € 3.859,17 €")
        findings = consistency_audit("synthetic", changed)["discrepancies"]
        self.assertIn("offer_vs_award_note", {f["kind"] for f in findings})
        self.assertEqual(findings[0]["expected"], "2350.00")

    def test_ellipsis_quote_keeps_separate_source_spans(self):
        source = ("The supplier offers equipment for the department.\n"
                  "The amount is 1.234,00 € net in the attached offer.\n")
        pieces = match_case_parts(
            "The supplier offers equipment ... amount is 1.234,00 € net", source)
        self.assertEqual(len(pieces), 2)
        self.assertTrue(all(part in source for part in pieces))
        distant = source.replace("\nThe amount", "\n" + "unrelated line\n" * 8 + "The amount")
        self.assertEqual(match_case_parts(
            "The supplier offers equipment ... amount is 1.234,00 € net", distant), [])


if __name__ == "__main__":
    unittest.main()
