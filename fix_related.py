#!/usr/bin/env python3
"""
fix_related.py — One-time script to auto-link related words across all entries.

Detects connections based on:
  1. Shared family_root (all members of a verb family link to each other)
  2. Word appears in another entry's related list (make it bidirectional)
  3. Word appears in another entry's notes or tags field
  4. Prefix variants (e.g. aufräumen ↔ einräumen ↔ ausräumen)

Usage:
    python fix_related.py --db words.json --dry-run   # preview changes
    python fix_related.py --db words.json              # apply changes
"""

import json
import re
import os
import argparse
from collections import defaultdict


# ── normalisation ──────────────────────────────────────────────────────────────

def normalise(word: str) -> str:
    """Lowercase, strip leading articles/pronouns for fuzzy matching."""
    w = word.lower().strip()
    w = re.sub(r'^(der|die|das|sich|ein|eine|einen|einem)\s+', '', w)
    return w.strip()

def norm_set(words: list) -> set:
    return {normalise(w) for w in words}


# ── connection detection ───────────────────────────────────────────────────────

def find_connections(db: list) -> dict:
    """
    Returns a dict: word_id -> set of word strings that should be related.
    """
    connections = defaultdict(set)

    # build lookup maps
    by_id   = {w['id']: w for w in db}
    by_norm = {normalise(w['word']): w for w in db}
    by_word = {w['word'].lower(): w for w in db}

    def find_entry(name: str):
        """Find a db entry by name (fuzzy)."""
        n = normalise(name)
        if n in by_norm:
            return by_norm[n]
        if name.lower() in by_word:
            return by_word[name.lower()]
        return None

    # ── Signal 1: shared family_root ──────────────────────────────────────────
    family_groups = defaultdict(list)
    for w in db:
        if w.get('family_root'):
            family_groups[w['family_root'].lower()].append(w)

    for root, members in family_groups.items():
        if len(members) < 2:
            continue
        for m in members:
            for other in members:
                if other['id'] != m['id']:
                    connections[m['id']].add(other['word'])

    # ── Signal 2: existing related lists → make bidirectional ─────────────────
    for w in db:
        for rel_name in w.get('related', []):
            target = find_entry(rel_name)
            if target and target['id'] != w['id']:
                # ensure w appears in target's connections too
                connections[target['id']].add(w['word'])
                connections[w['id']].add(target['word'])

    # ── Signal 3: tags like "similar to: X" or "verb family: X" ────────────────
    # Only use tags — much more reliable than free-text notes matching
    all_words_norm = {normalise(w['word']): w for w in db}
    all_words_lower = {w['word'].lower(): w for w in db}

    for w in db:
        for tag in w.get('tags', []):
            # parse structured tags: "similar to: word", "verb family: word"
            tag_lower = tag.lower()
            # extract the word after the colon
            if ':' in tag_lower:
                after_colon = tag_lower.split(':', 1)[1].strip()
                # might be a single word or comma-separated
                candidates = [c.strip() for c in after_colon.split(',')]
                for c in candidates:
                    c = c.strip()
                    if not c:
                        continue
                    # look up this candidate in the db
                    target = None
                    c_norm = re.sub(r'^(der|die|das|sich|ein|eine|einen|einem)\s+', '', c).strip()
                    if c_norm in all_words_norm:
                        target = all_words_norm[c_norm]
                    elif c in all_words_lower:
                        target = all_words_lower[c]
                    if target and target['id'] != w['id']:
                        connections[w['id']].add(target['word'])
                        connections[target['id']].add(w['word'])

    # ── Signal 4: negating/modifying prefix pairs ────────────────────────────
    # e.g. unvernünftig ↔ vernünftig, missverständnis ↔ verständnis
    # Only match if both words are the same type (or closely related types)
    MODIFYING_PREFIXES = ['un', 'miss', 'ur', 'über', 'unter', 'wider', 'wieder']
    ADJ_ADV_TYPES = {'adjective', 'adverb', 'adj/adv'}

    for w in db:
        bare = normalise(w['word'])
        for pfx in MODIFYING_PREFIXES:
            if bare.startswith(pfx) and len(bare) > len(pfx) + 2:
                stem = bare[len(pfx):]
                # look up the stem in the db
                target = by_norm.get(stem)
                if target and target['id'] != w['id']:
                    # only link if same type or both adj/adv related types
                    w_type = w.get('type', '')
                    t_type = target.get('type', '')
                    same_type = (w_type == t_type) or                                 (w_type in ADJ_ADV_TYPES and t_type in ADJ_ADV_TYPES) or                                 (w_type == 'noun' and t_type == 'noun')
                    if same_type:
                        connections[w['id']].add(target['word'])
                        connections[target['id']].add(w['word'])

    # ── Signal 5: derived_from field ─────────────────────────────────────────
    # e.g. erwiesen (derived_from: sich erweisen) links to sich erweisen
    for w in db:
        derived = w.get('derived_from')
        if not derived:
            continue
        target = find_entry(derived)
        if target and target['id'] != w['id']:
            connections[w['id']].add(target['word'])
            connections[target['id']].add(w['word'])

    return connections


# ── apply connections ──────────────────────────────────────────────────────────

def apply_connections(db: list, connections: dict, dry_run: bool) -> int:
    """Apply computed connections to the database. Returns total links added."""
    total_added = 0
    changes = []

    for w in db:
        new_related = connections.get(w['id'], set())
        existing = set(w.get('related', []))

        # only add words that aren't already there
        to_add = new_related - existing
        # remove self-references
        to_add = {r for r in to_add if normalise(r) != normalise(w['word'])}

        if to_add:
            sorted_additions = sorted(to_add)
            changes.append((w['word'], sorted_additions))
            if not dry_run:
                w['related'] = sorted(existing | to_add)
            total_added += len(to_add)

    if dry_run:
        print(f"\n  DRY RUN — {len(changes)} entries would be updated, {total_added} links added\n")
        print(f"  {'WORD':<35} NEW LINKS")
        print(f"  {'─'*35} {'─'*40}")
        for word, additions in sorted(changes):
            print(f"  {word:<35} + {', '.join(additions)}")
    else:
        print(f"\n  {len(changes)} entries updated, {total_added} links added.")

    return total_added


# ── main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Auto-link related words in words.json")
    parser.add_argument('--db', default='words.json', help='Path to words.json')
    parser.add_argument('--dry-run', action='store_true', help='Preview without saving')
    args = parser.parse_args()

    if not os.path.exists(args.db):
        print(f"Error: {args.db} not found.")
        return

    with open(args.db, encoding='utf-8') as f:
        db = json.load(f)

    print(f"\n  Loaded {len(db)} entries from {args.db}")
    print(f"  Detecting connections...\n")

    connections = find_connections(db)
    total = apply_connections(db, connections, args.dry_run)

    if not args.dry_run and total > 0:
        with open(args.db, 'w', encoding='utf-8') as f:
            json.dump(db, f, ensure_ascii=False, indent=2)
        print(f"  Saved to {args.db}\n")
    elif not args.dry_run:
        print("  No changes needed.\n")

if __name__ == '__main__':
    main()
