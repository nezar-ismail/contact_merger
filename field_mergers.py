from dataclasses import dataclass, field
from difflib import SequenceMatcher

from models import Contact, MergeDecision
from normalizer import (
    merge_text,
    names_are_similar,
    normalize_email,
    normalize_name,
    normalize_phone,
)


NAME_FIELDS = (
    "First Name",
    "Middle Name",
    "Last Name",
)

PHONE_PREFIX = "Phone "
EMAIL_PREFIX = "E-mail "
ADDRESS_PREFIX = "Address "
ORGANIZATION_PREFIX = "Organization "
NOTES_FIELD = "Notes"
BIRTHDAY_FIELD = "Birthday"


@dataclass
class MergeContext:
    decisions: list[MergeDecision] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    confidence_points: list[float] = field(default_factory=list)

    def add_decision(
        self,
        field: str,
        action: str,
        original,
        incoming,
        result,
        confidence: float = 1.0,
    ):
        add_decision(
            self.decisions,
            field,
            action,
            original,
            incoming,
            result,
            confidence,
        )
        self.confidence_points.append(confidence)

        if action.lower() in {"conflict", "warning"}:
            self.conflicts.append(field)

    @property
    def confidence(self) -> float:
        if not self.confidence_points:
            return 1.0

        return round(
            sum(self.confidence_points) / len(self.confidence_points),
            3,
        )


class FieldMerger:
    name = "Field"

    def merge(self, base: Contact, incoming: Contact, report: MergeContext):
        raise NotImplementedError

    @staticmethod
    def clean(value) -> str:
        if value is None:
            return ""

        return str(value).strip()

    def merge_scalar_field(
        self,
        base: Contact,
        incoming_contact: Contact,
        report: MergeContext,
        field_name: str,
        join: bool = True,
    ):
        current = self.clean(base.fields.get(field_name))
        incoming = self.clean(incoming_contact.fields.get(field_name))

        if not incoming:
            return

        if not current:
            base.fields[field_name] = incoming
            report.add_decision(
                field_name,
                "Copied",
                "",
                incoming,
                incoming,
                1.0,
            )
            return

        if current == incoming:
            return

        if join:
            merged = merge_text([current, incoming])
            confidence = text_confidence(current, incoming)
            action = "Merged" if merged != current else "Kept"
        else:
            merged = current
            confidence = 0.5
            action = "Conflict"

        if merged != current or action == "Conflict":
            base.fields[field_name] = merged
            report.add_decision(
                field_name,
                action,
                current,
                incoming,
                merged,
                confidence,
            )


class NameMerger(FieldMerger):
    name = "Name"

    def merge(self, base: Contact, incoming: Contact, report: MergeContext):
        for field_name in NAME_FIELDS:
            self.merge_scalar_field(
                base,
                incoming,
                report,
                field_name,
                join=True,
            )


class PhoneMerger(FieldMerger):
    name = "Phone"

    def merge(self, base: Contact, incoming: Contact, report: MergeContext):
        phones = {}

        for label, value in base.phones:
            normalized = normalize_phone(value)

            if normalized:
                phones[normalized] = (
                    self.clean(label),
                    self.clean(value),
                )

        for label, value in incoming.phones:
            normalized = normalize_phone(value)

            if not normalized:
                continue

            incoming_phone = (
                self.clean(label),
                self.clean(value),
            )

            if normalized in phones:
                merged_label = merge_label(
                    phones[normalized][0],
                    incoming_phone[0],
                )
                kept_value = longest_non_empty(
                    phones[normalized][1],
                    incoming_phone[1],
                )

                if (merged_label, kept_value) != phones[normalized]:
                    original = phones[normalized]
                    phones[normalized] = (merged_label, kept_value)
                    report.add_decision(
                        "Phone",
                        "Merged Label",
                        original,
                        incoming_phone,
                        phones[normalized],
                        0.95,
                    )
                else:
                    report.add_decision(
                        "Phone",
                        "Duplicate",
                        phones[normalized][1],
                        incoming_phone[1],
                        phones[normalized][1],
                        1.0,
                    )

                continue

            phones[normalized] = incoming_phone
            report.add_decision(
                "Phone",
                "Added",
                "",
                incoming_phone[1],
                incoming_phone[1],
                1.0,
            )

        base.phones = list(phones.values())
        base.phone_fingerprints = set(phones.keys())


class EmailMerger(FieldMerger):
    name = "Email"

    def merge(self, base: Contact, incoming: Contact, report: MergeContext):
        emails = {}

        for label, value in base.emails:
            normalized = normalize_email(value)

            if normalized:
                emails[normalized] = (
                    self.clean(label),
                    self.clean(value),
                )

        for label, value in incoming.emails:
            normalized = normalize_email(value)

            if not normalized:
                continue

            incoming_email = (
                self.clean(label),
                self.clean(value),
            )

            if normalized in emails:
                merged_label = merge_label(
                    emails[normalized][0],
                    incoming_email[0],
                )

                if merged_label != emails[normalized][0]:
                    original = emails[normalized]
                    emails[normalized] = (
                        merged_label,
                        emails[normalized][1],
                    )
                    report.add_decision(
                        "Email",
                        "Merged Label",
                        original,
                        incoming_email,
                        emails[normalized],
                        0.95,
                    )
                else:
                    report.add_decision(
                        "Email",
                        "Duplicate",
                        emails[normalized][1],
                        incoming_email[1],
                        emails[normalized][1],
                        1.0,
                    )

                continue

            emails[normalized] = incoming_email
            report.add_decision(
                "Email",
                "Added",
                "",
                incoming_email[1],
                incoming_email[1],
                1.0,
            )

        base.emails = list(emails.values())


class AddressMerger(FieldMerger):
    name = "Address"

    def merge(self, base: Contact, incoming: Contact, report: MergeContext):
        addresses = collect_numbered_fields(
            base.fields,
            ADDRESS_PREFIX,
        )
        seen = {
            field_group_fingerprint(address)
            for address in addresses
            if field_group_fingerprint(address)
        }

        for address in collect_numbered_fields(incoming.fields, ADDRESS_PREFIX):
            fingerprint = field_group_fingerprint(address)

            if not fingerprint:
                continue

            if fingerprint in seen:
                continue

            seen.add(fingerprint)
            addresses.append(address)
            report.add_decision(
                "Address",
                "Added",
                "",
                readable_field_group(address),
                readable_field_group(address),
                1.0,
            )

        rebuild_numbered_fields(
            base.fields,
            ADDRESS_PREFIX,
            addresses,
        )
        base.addresses = [
            readable_field_group(address)
            for address in addresses
        ]


class OrganizationMerger(FieldMerger):
    name = "Organization"

    def merge(self, base: Contact, incoming: Contact, report: MergeContext):
        fields = sorted(
            key
            for key in set(base.fields) | set(incoming.fields)
            if is_field_name(key) and key.startswith(ORGANIZATION_PREFIX)
        )

        for field_name in fields:
            self.merge_scalar_field(
                base,
                incoming,
                report,
                field_name,
                join=True,
            )

        base.organizations = {
            self.clean(base.fields.get(field_name))
            for field_name in fields
            if self.clean(base.fields.get(field_name))
        }


class NotesMerger(FieldMerger):
    name = "Notes"

    def merge(self, base: Contact, incoming: Contact, report: MergeContext):
        notes = []
        seen = set()

        for note in base.notes + incoming.notes:
            note = self.clean(note)

            if not note:
                continue

            normalized = note.casefold()

            if normalized in seen:
                continue

            seen.add(normalized)
            notes.append(note)

        merged = "\n\n------------------------\n\n".join(notes)
        current = self.clean(base.fields.get(NOTES_FIELD))

        if merged != current:
            report.add_decision(
                NOTES_FIELD,
                "Appended",
                current,
                incoming.fields.get(NOTES_FIELD, ""),
                merged,
                1.0,
            )

        base.notes = notes
        base.fields[NOTES_FIELD] = merged


class BirthdayMerger(FieldMerger):
    name = "Birthday"

    def merge(self, base: Contact, incoming: Contact, report: MergeContext):
        current = self.clean(base.fields.get(BIRTHDAY_FIELD))
        incoming_value = self.clean(incoming.fields.get(BIRTHDAY_FIELD))

        if not incoming_value:
            return

        if not current:
            base.fields[BIRTHDAY_FIELD] = incoming_value
            report.add_decision(
                BIRTHDAY_FIELD,
                "Copied",
                "",
                incoming_value,
                incoming_value,
                1.0,
            )
            return

        if current != incoming_value:
            report.add_decision(
                BIRTHDAY_FIELD,
                "Conflict",
                current,
                incoming_value,
                current,
                0.4,
            )


class PreserveRemainingMerger(FieldMerger):
    name = "Remaining Fields"

    handled_prefixes = (
        PHONE_PREFIX,
        EMAIL_PREFIX,
        ADDRESS_PREFIX,
        ORGANIZATION_PREFIX,
    )

    handled_fields = set(NAME_FIELDS) | {
        NOTES_FIELD,
        BIRTHDAY_FIELD,
    }

    def merge(self, base: Contact, incoming: Contact, report: MergeContext):
        for field_name, incoming_value in incoming.fields.items():
            if self.is_handled(field_name):
                continue

            incoming_text = self.clean(incoming_value)

            if not incoming_text:
                continue

            current = self.clean(base.fields.get(field_name))

            if not current:
                base.fields[field_name] = incoming_text
                report.add_decision(
                    field_name,
                    "Copied",
                    "",
                    incoming_text,
                    incoming_text,
                    1.0,
                )
                continue

            if current == incoming_text:
                continue

            report.add_decision(
                field_name,
                "Conflict",
                current,
                incoming_text,
                current,
                0.5,
            )

    def is_handled(self, field_name):
        if not is_field_name(field_name):
            return True

        if field_name in self.handled_fields:
            return True

        return any(
            field_name.startswith(prefix)
            for prefix in self.handled_prefixes
        )


MERGERS: tuple[FieldMerger, ...] = (
    NameMerger(),
    PhoneMerger(),
    EmailMerger(),
    AddressMerger(),
    OrganizationMerger(),
    NotesMerger(),
    BirthdayMerger(),
    PreserveRemainingMerger(),
)


def add_decision(
    decisions: list,
    field: str,
    action: str,
    original,
    incoming,
    result,
    confidence: float = 1.0,
):
    decisions.append(
        MergeDecision(
            field=field,
            action=action,
            original=str(original),
            incoming=str(incoming),
            result=str(result),
            confidence=confidence,
        )
    )


def choose_base_contact(contacts: list[Contact]) -> Contact:
    return max(
        contacts,
        key=lambda contact: (
            contact.score,
            len(contact.phones),
            len(contact.emails),
            len(contact.notes),
        ),
    )


def finalize_contact(contact: Contact):
    rebuild_labeled_values(
        contact,
        PHONE_PREFIX,
        contact.phones,
    )
    rebuild_labeled_values(
        contact,
        EMAIL_PREFIX,
        contact.emails,
    )


def add_group_warnings(group, report: MergeContext):
    has_conflict, names = detect_name_conflict(group)

    if has_conflict:
        report.add_decision(
            "NAME",
            "WARNING",
            "",
            ", ".join(names),
            "Review Recommended",
            0.45,
        )


def detect_name_conflict(group):
    names = []

    for contact in group:
        first = str(contact.fields.get("First Name", "")).strip()
        last = str(contact.fields.get("Last Name", "")).strip()
        full = f"{first} {last}".strip()

        if full:
            names.append(full)

    unique = []

    for name in names:
        if not any(names_are_similar(name, existing) for existing in unique):
            unique.append(name)

    return len(unique) > 1, unique


def merge_first_name(base: Contact, incoming: Contact, decisions):
    context = MergeContext(decisions=decisions)
    NameMerger().merge_scalar_field(
        base,
        incoming,
        context,
        "First Name",
        join=True,
    )


def merge_middle_name(base: Contact, incoming: Contact, decisions):
    context = MergeContext(decisions=decisions)
    NameMerger().merge_scalar_field(
        base,
        incoming,
        context,
        "Middle Name",
        join=True,
    )


def merge_last_name(base: Contact, incoming: Contact, decisions):
    context = MergeContext(decisions=decisions)
    NameMerger().merge_scalar_field(
        base,
        incoming,
        context,
        "Last Name",
        join=True,
    )


def merge_phones(base: Contact, incoming: Contact, decisions):
    PhoneMerger().merge(
        base,
        incoming,
        MergeContext(decisions=decisions),
    )


def merge_emails(base: Contact, incoming: Contact, decisions):
    EmailMerger().merge(
        base,
        incoming,
        MergeContext(decisions=decisions),
    )


def merge_organizations(base: Contact, incoming: Contact, decisions):
    OrganizationMerger().merge(
        base,
        incoming,
        MergeContext(decisions=decisions),
    )


def merge_notes(base: Contact, incoming: Contact, decisions):
    NotesMerger().merge(
        base,
        incoming,
        MergeContext(decisions=decisions),
    )


def merge_addresses(base: Contact, incoming: Contact, decisions):
    AddressMerger().merge(
        base,
        incoming,
        MergeContext(decisions=decisions),
    )


def merge_photo(base: Contact, incoming: Contact, decisions):
    PreserveRemainingMerger().merge_scalar_field(
        base,
        incoming,
        MergeContext(decisions=decisions),
        "Photo",
        join=False,
    )


def rebuild_phone_fields(contact: Contact):
    rebuild_labeled_values(
        contact,
        PHONE_PREFIX,
        contact.phones,
    )


def rebuild_email_fields(contact: Contact):
    rebuild_labeled_values(
        contact,
        EMAIL_PREFIX,
        contact.emails,
    )


def rebuild_labeled_values(contact: Contact, prefix: str, values):
    for key in list(contact.fields):
        if is_field_name(key) and key.startswith(prefix):
            contact.fields[key] = ""

    for index, (label, value) in enumerate(values, start=1):
        contact.fields[f"{prefix}{index} - Label"] = label
        contact.fields[f"{prefix}{index} - Value"] = value


def collect_numbered_fields(fields, prefix: str):
    groups = {}

    for key, value in fields.items():
        if not is_field_name(key) or not key.startswith(prefix):
            continue

        rest = key[len(prefix) :]
        number, separator, subfield = rest.partition(" - ")

        if not separator or not number.isdigit():
            continue

        groups.setdefault(int(number), {})[subfield] = value

    return [
        groups[number]
        for number in sorted(groups)
        if field_group_fingerprint(groups[number])
    ]


def rebuild_numbered_fields(fields, prefix: str, groups):
    for key in list(fields):
        if is_field_name(key) and key.startswith(prefix):
            fields[key] = ""

    for index, group in enumerate(groups, start=1):
        for subfield, value in group.items():
            fields[f"{prefix}{index} - {subfield}"] = value


def field_group_fingerprint(group):
    values = [
        str(value).strip().casefold()
        for value in group.values()
        if value is not None and str(value).strip()
    ]

    return "|".join(sorted(values))


def readable_field_group(group):
    values = [
        str(value).strip()
        for value in group.values()
        if value is not None and str(value).strip()
    ]

    return " / ".join(values)


def is_field_name(value):
    return isinstance(value, str) and value != ""


def merge_label(current, incoming):
    return merge_text(
        [
            current,
            incoming,
        ]
    )


def longest_non_empty(a, b):
    a = str(a or "").strip()
    b = str(b or "").strip()

    if len(b) > len(a):
        return b

    return a


def text_confidence(a, b):
    a = normalize_name(a)
    b = normalize_name(b)

    if not a or not b:
        return 1.0

    score = SequenceMatcher(
        None,
        " ".join(sorted(a.split())),
        " ".join(sorted(b.split())),
    ).ratio()

    if score >= 0.92:
        return 0.95

    if score >= 0.75:
        return 0.75

    return 0.55
