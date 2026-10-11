#!/usr/bin/env python3
"""
make_units.py: group the words into learning units for the Anki deck, and write anki/units.txt.

Run once (from the repo root):  python anki/make_units.py
Then edit anki/units.txt by hand if you like (move a word to another unit, rename a unit, change
the order of units). make_deck.py reads it: words are introduced unit by unit, in the order of the
file. Words that are not in the file (added later with vocab.py) come after all units.

How the units are made:
  * one topic per unit group (the word's first topic), everyday concrete topics before abstract ones;
  * words linked as contrast / antonym / synonym stay in the SAME unit, so they meet on the
    "Welches Wort passt?" card at the end of that unit;
  * words without a topic take the topic of a linked word or of their root verb; the rest form
    "Alltag" (core vocabulary) units, placed between the topic units;
  * a root verb never comes after a member of its family (nehmen before mitnehmen);
  * about 20 words per unit (a linked group is never split).
Running it again overwrites units.txt.
"""
import collections
import io
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

TOPIC_ORDER = [
    'home & objects', 'food & drink', 'body & health', 'nature & weather', 'travel & movement',
    'time', 'people & relationships', 'emotions & character', 'work & jobs', 'money & shopping',
    'language & communication', 'technology & media', 'culture & arts', 'materials & physical properties',
    'quantity & comparison', 'change & development', 'thinking & perception', 'goals, effort & outcomes',
    'society & politics', 'science & academia', 'connectors & constructions',
]
ALLTAG = 'Alltag'
UNIT_SIZE = 20
ALLTAG_EVERY = 3          # one Alltag unit after every 3 topic units
SAME_UNIT = ('contrast', 'antonym', 'synonym')


def bare(w):
    return re.sub(r'^sich\s+', '', w).strip()


def main():
    db = json.load(io.open(os.path.join(ROOT, 'words.json'), encoding='utf-8'))
    by_word = collections.defaultdict(list)
    for w in db:
        by_word[w['word']].append(w)
    by_id = {w['id']: w for w in db}

    # 1. linked groups (union-find over contrast / antonym / synonym)
    parent = {w['id']: w['id'] for w in db}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for w in db:
        for r in w.get('related', []):
            if isinstance(r, dict) and r.get('kind') in SAME_UNIT:
                for t in by_word.get(r['word'], []):
                    parent[find(w['id'])] = find(t['id'])
    groups = collections.defaultdict(list)
    for w in db:
        groups[find(w['id'])].append(w)

    # 2. topic of each group: the most common first topic; else via links, family, compound parts
    def own_topic(w):
        return w['topics'][0] if w.get('topics') else None

    def borrowed_topic(w):
        cands = []
        for r in w.get('related', []):
            if isinstance(r, dict):
                cands += [own_topic(t) for t in by_word.get(r['word'], [])]
        fam = (w.get('family_root') or '').strip()
        if fam and bare(fam) != bare(w['word']):
            cands += [own_topic(t) for t in by_word.get(fam, []) + by_word.get('sich ' + fam, [])]
        for p in w.get('compound_parts') or []:
            cands += [own_topic(t) for t in by_word.get(p, [])]
        cands = [c for c in cands if c]
        return collections.Counter(cands).most_common(1)[0][0] if cands else None

    group_topic = {}
    for g, ws in groups.items():
        ts = [own_topic(w) for w in ws if own_topic(w)]
        if not ts:
            ts = [borrowed_topic(w) for w in ws if borrowed_topic(w)]
        group_topic[g] = collections.Counter(ts).most_common(1)[0][0] if ts else ALLTAG

    # 3. units: per topic, groups in a stable order (families together), chunks of ~UNIT_SIZE
    def group_key(ws):
        w = ws[0]
        fam = bare(w.get('family_root') or w['word'])
        return (fam.lower(), bare(w['word']).lower() != fam.lower(), bare(w['word']).lower())
    by_topic = collections.defaultdict(list)
    for g, ws in groups.items():
        by_topic[group_topic[g]].append(sorted(ws, key=lambda w: bare(w['word']).lower()))

    def chunk(topic):
        units, cur = [], []
        for ws in sorted(by_topic.get(topic, []), key=group_key):
            if cur and len(cur) + len(ws) > UNIT_SIZE + 3:
                units.append(cur); cur = []
            cur += ws
        if cur:
            units.append(cur)
        # fold a very small last unit into the previous one
        if len(units) > 1 and len(units[-1]) < 8:
            last = units.pop()
            units[-1] += last
        return [(topic, u) for u in units]

    topic_units = [u for t in TOPIC_ORDER for u in chunk(t)]
    # a topic too small for a unit of its own joins its neighbour (technology & media + culture & arts)
    merged = []
    for t, u in topic_units:
        if merged and (len(u) < 10 or len(merged[-1][1]) < 10) and len(merged[-1][1]) + len(u) <= 30 \
                and merged[-1][0] != t:
            merged[-1] = (merged[-1][0] + ' + ' + t, merged[-1][1] + u)
        else:
            merged.append((t, u))
    topic_units = merged
    alltag_units = chunk(ALLTAG)
    units, a = [], 0
    for i, u in enumerate(topic_units):
        if i % ALLTAG_EVERY == 0 and a < len(alltag_units):
            units.append(alltag_units[a]); a += 1
        units.append(u)
    units += alltag_units[a:]

    # 4. a root verb never after a member of its family: move the root (and its linked group) earlier.
    #    Moving a group can move a family member too (bekommen goes along with geben), so repeat.
    def is_member(x, r):
        return (x is not r and x['type'] == 'verb' and r['type'] == 'verb'
                and bare(x.get('family_root') or '') == bare(r['word']) and bare(x['word']) != bare(r['word']))
    for _ in range(20):
        unit_of = {w['id']: i for i, (_, u) in enumerate(units) for w in u}
        changed = False
        for w in db:
            fam = (w.get('family_root') or '').strip()
            if not fam or bare(fam) == bare(w['word']) or w['type'] != 'verb':
                continue
            for r in by_word.get(fam, []) + by_word.get('sich ' + fam, []):
                if unit_of[r['id']] > unit_of[w['id']]:
                    move = groups[find(r['id'])]
                    src, dst = unit_of[r['id']], unit_of[w['id']]
                    units[src] = (units[src][0], [x for x in units[src][1] if x not in move])
                    at = next(i for i, x in enumerate(units[dst][1]) if x['id'] == w['id'])
                    units[dst][1][at:at] = move          # just before the family member
                    for x in move:
                        unit_of[x['id']] = dst
                    changed = True
        if not changed:
            break
    # ... and within a unit, the root comes before its family members (vertrauen before anvertrauen)
    for _, u in units:
        for _ in range(10):                          # chains: trauen > vertrauen > anvertrauen
            changed = False
            for r in list(u):
                first = next((i for i, x in enumerate(u) if is_member(x, r)), None)
                if first is not None and u.index(r) > first:
                    u.remove(r)
                    u.insert(first, r)
                    changed = True
            if not changed:
                break
    units = [(t, u) for t, u in units if u]

    # 5. write
    dup = {k for k, v in by_word.items() if len(v) > 1}
    count = collections.Counter(t for t, _ in units)
    seen = collections.Counter()
    out = ['# Learning units for the Anki deck (written by make_units.py; edit freely).',
           '# make_deck.py introduces the words unit by unit, in this order. Within a unit: first all',
           '# Bedeutung cards, then Produzieren, then the grammar, and last the consolidation cards',
           '# (Welches Wort passt?, Nebensatz, Komma). Move a line to move a word; a line starting with',
           '# "## " starts a unit (the text after it is only a name). Words missing here come at the end.',
           '# Words that share a spelling are written "word | id".', '']
    for t, u in units:
        seen[t] += 1
        name = t if count[t] == 1 else f'{t} {seen[t]}'
        out.append(f'## {name}')
        for w in u:
            out.append(f"{w['word']} | {w['id']}" if w['word'] in dup else w['word'])
        out.append('')
    io.open(os.path.join(HERE, 'units.txt'), 'w', encoding='utf-8').write('\n'.join(out))
    sizes = [len(u) for _, u in units]
    print(f'{len(units)} units, {sum(sizes)} words, {min(sizes)}-{max(sizes)} words per unit '
          f'-> {os.path.join(HERE, "units.txt")}')


if __name__ == '__main__':
    main()
