from pathlib import Path

#########################################################
# PATHS
#########################################################

BASE_DIR = Path(__file__).resolve().parent

INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
BACKUP_DIR = OUTPUT_DIR / "backup"
LOG_DIR = BASE_DIR / "logs"

INPUT_FILE = INPUT_DIR / "contacts.xlsx"

OUTPUT_FILE = OUTPUT_DIR / "merged_contacts.xlsx"

CSV_OUTPUT_FILE = OUTPUT_DIR / "merged_contacts.csv"

REPORT_FILE = OUTPUT_DIR / "duplicate_report.xlsx"

LOG_FILE = OUTPUT_DIR / "merge_log.txt"

#########################################################
# SAFETY
#########################################################

# True = Nothing will be modified.
# Only report duplicates.
DRY_RUN = False

# Create backup before merge
CREATE_BACKUP = True

#########################################################
# MATCHING
#########################################################

# RapidFuzz similarity
NAME_SIMILARITY = 92

# Merge only when at least one phone matches
REQUIRE_PHONE_MATCH = True

#########################################################
# NORMALIZATION
#########################################################

REMOVE_EXTENSIONS = True
REMOVE_PUNCTUATION = True
IGNORE_CASE = True

#########################################################
# PHONE
#########################################################

# Detect Phone 1..100 automatically
PHONE_PREFIX = "Phone"
PHONE_SUFFIX = "Value"

#########################################################
# EMAIL
#########################################################

EMAIL_PREFIX = "E-mail"
EMAIL_SUFFIX = "Value"

#########################################################
# ADDRESS
#########################################################

ADDRESS_PREFIX = "Address"

#########################################################
# ORGANIZATION
#########################################################

ORG_FIELD = "Organization Name"

#########################################################
# NOTES
#########################################################

NOTES_FIELD = "Notes"

#########################################################
# LOGGING
#########################################################

VERBOSE = True

#########################################################
# MERGE MODES
#########################################################

NAME_MERGE_MODE = "join"      # join | longest | first | review
NOTES_MERGE_MODE = "append"
ORG_MERGE_MODE = "join"
PHOTO_CONFLICT_MODE = "review"
