# Google Contacts XLSX Duplicate Merger

This project merges duplicate Google Contacts exported as `.xlsx` or `.csv` files.
Duplicates are detected by normalized phone numbers, grouped with Union-Find,
and merged without deleting information from the source rows.

## What It Produces

Running the project writes these files under `output/`:

- `merged_contacts.xlsx` - contacts ready to review or import back into Google Contacts.
- `merged_contacts.csv` - the same merged contacts in CSV format.
- `duplicate_report.xlsx` - one row per merge decision, including confidence and conflicts.
- `merge_log.txt` - readable text log of duplicate groups and merge decisions.

When `DRY_RUN = True`, the report and log are still produced, but
`merged_contacts.xlsx` and `merged_contacts.csv` keep the original contacts
instead of replacing duplicate groups with merged contacts.

If an output workbook is open in Excel or locked by OneDrive, Windows may block
overwriting it. In that case the app writes a timestamped fallback file, such as
`merged_contacts_20260629_173000.xlsx`, and prints the actual filename.

## Setup

Install the only runtime dependency:

```powershell
pip install -r requirements.txt
```

Create an `input/` directory next to the Python files and place the Google
Contacts export at:

```text
input/contacts.xlsx
```

Then run:

```powershell
python main.py
```

You can also pass a CSV or XLSX path directly:

```powershell
python main.py "C:\Users\NezarJoueh\Downloads\contacts.csv"
```

## Configuration

Settings live in `config.py`.

Important values:

- `INPUT_FILE` - source Google Contacts workbook.
- `OUTPUT_FILE` - merged contacts workbook path.
- `CSV_OUTPUT_FILE` - merged contacts CSV path.
- `REPORT_FILE` - duplicate report workbook path.
- `LOG_FILE` - merge log path.
- `DRY_RUN` - when `True`, generate reports without collapsing duplicate groups.
- `NAME_SIMILARITY` - threshold used when deciding whether names are similar.

## Merge Rules

The merge engine is plugin-based. Each field type has a focused merger:

- `NameMerger`
- `PhoneMerger`
- `EmailMerger`
- `AddressMerger`
- `OrganizationMerger`
- `NotesMerger`
- `BirthdayMerger`

Rules:

- Contacts are grouped when normalized phone fingerprints overlap.
- The most complete contact is chosen as the base row for each duplicate group.
- Different names are joined with ` / `.
- Similar names keep the longest version.
- Phone labels are preserved and merged when duplicate numbers use different labels.
- Email labels are preserved and merged when duplicate emails use different labels.
- Organizations, notes, and addresses are preserved.
- Birthdays and other scalar fields are flagged as conflicts when values differ.
- Unknown fields are not discarded; empty base fields are copied, and differing
  populated values are reported as conflicts.

## Confidence And Conflicts

Each merge decision receives a confidence score between `0.0` and `1.0`.
The duplicate group confidence is the average of its decision scores.

Typical meanings:

- `1.0` - exact duplicate, direct copy, or safe addition.
- `0.95` - high-confidence label/name merge.
- `0.75` - moderately similar text merge.
- `0.55` - low-confidence text merge that should be reviewed.
- `0.4` to `0.5` - conflict or warning.

Conflicts are listed in both `duplicate_report.xlsx` and `merge_log.txt`.

## Google Contacts Compatibility

The writer preserves the original column headers and appends any new columns
needed for additional phones, emails, addresses, or other fields created during
the merge. CSV input is read with UTF-8 BOM support, which matches many Google
Contacts exports. It uses Google Contacts-style names such as:

```text
Phone 1 - Label
Phone 1 - Value
E-mail 1 - Label
E-mail 1 - Value
Address 1 - Formatted
Organization Name
Notes
Birthday
```

## Project Structure

- `main.py` - command-line entry point.
- `loader.py` - loads contacts from XLSX into `Contact` objects.
- `matcher.py` - Union-Find implementation and contact grouping.
- `field_mergers.py` - plugin-based merge engine and field-specific merge rules.
- `merger.py` - compact merge orchestration over the field-merger plugins.
- `report.py` - merged contacts, duplicate report, and merge log generation.
- `normalizer.py` - phone, email, text, and name normalization.
- `models.py` - dataclasses for contacts and merge reports.
- `config.py` - paths and behavior flags.

## Safety Notes

Keep `DRY_RUN = True` for the first run and review `duplicate_report.xlsx`
before importing anything back into Google Contacts. The source workbook is read
only; merged results are written to `output/`.
