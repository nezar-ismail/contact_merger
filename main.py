import sys
from pathlib import Path

from config import CSV_OUTPUT_FILE, DRY_RUN, INPUT_FILE, LOG_FILE, OUTPUT_FILE, REPORT_FILE
from loader import load_contacts, read_headers
from merger import write_outputs
from utils import ensure_directories


def main():
    ensure_directories()

    input_file = selected_input_file()
    contacts = load_contacts(input_file)
    headers = read_headers(input_file)

    merged_contacts, reports = write_outputs(
        contacts,
        headers,
        output_file=OUTPUT_FILE,
        csv_output_file=CSV_OUTPUT_FILE,
        report_file=REPORT_FILE,
        log_file=LOG_FILE,
        dry_run=DRY_RUN,
    )
    written_paths = write_outputs.last_written_paths

    print(
        "Wrote "
        f"{written_paths['merged_contacts'].name}, "
        f"{written_paths['merged_contacts_csv'].name}, "
        f"{written_paths['duplicate_report'].name}, and "
        f"{written_paths['merge_log'].name}. "
        f"contacts={len(contacts)}, output_contacts={len(merged_contacts)}, "
        f"duplicate_groups={len(reports)}, DRY_RUN={DRY_RUN}"
    )


def selected_input_file():
    if len(sys.argv) > 1:
        return Path(sys.argv[1])

    return INPUT_FILE


if __name__ == "__main__":
    main()
