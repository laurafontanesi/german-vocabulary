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

CORE_FIELDS = ['Wort', 'Typ', 'Formen', 'Englisch', 'EnglischKurz',
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

CASE_DE = {'AKK': 'Akkusativ', 'DAT': 'Dativ', 'GEN': 'Genitiv'}


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
        if slot in ('praet', 'part', 'praes'):
            return from_exercise(w, slot, w['word'])
        if slot == 'refl':
            return from_exercise(w, slot, w['word'] + (' (Dativ)' if w.get('reflexive') == 'dat' else ' (Akkusativ)'))
        if slot.startswith('kasus'):
            ex = next((e for e in w.get('exercises', []) if e['slot'] == slot), None)
            c, n = ((ex or {}).get('form') or ':').split(':')
            label = f"{CASE_DE.get(c, c)} {'Plural' if n == 'PLU' else 'Singular'}"
            return from_exercise(w, slot, f'{label} · {w["word"]}')
        if slot.startswith('adj'):
            return from_exercise(w, slot, w['word'])
        # Lücke n: preposition/conjunction (pc n) or construction (cx n). The word itself would
        # give the answer away, so the hint is its meaning.
        n = slot[-1]
        return from_exercise(w, ('cx' if w.get('type') == 'construction' else 'pc') + n, meaning_hint(w))
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


def ex_komma(w, ctx):
    for ex in w.get('examples', []):
        s = ex['de']
        if s.count(',') != 1:
            continue
        if not re.search(r'\b(' + '|'.join(SUB_CONJ) + r'|der|die|das|den|dem)\b',
                         s, re.I):
            continue
        i = s.find(',')
        vor, nach = s[:i].split(), s[i + 1:].split()
        if not vor or not nach:
            continue
        return dict(Frage=s.replace(',', ''),
                    Antwort=strip_punct(vor[-1]) + ', ' + strip_punct(nach[0]),
                    Ganz=s, GanzEN=ex.get('en', ''),
                    Hinweis='Die zwei Wörter um das Komma')
    return None


def ex_praeposition(w, ctx):
    """Blank preposition + following article, so the case is typed, not named."""
    p = w.get('preposition')
    if not p:
        return None
    prep = p.split('+')[0].strip()
    fallback = None
    for ex in w.get('examples', []):
        toks = ex['de'].split()
        for i, tok in enumerate(toks[:-1]):
            if strip_punct(tok).lower() != prep.lower():
                continue
            nxt = strip_punct(toks[i + 1])
            if nxt.lower() in DETERMINERS:
                phrase = tok + ' ' + toks[i + 1]
                return dict(Frage=blank_phrase(ex['de'], phrase),
                            Antwort=strip_punct(tok) + ' ' + nxt,
                            Ganz=ex['de'], GanzEN=ex.get('en', ''), Hinweis=p)
            if fallback is None:
                fallback = dict(Frage=blank_phrase(ex['de'], tok),
                                Antwort=strip_punct(tok), Ganz=ex['de'],
                                GanzEN=ex.get('en', ''), Hinweis=p)
    return fallback


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


SUFFIXES = ('lichkeit', 'igkeit', 'keit', 'heit', 'schaft', 'ung', 'lich', 'isch', 'ig',
            'lang', 'sam', 'bar', 'haft', 'end', 'en', 'er', 'el', 'e', 'n', 't')


def word_roots(word):
    """Roots used to mask a definition: the word, then the word with derivational
    suffixes peeled off one at a time (glücklich -> glück, stundenlang -> stund).
    Roots shorter than 4 letters are not used."""
    w, roots = word.lower(), []
    while len(w) >= 4:
        roots.append(w)
        for s in SUFFIXES:
            if w.endswith(s) and len(w) - len(s) >= 4:
                w = w[:-len(s)]
                break
        else:
            break
    return sorted(set(roots), key=len)[:1]   # the shortest root covers the longer ones


def ex_definition(w, ctx):
    """German definition (from German Wiktionary) -> type the word.
    Words sharing the headword's stem are masked so the definition does not give it away."""
    d = w.get('definition_de')
    if not d:
        return None
    masked = d
    for stem in word_roots(bare(w['word'])):
        masked = re.sub(r'\b\w*' + re.escape(stem) + r'\w*', '…', masked, flags=re.I)
    return dict(Frage=masked, Antwort=w['word'], Ganz=d, GanzEN='',
                Hinweis='Bei Nomen mit Artikel' if w.get('type') == 'noun' else '')


# ── the registry ──────────────────────────────────────────────────────────────
# key, German label shown on the card, pill colour, builder, front hint

EXERCISES = [
    ('Praet',    'Präteritum',             'verb',   ex_slot('praet'),  ''),
    ('Part',     'Partizip II',            'verb',   ex_slot('part'),   ''),
    ('Praes',    'Präsens (er/sie/es)',    'verb',   ex_slot('praes'),  ''),
    ('Refl',     'Reflexivpronomen',       'verb',   ex_slot('refl'),   ''),
    ('Kasus1',   'Kasus',                  'noun',   ex_slot('kasus1'), ''),
    ('Kasus2',   'Kasus 2',                'noun',   ex_slot('kasus2'), ''),
    ('AdjArt',   'Adjektiv nach Artikel',  'adjadv', ex_slot('adj_art'), ''),
    ('AdjDet',   'Adjektiv nach Begleiter', 'adjadv', ex_slot('adj_det'), ''),
] + [
    (f'Luecke{n}', f'Lücke {n}',          'other',  ex_slot(f'gap{n}'), '') for n in range(1, 7)
] + [
    ('Praep',    'Präposition und Kasus',  'verb',   ex_praeposition, 'Lücken füllen'),
    ('Kontrast', 'Welches Wort passt?',    'other',  ex_kontrast,    ''),
    ('Neben',    'Nebensatz: Wortstellung', 'other', ex_nebensatz,   ''),
    ('Komma',    'Komma setzen',           'other',  ex_komma,       ''),
    ('Defin',    'Definition',             'other',  ex_definition,  ''),
]
# sentence exercises: the hint (word, case, meaning) is in the _Hinweis field, shown on the front
SENTENCE_KEYS = {'Praet', 'Part', 'Praes', 'Refl', 'Kasus1', 'Kasus2', 'AdjArt', 'AdjDet'} | \
                {f'Luecke{n}' for n in range(1, 7)}

# card order in the deck: grammar first, then the two translation directions
CARD_ORDER = [k for k, *_ in EXERCISES] + ['Produzieren', 'Bedeutung']


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
        if key in ('Kontrast', 'Praep') and got.get('Antwort') and 'class="hl"' not in got.get('Ganz', ''):
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
             '<div class="en gross">{{Englisch}}</div>',
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
        elif key in ('Kontrast', 'Defin'):
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
