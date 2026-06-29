from copy import deepcopy

from config import CSV_OUTPUT_FILE, DRY_RUN, LOG_FILE, OUTPUT_FILE, REPORT_FILE
from field_mergers import *
from matcher import build_contact_groups
from models import MergeGroup
from report import contact_to_row, write_duplicate_report, write_merge_log, write_merged_contacts


def merge_group(group):
    report = MergeContext()
    base = deepcopy(choose_base_contact(group))

    for incoming in group:
        if incoming.row == base.row:
            continue

        for field_merger in MERGERS:
            field_merger.merge(base, incoming, report)

    finalize_contact(base)
    add_group_warnings(group, report)

    return MergeGroup(group, base, report.decisions, report.confidence, sorted(set(report.conflicts)))


def merge_all_groups(groups, dry_run: bool = False):
    merged = []
    reports = []

    for group in groups.values():
        if len(group) == 1:
            merged.append(group[0])
            continue

        result = merge_group(group)
        reports.append(result)
        merged.extend(group if dry_run else [result.merged])

    return merged, reports


def write_outputs(
    contacts,
    headers,
    output_file=OUTPUT_FILE,
    csv_output_file=CSV_OUTPUT_FILE,
    report_file=REPORT_FILE,
    log_file=LOG_FILE,
    dry_run: bool = DRY_RUN,
):
    groups = build_contact_groups(contacts)
    merged_contacts, reports = merge_all_groups(groups, dry_run=dry_run)

    written_paths = {
        "merged_contacts": write_merged_contacts(output_file, merged_contacts, headers),
        "merged_contacts_csv": write_merged_contacts(csv_output_file, merged_contacts, headers),
        "duplicate_report": write_duplicate_report(report_file, reports),
        "merge_log": write_merge_log(log_file, reports, dry_run=dry_run),
    }
    write_outputs.last_written_paths = written_paths

    return merged_contacts, reports


write_outputs.last_written_paths = {}
