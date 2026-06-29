import csv
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook


REPORT_HEADERS = [
    "Group",
    "Rows",
    "Merged Row",
    "Confidence",
    "Conflicts",
    "Field",
    "Action",
    "Original",
    "Incoming",
    "Result",
    "Decision Confidence",
]


def report_rows(reports):
    rows = []

    for index, report in enumerate(reports, start=1):
        group_rows = ", ".join(
            str(contact.row)
            for contact in report.contacts
        )
        conflicts = ", ".join(report.conflicts)

        if not report.decisions:
            rows.append(
                [
                    index,
                    group_rows,
                    report.merged.row,
                    report.confidence,
                    conflicts,
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                ]
            )
            continue

        for decision in report.decisions:
            rows.append(
                [
                    index,
                    group_rows,
                    report.merged.row,
                    report.confidence,
                    conflicts,
                    decision.field,
                    decision.action,
                    decision.original,
                    decision.incoming,
                    decision.result,
                    decision.confidence,
                ]
            )

    return rows


def write_duplicate_report(path, reports):
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Duplicate Report"
    worksheet.append(REPORT_HEADERS)

    for row in report_rows(reports):
        worksheet.append(row)

    return save_workbook(workbook, path)


def write_merged_contacts(path, contacts, headers):
    path = Path(path)
    headers = expanded_headers(
        headers,
        contacts,
    )

    if path.suffix.lower() == ".csv":
        return write_contacts_csv(path, contacts, headers)

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Contacts"
    worksheet.append(list(headers))

    for contact in contacts:
        worksheet.append(contact_to_row(contact, headers))

    return save_workbook(workbook, path)


def write_contacts_csv(path, contacts, headers):
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    try:
        with path.open(
            "w",
            newline="",
            encoding="utf-8-sig",
        ) as handle:
            writer = csv.writer(handle)
            writer.writerow(headers)

            for contact in contacts:
                writer.writerow(contact_to_row(contact, headers))

        return path
    except PermissionError:
        fallback = fallback_path(path)

        with fallback.open(
            "w",
            newline="",
            encoding="utf-8-sig",
        ) as handle:
            writer = csv.writer(handle)
            writer.writerow(headers)

            for contact in contacts:
                writer.writerow(contact_to_row(contact, headers))

        print(
            f"Could not overwrite {path.name}; wrote {fallback.name} instead. "
            "Close the open file before the next run."
        )
        return fallback


def write_merge_log(path, reports, dry_run: bool = False):
    lines = build_merge_log_lines(
        reports,
        dry_run=dry_run,
    )
    path = Path(path)
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    return write_text_file(
        path,
        "\n".join(lines),
    )


def build_merge_log_lines(reports, dry_run: bool = False):
    lines = [
        f"DRY_RUN={dry_run}",
        f"duplicate_groups={len(reports)}",
        "",
    ]

    for index, report in enumerate(reports, start=1):
        rows = ", ".join(
            str(contact.row)
            for contact in report.contacts
        )
        conflicts = ", ".join(report.conflicts) or "none"

        lines.append(
            f"Group {index}: rows [{rows}] -> base row {report.merged.row}; "
            f"confidence={report.confidence}; conflicts={conflicts}"
        )

        for decision in report.decisions:
            lines.append(
                f"  - {decision.field}: {decision.action}; "
                f"confidence={decision.confidence}; "
                f"original={decision.original}; incoming={decision.incoming}; "
                f"result={decision.result}"
            )

        lines.append("")

    return lines


def summarize_reports(reports):
    conflict_count = 0
    decision_count = 0
    confidence_total = 0

    for report in reports:
        conflict_count += len(report.conflicts)
        decision_count += len(report.decisions)
        confidence_total += report.confidence

    average_confidence = 1.0

    if reports:
        average_confidence = round(
            confidence_total / len(reports),
            3,
        )

    return {
        "duplicate_groups": len(reports),
        "decisions": decision_count,
        "conflicts": conflict_count,
        "average_confidence": average_confidence,
    }


def contact_to_row(contact, headers):
    return [
        contact.fields.get(header, "")
        for header in headers
    ]


def expanded_headers(headers, contacts):
    expanded = [
        header
        for header in headers
        if header not in (None, "")
    ]
    seen = set(expanded)

    for contact in contacts:
        for field_name in contact.fields:
            if field_name not in seen:
                expanded.append(field_name)
                seen.add(field_name)

    return expanded


def save_workbook(workbook, path):
    path = Path(path)
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    try:
        workbook.save(path)
        return path
    except PermissionError:
        fallback = fallback_path(path)
        workbook.save(fallback)
        print(
            f"Could not overwrite {path.name}; wrote {fallback.name} instead. "
            "Close the open workbook before the next run."
        )
        return fallback


def write_text_file(path, text):
    path = Path(path)
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    try:
        path.write_text(
            text,
            encoding="utf8",
        )
        return path
    except PermissionError:
        fallback = fallback_path(path)
        fallback.write_text(
            text,
            encoding="utf8",
        )
        print(
            f"Could not overwrite {path.name}; wrote {fallback.name} instead. "
            "Close the open file before the next run."
        )
        return fallback


def fallback_path(path):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    return path.with_name(
        f"{path.stem}_{timestamp}{path.suffix}"
    )
