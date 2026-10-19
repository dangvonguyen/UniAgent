"""Source-bound business-trip facts. No rule verdict is delegated to the model."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from itertools import product
import re


GERMAN_MONTHS = {
    "januar": 1, "februar": 2, "märz": 3, "maerz": 3, "april": 4,
    "mai": 5, "juni": 6, "juli": 7, "august": 8, "september": 9,
    "oktober": 10, "november": 11, "dezember": 12,
}
DATE = re.compile(r"\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b")
NAMED_DATE = re.compile(
    r"\b(\d{1,2})\.\s*(Januar|Februar|März|Maerz|April|Mai|Juni|Juli|"
    r"August|September|Oktober|November|Dezember)\s+(\d{4})\b", re.I
)
FIELDS = {
    "request": re.compile(r"^\s*(?:Datum der Antragstellung|Antragstellung|Antragsdatum)\s*:\s*\|?", re.I),
    "trip_start": re.compile(r"^\s*Start\s*:\s*\|", re.I),
    "trip_end": re.compile(r"^\s*Ende\s*:\s*\|", re.I),
    "business_start": re.compile(r"^\s*Beginn Dienstgeschäft\s*:\s*\|", re.I),
    "business_end": re.compile(r"^\s*Ende Dienstgeschäft\s*:\s*\|", re.I),
}
FUNDING = re.compile(
    r"\b(?:Stipend(?:ium|ien)|Förderung|Foerderung|Drittmittel|"
    r"Doppelfinanzierung|Kostenübernahme|Kostenuebernahme|"
    r"Reisekostenzuschuss|Zuwendung|finanzier\w*|erstatt\w*|"
    r"übernimm\w*|uebernimm\w*|übernimmt|uebernimmt|Auszahlung|"
    r"ausgezahlt|gezahlt|bezahlt|erhalten(?:e|en|er|es)?|Zahlung|"
    r"kürzen|kuerzen)\b", re.I
)


@dataclass(frozen=True)
class SourceLine:
    document: str
    line_id: str
    text: str


def lines(documents: dict[str, str]):
    for document, content in documents.items():
        for index, line in enumerate(content.splitlines(), 1):
            if line.strip():
                yield SourceLine(document, f"{document}:L{index}", line.strip())


def parse_date_values(line: SourceLine):
    named = NAMED_DATE.search(line.text)
    if named:
        day, month, year = named.groups()
        return [date(int(year), GERMAN_MONTHS[month.casefold()], int(day))], named.group(), "named_month"
    numeric = DATE.search(line.text)
    if not numeric:
        return [], None, "missing"
    first, second, year = map(int, numeric.groups())
    options = []
    for day, month in ((first, second), (second, first)):
        try:
            parsed = date(year, month, day)
        except ValueError:
            continue
        if parsed not in options:
            options.append(parsed)
    return options, numeric.group(), "ambiguous" if len(options) > 1 else "unambiguous"


def date_finding(documents: dict[str, str]):
    """Only invariant contradictions can make a code-owned rejection.

    In particular, numeric 11.02 versus 10.03 is tried in both DMY and MDY
    interpretations; neither an implicit locale nor a model's timeline decides it.
    """
    applications = [
        doc for doc, text in documents.items()
        if "ANTRAG AUF DIENSTREISE" in text.upper() or "DIENSTREISEANTRAG" in text.upper()
    ]
    if len(applications) != 1:
        return {"basis": "code_date_check", "policy_ref": None,
                "status": "unresolved", "reason": "application_document_unresolved",
                "source_lines": [], "date_format_ambiguous": False}
    candidates = [line for line in lines({applications[0]: documents[applications[0]]})]
    fields = {}
    for key, pattern in FIELDS.items():
        matches = [line for line in candidates if pattern.search(line.text)]
        if len(matches) != 1:
            continue
        values, raw, fmt = parse_date_values(matches[0])
        if values:
            fields[key] = {"source": asdict(matches[0]), "raw_date": raw,
                           "format": fmt, "values": values}
    necessary = ("trip_start", "business_start", "business_end", "trip_end")
    if not all(key in fields for key in necessary):
        return {"basis": "code_date_check", "policy_ref": None,
                "status": "unresolved", "reason": "date_field_missing_or_duplicated",
                "source_lines": [fields[k]["source"] for k in fields],
                "date_format_ambiguous": any(x["format"] == "ambiguous" for x in fields.values())}
    selected = [key for key in ("request", *necessary) if key in fields]
    evaluations = []
    for combo in product(*(fields[key]["values"] for key in selected)):
        values = dict(zip(selected, combo))
        problems = []
        if "request" in values and values["request"] > values["trip_start"]:
            problems.append("request_after_departure")
        if values["business_end"] < values["business_start"]:
            problems.append("business_end_before_start")
        if not (values["trip_start"] <= values["business_start"] <=
                values["business_end"] <= values["trip_end"]):
            problems.append("business_activity_outside_trip")
        evaluations.append(tuple(dict.fromkeys(problems)))
    invariant = sorted(set.intersection(*(set(x) for x in evaluations))) if evaluations else []
    schedule_inconsistent = bool(evaluations) and all(
        "business_end_before_start" in problems or "business_activity_outside_trip" in problems
        for problems in evaluations
    )
    ambiguous = any(fields[k]["format"] == "ambiguous" for k in selected)
    if all(evaluations):
        status = "fail"
        reason = "contradiction_under_every_valid_date_interpretation"
    elif any(evaluations):
        status = "unresolved"
        reason = "date_format_ambiguous"
    else:
        status = "no_conflict"
        reason = "dates_consistent"
    return {
        "basis": "code_date_check", "policy_ref": None,
        "status": status, "reason": reason, "invariant_conflicts": invariant,
        "schedule_inconsistent_under_all_interpretations": schedule_inconsistent,
        "date_format_ambiguous": ambiguous,
        "source_lines": [fields[k]["source"] for k in selected],
        "parsed_values": {k: {"raw": fields[k]["raw_date"],
                              "format": fields[k]["format"],
                              "possible_iso_dates": [d.isoformat() for d in fields[k]["values"]]}
                          for k in selected},
        "interpretations_examined": len(evaluations),
    }


def funding_candidates(documents: dict[str, str]):
    result = []
    for doc, content in documents.items():
        document_lines = [SourceLine(doc, f"{doc}:L{i}", s.strip())
                          for i, s in enumerate(content.splitlines(), 1)]
        hits = {i for i, line in enumerate(document_lines) if FUNDING.search(line.text)}
        selected = {j for i in hits for j in range(max(0, i - 2),
                                                   min(len(document_lines), i + 3))}
        if hits:
            selected.update(i for i, line in enumerate(document_lines[:12])
                            if re.search(r"<[^<>\s]+@[^<>\s]+>", line.text) and
                            not line.text.casefold().startswith(("an:", "to:")))
        for i in sorted(selected):
            line = document_lines[i]
            if line.text:
                result.append({**asdict(line),
                               "terms": sorted(set(m.group() for m in FUNDING.finditer(line.text))),
                               "trigger": i in hits})
    return result


def funding_case_stage(documents: dict[str, str]):
    """Only an explicit claim form establishes the settlement stage."""
    headings = [text[:1800] for text in documents.values()]
    if any(re.search(r"\b(?:Reisekostenabrechnung|Antrag auf Reisekostenerstattung)\b",
                     text, re.I) for text in headings):
        return "expense_claim"
    return "application"


def verify_funding_fail(*, candidates: list[dict], classifications: list[dict],
                        policy: dict[str, str], reviewed_clauses: dict[str, dict],
                        clause_ref: str | None, case_stage: str = "application"):
    """A fail needs a complete line inventory and an express application-stage duty.

    Classifications are proposed by a model; every line and policy span is checked
    against immutable input. This does not guess the legal effect of an award.
    """
    issues = []
    by_id = {c["line_id"]: c for c in candidates}
    def close_lines(ids):
        numbers = [int(x.rsplit("L", 1)[1]) for x in ids if re.search(r":L\d+$", x)]
        return len(numbers) == len(ids) and numbers == sorted(set(numbers)) and (
            not numbers or numbers[-1] - numbers[0] <= 2)
    classified = {c.get("line_id") for c in classifications}
    if len(classifications) != len(classified) or classified != set(by_id):
        issues.append("funding_candidate_inventory_incomplete")
    for item in classifications:
        source = by_id.get(item.get("line_id"))
        if source is None:
            issues.append("classification_unknown_line")
            continue
        if item.get("relevant") and not item.get("covers_items"):
            issues.append("coverage_unresolved")
        if item.get("relevant"):
            covered_lines = [by_id.get(line_id) for line_id in item.get("covers_line_ids", [])]
            if (not covered_lines or any(line is None or line["document"] != source["document"]
                                         for line in covered_lines) or
                    not re.search(r"Kosten|Deckung|Flug|flight|hotel|Unterkunft|Reise|travel|"
                                  r"Übernachtung|Gebühr|fee|registration|paid|übernimmt|cover",
                                  " ".join(line["text"] for line in covered_lines), re.I)):
                issues.append("coverage_source_unverified")
        if item.get("relevant") and item.get("payer"):
            payer_line = by_id.get(item.get("payer_line_id"))
            if (payer_line is None or payer_line["document"] != source["document"] or
                    item["payer"].casefold() not in payer_line["text"].casefold()):
                issues.append("payer_not_in_source_span")
        elif item.get("relevant"):
            issues.append("payer_unresolved")
        if item.get("status") not in ("proposed", "awarded_future", "received", "paid_for_items", "internal", "unrelated"):
            issues.append("funding_status_unresolved")
        if item.get("relevant") and item.get("status") in ("received", "paid_for_items"):
            status_lines = [by_id.get(line_id) for line_id in item.get("status_line_ids", [])]
            if (not status_lines or any(line is None or line["document"] != source["document"]
                                        for line in status_lines)
                    or not re.search(r"erhalten|gezahlt|überwiesen|ueberwiesen|paid|received",
                                     " ".join(line["text"] for line in status_lines), re.I)):
                issues.append("received_benefit_source_unverified")
        if item.get("relevant") and item.get("status") == "awarded_future":
            payout = [by_id.get(line_id) for line_id in item.get("payout_line_ids", [])]
            payout_text = " ".join(line["text"] for line in payout if line)
            if (not payout or not close_lines(item.get("payout_line_ids", [])) or
                    any(line is None or line["document"] != source["document"] for line in payout)
                    or not re.search(r"Auszahlung|ausgezahlt|payment|payout", payout_text, re.I)
                    or not re.search(r"nach der Reise|after (?:the )?trip|after travel|später|later", payout_text, re.I)):
                issues.append("future_payout_source_unverified")
            reduction = [by_id.get(line_id) for line_id in item.get("reduction_line_ids", [])]
            reduction_text = " ".join(line["text"] for line in reduction if line)
            if (not reduction or not close_lines(item.get("reduction_line_ids", [])) or
                    any(line is None or line["document"] != source["document"] for line in reduction)
                    or not re.search(r"kürzen|kuerzen|reduc\w*|deduct\w*", reduction_text, re.I)
                    or not (re.search(r"\buns\b|\bwir\b|\bwe\b|\bour\b", reduction_text, re.I)
                            or item.get("payer", "").casefold() in reduction_text.casefold())):
                issues.append("grantor_reduction_source_unverified")
            if item.get("reduction_actor") != item.get("payer"):
                issues.append("reduction_actor_not_grantor")
    external = [item for item in classifications if item.get("relevant") and
                item.get("status") in ("awarded_future", "received", "paid_for_items")]
    if not external:
        issues.append("external_funding_line_unverified")
    if external and not any(item.get("overlap_with_request") for item in external):
        issues.append("overlap_not_verified")
    clause = reviewed_clauses.get(clause_ref or "")
    stage = "expense_claim" if (case_stage == "expense_claim" and external and
                                all(item.get("status") in ("received", "paid_for_items")
                                    for item in external)) else "application"
    needed_action = "offset_received_benefit" if stage == "expense_claim" else "allocate_external_benefit"
    if not clause or clause.get("stage") != stage or clause.get("action") != needed_action:
        issues.append("application_stage_policy_gap" if stage == "application"
                      else "expense_claim_policy_gap")
    elif not clause.get("quote") or clause["quote"] not in policy.get(clause_ref or "", ""):
        issues.append("policy_clause_span_unverified")
    return {"verdict": "unknown" if issues else "fail",
            "issues": sorted(set(issues)), "candidate_lines": len(by_id),
            "classified_lines": len(classified & set(by_id))}


def reviewed_funding_clauses(policy: dict[str, str]):
    """Review only an express duty to offset a benefit already received.

    The pre-trip disclosure wording cannot establish an application-stage
    allocation duty, even when the retrieved page contains both sentences.
    """
    clauses = {}
    marker = re.compile(
        r"Die erhaltenen Leistungen von dritter Seite werden.{0,500}?"
        r"(?:angerechnet|gekürzt|gekuerzt)", re.I | re.S
    )
    for ref, passage in policy.items():
        match = marker.search(passage)
        if match:
            clauses[ref] = {"stage": "expense_claim", "action": "offset_received_benefit",
                            "quote": match.group()}
    return clauses


def guard_funding_fail(*, verdict: str, candidates: list[dict],
                       classifications: list[dict], conditions: list[dict],
                       policy: dict[str, str], clause_ref: str | None,
                       case_stage: str = "application"):
    if verdict != "fail":
        return {"verdict": verdict, "issues": [], "candidate_lines": len(candidates),
                "classified_lines": len(classifications)}
    result = verify_funding_fail(
        candidates=candidates, classifications=classifications, policy=policy,
        reviewed_clauses=reviewed_funding_clauses(policy), clause_ref=clause_ref,
        case_stage=case_stage,
    )
    result["issues"] = sorted(set(result["issues"] + verify_conditions_used(conditions, policy)))
    if result["issues"]:
        result["verdict"] = "unknown"
    return result


def possible_external_awards(candidates: list[dict]) -> list[str]:
    """Flag an unresolved external award; never infer a policy violation from it.

    The three independent signals must occur in the same source document. An
    internal project cost centre alone and a conference discount alone do not
    satisfy this screen. The output remains only a review trigger.
    """
    by_document = {}
    for line in candidates:
        by_document.setdefault(line["document"], []).append(line)
    hits = []
    for lines in by_document.values():
        joined = "\n".join(line["text"] for line in lines)
        if (re.search(r"Stipendium|Zusage|Kostenübernahme|travel grant|grant award|"
                      r"external funding|Dritt(?:mittel|finanzierung)", joined, re.I)
            and re.search(r"Auszahlung|ausgezahlt|payout|payment|gezahlt", joined, re.I)
            and re.search(r"Flug|flight|Unterkunft|hotel|Reise|travel|"
                          r"Registrierung|registration|Gebühr|fee", joined, re.I)):
            hits.extend(line["line_id"] for line in lines)
    return hits


def verify_conditions_used(conditions: list[dict], policy: dict[str, str]):
    """Check exact policy spans, then enforce a reviewed role and decision stage."""
    issues = []
    for item in conditions:
        quote = item.get("quote", "")
        ref = item.get("ref", "")
        if not quote or quote not in policy.get(ref, ""):
            issues.append("policy_condition_span_unverified")
        if item.get("stage") not in ("application", "after_trip", "expense_claim"):
            issues.append("condition_stage_unresolved")
        if item.get("role") not in ("requires", "permits", "excludes", "defines"):
            issues.append("condition_role_unresolved")
    return sorted(set(issues))
