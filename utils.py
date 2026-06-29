"""
Utility helpers.
"""

import shutil
from pathlib import Path

from config import *


def ensure_directories():

    OUTPUT_DIR.mkdir(
        exist_ok=True
    )

    BACKUP_DIR.mkdir(
        exist_ok=True
    )

    LOG_DIR.mkdir(
        exist_ok=True
    )


def backup_input():

    if not CREATE_BACKUP:
        return

    backup = BACKUP_DIR / INPUT_FILE.name

    shutil.copy2(
        INPUT_FILE,
        backup
    )


def log(message):

    if VERBOSE:
        print(message)

    with open(
        LOG_FILE,
        "a",
        encoding="utf8"
    ) as f:

        f.write(message + "\n")


####################################################
# COLUMN DETECTION
####################################################

def detect_phone_columns(headers):

    result = []

    for i, h in enumerate(headers):

        if h is None:
            continue

        h = str(h)

        if (
            PHONE_PREFIX in h
            and PHONE_SUFFIX in h
        ):

            result.append(i)

    return result


def detect_email_columns(headers):

    result = []

    for i, h in enumerate(headers):

        if h is None:
            continue

        h = str(h)

        if (
            EMAIL_PREFIX in h
            and EMAIL_SUFFIX in h
        ):

            result.append(i)

    return result


def detect_address_columns(headers):

    result = []

    for i, h in enumerate(headers):

        if h is None:
            continue

        h = str(h)

        if ADDRESS_PREFIX in h:

            result.append(i)

    return result


####################################################
# SCORE
####################################################

def contact_score(values):
    """
    Higher score = more complete contact.
    """

    score = 0

    for value in values:

        if value is None:
            continue

        value = str(value).strip()

        if value == "":
            continue

        score += 1

    return score