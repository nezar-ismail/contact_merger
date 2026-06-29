from dataclasses import dataclass, field
from typing import Dict, List, Set, Any


@dataclass
class Contact:

    # Original row number in Excel
    row: int

    # Score of completeness
    score: int

    # Dictionary of ALL Excel fields
    fields: Dict[str, Any]

    # Normalized phone fingerprints
    phone_fingerprints: Set[str] = field(default_factory=set)

    # Unique phone numbers
    phones: List[tuple] = field(default_factory=list)
    # (label,value)

    # Unique emails
    emails: List[tuple] = field(default_factory=list)

    # Organizations
    organizations: Set[str] = field(default_factory=set)

    # Notes
    notes: List[str] = field(default_factory=list)

    # Addresses
    addresses: List[str] = field(default_factory=list)


@dataclass
class MergeDecision:

    field: str

    action: str

    original: str

    incoming: str

    result: str

    confidence: float = 1.0


@dataclass
class MergeGroup:

    contacts: List[Contact]

    merged: Contact

    decisions: List[MergeDecision]

    confidence: float = 1.0

    conflicts: List[str] = field(default_factory=list)

@dataclass
class MergeAccumulator:

    first_names: List[str] = field(default_factory=list)

    middle_names: List[str] = field(default_factory=list)

    last_names: List[str] = field(default_factory=list)

    phones: Dict[str, tuple] = field(default_factory=dict)

    emails: Dict[str, tuple] = field(default_factory=dict)

    organizations: Set[str] = field(default_factory=set)

    notes: List[str] = field(default_factory=list)

    addresses: Set[str] = field(default_factory=set)

    photos: Set[str] = field(default_factory=set)
