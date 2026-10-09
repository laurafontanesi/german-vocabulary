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

Command line (after the other AI has answered):
    python3 exercise_check.py answers.txt        -> exercises_generated.json + a report on screen
Answers already in exercises_generated.json are skipped (so corrections made in review survive);
--recheck checks them again from the answer file. My corrections from reading the answers are in
answers_review_fixes.txt (with a "review" note each); give that file last so it wins:
    python3 exercise_check.py answers_batch*.txt answers_review_fixes.txt --recheck
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


def det_readings(morph, det):
    """{(case, num, gen)} and declension type for a determiner token."""
    out, kind = set(), None
    for lemma, tag in morph.get(det):
        t = tag.split(":")
        if t[0] == "ART" or (t[0] == "PRO" and t[1] in ("POS", "DEM", "IND") and "STV" not in t):
            if len(t) >= 5:
                out.add((t[2], t[3], t[4]))
                lem = lemma.lower()
                kind = "DEF" if (lem in DER_TYPE or t[1] == "DEF") else ("IND" if lem in EIN_TYPE else kind)
    if not out:
        for lemma, tag in morph.get(det):               # viele, einige, zwei...
            t = tag.split(":")
            if t[0] in ("ADJ", "ZAL") and lemma.lower() in QUANT:
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
    if re.search(r"[^aeiouäöü]e[lr]$", w):
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


def governing_case(tokens, i):
    """Case required by a preposition directly before the noun phrase starting at token i (None if unclear)."""
    if i == 0:
        return None
    p = tokens[i - 1].lower()
    if p in PREP_DAT:
        return "DAT"
    if p in PREP_AKK:
        return "AKK"
    if p in PREP_GEN:
        return "GEN"
    return None


# ── the check ─────────────────────────────────────────────────────────────────

def verb_parts(form):
    """'nahm sich mit' -> ['nahm', 'mit'];  'sandte / sendete' -> alternatives handled by the caller."""
    return [p for p in form.split() if p != "sich"]


def check(entry, slot, form, answer, morph, used=()):
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
    if not 5 <= len(ts) <= 16:
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
        for parts in alts:
            want = parts if (sep and len(parts) > 1) else parts[:1]
            if [m.lower() for m in marked] == [p.lower() for p in want]:
                ok_alt = parts
        if ok_alt is None:
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

    elif slot == "part":
        if [m.lower() for m in marked] != [form.lower()]:
            problems.append(f"brackets {marked} but the participle is «{form}»")
        low = {t.lower() for t in ts}
        aux = (entry.get("auxiliary") or "haben").lower()
        has_h, has_s = bool(low & AUX_HABEN), bool(low & AUX_SEIN)
        if not (has_h or has_s or low & AUX_PASSIVE):
            problems.append("no auxiliary verb: not a Perfekt")
        elif aux.startswith("sein") and not has_s and not (low & AUX_PASSIVE):
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
                    g = governing_case(ts, j)
                    cases = {c for c, _, _ in agree}
                    if g and g not in cases and not (ts[j - 1].lower() in PREP_TWO_WAY):
                        problems.append(f"«{ts[j - 1]}» requires {g}, but the phrase is {'/'.join(sorted(cases))}")

    elif slot.startswith("kasus"):
        case, num = form.split(":")
        if answer.get("note") in ("singular", "plural"):
            new = "SIN" if answer["note"] == "singular" else "PLU"
            if new != num:
                warnings.append(f"{answer['note']} instead of {'plural' if num == 'PLU' else 'singular'} (noted)")
            num = new
        noun = bare(word)
        if len(marked) != 2:
            problems.append(f"brackets {marked}: expected determiner and noun")
        else:
            dk, nk = idx
            det, nn = ts[dk], ts[nk]
            adjs = ts[dk + 1:nk]
            # the lexicon itself, then article/plural from words.json, then the compound's last element
            reads = noun_readings(morph, nn, noun, suffixes=False) or entry_noun_readings(entry, nn) \
                or noun_readings(morph, nn, noun)
            agree, _ = np_agreement(morph, det, adjs, nn, noun, reads)
            if not reads:
                problems.append(f"«{nn}» is not a form of «{noun}»")
            elif not agree:
                problems.append(f"«{' '.join(ts[dk:nk + 1])}» does not agree")
            else:
                fits = {(c, n) for c, n, _ in agree}
                if (case, num) not in fits:
                    problems.append(f"asked for {case} {num}, the phrase can only be "
                                    + ", ".join(f"{c} {n}" for c, n in sorted(fits)))
                else:
                    g = governing_case(ts, dk)
                    if g and g != case:
                        problems.append(f"«{ts[dk - 1]}» requires {g}")
                    elif not g and len({c for c, n in fits if n == num}) > 1:
                        warnings.append("case depends on the verb: check by eye")

    elif slot.startswith("pc"):
        if [m.lower() for m in marked] != [word.lower()]:
            problems.append(f"brackets {marked}, expected «{word}»")
        elif sum(1 for t in ts if t.lower() == word.lower()) != 1:
            problems.append(f"«{word}» appears more than once")

    status = "error" if problems else ("check" if warnings else "ok")
    return dict(status=status, problems=problems + warnings, de=plain, en=en, blanks=spans)


# ── command line ──────────────────────────────────────────────────────────────

def read_answers(path):
    s = open(path, encoding="utf-8").read()
    dec, i, out = json.JSONDecoder(), 0, []
    while True:
        while i < len(s) and s[i].isspace():
            i += 1
        if i >= len(s):
            return out
        o, i = dec.raw_decode(s, i)
        out.append(o)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    db = {w["id"]: w for w in json.load(open(os.path.join(HERE, "words.json"), encoding="utf-8"))}
    inv = json.load(open(os.path.join(HERE, "exercises_inventory.json"), encoding="utf-8"))
    out_path = os.path.join(HERE, "exercises_generated.json")
    done = json.load(open(out_path, encoding="utf-8")) if os.path.exists(out_path) else {}

    recheck = "--recheck" in sys.argv
    answers = []
    for p in [a for a in sys.argv[1:] if not a.startswith("--")]:
        answers += read_answers(p)
    # entries already checked (and possibly corrected in review) are kept unless --recheck
    answers = [a for a in answers if recheck or a["id"] not in done]
    morph = Morph()
    morph.load(with_suffixes({t for a in answers for t in toks(parse_bracketed(a.get("de", ""))[0])}))

    counts = collections.Counter()
    for a in answers:
        wid, slot = a["id"].split("|")
        if wid not in inv or slot not in inv[wid]["slots"]:
            print(f"?? unknown id {a['id']}"); continue
        s = inv[wid]["slots"][slot]
        used = [x["chosen"]["de"] for x in inv[wid]["slots"].values() if x["chosen"]]
        used += [e["de"] for e in db[wid].get("examples", [])]
        used += [v["de"] for k, v in done.items() if k.startswith(wid + "|") and k != a["id"] and v.get("de")]
        r = check(db[wid], slot, s["form"], a, morph, used)
        r["source"] = "generated" if not a.get("review") else "generated, rewritten in review"
        if a.get("review"):
            r["review"] = a["review"]
        r["label"] = s["label"]
        if a.get("note") == "singular":
            r["label"] = s["label"].replace("Plural", "Singular")
        elif a.get("note") == "plural":
            r["label"] = s["label"].replace("Singular", "Plural")
        r["form"] = s["form"]
        if slot.startswith("kasus") and a.get("note") in ("singular", "plural"):
            r["form"] = s["form"].split(":")[0] + (":SIN" if a["note"] == "singular" else ":PLU")
        done[a["id"]] = r
        counts[r["status"]] += 1
        if r["status"] != "ok":
            print(f"{r['status'].upper():<6} {a['id']:<34} {a.get('de') or ''}")
            for p in r["problems"]:
                print(f"         - {p}")
    json.dump(done, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n" + ", ".join(f"{k}: {v}" for k, v in counts.most_common()) + f"   -> {out_path}")


if __name__ == "__main__":
    main()
