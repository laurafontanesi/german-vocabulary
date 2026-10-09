#!/usr/bin/env python3
"""Check exercise sentences before they go into words.json.

Used now for the sentences written by another AI for the missing slots, and later by vocab.py for the
sentences it generates for each new word. Each sentence comes with the hidden words in [square brackets]:

    Gestern [nahm] ich den Schirm [mit].

What is checked, per slot:
  praet / praes   the bracketed words are exactly the stored verb form; a separable particle closes its clause;
                  a verb without particle is not followed by a clause-final particle (that would be another verb)
  part            the participle as stored, with an auxiliary in the sentence
  refl            mich/dich (accusative) or mir/dir (dative), with ich/du as subject in the same clause
  adj_art/adj_det the adjective is a form of the word, between a determiner of the right kind and a noun, and
                  determiner + adjective + noun agree in case, number and gender (Morphy full-form lexicon)
  kasus           determiner + noun of this word, agreeing with each other in the requested case and number
  pc              the word appears once and is the only thing bracketed
  all             length, current spelling, unsuitable content, English present, not a copy of a used sentence

Results are "ok", "check" (could not be verified automatically: a person looks at it) or "error".

Also here: which exercises a word gets (slots_for), finding them in sentences that already exist
(find_in), and the instructions for generating the missing ones (generation_prompt). vocab.py uses all
of it. Needs data/dictionary.dump (see README, "Data sources").

The one-time backfill used an older copy with a command line for answer files: backfill/exercise_check.py.
"""
import collections
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DICT_PATH = os.path.join(HERE, "data", "dictionary.dump")

TOKEN = re.compile(r"[A-Za-zÄÖÜäöüß]+")
OLD_SPELLING = re.compile(r"\b(daß|muß\w*|wuß\w*|gewußt|läßt|paßt|bißchen|Schluß|Fluß|Kuß|Haß|naß|"
                          r"eßt|ißt|mißt|vergißt|Prozeß|Streß|Paß|faßt|küßt|mußt|müßt|letztemal|nächstemal|"
                          r"Photo\w*|(?:heute|gestern|morgen) nacht|um so (?:mehr|weniger|besser|schlimmer))\b")
UNSUITABLE = re.compile(r"(?i)\b(sex\w*|nackt\w*|vergewaltig\w*|selbstmord\w*|umbring\w*|drogen|kokain|"
                        r"ermord\w*|leiche\w*|töten|tötete|nazi\w*|hitler|bombe\w*)\b")
AUX_HABEN = {"habe", "hast", "hat", "haben", "habt", "hatte", "hattest", "hatten", "hattet", "hätte", "hättest",
             "hätten", "hättet", "hab"}
AUX_SEIN = {"bin", "bist", "ist", "sind", "seid", "war", "warst", "waren", "wart", "wäre", "wären", "sein"}
AUX_PASSIVE = {"wird", "werden", "wurde", "wurden", "worden"}
PARTICLES = {"ab", "an", "auf", "aus", "bei", "ein", "fest", "fort", "her", "hin", "los", "mit", "nach",
             "vor", "weg", "zu", "zurück", "zusammen", "um", "durch", "über", "unter", "wieder", "teil",
             "heraus", "herum", "hinaus", "vorbei", "kennen", "statt", "fern", "frei", "hoch", "nieder"}

DER_TYPE = {"der", "die", "das", "dies", "jen", "jed", "welch", "manch", "solch"}
EIN_TYPE = {"ein", "kein", "mein", "dein", "sein", "ihr", "unser", "euer"}
QUANT = {"viel", "wenig", "einig", "mehrer", "zwei", "drei", "vier", "fünf"}
ARTICLES = {"der", "die", "das", "ein"}                    # for adj_art; the rest are adj_det determiners

SUBORD = {"dass", "weil", "wenn", "ob", "als", "obwohl", "nachdem", "bevor", "während", "seit", "seitdem",
          "sobald", "damit", "falls", "da", "bis", "indem", "sodass", "solange", "wie", "wo", "warum"}
PREP_DAT = {"mit", "bei", "von", "zu", "aus", "nach", "seit", "gegenüber", "außer"}
PREP_AKK = {"für", "durch", "gegen", "ohne", "um"}
PREP_GEN = {"wegen", "trotz", "während", "aufgrund", "infolge", "statt", "anstelle", "innerhalb",
            "außerhalb", "angesichts", "anhand"}
PREP_TWO_WAY = {"in", "an", "auf", "unter", "über", "vor", "hinter", "neben", "zwischen"}


def toks(s):
    return TOKEN.findall(s)


def bare(word):
    return re.sub(r"^(der|die|das|der/die|sich)\s+", "", word).strip()


# ── bracket parsing ───────────────────────────────────────────────────────────

def parse_bracketed(text):
    """'Gestern [nahm] ich ihn [mit].' -> ('Gestern nahm ich ihn mit.', [[8,12],[22,25]], ['nahm','mit'])."""
    plain, spans, marked = "", [], []
    pos = 0
    for m in re.finditer(r"\[([^\[\]]+)\]", text):
        plain += text[pos:m.start()]
        a = len(plain)
        plain += m.group(1)
        spans.append([a, len(plain)]); marked.append(m.group(1))
        pos = m.end()
    plain += text[pos:]
    return plain, spans, marked


def token_index_at(plain, start):
    for k, m in enumerate(TOKEN.finditer(plain)):
        if m.start() == start:
            return k
    return None


def clause_of_index(plain, k):
    """Token indexes of the clause (between punctuation) containing token k."""
    pos = [m.start() for m in TOKEN.finditer(plain)]
    for seg in re.finditer(r'[^,.;:!?„“"–—]+', plain):
        ks = [i for i, p in enumerate(pos) if seg.start() <= p < seg.end()]
        if k in ks:
            return ks
    return []


# ── morphology ────────────────────────────────────────────────────────────────

class Morph:
    """Full-form lookup in the Morphy/LanguageTool dump: {form: [(lemma, tag)]}, one file pass per batch."""

    def __init__(self, path=DICT_PATH):
        self.path = path
        self.cache = {}

    def load(self, forms):
        need = {f for f in forms if f not in self.cache}
        need |= {f[:1].lower() + f[1:] for f in need}     # sentence-initial capitals
        need = {f for f in need if f not in self.cache}
        if not need:
            return
        found = collections.defaultdict(list)
        keys = {f.encode("utf-8") for f in need}
        with open(self.path, "rb") as fh:
            for line in fh:
                p = line.rstrip(b"\n").split(b"_", 2)
                if len(p) == 3 and p[1] in keys:
                    found[p[1].decode("utf-8")].append((p[0].decode("utf-8"), p[2].decode("utf-8")))
        for f in need:
            self.cache[f] = found.get(f, [])

    def get(self, form):
        r = list(self.cache.get(form, []))
        if form[:1].isupper():                              # sentence start: Sein/sein, Ihre/ihre
            r += self.cache.get(form[:1].lower() + form[1:], [])
        return r


def with_suffixes(forms):
    """Forms plus the endings of capitalised words, so compounds missing from the lexicon (Spielfilm)
    can be looked up through their last element (Film)."""
    out = set(forms)
    for f in forms:
        if f[:1].isupper():
            out |= {f[k:].capitalize() for k in range(1, len(f) - 2)}
    return out


_DMN = {("DAT", "SIN", "MAS"), ("DAT", "SIN", "NEU")}
CONTRACTIONS = {"zum": _DMN, "im": _DMN, "am": _DMN, "vom": _DMN, "beim": _DMN,
                "zur": {("DAT", "SIN", "FEM")},
                "ins": {("AKK", "SIN", "NEU")}, "ans": {("AKK", "SIN", "NEU")}, "aufs": {("AKK", "SIN", "NEU")}}


def det_readings(morph, det):
    """{(case, num, gen)} and declension type for a determiner token."""
    if det.lower() in CONTRACTIONS:                         # zur = zu der, ins = in das
        return set(CONTRACTIONS[det.lower()]), "DEF"
    out, kind = set(), None
    for lemma, tag in morph.get(det):
        t = tag.split(":")
        if t[0] == "ART" or (t[0] == "PRO" and t[1] in ("POS", "DEM", "IND", "INR", "RIN") and "STV" not in t):
            if len(t) >= 5:
                out.add((t[2], t[3], t[4]))
                lem = lemma.lower()
                kind = "DEF" if (lem in DER_TYPE or t[1] == "DEF") else ("IND" if lem in EIN_TYPE else kind)
    if not out:
        for lemma, tag in morph.get(det):               # viele, einige, zwei...
            t = tag.split(":")
            if t[0] in ("ADJ", "ZAL") and (lemma.lower() in QUANT or lemma.lower() == "solch"):
                if len(t) >= 4 and t[1] in ("NOM", "AKK", "DAT", "GEN"):
                    out.add((t[1], t[2], t[3])); kind = "SOL"
        if det.lower() in QUANT:
            kind = "SOL"
    return out, kind


# adjective endings by declension (SOL strong, DEF weak after der-words, IND mixed after ein-words)
CASES, GENS = ("NOM", "AKK", "DAT", "GEN"), ("MAS", "FEM", "NEU")
ENDING = {
    "SOL": {"NOM": ("er", "e", "es", "e"), "AKK": ("en", "e", "es", "e"),
            "DAT": ("em", "er", "em", "en"), "GEN": ("en", "er", "en", "er")},
    "DEF": {"NOM": ("e", "e", "e", "en"), "AKK": ("en", "e", "e", "en"),
            "DAT": ("en", "en", "en", "en"), "GEN": ("en", "en", "en", "en")},
    "IND": {"NOM": ("er", "e", "es", "en"), "AKK": ("en", "e", "es", "en"),
            "DAT": ("en", "en", "en", "en"), "GEN": ("en", "en", "en", "en")},
}


def adj_stems(word):
    """Stems an attributive form can be built on: sensibel -> sensibl, teuer -> teur, nächste -> nächst."""
    w = word.lower()
    out = {w}
    if w.endswith("e"):
        out.add(w[:-1])
    if re.search(r"([^aeiouäöü]|eu|au)e[lr]$", w):
        out.add(w[:-2] + w[-1])
    if w.endswith("ch") and w[:-2].endswith("o"):
        out.add(w[:-1] + "h")                            # hoch -> hoh
    return out


def adj_ending(token, word=None):
    """The inflection ending of an attributive adjective, or None. With `word`, the stem must be that word."""
    t = token.lower()
    for e in ("en", "em", "er", "es", "e"):
        if t.endswith(e):
            stem = t[:-len(e)]
            if word is None:
                if len(stem) >= 3:
                    return e
            elif stem in adj_stems(word):
                return e
    return None


def adj_readings(morph, adj, decl, word=None):
    """{(case, num, gen)} an attributive adjective can stand for after a determiner of type `decl`."""
    e = adj_ending(adj, word)
    if e is None:
        return set()
    out = set()
    for d in ([decl] if decl else ENDING):
        for c in CASES:
            row = ENDING[d][c]
            for gi, g in enumerate(GENS):
                if row[gi] == e:
                    out.add((c, "SIN", g))
            if row[3] == e:
                out |= {(c, "PLU", g) for g in GENS}
    return out


def noun_readings(morph, noun, lemma=None, suffixes=True):
    """{(case, num, gen)} for a noun form; compounds missing from the lexicon go through their last element."""
    for k in range(0, max(1, len(noun) - 2) if suffixes else 1):
        form = noun if k == 0 else noun[k:].capitalize()
        out = set()
        for lem, tag in morph.get(form):
            t = tag.split(":")
            if t[0] == "SUB" and len(t) >= 4 and t[1] in CASES and \
                    (lemma is None or lemma.lower().endswith(lem.lower())):
                out.add((t[1], t[2], t[3]))
        if out:
            return out
    return set()


def entry_noun_readings(entry, form):
    """Fallback when the lexicon does not know the noun (Entscheidungsfindung) or lists only its singular
    (Abgas for die Abgase): build the readings from the article and plural stored in words.json."""
    m = re.match(r"(der|die|das)\s+(.+)", entry.get("word", ""))
    if not m:
        return set()
    gen = {"der": "MAS", "die": "FEM", "das": "NEU"}[m.group(1)]
    sing = m.group(2).strip()
    pl = bare(entry.get("plural") or "") or None
    if entry.get("plural") and entry["plural"].strip() == entry["word"].strip():
        sing = None                                       # plural-only noun (die Fallzahlen)
    out = set()
    if sing and form == sing:
        out |= {(c, "SIN", gen) for c in ("NOM", "AKK", "DAT")} | ({("GEN", "SIN", gen)} if gen == "FEM" else set())
    if sing and gen != "FEM" and form in (sing + "s", sing + "es"):
        out.add(("GEN", "SIN", gen))
    if pl and form == pl:
        out |= {(c, "PLU", gen) for c in ("NOM", "AKK", "GEN")} | ({("DAT", "PLU", gen)} if pl[-1] in "ns" else set())
    if pl and pl[-1] not in "ns" and form == pl + "n":
        out.add(("DAT", "PLU", gen))
    return out


def np_agreement(morph, det, adjs, noun, noun_lemma=None, noun_reads=None):
    """Readings shared by determiner, adjectives and noun; empty = they do not agree."""
    def norm(rs):                                        # plural: gender plays no role (Eltern = NOG)
        return {(c, n, "*" if n == "PLU" else g) for c, n, g in rs}
    d, kind = det_readings(morph, det) if det else (set(), "SOL")
    r = norm(noun_reads if noun_reads is not None else noun_readings(morph, noun, noun_lemma))
    if det:
        r &= norm(d)
    for a in adjs:
        r &= norm(adj_readings(morph, a, kind))
    return r, kind


def governing_cases(tokens, i):
    """Cases a preposition directly before the noun phrase at token i allows (None: no preposition).
    Two-way prepositions (in, an, auf…) allow dative or accusative."""
    if i == 0:
        return None
    p = tokens[i - 1].lower()
    for preps, cases in ((PREP_DAT, {"DAT"}), (PREP_AKK, {"AKK"}), (PREP_GEN, {"GEN"}),
                         (PREP_TWO_WAY, {"DAT", "AKK"})):
        if p in preps:
            return cases
    return None


# ── the check ─────────────────────────────────────────────────────────────────

def verb_parts(form):
    """'nahm sich mit' -> ['nahm', 'mit'];  'sandte / sendete' -> alternatives handled by the caller."""
    return [p for p in form.split() if p != "sich"]


def check(entry, slot, form, answer, morph, used=(), min_words=5):
    """Returns dict(status, problems, de, en, blanks). `form` as in the inventory ('nahm mit', 'DAT:PLU'...)."""
    problems, warnings = [], []
    if "skip" in answer:
        return dict(status="skip", problems=[answer["skip"]], de=None, en=None, blanks=[])
    plain, spans, marked = parse_bracketed(answer.get("de", ""))
    en = (answer.get("en") or "").strip()
    ts = toks(plain)
    word = entry["word"]

    # general
    if not spans:
        problems.append("nothing in brackets")
    if not en:
        problems.append("English translation missing")
    if "[" in en or "]" in en:
        problems.append("brackets in the English")
    if not min_words <= len(ts) <= 16:
        problems.append(f"{len(ts)} words")
    elif len(ts) > 14:
        warnings.append(f"{len(ts)} words (long)")
    if OLD_SPELLING.search(plain):
        problems.append("old spelling")
    bad = UNSUITABLE.search(plain)
    if bad and not bad.group(0).lower().startswith(bare(word).lower()[:4]):   # the word itself (töten) is fine
        problems.append("unsuitable content")
    if plain.strip() in {u.strip() for u in used}:
        problems.append("same as a sentence already used")
    idx = [token_index_at(plain, a) for a, _ in spans]
    if any(i is None for i in idx) or any(not re.fullmatch(TOKEN.pattern, m) for m in marked):
        problems.append("a bracket does not hold exactly one word")
    if problems:
        return dict(status="error", problems=problems + warnings, de=plain, en=en, blanks=spans)

    if slot in ("praet", "praes"):
        alts = [verb_parts(a.strip()) for a in form.split("/")] if "/" in form else [verb_parts(form)]
        sep = entry.get("is_separable")
        ok_alt = None
        joined = False
        for parts in alts:
            want = parts if (sep and len(parts) > 1) else parts[:1]
            if [m.lower() for m in marked] == [p.lower() for p in want]:
                ok_alt = parts
            elif sep and len(parts) > 1 and [m.lower() for m in marked] == [(parts[-1] + parts[0]).lower()]:
                ok_alt, joined = parts, True                  # ..., als ich ihn [kennenlernte]
        if ok_alt is not None and joined:
            clause = clause_of_index(plain, idx[0])
            if not clause or clause[-1] != idx[0]:
                problems.append(f"«{marked[0]}» is the joined form: it must close a subordinate clause")
        elif ok_alt is None:
            problems.append(f"brackets {marked} but the form is «{form}»")
        else:
            head_k = idx[0]
            clause = clause_of_index(plain, head_k)
            last = clause[-1] if clause else None
            if sep and len(ok_alt) > 1:
                c0 = ts[clause[0]].lower() if clause else ""
                nxt = ts[clause[0] + 1] if clause and clause[0] + 1 < len(ts) else ""
                as_prep = c0 in {"während", "seit", "bis", "als", "wie"} and \
                    (det_readings(morph, nxt)[0] or (nxt[:1].isupper() and nxt not in {"Sie", "Ihr"}))
                if c0 in SUBORD and not as_prep:
                    problems.append(f"subordinate clause («{ts[clause[0]]}»): the verb would be joined "
                                    f"(«{ok_alt[-1]}{ok_alt[0]}»), not split")
                elif idx[-1] != last:
                    problems.append("the separable particle does not close the clause")
            elif last is not None and last != head_k and ts[last].lower() in PARTICLES \
                    and ts[last].lower() not in {p.lower() for p in ok_alt}:
                warnings.append(f"clause ends with «{ts[last]}»: maybe another verb")
            if sum(1 for t in ts if t.lower() == ok_alt[0].lower()) != 1:
                problems.append("the verb form appears more than once")
            k = idx[0]
            nxt_cap = k + 1 < len(ts) and ts[k + 1][:1].isupper() and ts[k + 1] not in {"Sie", "Ihnen", "Ihr", "Ich"}
            if k > 0 and det_readings(morph, ts[k - 1])[0] and nxt_cap:
                problems.append(f"«{ts[k - 1]} {ts[k]} {ts[k + 1]}»: an adjective here, not the verb")
            elif k == 0 and nxt_cap and not plain.rstrip().endswith("?"):
                problems.append(f"«{ts[0]} {ts[1]}» at the start: an adjective, not the verb")

    elif slot == "part":
        if [m.lower() for m in marked] != [form.lower()]:
            problems.append(f"brackets {marked} but the participle is «{form}»")
        low = {t.lower() for t in ts}
        aux = (entry.get("auxiliary") or "haben").lower()
        has_h, has_s = bool(low & AUX_HABEN), bool(low & AUX_SEIN)
        if not (has_h or has_s or low & AUX_PASSIVE):
            problems.append("no auxiliary verb: not a Perfekt")
        elif aux.startswith("sein") and not has_s and not (low & AUX_PASSIVE) \
                and not low & {"sich", "mich", "dich", "uns", "euch"}:
            problems.append("verb takes «sein» but the sentence uses «haben»")
        elif aux.startswith("haben") and not has_h and not (low & AUX_PASSIVE):
            warnings.append("verb takes «haben» but no form of haben found (Zustandspassiv?)")

    elif slot == "refl":
        allowed = {"mir": "ich", "dir": "du"} if entry.get("reflexive") == "dat" else {"mich": "ich", "dich": "du"}
        if len(marked) != 1 or marked[0] not in allowed:
            problems.append(f"brackets {marked}, expected one of {sorted(allowed)}")
        else:
            clause = clause_of_index(plain, idx[0])
            if allowed[marked[0]] not in {ts[k].lower() for k in clause}:
                problems.append(f"«{marked[0]}» without «{allowed[marked[0]]}» as subject in the same clause")

    elif slot in ("adj_art", "adj_det"):
        if len(marked) != 1:
            problems.append(f"brackets {marked}: only the adjective should be marked")
        else:
            k = idx[0]
            a = ts[k]
            if adj_ending(a, word) is None:
                problems.append(f"«{a}» is not an inflected form of «{word}»")
            # determiner before (possibly another adjective in between), noun after
            j = k - 1
            adjs = [a]
            while j >= 0 and ts[j][:1].islower() and adj_ending(ts[j]) and not det_readings(morph, ts[j])[0]:
                adjs.append(ts[j]); j -= 1
            n = k + 1
            while n < len(ts) and ts[n][:1].islower() and adj_ending(ts[n]):
                adjs.append(ts[n]); n += 1
            if j < 0 or not det_readings(morph, ts[j])[0]:
                problems.append("no determiner before the adjective")
            elif n >= len(ts) or not ts[n][:1].isupper():
                problems.append("no noun after the adjective")
            else:
                det = ts[j]
                lem = {l.lower() for l, t in morph.get(det) if t.startswith(("ART", "PRO"))}
                is_article = bool(lem & ARTICLES)
                if slot == "adj_art" and not is_article:
                    problems.append(f"«{det}» is not an article (task: article + adjective + noun)")
                if slot == "adj_det" and is_article:
                    problems.append(f"«{det}» is an article (task: possessive/dieser/jeder/kein + adjective + noun)")
                agree, kind = np_agreement(morph, det, adjs, ts[n])
                if not noun_readings(morph, ts[n]):
                    warnings.append(f"«{ts[n]}» not in the lexicon: agreement not checked")
                elif not agree:
                    problems.append(f"«{det} {a} {ts[n]}»: the ending does not agree")
                else:
                    gs = governing_cases(ts, j)
                    cases = {c for c, _, _ in agree}
                    if gs and not gs & cases:
                        problems.append(f"«{ts[j - 1]}» requires {'/'.join(sorted(gs))}, "
                                        f"but the phrase is {'/'.join(sorted(cases))}")

    elif slot.startswith("kasus"):
        case, num = form.split(":")
        if answer.get("note") in ("singular", "plural"):
            new = "SIN" if answer["note"] == "singular" else "PLU"
            if new != num:
                warnings.append(f"{answer['note']} instead of {'plural' if num == 'PLU' else 'singular'} (noted)")
            num = new
        noun = bare(word)
        dk = nk = None
        if len(marked) == 2:
            dk, nk = idx
        elif len(marked) == 1:                             # no determiner: mit bunten [Stiften], vor [Gewittern]
            nk = idx[0]
            j = nk - 1
            while j >= 0 and ts[j][:1].islower() and adj_ending(ts[j]) and not det_readings(morph, ts[j])[0]:
                j -= 1
            if j >= 0 and (det_readings(morph, ts[j])[0] or ts[j].lower() in CONTRACTIONS):
                problems.append(f"«{ts[j]}» belongs to the noun phrase: mark it too")
                nk = None
            dk = j + 1
        else:
            problems.append(f"brackets {marked}: expected determiner and noun")
        if nk is not None:
            det = ts[dk] if len(marked) == 2 else None
            nn = ts[nk]
            adjs = ts[dk + 1:nk] if det else ts[dk:nk]
            # the lexicon itself, then article/plural from words.json, then the compound's last element
            reads = noun_readings(morph, nn, noun, suffixes=False) or entry_noun_readings(entry, nn) \
                or noun_readings(morph, nn, noun)
            agree, _ = np_agreement(morph, det, adjs, nn, noun, reads)
            if not reads:
                problems.append(f"«{nn}» is not a form of «{noun}»")
            elif not agree:
                problems.append(f"«{' '.join(ts[dk:nk + 1])}» does not agree")
            elif not det and num != "PLU":
                problems.append("a singular noun without determiner shows no case")
            else:
                fits = {(c, n) for c, n, _ in agree}
                if (case, num) not in fits:
                    problems.append(f"asked for {case} {num}, the phrase can only be "
                                    + ", ".join(f"{c} {n}" for c, n in sorted(fits)))
                else:
                    gs = governing_cases(ts, dk)
                    if gs and case not in gs:
                        problems.append(f"«{ts[dk - 1]}» requires {'/'.join(sorted(gs))}")
                    elif len({c for c, n in fits if n == num and (not gs or c in gs)}) > 1:
                        warnings.append("case depends on the verb: check by eye")

    elif slot.startswith("pc"):
        if [m.lower() for m in marked] != [word.lower()]:
            problems.append(f"brackets {marked}, expected «{word}»")
        elif sum(1 for t in ts if t.lower() == word.lower()) != 1:
            problems.append(f"«{word}» appears more than once")

    elif slot.startswith("cx"):
        cb = construction_blanks(word, plain)
        if not cb:
            problems.append(f"the construction «{word}» is not in the sentence")
        else:
            spans = cb                                     # the fixed words of the pattern, whatever was marked

    status = "error" if problems else ("check" if warnings else "ok")
    return dict(status=status, problems=problems + warnings, de=plain, en=en, blanks=spans)


# ── which exercises a word gets ───────────────────────────────────────────────

CASE_NAME = {"AKK": "accusative", "DAT": "dative", "GEN": "genitive", "NOM": "nominative"}
NUM_NAME = {"SIN": "singular", "PLU": "plural"}
ADVERB_SENSE = {"gerade", "unbedingt", "nieder"}     # tagged "both", but the recorded meaning is the adverb


def slots_for(entry, stem_changes=None):
    """[{slot, label, form}] for one word. `stem_changes(entry)` says whether the present tense changes
    the stem (lexicon.changes_stem); without it, the Präsens slot is left out."""
    t, word = entry.get("type"), entry.get("word", "")
    out = []
    if t == "verb":
        if entry.get("past_tense"):
            out.append(dict(slot="praet", label="Präteritum", form=entry["past_tense"]))
        pa = (entry.get("past_participle") or "").split("/")[0].strip()
        if pa:
            out.append(dict(slot="part", label="Partizip II", form=pa))
        if entry.get("present_3sg") and stem_changes and stem_changes(entry):
            out.append(dict(slot="praes", label="Präsens, er/sie/es", form=entry["present_3sg"]))
        r = entry.get("reflexive")
        if r in ("akk", "dat"):
            out.append(dict(slot="refl", label=f"Reflexivpronomen ({'Dat.' if r == 'dat' else 'Akk.'})",
                            form="mir/dir" if r == "dat" else "mich/dich"))
    elif t == "noun":
        out += [dict(slot="kasus1", label="", form=None), dict(slot="kasus2", label="", form=None)]
    elif t == "adj/adv" and entry.get("usage") != "adverb only" and " " not in word \
            and entry.get("id") not in ADVERB_SENSE:
        out += [dict(slot="adj_art", label="Artikel + Adjektiv + Nomen", form=word),
                dict(slot="adj_det", label="Begleiter + Adjektiv + Nomen", form=word)]
    elif t == "prep/conj":
        out += [dict(slot=f"pc{n}", label=f"Satz mit {word}", form=word) for n in range(1, 7)]
    elif t == "construction":
        out += [dict(slot=f"cx{n}", label=f"Satz mit {word}", form=word) for n in range(1, 3)]
    return out


def kasus_label(form):
    c, n = form.split(":")
    return f"{c} {'Plural' if n == 'PLU' else 'Singular'}"


def kasus_options(entry, taken_cases, rnd):
    """A random (case:number) for a noun slot: not nominative, not a case already used, plural only if
    the noun has one, and only plural for plural-only nouns (die Fallzahlen)."""
    plural_only = (entry.get("plural") or "").strip() == entry.get("word", "").strip()
    nums = ["PLU"] if plural_only else (["SIN", "PLU"] if entry.get("plural") else ["SIN"])
    options = [f"{c}:{n}" for c in ("AKK", "DAT", "GEN") for n in nums if c not in taken_cases]
    return rnd.choice(options) if options else None


# construction slots: which words to hide. Verb parts of a pattern match any form of that verb.
VERB_FORMS = {
    "sein": {"bin", "bist", "ist", "sind", "seid", "war", "warst", "waren", "wart"},
    "haben": {"habe", "hast", "hat", "haben", "habt", "hatte", "hattest", "hatten", "hattet"},
    "brauchen": {"brauche", "brauchst", "braucht", "brauchen", "brauchte", "brauchtest", "brauchten"},
    "werden": {"werde", "wirst", "wird", "werden", "werdet", "wurde", "wurden"},
}
PLACEHOLDERS = {"x", "y", "infinitiv", "ich"}


def construction_blanks(pattern, de):
    """Spans of the fixed words of a construction (je … desto, sein + zu + Infinitiv, Lieblings-)."""
    words = [w for w in re.findall(r"[A-Za-zÄÖÜäöüß]+-?", pattern) if w.lower().rstrip("-") not in PLACEHOLDERS]
    spans = []
    tk = [(m.start(), m.end(), m.group()) for m in TOKEN.finditer(de)]
    for w in words:
        if w.endswith("-"):                                  # prefix: Lieblings- -> the prefix inside the word
            stem = w[:-1]
            for a, b, t in tk:
                if t.startswith(stem) and len(t) > len(stem):
                    spans.append([a, a + len(stem)]); break
            continue
        forms = VERB_FORMS.get(w.lower()) or next((f for f in VERB_FORMS.values() if w.lower() in f), {w.lower()})
        for a, b, t in tk:
            if t.lower() in forms and [a, b] not in spans:
                spans.append([a, b]); break
    return sorted(spans)


# ── finding exercises in sentences you already have ──────────────────────────

def bracket(plain, picks):
    """picks: token indexes -> the sentence with those tokens in [brackets]."""
    pos = [(m.start(), m.end()) for m in TOKEN.finditer(plain)]
    out, last = "", 0
    for k in sorted(picks):
        a, b = pos[k]
        out += plain[last:a] + "[" + plain[a:b] + "]"; last = b
    return out + plain[last:]


def noun_case_in(entry, plain, morph):
    """(case:number, token picks) when the sentence has this noun with a determiner in exactly one
    possible case other than the nominative; else None."""
    ts = toks(plain)
    noun = bare(entry["word"])
    hits = []
    for i, t in enumerate(ts):
        if t[:1].isupper() and i > 0:
            reads = noun_readings(morph, t, noun, suffixes=False) or entry_noun_readings(entry, t)
            if reads:
                hits.append((i, reads))
    if len(hits) != 1:
        return None
    i, reads = hits[0]
    j = i - 1
    while j >= 0 and ts[j][:1].islower() and adj_ending(ts[j]) and not det_readings(morph, ts[j])[0]:
        j -= 1
    if j < 0 or not det_readings(morph, ts[j])[0]:
        return None
    agree, _ = np_agreement(morph, ts[j], ts[j + 1:i], ts[i], noun, reads)
    fits = {(c, n) for c, n, _ in agree}
    gs = governing_cases(ts, j)
    if gs:
        fits = {(c, n) for c, n in fits if c in gs}
    if len(fits) != 1:
        return None
    c, n = next(iter(fits))
    return (f"{c}:{n}", [j, i]) if c != "NOM" else None


def find_in(entry, spec, plain, en, morph, used=()):
    """Can this existing sentence serve the exercise `spec`? Returns a checked exercise or None."""
    ts = toks(plain)
    slot, form, word = spec["slot"], spec["form"], entry["word"]
    picks = None
    if slot in ("praet", "praes"):
        alts = [verb_parts(a.strip()) for a in form.split("/")]
        for parts in alts:
            ks = [k for k, t in enumerate(ts) if t.lower() == parts[0].lower()]
            if len(ks) != 1:
                continue
            picks = ks
            if entry.get("is_separable") and len(parts) > 1:
                clause = clause_of_index(plain, ks[0])
                if not clause or ts[clause[-1]] != parts[-1]:
                    picks = None; continue
                picks = [ks[0], clause[-1]]
            break
    elif slot == "part":
        ks = [k for k, t in enumerate(ts) if t.lower() == form.lower()]
        picks = ks if len(ks) == 1 else None
    elif slot == "refl":
        prons = ("mir", "dir") if form == "mir/dir" else ("mich", "dich")
        ks = [k for k, t in enumerate(ts) if t in prons]
        picks = ks if len(ks) == 1 else None
    elif slot in ("adj_art", "adj_det"):
        ks = [k for k, t in enumerate(ts) if adj_ending(t, word)]
        picks = ks if len(ks) == 1 else None
    elif slot.startswith("kasus"):
        r = noun_case_in(entry, plain, morph)
        if not r or (form and r[0] != form):
            return None
        form, picks = r
    elif slot.startswith("pc"):
        ks = [k for k, t in enumerate(ts) if t.lower() == word.lower()]
        picks = ks if len(ks) == 1 else None
    elif slot.startswith("cx"):
        spans = construction_blanks(word, plain)
        return dict(status="ok", problems=[], de=plain, en=en, blanks=spans) if spans else None
    if not picks:
        return None
    r = check(entry, slot, form, {"de": bracket(plain, picks), "en": en or "-"}, morph, used, min_words=3)
    if r["status"] == "ok":
        r["form"] = form
        return r
    return None


# ── asking the model for the missing ones ────────────────────────────────────

def task_text(entry, spec):
    """The instruction for one missing exercise (same wording as the backfill request)."""
    word, slot, form = entry["word"], spec["slot"], spec["form"]
    if slot in ("praet", "praes"):
        what = ("Präteritum, exactly the form «{f}» (ich or er/sie/es)" if slot == "praet"
                else "Präsens, 3rd person singular, exactly «{f}»")
        if " / " in form:
            alts = [a.strip() for a in form.split("/")]
            return what.format(f=alts[0]) + f" (or «{alts[1]}»). Mark the verb form, e.g. [{alts[0]}]."
        parts = verb_parts(form)
        note = " The verb is reflexive: use the pronoun that fits the subject (mich, dich, sich...), unmarked." \
            if "sich" in form.split() else ""
        if len(parts) > 1 and entry.get("is_separable"):
            mark = " and ".join(f"[{p}]" for p in parts)
            return (what.format(f=" ... ".join(parts)) + ". Separable verb: the particle goes to the end of the "
                    f"main clause, never split it in a subordinate clause.{note} Mark {mark}.")
        if len(parts) > 1:
            return (what.format(f=parts[0]) + f", used with the preposition «{' '.join(parts[1:])}».{note} "
                    f"Mark only [{parts[0]}].")
        return what.format(f=parts[0]) + f".{note} Mark only [{parts[0]}]."
    if slot == "part":
        return (f"Perfekt or Plusquamperfekt with «{entry.get('auxiliary') or 'haben'}», participle «{form}». "
                f"Mark only [{form}].")
    if slot == "refl":
        case = "dative (mir/dir)" if form == "mir/dir" else "accusative (mich/dich)"
        return (f"Reflexive verb, pronoun in the {case}. Use ich or du as subject so the pronoun is not «sich». "
                f"Mark only the reflexive pronoun, e.g. [mich].")
    if slot == "adj_art":
        return (f"Article (der/die/das/ein/eine, any case) + inflected «{word}» + noun. "
                f"Mark only the inflected adjective.")
    if slot == "adj_det":
        return (f"Possessive (mein, dein, sein, ihr, unser, euer), dieser, jeder or kein + inflected «{word}» "
                f"+ noun. Mark only the inflected adjective.")
    if slot.startswith("kasus"):
        c, n = form.split(":")
        return (f"The noun in the {CASE_NAME[c]} {NUM_NAME[n]} (sg. {word}, pl. {entry.get('plural') or 'no plural'}) "
                f"with a determiner (article, possessive, dieser, kein...). The case must be clearly required by a "
                f"preposition or the verb. Mark the determiner and the noun separately, e.g. [den] [Kindern]; "
                f"leave any adjective in between unmarked."
                + (" If the plural sounds unnatural, use the singular in the same case and add "
                   "\"note\": \"singular\"." if n == "PLU" else ""))
    if slot.startswith("pc"):
        return f"A sentence using «{word}» in the meaning given. Mark only the word."
    if slot.startswith("cx"):
        return f"A sentence using the construction «{word}». Mark its fixed words, e.g. [je] ... [desto]."
    raise ValueError(slot)


RULES = """Rules for every sentence:
1. One sentence, 6 to 14 words, natural standard German as a teacher would write it (use ß where standard German does).
2. Use the word in the meaning given; if it has several, use the first unless the task says otherwise.
3. The target form appears exactly once, exactly as the task names it.
4. Mark with square brackets only what the task says to mark, whole words only: Gestern [nahm] ich den Schirm [mit].
5. The context makes the answer unambiguous; for case tasks the preposition or verb that requires the case is in the sentence.
6. Everyday, concrete situations (work, home, travel, friends, health, weather, studying). No famous people,
   no violence, sex, drugs or politics. Vary subjects and situations.
7. Do not copy the sentences listed as already used.
8. Natural English translation, no brackets.
9. If a task cannot be done naturally, answer {"id": ..., "skip": "short reason"} instead."""


def generation_prompt(entry, specs, used, feedback=None):
    meanings = " / ".join(d["meaning"] for d in entry.get("definitions", []) if d.get("meaning")) or "(see word)"
    lines = [f"- {entry['id']}|{s['slot']}: {task_text(entry, s)}" for s in specs]
    fb = ""
    if feedback:
        fb = "\n\nYour previous attempt had these problems; avoid them:\n" + "\n".join(f"- {f}" for f in feedback)
    used_txt = "\n".join(f"- {u}" for u in dict.fromkeys(used)) or "- (none)"
    return f"""Write German gap-fill exercise sentences for a vocabulary trainer. The learner is an adult at
level B1/B2, a native Italian speaker living in Zurich.

Word: {entry['word']} ({entry.get('type')}; {meanings})

{RULES}

Already used (do not copy):
{used_txt}

Tasks:
{chr(10).join(lines)}{fb}

Return ONLY JSON Lines, one line per task, in the same order, nothing else:
{{"id": "<task id>", "de": "German sentence with [brackets]", "en": "English translation"}}"""


def read_answers_text(s):
    """Parse JSON objects written one after another (JSON Lines, or several on one line)."""
    s = re.sub(r"^```[a-z]*\n?|\n?```$", "", s.strip())
    dec, i, out = json.JSONDecoder(), 0, []
    while i < len(s):
        while i < len(s) and s[i] not in "{":
            i += 1
        if i >= len(s):
            break
        try:
            o, i = dec.raw_decode(s, i)
            out.append(o)
        except json.JSONDecodeError:
            i += 1
    return out


def read_answers(path):
    return read_answers_text(open(path, encoding="utf-8").read())


def show(ex):
    """'Gestern [nahm] ich …' for display."""
    d, out, last = ex["de"], "", 0
    for a, b in ex["blanks"]:
        out += d[last:a] + "[" + d[a:b] + "]"; last = b
    return out + d[last:]


def available():
    return os.path.exists(DICT_PATH)
