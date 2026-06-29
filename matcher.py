"""
matcher.py

Responsible for grouping contacts that share at least one
normalized phone number.

Uses Union-Find (Disjoint Set).
"""

from collections import defaultdict

from normalizer import phone_fingerprints


class UnionFind:

    def __init__(self):
        self.parent = {}
        self.rank = {}

    def make_set(self, item):
        self.parent[item] = item
        self.rank[item] = 0

    def find(self, item):

        if self.parent[item] != item:
            self.parent[item] = self.find(self.parent[item])

        return self.parent[item]

    def union(self, a, b):

        ra = self.find(a)
        rb = self.find(b)

        if ra == rb:
            return

        if self.rank[ra] < self.rank[rb]:
            self.parent[ra] = rb

        elif self.rank[ra] > self.rank[rb]:
            self.parent[rb] = ra

        else:
            self.parent[rb] = ra
            self.rank[ra] += 1


def build_duplicate_groups(contacts, phone_columns):
    """
    contacts:
        list of dictionaries

    phone_columns:
        indices of Phone columns

    Returns

        groups
        {
            root:[
                contact1,
                contact2
            ]
        }
    """

    uf = UnionFind()

    fingerprint_map = defaultdict(list)

    for contact in contacts:

        uf.make_set(contact["row"])

        fingerprints = set()

        for col in phone_columns:

            phone = contact["values"][col]

            fingerprints.update(
                phone_fingerprints(phone)
            )

        contact["fingerprints"] = fingerprints

        for fp in fingerprints:
            fingerprint_map[fp].append(contact["row"])

    for rows in fingerprint_map.values():

        if len(rows) < 2:
            continue

        first = rows[0]

        for row in rows[1:]:
            uf.union(first, row)

    groups = defaultdict(list)

    row_lookup = {
        c["row"]: c
        for c in contacts
    }

    for row in row_lookup:

        root = uf.find(row)

        groups[root].append(
            row_lookup[row]
        )

    return groups


def build_contact_groups(contacts):
    contacts = list(contacts)
    uf = UnionFind()
    fingerprint_map = defaultdict(list)

    for contact in contacts:
        uf.make_set(contact.row)

        for fingerprint in contact.phone_fingerprints:
            fingerprint_map[fingerprint].append(contact.row)

    for rows in fingerprint_map.values():
        if len(rows) < 2:
            continue

        first = rows[0]

        for row in rows[1:]:
            uf.union(first, row)

    groups = defaultdict(list)
    row_lookup = {
        contact.row: contact
        for contact in contacts
    }

    for row, contact in row_lookup.items():
        root = uf.find(row)
        groups[root].append(contact)

    return groups
