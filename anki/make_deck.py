#!/usr/bin/env python3
"""
make_deck.py — build the Anki deck from words.json.

Design, so this stays maintainable:

  * ONE registry of exercises (EXERCISES).  Each has a key, a label, a colour
    and a builder function.  Adding an exercise means adding one entry and one
    builder — nothing else changes.

  * EVERY exercise gets the SAME six fields, named <Key>_Frage, _Antwort,
    _Ganz, _GanzEN, _Hinweis, _Quelle.  The field list therefore never shifts around
    when an exercise changes, which was the old problem.

  * Builders return a dict, not a tuple, so a missing key cannot silently
    shift values into the wrong column.

  * This script also WRITES the card templates, the field list and the CSS.
    They are generated from the same registry as the data, so the names in the
    templates can never drift from the names in the file again.

Lives in anki/ next to its output; words.json and lexicon.py are one level up.

Usage (from the repo root):
    python anki/make_deck.py
writes anki/deutsch.apkg (if genanki is installed: pip install genanki), and always
anki/deutsch.txt, anki/templates.md and anki/styling.css.

deutsch.apkg is the easy way: double-click it and Anki creates the note type with all fields,
card types and styling, plus the deck. Importing it again later updates the same notes (each
note's id comes from the word's id in words.json), so your review history is kept.
The .txt + templates.md route does the same by hand.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)                      # lexicon.py lives in the repo root

from lexicon import changes_stem
import argparse
import io
import json
import os
import random
import re

# ── configuration ─────────────────────────────────────────────────────────────

VOICES = 'Apple_Anna_(Premium),com.google.android.tts-de-de-x-nfh-local'

PALETTE = {
    'paper':   '#f7f5f0',
    'ink':     '#1a1a18',
    'ink2':    '#4a4a44',
    'muted':   '#8a8a80',
    'rule':    '#d8d0c4',
    'chip_bg': '#efe9de',
    'chip_br': '#e2dccf',
    'accent':  '#c0392b',   # the revealed answer
    'english': '#6b4ea8',   # purple: never collides with Anki's type colours
    'verb':    ('#dce8f5', '#1a4a72'),
    'noun':    ('#f0e6c4', '#7a5800'),
    'adjadv':  ('#d4eae8', '#1a4a47'),
    'other':   ('#efe9de', '#4a4a44'),
}

CORE_FIELDS = ['Wort', 'Typ', 'Formen', 'Englisch', 'EnglischFrage', 'EnglischKurz',
               'Beispiel', 'BeispielEN', 'Beispiel2', 'Beispiel2EN',
               'Verwandt', 'Notiz']

SLOTS = ['Frage', 'Antwort', 'Ganz', 'GanzEN', 'Hinweis', 'Quelle']

ARTICLES = {'der', 'die', 'das', 'den', 'dem', 'des',
            'ein', 'eine', 'einen', 'einem', 'einer', 'eines'}
POSSESSIVES = {'mein', 'meine', 'meinen', 'meinem', 'meiner',
               'sein', 'seine', 'seinen', 'seinem', 'seiner',
               'ihr', 'ihre', 'ihren', 'ihrem', 'ihrer',
               'kein', 'keine', 'keinen', 'keinem', 'keiner',
               'dieser', 'diese', 'dieses', 'diesen', 'diesem'}
DETERMINERS = ARTICLES | POSSESSIVES
SUB_CONJ = ['weil', 'dass', 'obwohl', 'wenn', 'damit', 'während', 'bevor',
            'nachdem', 'sobald', 'falls', 'ob', 'seitdem']
PUNCT = '.,:;!?»«""„“()'


# ── small helpers ─────────────────────────────────────────────────────────────

def esc(s):
    return (s or '').replace('\t', ' ').replace('\n', ' ').strip()


def bare(word):
    return re.sub(r'^(der|die|das|sich)\s+', '', (word or '')).strip()


def strip_punct(tok):
    return tok.strip(PUNCT)


def chips(items, cls='chip'):
    return ' '.join('<span class="%s">%s</span>' % (cls, str(c).replace('&', '&amp;'))
                    for c in items if c)


def blank_phrase(sentence, phrase):
    """Replace phrase with a gap, one gap per word it contained."""
    gap = ' '.join(['___'] * len(phrase.split()))
    return sentence.replace(phrase, gap, 1)


# ── the three descriptive fields ──────────────────────────────────────────────

USAGE_LABEL = {
    'both': 'Adjektiv und Adverb',
    'adjective only': 'nur Adjektiv',
    'adverb only': 'nur Adverb',
    'preposition only': 'nur Präposition',
    'conjunction only': 'nur Konjunktion',
}


VERB_CLASS_LABEL = {'regular': 'regelmäßig', 'irregular': 'unregelmäßig', 'mixed': 'gemischt'}


def formen(w):
    t, out = w.get('type'), []
    if t == 'noun':
        out.append('Pl: ' + (w.get('plural') or 'kein Plural'))
    if w.get('compound_parts'):
        parts = [re.sub(r'^(der|die|das|der/die)\s+', '', x) for x in w['compound_parts']]
        out.append(' + '.join(parts))
    elif t == 'verb':
        if w.get('verb_class'):
            out.append(VERB_CLASS_LABEL.get(w['verb_class'], w['verb_class']))
        if changes_stem(w['word'], w.get('present_3sg'), w.get('prefix'), w.get('is_separable')):
            out.append('er ' + w['present_3sg'])
        if w.get('imperative'):
            out.append(w['imperative'] + '!')
        if w.get('past_tense'):
            out.append(w['past_tense'])
        if w.get('past_participle'):
            aux = {'haben': 'hat', 'sein': 'ist'}.get(w.get('auxiliary'), '')
            out.append((aux + ' ' + w['past_participle']).strip())
        elif w.get('auxiliary'):
            out.append(w['auxiliary'])
        if w.get('konjunktiv_2'):
            out.append('Konj. II: ' + w['konjunktiv_2'])
        if w.get('is_separable'):
            out.append('trennbar')
        if w.get('reflexive'):
            out.append({'dat': 'sich + Dat.'}.get(w['reflexive'], 'sich + Akk.'))
        if w.get('preposition'):
            out.append(w['preposition'])
        fam = (w.get('family_root') or '').strip()
        if fam and fam.lower() not in (bare(w['word']).lower(), w['word'].lower()):
            out.append('Familie: ' + fam)
    elif t in ('adj/adv', 'prep/conj'):
        if w.get('usage'):
            out.append(USAGE_LABEL.get(w['usage'], w['usage']))
        if w.get('derived_from'):
            out.append('von ' + w['derived_from'])
    return chips(out)


def englisch(w):
    defs = w.get('definitions', [])
    lines = []
    for i, d in enumerate(defs, 1):
        m = (d.get('meaning') or '').strip()
        n = d.get('note')
        lines.append((f'{i}. ' if len(defs) > 1 else '')
                     + m + (f' <i>({n})</i>' if n else ''))
    return '<br>'.join(lines)


GAP = '<span class="gap">___</span>'
SMALL = {'auf', 'an', 'aus', 'bei', 'für', 'mit', 'nach', 'über', 'um', 'von', 'vor', 'zu', 'in', 'ab', 'ein',
         'der', 'die', 'das', 'den', 'dem', 'des', 'sich', 'etw', 'jmdn', 'jmdm', 'jdn', 'jdm', 'es'}


def word_forms(w):
    """Lower-case spellings of the word itself (endings included), to hide it on the English side."""
    base = re.sub(r'^(sich|der|die|das)\s+', '', w['word'].strip(), flags=re.I)
    toks = [t for t in re.findall(r"[\wäöüß]+", base.lower()) if t not in SMALL and len(t) > 2]
    for k in ('past_tense', 'past_participle', 'present_3sg', 'imperative', 'plural'):
        for v in re.split(r'[\s/,]+', str(w.get(k) or '').lower()):
            if len(v) > 2 and v not in SMALL and v != '-':
                toks.append(v.lstrip('-'))
    forms = set(toks)
    t = w.get('type')
    for tok in toks[:1] if toks else []:
        if t == 'verb':
            pfx = (w.get('prefix') or '').strip('-').lower() if w.get('is_separable') else ''
            stems = {re.sub(r'e?n$', '', tok)}
            if pfx and tok.startswith(pfx):
                stems.add(re.sub(r'e?n$', '', tok[len(pfx):]))
                forms.add(pfx + 'zu' + tok[len(pfx):])
            for st in stems:
                forms |= {st + e for e in ('', 'e', 'st', 't', 'en', 'et', 'est', 'te', 'test', 'ten', 'tet', 'end')}
        elif t == 'noun':
            forms |= {tok + e for e in ('s', 'es', 'n', 'en', 'e', 'er', 'ern')}
        else:
            forms |= {tok + e for e in ('e', 'en', 'er', 'es', 'em')}
    return {f for f in forms if len(f) > 2}


def hide_word(text, forms):
    """The word, its forms, and the word inside a longer word (krankheits___, Regen___, die ___in)."""
    longer = sorted((f for f in forms if len(f) >= 4), key=len, reverse=True)

    def rep(m):
        t = m.group()
        low = t.lower()
        if low in forms:
            return GAP
        for f in longer:
            i = low.find(f)
            if i >= 0 and len(low) > len(f) + 1:
                return t[:i] + GAP + t[i + len(f):]
        return t
    return re.sub(r"[\wäöüß]+", rep, text)


def englisch_frage(w):
    """Englisch for the Produzieren front: the German word itself is hidden (___) where it appears in
    a German phrase of a meaning ("den Tisch decken: to set the table") or in a note
    ("e.g. Ich bin gerade zurückgekommen"). Plain English meanings are left alone (stehen: "to stand")."""
    forms = word_forms(w)
    defs = w.get('definitions', [])
    lines = []
    for i, d in enumerate(defs, 1):
        m = (d.get('meaning') or '').strip()
        sep = re.search(r'\s[—–]\s|:\s|\s=\s', m)
        if sep:
            m = hide_word(m[:sep.start()], forms) + m[sep.start():]
        n = d.get('note')
        lines.append((f'{i}. ' if len(defs) > 1 else '')
                     + m + (f' <i>({hide_word(n, forms)})</i>' if n else ''))
    return '<br>'.join(lines)


def englisch_kurz(w):
    """One short, typeable answer: first meaning, first alternative."""
    m = ''
    for d in w.get('definitions', []):
        m = (d.get('meaning') or '').strip()
        if m:
            break
    if not m:
        return ''
    m = re.sub(r'\s*\([^)]*\)?\s*$', '', m)
    m = re.sub(r'\s*\([^)]*\)\s*', ' ', m)
    m = re.split(r'\s+[—–-]\s+', m)[0]
    m = re.split(r'[,;/]|\s+or\s+', m)[0].strip()
    if w.get('type') == 'verb':
        m = re.sub(r'^to\s+', '', m, flags=re.I)
    elif w.get('type') == 'noun':
        m = re.sub(r'^(the|a|an)\s+', '', m, flags=re.I)
    m = m.replace('…', '...')
    m = re.sub(r'\s*\.\.\.\s*', ' ... ', m)       # one consistent spacing
    return re.sub(r'\s{2,}', ' ', m).strip()


# ── exercise builders ─────────────────────────────────────────────────────────
# Each returns a dict with the keys Frage, Antwort, Ganz, GanzEN, Hinweis,
# or None when the word's data does not support that exercise.

# Sentence exercises come from the `exercises` field of words.json (checked by exercise_check.py);
# these builders only turn one of them into card fields.

CASE_DE = {'NOM': 'Nominativ', 'AKK': 'Akkusativ', 'DAT': 'Dativ', 'GEN': 'Genitiv'}


def gaps(ex):
    """The sentence with one ___ per hidden word, and the hidden words."""
    out, last, answers = '', 0, []
    for a, b in ex['blanks']:
        out += ex['de'][last:a] + '___'
        answers.append(ex['de'][a:b])
        last = b
    return out + ex['de'][last:], answers


def from_exercise(w, slot, hint):
    ex = next((e for e in w.get('exercises', []) if e['slot'] == slot and e.get('blanks')), None)
    if not ex:
        return None
    frage, answers = gaps(ex)
    ganz, last = '', 0
    for a, b in ex['blanks']:
        ganz += ex['de'][last:a] + '<span class="hl">' + ex['de'][a:b] + '</span>'
        last = b
    ganz += ex['de'][last:]
    if len(answers) > 1:
        hint = (hint + ' · ' if hint else '') + f'{len(answers)} Lücken, mit Leerzeichen'
    src = ex.get('source', '')
    quelle = ''
    if src.startswith('tatoeba:'):
        sid = src.split(':', 1)[1]
        quelle = (f'Satz von <a href="https://tatoeba.org/en/sentences/show/{sid}">Tatoeba #{sid}</a> '
                  '(CC BY 2.0 FR)')
    return dict(Frage=frage, Antwort=' '.join(answers), Ganz=ganz, GanzEN=ex.get('en', ''),
                Hinweis=hint, Quelle=quelle)


def meaning_hint(w):
    d = (w.get('definitions') or [{}])[0].get('meaning', '')
    return 'Bedeutung: ' + d if d else ''


def ex_slot(slot):
    def build(w, ctx):
        if slot in ('praet', 'praes'):
            return from_exercise(w, slot, w['word'])
        if slot == 'part':                         # auxiliary and participle: [ist] … [gereist]
            return from_exercise(w, slot, w['word'] + ' · Hilfsverb + Partizip II')
        if slot == 'refl':
            return from_exercise(w, slot, w['word'] + (' (Dativ)' if w.get('reflexive') == 'dat' else ' (Akkusativ)'))
        if slot.startswith('dekl'):
            # the whole phrase (determiner + adjective + noun) is one gap; the hint gives the case
            # and number, the noun and the adjective in their dictionary forms
            ex = next((e for e in w.get('exercises', []) if e['slot'] == slot), None)
            c, n = ((ex or {}).get('form') or ':').split(':')
            label = f"{CASE_DE.get(c, c)} {'Plural' if n == 'PLU' else 'Singular'}"
            adj = (ex or {}).get('adj') or ''
            got = from_exercise(w, slot, f'{label} · {w["word"]}' + (f' · {adj}' if adj else ''))
            if got:
                got['Frage'] = got['Frage'].replace('___', '______', 1)       # a longer gap for a phrase
            return got
        if slot.startswith('prep'):
            ex = next((e for e in w.get('exercises', []) if e['slot'] == slot), None)
            case = ((ex or {}).get('form') or '+').split('+')[1].strip()
            return from_exercise(w, slot, f"{w['word']} · Präposition + Artikel ({CASE_DE.get(case, case)})")
        # Konnektor n: preposition/conjunction. The word itself would give the answer away, so the
        # hint is its meaning.
        return from_exercise(w, 'pc' + slot[-1], meaning_hint(w))
    return build


def ex_nebensatz(w, ctx):
    for ex in w.get('examples', []):
        s = ex['de']
        m = re.search(r'\b(' + '|'.join(SUB_CONJ) + r')\b', s, re.I)
        if not m:
            continue
        clause = re.split(r'[,.!?;]', s[m.start():])[0].strip()
        toks = clause.split()
        if not (4 <= len(toks) <= 9):
            continue
        shuffled = toks[:]
        for _ in range(12):
            ctx['rng'].shuffle(shuffled)
            if shuffled != toks:
                break
        return dict(Frage=' / '.join(shuffled), Antwort=clause, Ganz=s,
                    GanzEN=ex.get('en', ''), Hinweis='Wo steht das Verb?')
    return None


def ex_kontrast(w, ctx):
    """One confusable partner, the word blanked together with its determiner."""
    partners = [x['word'] for x in w.get('related', [])
                if isinstance(x, dict) and x['kind'] in ('contrast', 'antonym')
                and ctx['by_word'].get(x['word'], {}).get('type') == w.get('type')]
    if not partners:
        return None

    stem = bare(w['word'])[:max(4, len(bare(w['word'])) - 3)].lower()
    for ex in w.get('examples', []):
        toks = ex['de'].split()
        for i, tok in enumerate(toks):
            cand = strip_punct(tok)
            if len(cand) < 4 or not cand.lower().startswith(stem):
                continue
            prev = strip_punct(toks[i - 1]) if i > 0 else ''
            prev2 = strip_punct(toks[i - 2]) if i > 1 else ''
            frage = None
            if prev.lower() in DETERMINERS:
                phrase = toks[i - 1] + ' ' + tok
                antwort = prev + ' ' + cand
            elif w.get('type') == 'noun' and prev[:1].islower() \
                    and re.search(r'(e|en|em|er|es)$', prev) \
                    and (prev2.lower() in DETERMINERS
                         or prev.lower() in ('viele', 'vielen', 'wenige', 'einige', 'mehrere',
                                             'andere', 'beide', 'alle', 'manche')):
                # "ein ausgezeichnetes Gedächtnis": the adjective ending would give the
                # gender away, so article + adjective + noun are blanked together and
                # the adjective is shown in its base form.
                base = re.sub(r'(en|em|er|es|e)$', '', prev)
                start = i - 2 if prev2.lower() in DETERMINERS else i - 1
                phrase = ' '.join(toks[start:i + 1])
                antwort = ' '.join(strip_punct(t) for t in toks[start:i + 1])
                blanks = '___ ' if start == i - 2 else ''
                tail = tok[len(tok.rstrip('.,;:!?')):]          # keep "." after the noun
                frage = ex['de'].replace(phrase, f'{blanks}({base}) ___{tail}', 1)
            else:
                phrase, antwort = tok, cand
            # options without articles: the article would be a second giveaway
            opts = [bare(w['word']), bare(partners[0])]
            ctx['rng'].shuffle(opts)
            return dict(Frage=frage or blank_phrase(ex['de'], phrase), Antwort=antwort,
                        Ganz=ex['de'], GanzEN=ex.get('en', ''),
                        Hinweis='  /  '.join(opts))
    return None


# ── the registry ──────────────────────────────────────────────────────────────
# key, German label shown on the card, pill colour, builder, front hint

EXERCISES = [
    ('Praet',    'Präteritum',             'verb',   ex_slot('praet'),  ''),
    ('Part',     'Perfekt',                'verb',   ex_slot('part'),   ''),
    ('Praes',    'Präsens (er/sie/es)',    'verb',   ex_slot('praes'),  ''),
    ('Refl',     'Reflexivpronomen',       'verb',   ex_slot('refl'),   ''),
    ('Dekl',     'Deklination',            'noun',   ex_slot('dekl'),   ''),
    ('DeklPl',   'Deklination Plural',     'noun',   ex_slot('dekl_pl'), ''),
    ('Praep1',   'Präposition',            'other',  ex_slot('prep1'),  ''),
    ('Praep2',   'Präposition 2',          'other',  ex_slot('prep2'),  ''),
] + [
    (f'Konnektor{n}', f'Konnektor {n}',   'other',  ex_slot(f'gap{n}'), '') for n in range(1, 5)
] + [
    ('Kontrast', 'Welches Wort passt?',    'other',  ex_kontrast,    ''),
    ('Neben',    'Nebensatz: Wortstellung', 'other', ex_nebensatz,   ''),
]
# sentence exercises: the hint (word, case, meaning) is in the _Hinweis field, shown on the front
SENTENCE_KEYS = {'Praet', 'Part', 'Praes', 'Refl', 'Dekl', 'DeklPl',
                 'Praep1', 'Praep2'} | {f'Konnektor{n}' for n in range(1, 5)}

# card order within a word: first recognise it (Bedeutung), then produce it (Produzieren), then
# its grammar, and last the cards that need it to be known well (contrast, word order)
CARD_ORDER = ['Bedeutung', 'Produzieren',
              'Praes', 'Refl', 'Praep1', 'Praep2', 'Part', 'Praet',
              'Dekl', 'DeklPl', 'Konnektor1', 'Konnektor2', 'Konnektor3', 'Konnektor4',
              'Kontrast', 'Neben']
assert sorted(CARD_ORDER) == sorted([k for k, *_ in EXERCISES] + ['Bedeutung', 'Produzieren'])


def all_fields():
    f = list(CORE_FIELDS)
    for key, *_ in EXERCISES:
        f += [f'{key}_{slot}' for slot in SLOTS]
    return f


# ── note building ─────────────────────────────────────────────────────────────

def build_note(w, ctx):
    r = {f: '' for f in all_fields()}
    exs = w.get('examples', [])
    r['Wort'] = w['word']
    r['Typ'] = w.get('type', '')
    r['Formen'] = formen(w)
    r['Englisch'] = englisch(w)
    r['EnglischFrage'] = englisch_frage(w)
    r['EnglischKurz'] = englisch_kurz(w)
    if exs:
        r['Beispiel'] = exs[0].get('de', '')
        r['BeispielEN'] = exs[0].get('en', '')
    if len(exs) > 1:
        r['Beispiel2'] = exs[1].get('de', '')
        r['Beispiel2EN'] = exs[1].get('en', '')
    KIND_MARK = {'contrast': 'vs. ', 'antonym': '≠ ', 'synonym': '= ', 'derived': '← ', 'compound': '+ '}
    r['Verwandt'] = chips([KIND_MARK.get(x['kind'], '') + x['word']
                           for x in w.get('related', []) if isinstance(x, dict)], 'chip rel')
    r['Notiz'] = w.get('notes') or ''

    made = []
    for key, label, pill, builder, hint in EXERCISES:
        got = builder(w, ctx)
        if not got:
            continue
        if key == 'Kontrast' and got.get('Antwort') and 'class="hl"' not in got.get('Ganz', ''):
            got['Ganz'] = got['Ganz'].replace(got['Antwort'], f'<span class="hl">{got["Antwort"]}</span>', 1)
        for slot in SLOTS:
            r[f'{key}_{slot}'] = got.get(slot, '')
        made.append(key)

    tags = [w.get('type', 'other').replace('/', '-')]
    tags += [t.replace(' ', '-').replace('&', 'und') for t in w.get('topics', [])]
    tags += ['uebung::' + k.lower() for k in made]
    return r, tags, made


# ── introduction order ────────────────────────────────────────────────────────

def spread(rows):
    """Keep semantically adjacent words apart when they are introduced."""
    def key(r):
        return set(r['_topics']) | set(r['_family']) | set(r['_related'])
    rest, out = list(rows), []
    out.append(rest.pop(0))
    while rest:
        last = key(out[-1])
        prev = key(out[-2]) if len(out) > 1 else set()
        pick = next((i for i, r in enumerate(rest)
                     if not (key(r) & last) and not (key(r) & prev)), None)
        if pick is None:
            pick = next((i for i, r in enumerate(rest) if not (key(r) & last)), 0)
        out.append(rest.pop(pick))
    return out


# ── output: data file ─────────────────────────────────────────────────────────

def write_data(path, rows, fields):
    with io.open(path, 'w', encoding='utf-8') as f:
        f.write('#separator:tab\n#html:true\n#notetype:Deutsch\n#deck:Deutsch\n')
        f.write('#columns:' + '\t'.join(fields + ['Tags']) + '\n')
        f.write(f'#tags column:{len(fields) + 1}\n')
        for r, tags in rows:
            f.write('\t'.join([esc(r[c]) for c in fields] + [' '.join(tags)]) + '\n')


# ── output: templates, generated from the same registry ───────────────────────

def tts(field):
    return '{{tts de_DE voices=%s:%s}}' % (VOICES, field)


def block(label, inner, field=None):
    """A labelled section of the back; with `field`, only shown when that field has content."""
    b = f'<div class="block"><div class="label">{label}</div>{inner}</div>'
    return '{{#%s}}%s{{/%s}}' % (field, b, field) if field else b


def word_block(with_examples=True, with_meaning=True):
    """The shared lower part of every back: meaning, forms, examples, related words, note."""
    b = []
    if with_meaning:
        b.append(block('Bedeutung', '<div class="en">{{Englisch}}</div>', 'Englisch'))
    b.append(block('Formen', '<div class="chips">{{Formen}}</div>', 'Formen'))
    if with_examples:
        b.append(block('Beispiele',
                       '<div class="bsp">{{Beispiel}} ' + tts('Beispiel') + '</div>'
                       '{{#BeispielEN}}<div class="en2">{{BeispielEN}}</div>{{/BeispielEN}}'
                       '{{#Beispiel2}}<div class="bsp">{{Beispiel2}} ' + tts('Beispiel2') + '</div>{{/Beispiel2}}'
                       '{{#Beispiel2EN}}<div class="en2">{{Beispiel2EN}}</div>{{/Beispiel2EN}}', 'Beispiel'))
    b.append(block('Verwandt', '<div class="chips">{{Verwandt}}</div>', 'Verwandt'))
    b.append('{{#Notiz}}<div class="notiz">{{Notiz}}</div>{{/Notiz}}')
    return '\n'.join(b)


def card(*parts):
    return '<div class="karte">\n' + '\n'.join(parts) + '\n</div>'


def templates():
    out = {}

    out['Bedeutung'] = (
        card('<div class="kopf">Bedeutung <span class="pill other">{{Typ}}</span></div>',
             '<div class="wort">{{Wort}}</div>',
             '<div class="hinweis">kurze englische Bedeutung</div>',
             '{{type:EnglischKurz}}'),
        card('<div class="kopf">Bedeutung <span class="pill other">{{Typ}}</span></div>',
             '<div class="wort">{{Wort}}</div>',
             '<hr id=answer>',
             '{{type:EnglischKurz}}',
             word_block()))

    out['Produzieren'] = (
        card('<div class="kopf">Produzieren <span class="pill other">{{Typ}}</span></div>',
             '<div class="en gross">{{EnglischFrage}}</div>',
             '<div class="hinweis">Nomen mit Artikel</div>',
             '{{type:Wort}}'),
        card('<div class="kopf">Produzieren <span class="pill other">{{Typ}}</span></div>',
             '<div class="en gross">{{Englisch}}</div>',
             '<hr id=answer>',
             '{{type:Wort}}',
             word_block(with_meaning=False)))

    for key, label, pill, _builder, hint in EXERCISES:
        F, A = f'{key}_Frage', f'{key}_Antwort'
        G, GE, H, Q = f'{key}_Ganz', f'{key}_GanzEN', f'{key}_Hinweis', f'{key}_Quelle'
        title = label.rstrip(' 0123456789') if key in SENTENCE_KEYS else label
        head = f'<div class="kopf">{title} <span class="pill {pill}">{{{{Typ}}}}</span></div>'
        en_front = '{{#%s}}<div class="en2">{{%s}}</div>{{/%s}}' % (GE, GE, GE)
        # front: what is asked, then the hint, then the box
        front = ['{{#%s}}' % F, head, '<div class="satz">{{%s}}</div>' % F]
        if key in SENTENCE_KEYS:
            front += [en_front, '<div class="hinweis">{{%s}}</div>' % H]
        elif key == 'Kontrast':
            front.append('{{#%s}}<div class="hinweis">{{%s}}</div>{{/%s}}' % (H, H, H))
        else:
            if hint:
                front.append('<div class="hinweis">%s</div>' % hint)
            front.append('<div class="hinweis">{{Wort}}</div>')
        front += ['{{type:%s}}' % A, '{{/%s}}' % F]
        # back: the word, the typed answer, the full sentence with the answer marked, then the rest
        back = [head, '<div class="wort">{{Wort}}</div>', '<hr id=answer>', '{{type:%s}}' % A,
                '<div class="satz">{{%s}} %s</div>' % (G, tts(G)),
                en_front,
                word_block(with_examples=False),
                '{{#%s}}<div class="quelle">{{%s}}</div>{{/%s}}' % (Q, Q, Q)]
        out[key] = (card(*front), card(*back))
    return out


def write_templates(path, fields):
    t = templates()
    labels = {k: label for k, label, *_ in EXERCISES}
    labels.update(Produzieren='Produzieren', Bedeutung='Bedeutung')
    with io.open(path, 'w', encoding='utf-8') as f:
        f.write('# Card templates (generated — do not edit by hand)\n\n')
        f.write('Note type: **Deutsch**. Create the %d fields in exactly this '
                'order, then one card type per section below, named as in the heading, '
                'and paste its front and back.\n\n' % len(fields))
        f.write('## Fields\n\n```\n' + ', '.join(fields) + '\n```\n\n')
        f.write('Tags are column %d.\n\n' % (len(fields) + 1))
        for i, key in enumerate(CARD_ORDER, 1):
            tpl = t.get(key)
            if not tpl:
                continue
            f.write(f'## {i} — {labels[key]}\n\n**Front**\n```html\n{tpl[0]}\n```\n\n'
                    f'**Back**\n```html\n{tpl[1]}\n```\n\n')


def write_css(path):
    p = PALETTE
    css = f""".card {{
  font-family: Georgia, 'Iowan Old Style', serif;
  font-size: 20px; text-align: center; line-height: 1.45;
  background: {p['paper']}; color: {p['ink']}; padding: 24px 16px;
}}
.card.nightMode, .nightMode .card {{ background: {p['paper']}; color: {p['ink']}; }}
.karte {{ max-width: 620px; margin: 0 auto; }}

/* header: what kind of card, and the word type */
.kopf {{ font-family: -apple-system, Helvetica, sans-serif; font-size: 11px;
        letter-spacing: .1em; text-transform: uppercase; color: {p['muted']};
        margin-bottom: 20px; }}
.pill {{ display: inline-block; padding: 2px 9px; border-radius: 10px; margin-left: 6px;
        font-size: 10px; letter-spacing: .08em; }}
.verb   {{ background: {p['verb'][0]};   color: {p['verb'][1]}; }}
.noun   {{ background: {p['noun'][0]};   color: {p['noun'][1]}; }}
.adjadv {{ background: {p['adjadv'][0]}; color: {p['adjadv'][1]}; }}
.other  {{ background: {p['other'][0]};  color: {p['other'][1]}; }}

/* the main content */
.wort   {{ font-size: 32px; font-weight: 600; letter-spacing: -.01em; }}
.satz   {{ font-size: 22px; line-height: 1.5; margin: 16px 0 4px 0; }}
.hl     {{ font-weight: 600; color: {p['ink']};
          border-bottom: 2px solid {p['accent']}; padding: 0 1px; }}
.en2    {{ color: {p['english']}; font-size: 15px; font-style: italic; opacity: .9;
          margin-bottom: 6px; }}
.en     {{ color: {p['english']}; font-size: 16px; line-height: 1.5; }}
.en.gross {{ font-size: 22px; line-height: 1.4; }}
.gap    {{ font-style: normal; color: {p['muted']}; letter-spacing: .05em; }}
.hinweis {{ font-family: -apple-system, Helvetica, sans-serif; font-size: 13px;
           color: {p['muted']}; margin: 10px 0 14px 0; }}
hr#answer {{ border: none; border-top: 1px solid {p['rule']}; margin: 20px 0 16px 0; }}

/* the typed answer and Anki's comparison */
input#typeans {{ font-family: ui-monospace, Menlo, monospace; font-size: 18px; text-align: center;
                width: 80%; max-width: 360px; padding: 8px 10px; border: 1px solid {p['rule']};
                border-radius: 6px; background: #fdfcf8; color: {p['ink']}; }}
code#typeans {{ font-family: ui-monospace, Menlo, monospace; font-size: 18px; }}
.typeGood   {{ background: #d4eae8; color: #1a4a47; }}
.typeBad    {{ background: #e8d5d0; color: #c0392b; }}
.typeMissed {{ background: #e9e4d6; color: #6a6356; }}

/* the lower part of the back: labelled sections */
.block  {{ margin-top: 18px; padding-top: 12px; border-top: 1px solid {p['chip_br']}; }}
.label  {{ font-family: -apple-system, Helvetica, sans-serif; font-size: 10px;
          letter-spacing: .12em; text-transform: uppercase; color: {p['muted']};
          margin-bottom: 8px; }}
.chips  {{ line-height: 2.2; }}
.chip   {{ display: inline-block;
          font-family: ui-monospace, Menlo, monospace; font-size: 13px;
          background: {p['chip_bg']}; color: {p['ink2']};
          border: 1px solid {p['chip_br']}; border-radius: 4px;
          padding: 3px 8px; margin: 0 2px; }}
.chip.rel {{ font-family: Georgia, serif; font-size: 14px; background: transparent;
            border-radius: 12px; border-color: {p['rule']}; }}
.bsp    {{ font-size: 17px; line-height: 1.5; margin-top: 4px; }}
.notiz  {{ font-family: -apple-system, Helvetica, sans-serif; font-size: 13px;
          color: {p['muted']}; font-style: italic; margin-top: 16px; }}
.quelle {{ font-family: -apple-system, Helvetica, sans-serif; font-size: 11px;
          color: {p['muted']}; margin-top: 10px; }}
.quelle a {{ color: {p['muted']}; }}
.loesung {{ color: {p['accent']}; font-weight: 600; }}

/* Anki's play button: small, next to the sentence */
.replay-button svg {{ width: 22px; height: 22px; vertical-align: -3px; }}
.replay-button svg circle {{ fill: {p['chip_bg']}; stroke: {p['rule']}; }}
.replay-button svg path {{ fill: {p['ink2']}; }}
"""
    io.open(path, 'w', encoding='utf-8').write(css)
    return css


# ── output: a ready-to-import Anki package ────────────────────────────────────
# Fixed ids: Anki recognises the note type and the deck again on every new import.
MODEL_ID = 1728311904
DECK_ID = 1728311905


def write_apkg(path, rows, fields, css):
    try:
        import genanki
    except ImportError:
        return False
    t = templates()
    labels = {k: label for k, label, *_ in EXERCISES}
    labels.update(Produzieren='Produzieren', Bedeutung='Bedeutung')
    model = genanki.Model(
        MODEL_ID, 'Deutsch',
        fields=[{'name': f} for f in fields],
        templates=[{'name': labels[k], 'qfmt': t[k][0], 'afmt': t[k][1]} for k in CARD_ORDER if k in t],
        css=css)
    deck = genanki.Deck(DECK_ID, 'Deutsch')
    for r, tags in rows:
        deck.add_note(genanki.Note(model=model, fields=[esc(r[c]) for c in fields],
                                   tags=tags, guid=genanki.guid_for('deutsch', r['_id'])))
    genanki.Package(deck).write_to_file(path)
    return True


# ── introduction order: learning units (anki/units.txt) ───────────────────────
# New cards are shown in the order of their position ("due" in Anki). Words in units.txt are
# introduced unit by unit; within a unit first all Bedeutung cards, then all Produzieren cards,
# then the grammar (in CARD_ORDER), and last the consolidation cards. A contrast card waits until
# both words of the pair have been introduced. Words not in units.txt (added later) follow, in
# the same pattern, in groups of 20.

CONSOLIDATION = ['Kontrast', 'Neben']


def read_units(path, db):
    """{word id: (unit number, place in unit)} from units.txt; words are matched by spelling,
    or by id after '|' when a spelling is shared."""
    if not os.path.exists(path):
        return {}, 0
    by_word = {}
    for w in db:
        by_word.setdefault(w['word'], []).append(w['id'])
    ids = {w['id'] for w in db}
    out, unit, place = {}, -1, 0
    for line in io.open(path, encoding='utf-8'):
        line = line.rstrip('\n')
        if line.startswith('## '):
            unit += 1; place = 0
            continue
        if not line.strip() or line.startswith('#') or unit < 0:
            continue
        word, _, wid = [x.strip() for x in line.partition('|')]
        wid = wid if wid in ids else (by_word.get(word) or [None])[0]
        if wid and wid not in out:
            out[wid] = (unit, place); place += 1
        elif not wid:
            print(f'  units.txt: "{word}" is not in words.json, skipped')
    return out, unit + 1


def card_positions(rows, units, n_units):
    """{(word id, card key): position}, for every card a note will have."""
    unit_of = dict(units)
    extra = [r['_id'] for r, _ in rows if r['_id'] not in unit_of]
    for i, wid in enumerate(extra):                    # later additions: groups of 20 after the units
        unit_of[wid] = (n_units + i // 20, i % 20)
    order = {k: i for i, k in enumerate(CARD_ORDER)}
    keys = []
    for r, _ in rows:
        u, place = unit_of[r['_id']]
        for k in CARD_ORDER:
            if k in ('Bedeutung', 'Produzieren'):
                phase, uu = (0 if k == 'Bedeutung' else 1), u
            elif k in CONSOLIDATION:
                phase, uu = 3, u
                if k == 'Kontrast' and r.get('_partner') in unit_of:
                    uu = max(u, unit_of[r['_partner']][0])
            else:
                phase, uu = 2, u
            keys.append(((uu, phase, order[k], place), (r['_id'], k)))
    return {card: i for i, (_, card) in enumerate(sorted(keys))}


def set_positions(path, rows, positions):
    """Write the positions into the package: it is a zip with an SQLite collection inside."""
    import sqlite3, tempfile, zipfile, hashlib
    keys = [k for k in CARD_ORDER if k in templates()]
    tmp = tempfile.mkdtemp()
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        z.extractall(tmp)
    db = sqlite3.connect(os.path.join(tmp, 'collection.anki2'))
    guid_of = {}
    import genanki
    for r, _ in rows:
        guid_of[genanki.guid_for('deutsch', r['_id'])] = r['_id']
    nid_to_id = {nid: guid_of.get(g) for nid, g in db.execute('select id, guid from notes')}
    for cid, nid, ord_ in db.execute('select id, nid, ord from cards').fetchall():
        pos = positions.get((nid_to_id.get(nid), keys[ord_]))
        if pos is not None:
            db.execute('update cards set due = ? where id = ?', (pos, cid))
    db.commit(); db.close()
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        for n in names:
            z.write(os.path.join(tmp, n), n)


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default=os.path.join(ROOT, 'words.json'))
    ap.add_argument('--out-dir', default=HERE)
    ap.add_argument('--no-spread', action='store_true',
                    help='keep database order instead of separating similar words')
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    db = json.load(io.open(args.db, encoding='utf-8'))
    ctx = {'rng': random.Random(42),
           'by_word': {w['word']: w for w in db}}

    fields = all_fields()
    rows, counts = [], {k: 0 for k, *_ in EXERCISES}
    for w in db:
        r, tags, made = build_note(w, ctx)
        for k in made:
            counts[k] += 1
        r['_id'] = w['id']
        partners = [x['word'] for x in w.get('related', [])
                    if isinstance(x, dict) and x['kind'] in ('contrast', 'antonym')
                    and ctx['by_word'].get(x['word'], {}).get('type') == w.get('type')]
        r['_partner'] = ctx['by_word'][partners[0]]['id'] if partners else None
        r['_topics'] = w.get('topics', [])
        r['_family'] = [w['family_root']] if w.get('family_root') else []
        r['_related'] = [x['word'] for x in w.get('related', []) if isinstance(x, dict)]
        rows.append((r, tags))

    if not args.no_spread:
        ordered = spread([r for r, _ in rows])
        index = {id(r): i for i, r in enumerate(ordered)}
        rows.sort(key=lambda rt: index[id(rt[0])])

    data = os.path.join(args.out_dir, 'deutsch.txt')
    write_data(data, rows, fields)
    write_templates(os.path.join(args.out_dir, 'templates.md'), fields)
    css = write_css(os.path.join(args.out_dir, 'styling.css'))
    apkg = write_apkg(os.path.join(args.out_dir, 'deutsch.apkg'), rows, fields, css)
    units, n_units = read_units(os.path.join(HERE, 'units.txt'), db)
    if apkg:
        set_positions(os.path.join(args.out_dir, 'deutsch.apkg'), rows,
                      card_positions(rows, units, n_units))
        print(f'Reihenfolge: {n_units} Lerneinheiten aus units.txt'
              + (f', {sum(1 for r, _ in rows if r["_id"] not in units)} weitere Wörter danach' if units else ''))

    base = len(rows) * 2
    print(f'{len(rows)} Notizen, {len(fields)} Felder, Tags = Spalte {len(fields)+1}')
    print(f'  Bedeutung + Produzieren : {base}')
    for key, label, *_ in EXERCISES:
        print(f'  {label:<24}: {counts[key]}')
    print(f'  insgesamt               : {base + sum(counts.values())}')
    print(f'\ngeschrieben nach {args.out_dir}/: ' + ('deutsch.apkg, ' if apkg else '')
          + 'deutsch.txt, templates.md, styling.css')
    if not apkg:
        print('(für deutsch.apkg, das Anki direkt importiert: pip install genanki)')


if __name__ == '__main__':
    main()
