#!/usr/bin/env python3
"""
fix_related.py — keep the typed `related` links in words.json consistent.

`related` is a list of {"word": ..., "kind": ...} with kind in
synonym | antonym | contrast | derived.  Verb families are NOT stored here;
they are already encoded by `family_root`.

This script:
  1. drops links whose target is not in the database
  2. makes every link bidirectional, copying the kind
  3. reports words that have no links at all (so you can add some)

Usage:
    python fix_related.py --db words.json --dry-run
    python fix_related.py --db words.json
"""

import argparse
import json
import os
import re

KINDS = {'synonym', 'antonym', 'contrast', 'derived'}


def normalise(word):
    return re.sub(r'^(der|die|das|sich)\s+', '', word.lower().strip()).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default='words.json')
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    if not os.path.exists(args.db):
        print(f'{args.db} not found'); return

    db = json.load(open(args.db, encoding='utf-8'))
    by_word = {w['word']: w for w in db}
    by_norm = {normalise(w['word']): w for w in db}

    dropped, added, legacy = [], [], 0
    for w in db:
        clean = []
        for r in w.get('related', []):
            if isinstance(r, str):            # legacy plain-string link
                legacy += 1
                r = {'word': r, 'kind': 'contrast'}
            tgt = by_word.get(r.get('word', '')) or by_norm.get(normalise(r.get('word', '')))
            if not tgt or tgt['id'] == w['id'] or r.get('kind') not in KINDS:
                dropped.append((w['word'], r.get('word'))); continue
            clean.append({'word': tgt['word'], 'kind': r['kind']})
        w['related'] = clean

    for w in db:
        for r in w['related']:
            tgt = by_word[r['word']]
            if w['word'] not in {x['word'] for x in tgt['related']}:
                tgt['related'].append({'word': w['word'], 'kind': r['kind']})
                added.append((tgt['word'], w['word'], r['kind']))

    for w in db:
        w['related'].sort(key=lambda x: (['contrast', 'antonym', 'synonym', 'derived']
                                         .index(x['kind']), x['word']))

    lonely = [w['word'] for w in db if not w['related']]
    print(f'  {len(db)} entries')
    print(f'  {legacy} legacy string links converted')
    print(f'  {len(dropped)} dangling links dropped')
    for a, b in dropped[:20]:
        print(f'      {a}  ->  {b}')
    print(f'  {len(added)} back-links added')
    print(f'  {len(lonely)} words without any related link')

    if args.dry_run:
        print('  (dry run, nothing written)')
        return
    json.dump(db, open(args.db, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print(f'  saved {args.db}')


if __name__ == '__main__':
    main()
