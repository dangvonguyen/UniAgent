#!/usr/bin/env python3
"""Conservative, source-backed checks for internal procurement documents.

This tool extracts source-backed findings. It never reads decision-trail or
ground-truth files, and it does not turn an incomplete policy packet into a
rejection. Every reported amount is taken from the submitted PDFs.
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import subprocess
from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path

if __package__:  # package import (pipeline)
    from . import procurement_award as _award
    from . import procurement_consistency as _consistency
else:  # plain script import (offline runners)
    import procurement_award as _award
    import procurement_consistency as _consistency


MONEY = r"(?:\d{1,3}(?:\.\d{3})+|\d+),\d{2}\s*€"
MONEY_RE = re.compile(MONEY)
SUM_RE = re.compile(rf"(?im)^\s*Summe\s+netto\s+({MONEY})")
GERMAN_COUNTS = {
    "ein": 1, "eins": 1, "eine": 1, "zwei": 2, "drei": 3,
    "vier": 4, "fünf": 5, "sechs": 6,
}


@dataclass(frozen=True)
class Source:
    document: str
    quote: str


@dataclass(frozen=True)
class Finding:
    rule_id: str
    kind: str
    detail: str
    sources: tuple[Source, ...]
    # "document": the PDFs contradict themselves. "policy": needs an external duty.
    basis: str = "document"


def money(s: str) -> Decimal:
    return Decimal(re.search(MONEY, s).group(0).replace("€", "").strip()
                   .replace(".", "").replace(",", "."))


def material_difference(left: Decimal, right: Decimal) -> bool:
    # Screening threshold, not a claim that policy permits smaller errors.
    # Small differences remain visible in the evidence if inspected manually.
    return abs(left - right) > max(Decimal("1.00"), min(left, right) * Decimal("0.01"))


def pdf_text(path: Path) -> str:
    return subprocess.run(
        ["pdftotext", "-layout", str(path), "-"],
        capture_output=True, text=True, check=True,
    ).stdout


def _net_line(text: str) -> tuple[Decimal, str] | None:
    match = SUM_RE.search(text)
    return (money(match.group(1)), match.group(0).strip()) if match else None


def _form_arithmetic(name: str, text: str) -> list[Finding]:
    section = re.search(r"(?ms)^\s*3\.\s*Positionen\s*\n(.*?)^\s*4\.\s*Begründung", text)
    if not section or "GP netto" not in section.group(1):
        return []
    total = _net_line(section.group(1))
    if not total:
        return []
    items: list[tuple[Decimal, str]] = []
    issues: list[Finding] = []
    for line in section.group(1).splitlines():
        if not re.match(r"^\s*\d+\s+\S", line):
            continue
        amounts = list(MONEY_RE.finditer(line))
        if len(amounts) != 2:
            continue
        count_match = re.search(r"(\d+)\s*$", line[:amounts[0].start()])
        if not count_match:
            continue
        count = Decimal(count_match.group(1))
        unit = money(amounts[0].group(0))
        line_total = money(amounts[1].group(0))
        items.append((line_total, line.strip()))
        if material_difference(count * unit, line_total):
            issues.append(Finding(
                "amount_calculation", "line_multiplication",
                f"{count} × {unit} = {count * unit}, but the line states {line_total}",
                (Source(name, line.strip()),),
            ))
    # A partially parsed item table cannot justify an aggregate finding.
    numbered_lines = [l for l in section.group(1).splitlines()
                      if re.match(r"^\s*\d+\s+\S", l)]
    if items and len(items) == len(numbered_lines):
        calculated = sum((v for v, _ in items), Decimal(0))
        declared, total_quote = total
        if material_difference(calculated, declared):
            issues.append(Finding(
                "amount_calculation", "form_total",
                f"Sum of {len(items)} line totals is {calculated}, but form states {declared}",
                tuple(Source(name, quote) for _, quote in items)
                + (Source(name, total_quote),),
            ))
    return issues


def _declared_offer_count(name: str, text: str, other_documents: dict[str, str],
                          policy_offer_count: int | None = None,
                          policy_offer_source: Source | None = None) -> list[Finding]:
    method = re.search(r"(?im)^\s*Vergabeart\s+.*?\b(\d+|eins?|eine|zwei|drei|vier|fünf|sechs)\s+schriftliche\s+Angebote", text)
    selected_method = re.search(r"(?im)^\s*Vergabeart\s+Preisvergleich\b.*$", text)
    count = re.search(r"(?im)^\s*Eingeholte\s+Angebote\s+(\d+)\s*$", text)
    if not selected_method or not count:
        return []
    if method:
        raw = method.group(1).lower()
        required = int(raw) if raw.isdecimal() else GERMAN_COUNTS.get(raw, 0)
        basis = "The request itself declares"
    elif policy_offer_count is not None:
        required = policy_offer_count
        basis = "The supplied policy trace says"
    else:
        return []
    # A general quotation can expressly exempt framework purchases. A checked
    # "no" in this request is evidence against that exception; silence is not.
    framework_no = re.search(
        r"(?im)^\s*Rahmenvertragsprodukt\s+\[\s*\]\s*ja\s+\[\s*[Xx]\s*\]\s*nein\b.*$",
        text,
    )
    if (policy_offer_source is not None
            and re.search(r"(?i)Ausnahme\s+bei\s+Rahmenvertrag", policy_offer_source.quote)
            and not framework_no):
        return []
    reported = int(count.group(1))
    attached_offers = sum(name.lower().startswith("angebot-") and name.lower().endswith(".pdf")
                          for name in other_documents)
    if required <= reported or attached_offers >= required:
        return []
    # PDF extraction failures or a standalone offer embedded under a different
    # filename make the absence claim unsafe. Do not automatically reject.
    if any(not body.strip() for body in other_documents.values()):
        return []
    for document, body in other_documents.items():
        if document == name:
            # The request cites the chosen offer and its total; it is not an
            # additional independent quotation just for mentioning that ID.
            continue
        if document.lower().startswith("angebot-") and document.lower().endswith(".pdf"):
            continue
        if (re.search(r"(?i)\bAngebot\s+(?:Nr\.?\s*|snummer\s*)?[A-Z]*[-/]?\d[\w/-]*", body)
                and re.search(r"(?i)\b(?:Summe\s+netto|Angebotssumme)\b", body)):
            return []
    offer_sources = []
    for document, body in other_documents.items():
        if document.lower().startswith("angebot-") and document.lower().endswith(".pdf"):
            nonempty = [line.strip() for line in body.splitlines() if line.strip()]
            if nonempty:
                offer_line = next((line for line in nonempty if re.search(r"(?i)\bAngebot\b", line)), nonempty[0])
                offer_sources.append(Source(document, offer_line))
    return [Finding(
        "comparison_offers", "declared_method_missing_offers",
        f"{basis} a {required}-offer comparison method, the request reports {reported}, "
        f"and includes {attached_offers} separately attached offer PDFs; "
        "no standalone offer was detected under another filename",
        (Source(name, selected_method.group(0).strip()), Source(name, count.group(0).strip()))
        + ((Source(name, framework_no.group(0).strip()),) if framework_no else ())
        + tuple(offer_sources)
        + ((policy_offer_source,) if policy_offer_source else ()),
        basis="document" if method else "policy",
    )]


def policy_offer_count_from_quotes(items: list[dict[str, str]]) -> tuple[int, Source] | None:
    """Extract a general quoted offer-count principle with its source."""
    candidates: dict[int, Source] = {}
    for item in items:
        quote = item.get("quote", "")
        # Only a stated general principle, never a product-specific example.
        found = re.search(
            r"(?i)Grundsätzlich\s+müssen\s+(\d+|eins?|eine|zwei|drei|vier|fünf|sechs)\s+Angebote",
            quote,
        )
        if found:
            raw = found.group(1).lower()
            count = int(raw) if raw.isdecimal() else GERMAN_COUNTS[raw]
            candidates[count] = Source(
                f"{item.get('corpus', 'unknown')}/{item.get('doc_id', 'unknown')}", quote
            )
    return next(iter(candidates.items())) if len(candidates) == 1 else None


def policy_offer_count_from_trace(path: Path) -> tuple[int, Source] | None:
    """Read an existing GPT digest; never infer a count from a case PDF."""
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        for line in stream:
            event = json.loads(line)
            output = event.get("output") or {}
            if (event.get("event_type") != "observation"
                    or output.get("rule_id") not in {
                        "comparison_offers", "framework_contract_sourcing"
                    }
                    or "policy_quotes" not in output):
                continue
            return policy_offer_count_from_quotes(output["policy_quotes"])
    return None


def _strict_findings(case_id: str, documents: dict[str, str]) -> list[Finding]:
    """Offer/cart/award cross-checks that take prices from the original offers only."""
    out: list[Finding] = []
    consistency = _consistency.audit_texts(case_id, documents)
    for d in consistency["discrepancies"]:
        out.append(Finding(
            "document_consistency", d["kind"],
            f"{d['kind']}: {d['offer_id']} should be {d['expected']} net "
            f"per the referenced original, but the other document states {d['stated']}",
            tuple(Source(s["document"], s["quote"]) for s in d["sources"]),
        ))
    award = _award.audit_texts(case_id, documents)
    if award["assessment"] == "selection_contradicts_stated_criterion":
        out.append(Finding(
            "award_selection", "selected_above_cheapest_equivalent_offer",
            f"Award note states net price decides among equally suitable offers; selected "
            f"offer {award['selected_offer_id']} is {award['selected_net']} net, lowest linked "
            f"original offer is {award['lowest_equivalent_net']} net (+{award['difference_net']})",
            tuple(Source(s["document"], s["quote"]) for s in award["evidence"]),
            basis="policy",
        ))
    return out


def audit_case(case_dir: Path, policy_offer_count: int | None = None,
               policy_offer_source: Source | None = None,
               documents: dict[str, str] | None = None) -> list[Finding]:
    if documents is None:
        documents = {p.name: pdf_text(p) for p in sorted(case_dir.glob("*.pdf"))}
    issues: list[Finding] = []
    form = documents.get("beschaffungsantrag.pdf")
    if form:
        issues.extend(_form_arithmetic("beschaffungsantrag.pdf", form))
        issues.extend(_declared_offer_count(
            "beschaffungsantrag.pdf", form, documents,
            policy_offer_count, policy_offer_source))
    issues.extend(_strict_findings(case_dir.name, documents))
    return issues


def audit_coverage(case_id: str, documents: dict[str, str]) -> dict[str, list[str]]:
    """Report comparisons that were not safe to make; never infer compliance."""
    gaps = {"amount_calculation": [], "document_consistency": [],
            "award_selection": []}
    form = documents.get("beschaffungsantrag.pdf", "")
    section = re.search(r"(?ms)^\s*3\.\s*Positionen\s*\n(.*?)^\s*4\.\s*Begründung", form)
    if section and "GP netto" in section.group(1):
        numbered = [line for line in section.group(1).splitlines()
                    if re.match(r"^\s*\d+\s+\S", line)]
        parsed = [line for line in numbered if len(MONEY_RE.findall(line)) == 2]
        if len(parsed) != len(numbered):
            gaps["amount_calculation"].append(
                f"Only {len(parsed)}/{len(numbered)} item rows have two readable amounts")
        if not _net_line(section.group(1)):
            gaps["amount_calculation"].append("Request net total unreadable")
    else:
        gaps["amount_calculation"].append("No complete item table to audit")
    gaps["document_consistency"] = _consistency.audit_texts(
        case_id, documents)["coverage_gaps"]
    gaps["award_selection"] = _award.audit_texts(
        case_id, documents)["coverage_gaps"]
    return gaps


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True,
                        help="Directory containing procurement case directories")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--policy-trace", type=Path,
                        help="Saved framework or comparison trace for an optional policy offer count")
    args = parser.parse_args()
    cases = sorted(args.input.glob("beschaffungsantrag-*"))
    if not cases:
        parser.error("No beschaffungsantrag-* directories found")
    policy = (policy_offer_count_from_trace(args.policy_trace)
              if args.policy_trace else None)
    policy_count, policy_source = policy if policy else (None, None)
    result = {case.name: [asdict(issue) for issue in audit_case(
        case, policy_count, policy_source)]
              for case in cases}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    for case, findings in result.items():
        kinds = ", ".join(f["rule_id"] + ":" + f["kind"] for f in findings)
        print(f"{case}: {kinds or 'no verified discrepancy'}")
    print(f"Report: {args.output}")


if __name__ == "__main__":
    main()
