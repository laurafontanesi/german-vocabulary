#!/usr/bin/env python3
"""
make_deck.py — build the Anki deck from words.json.

Design, so this stays maintainable:

  * ONE registry of exercises (EXERCISES).  Each has a key, a label, a colour
    and a builder function.  Adding an exercise means adding one entry and one
    builder — nothing else changes.

  * EVERY exercise gets the SAME five fields, named <Key>_Frage, _Antwort,
    _Ganz, _GanzEN, _Hinweis.  The field list therefore never shifts around
    when an exercise changes, which was the old problem.

  * Builders return a dict, not a tuple, so a missing key cannot silently
    shift values into the wrong column.

  * This script also WRITES the card templates, the field list and the CSS.
    They are generated from the same registry as the data, so the names in the
    templates can never drift from the names in the file again.

Lives in anki/ next to its output; words.json and lexicon.py are one level up.

Usage (from the repo root):
    python anki/make_deck.py
writes anki/deutsch.txt, anki/templates.md and anki/styling.css.
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

SLOTS = ['Frage', 'Antwort', 'Ganz', 'GanzEN', 'Hinweis']

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


def chips(items):
    return ' '.join('<span class="chip">%s</span>' % str(c).replace('&', '&amp;')
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
            out.append('reflexiv')
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

def ex_konjugation(w, ctx):
    if w.get('type') != 'verb':
        return None
    inf = bare(w['word']).lower()
    for ex in w.get('examples', []):
        s = ex['de']
        for key, label in (('past_participle', 'Partizip II'),
                           ('past_tense', 'Präteritum')):
            form = (w.get(key) or '').lower().split(' ')[0]
            if form and re.search(r'\b' + re.escape(form) + r'\b', s, re.I):
                return dict(Frage=re.sub(r'\b' + re.escape(form) + r'\b', '___', s,
                                         count=1, flags=re.I),
                            Antwort=form, Ganz=s, GanzEN=ex.get('en', ''),
                            Hinweis=label)
        stem = re.sub(r'(en|n)$', '', inf)
        if len(stem) >= 3:
            m = re.search(r'\b(' + re.escape(stem) + r'\w*)\b', s, re.I)
            if m and m.group(1).lower() != inf:
                return dict(Frage=s.replace(m.group(1), '___', 1),
                            Antwort=m.group(1).lower(), Ganz=s,
                            GanzEN=ex.get('en', ''), Hinweis='Präsens')
    return None


def ex_kasus(w, ctx):
    """Only case-marked articles: the citation form is already the EN->DE card."""
    if w.get('type') != 'noun':
        return None
    stem = bare(w['word']).lower()[:5]
    for ex in w.get('examples', []):
        toks = ex['de'].split()
        for i, tok in enumerate(toks[:-1]):
            art = strip_punct(tok)
            if art.lower() not in DETERMINERS:
                continue
            if art.lower() in ('der', 'die', 'das', 'ein', 'eine'):
                continue
            for j in range(i + 1, min(i + 4, len(toks))):
                if strip_punct(toks[j]).lower().startswith(stem):
                    return dict(Frage=blank_phrase(ex['de'], art),
                                Antwort=art.lower(), Ganz=ex['de'],
                                GanzEN=ex.get('en', ''), Hinweis='')
    return None


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


def ex_adjektiv(w, ctx):
    if w.get('type') != 'adj/adv':
        return None
    base = w['word'].lower()
    for ex in w.get('examples', []):
        toks = ex['de'].split()
        for i, tok in enumerate(toks[:-1]):
            cand, low = strip_punct(tok), strip_punct(tok).lower()
            nxt = strip_punct(toks[i + 1])
            if low.startswith(base) and len(low) > len(base) and nxt[:1].isupper():
                ending = low[len(base):]
                if 1 <= len(ending) <= 3:
                    return dict(Frage=ex['de'].replace(cand, base + '___', 1),
                                Antwort=ending, Ganz=ex['de'],
                                GanzEN=ex.get('en', ''), Hinweis='Nur die Endung')
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
    ('Konj',     'Konjugation',            'verb',   ex_konjugation, ''),
    ('Kasus',    'Artikel und Kasus',      'noun',   ex_kasus,       'Welcher Artikel?'),
    ('Praep',    'Präposition und Kasus',  'verb',   ex_praeposition, 'Lücken füllen'),
    ('Kontrast', 'Welches Wort passt?',    'other',  ex_kontrast,    ''),
    ('Neben',    'Nebensatz: Wortstellung', 'other', ex_nebensatz,   ''),
    ('Komma',    'Komma setzen',           'other',  ex_komma,       ''),
    ('Adj',      'Adjektivendung',         'adjadv', ex_adjektiv,    ''),
    ('Defin',    'Definition',             'other',  ex_definition,  ''),
]

# card order in the deck: grammar first, then the two translation directions
CARD_ORDER = ['Konj', 'Kasus', 'Praep', 'Kontrast', 'Neben', 'Komma', 'Adj',
              'Defin', 'Produzieren', 'Bedeutung']


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
    KIND_MARK = {'contrast': '', 'antonym': '≠ ', 'synonym': '= ', 'derived': '← '}
    r['Verwandt'] = chips([KIND_MARK.get(x['kind'], '') + x['word']
                           for x in w.get('related', []) if isinstance(x, dict)])
    r['Notiz'] = w.get('notes') or ''

    made = []
    for key, label, pill, builder, hint in EXERCISES:
        got = builder(w, ctx)
        if not got:
            continue
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


def word_block(with_second=True):
    """The shared bottom of every back template."""
    b = ['<div class="formen">{{Formen}}</div>']
    if with_second:
        b += ['<div class="satz">{{Beispiel}}</div>',
              '{{#BeispielEN}}<div class="en2">{{BeispielEN}}</div>{{/BeispielEN}}',
              '{{#Beispiel2}}<div class="satz">{{Beispiel2}}</div>{{/Beispiel2}}',
              '{{#Beispiel2EN}}<div class="en2">{{Beispiel2EN}}</div>{{/Beispiel2EN}}']
    b += ['{{#Verwandt}}<div class="chips">{{Verwandt}}</div>{{/Verwandt}}',
          '{{#Notiz}}<div class="notiz">{{Notiz}}</div>{{/Notiz}}']
    return '\n'.join(b)


def templates():
    out = {}

    out['Bedeutung'] = (
        '\n'.join([
            '<div class="kopf">Bedeutung <span class="pill other">{{Typ}}</span></div>',
            '<div class="wort">{{Wort}}</div>',
            '<div class="hinweis">Kurze englische Bedeutung</div>',
            '{{type:EnglischKurz}}']),
        '\n'.join([
            '<div class="kopf">Bedeutung</div>',
            '<div class="wort">{{Wort}}</div>',
            '<hr id=answer>',
            '{{type:EnglischKurz}}',
            '<div class="en">{{Englisch}}</div>',
            word_block(),
            tts('Beispiel'),
            '{{#Beispiel2}}' + tts('Beispiel2') + '{{/Beispiel2}}']))

    out['Produzieren'] = (
        '\n'.join([
            '<div class="kopf">Produzieren <span class="pill other">{{Typ}}</span></div>',
            '<div class="en">{{Englisch}}</div>',
            '<div class="hinweis">Bei Nomen mit Artikel</div>',
            '{{type:Wort}}']),
        '\n'.join([
            '<div class="kopf">Produzieren</div>',
            '<div class="en">{{Englisch}}</div>',
            '<hr id=answer>',
            '{{type:Wort}}',
            word_block(),
            tts('Beispiel'),
            '{{#Beispiel2}}' + tts('Beispiel2') + '{{/Beispiel2}}']))

    for key, label, pill, _builder, hint in EXERCISES:
        F, A = f'{key}_Frage', f'{key}_Antwort'
        G, GE, H = f'{key}_Ganz', f'{key}_GanzEN', f'{key}_Hinweis'
        head = (f'<div class="kopf">{label} '
                f'<span class="pill {pill}">{{{{{H}}}}}</span></div>'
                if key in ('Konj',) else
                f'<div class="kopf">{label}</div>')
        front = ['{{#%s}}' % F, head, '<div class="satz">{{%s}}</div>' % F]
        if key in ('Kontrast', 'Defin'):
            front.append('{{#%s}}<div class="hinweis">{{%s}}</div>{{/%s}}' % (H, H, H))
        elif hint:
            front.append('<div class="hinweis">%s</div>' % hint)
        if key not in ('Konj', 'Kontrast', 'Defin'):
            front.append('<div class="hinweis">{{Wort}}</div>')
        front += ['{{type:%s}}' % A, '{{/%s}}' % F]

        back = [head, '<div class="wort">{{Wort}}</div>', '<hr id=answer>',
                '{{type:%s}}' % A,
                '<div class="en">{{Englisch}}</div>',
                '<div class="satz">{{%s}}</div>' % G,
                '{{#%s}}<div class="en2">{{%s}}</div>{{/%s}}' % (GE, GE, GE),
                word_block(with_second=False),
                tts(G)]
        out[label if key != 'Kontrast' else 'Kontrast'] = ('\n'.join(front),
                                                           '\n'.join(back))
    return out


def write_templates(path, fields):
    t = templates()
    names = {'Konj': 'Konjugation', 'Kasus': 'Artikel und Kasus',
             'Praep': 'Präposition und Kasus', 'Kontrast': 'Kontrast',
             'Neben': 'Nebensatz: Wortstellung', 'Komma': 'Komma setzen',
             'Adj': 'Adjektivendung', 'Defin': 'Definition'}
    order = [(k, names.get(k, k)) for k in CARD_ORDER]
    with io.open(path, 'w', encoding='utf-8') as f:
        f.write('# Card templates (generated — do not edit by hand)\n\n')
        f.write('Note type: **Deutsch**. Create the %d fields in exactly this '
                'order, then paste each template.\n\n' % len(fields))
        f.write('## Fields\n\n```\n' + ', '.join(fields) + '\n```\n\n')
        f.write('Tags are column %d.\n\n' % (len(fields) + 1))
        for i, (key, label) in enumerate(order, 1):
            name = label if key in names else key
            tpl = t.get(name) or t.get(key)
            if not tpl:
                continue
            f.write(f'## {i} — {name}\n\n**Front**\n```html\n{tpl[0]}\n```\n\n'
                    f'**Back**\n```html\n{tpl[1]}\n```\n\n')


def write_css(path):
    p = PALETTE
    css = f""".card {{
  font-family: Georgia, 'Iowan Old Style', serif;
  font-size: 20px; text-align: center;
  background: {p['paper']}; color: {p['ink']}; padding: 20px;
}}
.card.nightMode, .nightMode .card {{ background: {p['paper']}; color: {p['ink']}; }}
.kopf {{ font-family: -apple-system, Helvetica, sans-serif; font-size: 11px;
        letter-spacing: .08em; text-transform: uppercase; color: {p['muted']};
        margin-bottom: 18px; }}
.pill {{ display: inline-block; padding: 3px 10px; border-radius: 10px;
        font-size: 11px; letter-spacing: .06em; }}
.verb   {{ background: {p['verb'][0]};   color: {p['verb'][1]}; }}
.noun   {{ background: {p['noun'][0]};   color: {p['noun'][1]}; }}
.adjadv {{ background: {p['adjadv'][0]}; color: {p['adjadv'][1]}; }}
.other  {{ background: {p['other'][0]};  color: {p['other'][1]}; }}
.wort   {{ font-size: 30px; font-weight: 600; }}
.satz   {{ font-size: 21px; line-height: 1.5; margin: 14px 0 2px 0; }}
.en     {{ color: {p['english']}; font-size: 18px; }}
.en2    {{ color: {p['english']}; font-size: 15px; opacity: .85;
          margin-bottom: 10px; }}
.formen, .chips {{ margin-top: 12px; line-height: 2.1; }}
.chip   {{ display: inline-block;
          font-family: ui-monospace, Menlo, monospace; font-size: 13px;
          background: {p['chip_bg']}; color: {p['ink2']};
          border: 1px solid {p['chip_br']}; border-radius: 4px;
          padding: 4px 9px; margin: 0 3px; }}
.notiz  {{ font-family: -apple-system, Helvetica, sans-serif; font-size: 13px;
          color: {p['muted']}; font-style: italic; margin-top: 10px; }}
.hinweis {{ font-family: -apple-system, Helvetica, sans-serif; font-size: 13px;
           color: {p['muted']}; margin-top: 8px; }}
.loesung {{ color: {p['accent']}; font-weight: 600; }}
hr#answer {{ border: none; border-top: 1px solid {p['rule']}; margin: 18px 0; }}
input#typeans {{ font-family: Georgia, serif; font-size: 20px;
                padding: 6px 10px; border: 1px solid {p['rule']};
                border-radius: 4px; background: #fdfcf8; color: {p['ink']}; }}
/* Anki's own diff colours — kept clear of the purple used for English */
.typeGood   {{ background: #d4eae8; color: #1a4a47; }}
.typeBad    {{ background: #e8d5d0; color: #c0392b; }}
.typeMissed {{ background: #e9e4d6; color: #6a6356; }}
"""
    io.open(path, 'w', encoding='utf-8').write(css)


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
    write_css(os.path.join(args.out_dir, 'styling.css'))

    base = len(rows) * 2
    print(f'{len(rows)} Notizen, {len(fields)} Felder, Tags = Spalte {len(fields)+1}')
    print(f'  Bedeutung + Produzieren : {base}')
    for key, label, *_ in EXERCISES:
        print(f'  {label:<24}: {counts[key]}')
    print(f'  insgesamt               : {base + sum(counts.values())}')
    print(f'\ngeschrieben nach {args.out_dir}/: deutsch.txt, templates.md, styling.css')


if __name__ == '__main__':
    main()
