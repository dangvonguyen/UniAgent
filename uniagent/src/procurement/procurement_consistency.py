#!/usr/bin/env python3
"""Source-backed cross-document amount checks for one procurement rule.

Only compare documents with an unambiguous offer number. A mismatch is a
diagnostic finding; absent or unreadable evidence never becomes a pass.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from decimal import Decimal
from pathlib import Path


MONEY = re.compile(r"(?<!\d)(?:\d{1,3}(?:\.\d{3})+|\d+),\d{2}\s*€")
NET_SUM = re.compile(r"(?im)^\s*Summe\s+netto\s+([^\n]+)")
OFFER_ID = re.compile(r"(?i)\b(?:Angebot\s*(?:[- ]\s*Nr\.?)?\s+|Nr\.\s+)([A-Z0-9][A-Z0-9/-]*(?:\s+\d{2,5}(?:/\d{2,5})?){0,3})")


def money(text: str) -> Decimal:
    match = MONEY.search(text)
    if match is None:
        raise ValueError("Expected euro amount")
    return Decimal(match.group().replace("€", "").strip().replace(".", "").replace(",", "."))


def offer_number(text: str) -> str | None:
    for line in text.splitlines()[:35]:
        if not (m := OFFER_ID.search(line)):
            continue
        candidate = m.group(1).strip()
        if any(char.isdigit() for char in candidate) and len(candidate) <= 30:
            return candidate
    return None


def offer_net(text: str) -> tuple[Decimal, str] | None:
    if not (m := NET_SUM.search(text)) or not MONEY.search(m.group(1)):
        return None
    return money(m.group(1)), m.group().strip()


def _id_in_line(offer_id: str, line: str) -> bool:
    phrase = r"\s+".join(re.escape(part) for part in offer_id.split())
    return bool(re.search(r"(?<![\w/-])" + phrase + r"(?![\w/-])", line, re.I))


def _award_money_rows(note: str, offer_id: str) -> list[str]:
    """Find a price row by its full ID, including an ID wrapped by PDF text.

    Some table cells wrap the final digits onto the next physical line. Only
    rejoin where the exact ID from the independent offer is reconstructed;
    retain both original lines in the evidence excerpt.
    """
    lines = note.splitlines()
    matched: list[str] = []
    for index, line in enumerate(lines):
        if not MONEY.search(line):
            continue
        if _id_in_line(offer_id, line):
            matched.append(line)
            continue
        if index + 1 >= len(lines):
            continue
        next_line = lines[index + 1]
        for width in range(2, min(7, len(offer_id) - 5) + 1):
            prefix, suffix = offer_id[:-width], offer_id[-width:]
            prefix_pattern = (r"(?<![\w/-])"
                              + r"\s+".join(re.escape(part) for part in prefix.split())
                              + r"(?![\w/-])")
            head = re.search(prefix_pattern, line, re.I)
            tail = next((m for m in re.finditer(
                r"(?<![\w/-])" + re.escape(suffix) + r"(?![\w/-])", next_line)
                if head and abs(m.start() - head.start()) <= 3), None)
            if suffix.isdecimal() and head and tail and not MONEY.search(next_line):
                matched.append(line + "\n" + next_line)
                break
    return matched


def compare_offer(offer_name: str, offer_text: str,
                  other_documents: dict[str, str]) -> tuple[list[dict], list[str], int]:
    offer_id = offer_number(offer_text)
    net = offer_net(offer_text)
    if not offer_id or not net:
        return [], [f"{offer_name}: no unique offer number or net sum"], 0
    offered, offered_line = net
    findings: list[dict] = []
    gaps: list[str] = []
    comparisons = 0

    form = other_documents.get("beschaffungsantrag.pdf")
    if form:
        # The form's total is tied to the chosen supplier only when its vendor
        # field explicitly names this offer. Do not compare against other bids.
        vendor_lines = [line for line in form.splitlines()
                        if re.search(r"(?i)^\s*Vorgesehener\s+Lieferant\b", line)]
        if len(vendor_lines) == 1 and _id_in_line(offer_id, vendor_lines[0]):
            declared = offer_net(form)
            if declared:
                comparisons += 1
                if offered != declared[0]:
                    findings.append({"kind": "request_vs_chosen_offer",
                                     "offer_id": offer_id,
                                     "expected": str(offered), "stated": str(declared[0]),
                                     "sources": [
                                         {"document": offer_name, "quote": offered_line},
                                         {"document": "beschaffungsantrag.pdf", "quote": vendor_lines[0].strip()},
                                         {"document": "beschaffungsantrag.pdf", "quote": declared[1]},
                                     ]})
            else:
                gaps.append("Selected offer referenced but request net total unreadable")

    note = other_documents.get("vergabevermerk.pdf")
    if note:
        rows = _award_money_rows(note, offer_id)
        if len(rows) == 1:
            comparisons += 1
            stated = money(rows[0])  # First currency column is labelled netto.
            if offered != stated:
                findings.append({"kind": "offer_vs_award_note",
                                 "offer_id": offer_id,
                                 "expected": str(offered), "stated": str(stated),
                                 "sources": [
                                     {"document": offer_name, "quote": offered_line},
                                     {"document": "vergabevermerk.pdf", "quote": rows[0].strip()},
                                 ]})
        elif len(rows) > 1:
            gaps.append(f"Offer {offer_id} has multiple money rows in award note")
        else:
            gaps.append(f"Offer {offer_id} has no matching money row in award note")

    # An email may reference a particular offer while stating the entire
    # order net on a later line. Only compare where one offer is referenced in
    # the same document; do not assign a combined email total to one of many.
    for email_name, email in other_documents.items():
        if not email_name.startswith("email-"):
            continue
        if sum(bool(_id_in_line(id_, email)) for id_ in _offer_ids(other_documents)) != 1:
            continue
        if not _id_in_line(offer_id, email):
            continue
        summary = [line for line in email.splitlines()
                   if re.search(r"(?i)^\s*Summe\b", line) and "netto" in line.lower()
                   and MONEY.search(line)]
        if len(summary) != 1:
            continue
        comparisons += 1
        stated = money(summary[0])
        if offered != stated:
            findings.append({"kind": "email_vs_attached_offer",
                             "offer_id": offer_id,
                             "expected": str(offered), "stated": str(stated),
                             "sources": [
                                 {"document": offer_name, "quote": offered_line},
                                 {"document": email_name, "quote": summary[0].strip()},
                             ]})
    return findings, gaps, comparisons


def _offer_ids(documents: dict[str, str]) -> list[str]:
    return [n for name, body in documents.items() if name.startswith("angebot-")
            if (n := offer_number(body))]


def audit_texts(case_id: str, documents: dict[str, str]) -> dict:
    findings: list[dict] = []
    gaps: list[str] = []
    comparisons = 0
    offers = [(name, body) for name, body in documents.items()
              if re.fullmatch(r"angebot-.*\.pdf", name, re.I)]
    for name, body in offers:
        errors, missing, compared = compare_offer(name, body, documents)
        findings.extend(errors)
        gaps.extend(missing)
        comparisons += compared
    cart = documents.get("wps-warenkorb.pdf")
    form = documents.get("beschaffungsantrag.pdf")
    if cart and form:
        cart_id = re.search(r"(?i)\bWarenkorb\s+([\w-]+)", cart)
        if cart_id and _id_in_line(cart_id.group(1), form):
            source = re.search(r"(?im)^\s*Warenwert\s+netto\s+[^\n]*", cart)
            declared = offer_net(form)
            if source and declared and MONEY.search(source.group()):
                comparisons += 1
                expected = money(source.group())
                if expected != declared[0]:
                    findings.append({"kind": "cart_vs_request", "offer_id": cart_id.group(1),
                                     "expected": str(expected), "stated": str(declared[0]),
                                     "sources": [
                                         {"document": "wps-warenkorb.pdf", "quote": source.group().strip()},
                                         {"document": "beschaffungsantrag.pdf", "quote": declared[1]},
                                     ]})
            else:
                gaps.append("Referenced cart or request net total unreadable")
        else:
            gaps.append("Cart not explicitly linked to request by cart number")

    # Split invoices are not individually comparable to the whole offer. A
    # matching offer number on every invoice lets us check their combined net;
    # disagreement remains a gap because more invoices may exist.
    invoices = [(name, text) for name, text in documents.items()
                if name.startswith("rechnung-")]
    if invoices:
        reconciled = False
        for _, offer_text in offers:
            identity = offer_number(offer_text)
            total = offer_net(offer_text)
            if not identity or not total or not all(_id_in_line(identity, text) for _, text in invoices):
                continue
            parts = [offer_net(text) for _, text in invoices]
            if any(value is None for value in parts):
                continue
            if sum((value[0] for value in parts), Decimal(0)) == total[0]:
                comparisons += 1
                reconciled = True
            break
        if not reconciled:
            gaps.append("Invoices not reconciled to a complete, explicitly referenced offer")
    if not offers and not comparisons:
        gaps.append("No attached offer or linked catalogue cart to compare")
    if any(not body.strip() for body in documents.values()):
        gaps.append("One or more PDFs have no extractable text")
    return {"case_id": case_id, "rule_id": "document_consistency",
            "assessment": "discrepancy" if findings else "needs_review" if gaps or not comparisons else "checked",
            "comparisons": comparisons, "discrepancies": findings, "coverage_gaps": gaps}


def update_master(master: Path, template: Path, runs_dir: Path) -> None:
    start, end = "<!-- RULE4_RUNS_START -->", "<!-- RULE4_RUNS_END -->"
    body = master.read_text(encoding="utf-8") if master.exists() else template.read_text(encoding="utf-8")
    lines = []
    for report in sorted(runs_dir.glob("document_consistency*/consistency-audit.json")):
        try:
            data = json.loads(report.read_text(encoding="utf-8"))
            counts = {k: sum(x["assessment"] == k for x in data)
                      for k in ("discrepancy", "needs_review", "checked")}
        except (OSError, ValueError, TypeError, KeyError):
            continue
        name = report.parent.name
        lines.append(f"| [{name}]({name}/consistency-audit.json) | "
                     f"{counts['discrepancy']} discrepancy, "
                     f"{counts['needs_review']} needs review, "
                     f"{counts['checked']} checked |")
    generated = start + "\n" + "\n".join(lines or ["| Chưa chạy | — |"] ) + "\n" + end
    if start in body and end in body and body.index(start) < body.index(end):
        body = body[:body.index(start)] + generated + body[body.index(end)+len(end):]
    else:
        body = body.rstrip() + "\n\n## Các lượt rule 4\n\n| Báo cáo | Chẩn đoán |\n| --- | --- |\n" + generated + "\n"
    master.parent.mkdir(parents=True, exist_ok=True)
    master.write_text(body.rstrip() + "\n", encoding="utf-8")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--master-readme", type=Path)
    p.add_argument("--readme-template", type=Path)
    args = p.parse_args()
    cases = sorted(x for x in args.input.glob("beschaffungsantrag-*") if x.is_dir())
    if not cases:
        p.error("No procurement case directories")
    results = []
    for case in cases:
        docs = {file.name: subprocess.run(
            ["pdftotext", "-layout", str(file), "-"],
            capture_output=True, check=True, text=True).stdout
            for file in sorted(case.glob("*.pdf"))}
        results.append(audit_texts(case.name, docs))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for row in results:
        print(f"{row['case_id']}: {row['assessment']}; comparisons={row['comparisons']}, "
              f"discrepancies={len(row['discrepancies'])}, "
              f"coverage_gaps={len(row['coverage_gaps'])}")
    print(f"Report: {args.output}")
    if args.master_readme:
        if not args.readme_template:
            p.error("--readme-template required with --master-readme")
        update_master(args.master_readme, args.readme_template, args.output.parent.parent)
        print(f"Main README: {args.master_readme}")


if __name__ == "__main__":
    main()
