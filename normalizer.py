import re
from difflib import SequenceMatcher

from config import NAME_SIMILARITY

##############################################################
# TEXT
##############################################################

def normalize_text(text: str | None) -> str:

    if text is None:
        return ""

    text = str(text)

    text = text.strip()

    text = re.sub(r"\s+", " ", text)

    return text


##############################################################
# EMAIL
##############################################################

def normalize_email(email):

    email = normalize_text(email)

    return email.lower()


##############################################################
# PHONE
##############################################################

def normalize_phone(phone):

    if phone is None:
        return ""

    phone = str(phone)

    phone = phone.strip()

    phone = re.sub(
        r"(ext|extension|x)\s*\d+$",
        "",
        phone,
        flags=re.IGNORECASE,
    )

    phone = re.sub(r"\D", "", phone)

    return phone


def phone_fingerprints(phone):

    phone = normalize_phone(phone)

    if phone == "":
        return set()

    fp = {phone}

    if phone.startswith("00"):
        fp.add(phone[2:])

    # Jordan

    if phone.startswith("962"):

        local = "0" + phone[3:]

        fp.add(local)

    if phone.startswith("0"):

        fp.add(phone[1:])

        fp.add("962" + phone[1:])

    if len(phone) == 9 and phone.startswith("7"):

        fp.add("0" + phone)

        fp.add("962" + phone)

    return fp


##############################################################
# NAME
##############################################################

def normalize_name(name):

    name = normalize_text(name)

    name = name.lower()

    name = re.sub(r"[.,;:_\-]+", " ", name)

    name = re.sub(r"\s+", " ", name)

    return name.strip()


def names_are_similar(a, b):

    a = normalize_name(a)

    b = normalize_name(b)

    if not a or not b:
        return False

    a_tokens = " ".join(sorted(a.split()))

    b_tokens = " ".join(sorted(b.split()))

    score = SequenceMatcher(
        None,
        a_tokens,
        b_tokens,
    ).ratio() * 100

    return score >= NAME_SIMILARITY


##############################################################
# SMART MERGE
##############################################################

def merge_text(values):

    cleaned = []

    for value in values:

        value = normalize_text(value)

        if value == "":
            continue

        duplicate = False

        for existing in cleaned:

            if names_are_similar(existing, value):

                duplicate = True

                if len(value) > len(existing):

                    cleaned.remove(existing)

                    cleaned.append(value)

                break

        if not duplicate:

            cleaned.append(value)

    return " / ".join(cleaned)
