#!/usr/bin/env python3
"""
vocab.py — Laura's German vocabulary manager
Usage:
  python vocab.py list                  show all words
  python vocab.py list --topic work     filter by topic
  python vocab.py list --type verb      filter by word type
  python vocab.py show nehmen           show full entry for a word
  python vocab.py add                   add a new word (AI-assisted)
  python vocab.py add --manual          add a word without AI
  python vocab.py edit nehmen           edit an existing entry
  python vocab.py delete nehmen         delete a word
  python vocab.py topics                show all topics
  python vocab.py family nehmen         show a verb family
  python vocab.py exercises nehmen      check / fill / replace the exercise sentences of a word
"""

import json
import sys
import os
import random
import re
import urllib.request
import urllib.error
from datetime import datetime

try:                                   # optional: full-form lexicon, see README "Data sources"
    from lexicon import Lexicon, changes_stem, german_definition
    LEXICON = Lexicon()
except ImportError:
    LEXICON = None
    german_definition = None
VERB_CLASSES = ["regular", "irregular", "mixed"]

try:                                   # exercise sentences: needs data/dictionary.dump as well
    import exercise_check as EX
    EX_OK = EX.available()
except ImportError:
    EX, EX_OK = None, False
MODEL = "claude-sonnet-5-5"


def norm_reflexive(v):
    """Reflexive is "akk", "dat" or False. Accepts old booleans and typed answers."""
    if v in (None, False, "", "no", "n", "false", "False", "—", "-"):
        return False
    v = str(v).strip().lower()
    if v.startswith("d"):
        return "dat"
    if v.startswith(("a", "y", "t")):          # akk, yes, true -> accusative (the usual case)
        return "akk"
    return False


def reflexive_label(v):
    return {"akk": "sich + Akk.", "dat": "sich + Dat."}.get(norm_reflexive(v), "")

DB_PATH  = os.path.join(os.path.dirname(__file__), "words.json")
# The API key lives OUTSIDE the repo, in ../Claude_API/.env, so it can never be
# committed or read by tools that only see this folder. A .env next to this file
# or an ANTHROPIC_API_KEY environment variable also work.
_HERE = os.path.dirname(os.path.abspath(__file__))
ENV_PATHS = [os.path.join(os.path.dirname(_HERE), "Claude_API", ".env"),
             os.path.join(_HERE, ".env")]

WORD_TYPES = ["noun", "verb", "adj/adv", "prep/conj", "expression", "construction", "other"]
GENDERS    = ["der", "die", "das"]
# Closed list of topics. A word gets 0 to 2 of them, and only when it is clearly
# ABOUT the domain. Core vocabulary (brauchen, bekommen, liegen) has no topic;
# "no topic" is a deliberate answer, not a gap. The FIRST definition decides; a
# secondary meaning earns a topic only if one of the examples illustrates it.
# The definitions below are what the model sees, so keep the exclusions sharp.
TOPICS = {
    "home & objects":
        "Housing, rooms, furnishings, household objects, clothing, cleaning and domestic maintenance. Exclude general physical actions merely illustrated with a household object.",
    "food & drink":
        "Food, beverages, preparation, eating, drinking and dining. Include verbs only when a food-related meaning is explicitly recorded.",
    "body & health":
        "Anatomy, bodily functions, physical sensations, illness, treatment, hygiene, recovery, sport. Include physical exhaustion; distinguish it from emotional distress.",
    "thinking & perception":
        "Knowledge, memory, attention, reasoning, judgement, decisions and sensory perception. Include looking and noticing; exclude general comparisons between objects.",
    "emotions & character":
        "Feelings, moods, preferences, temperament and personal dispositions. Exclude general usefulness, size or quality unless the meaning concerns a person's character.",
    "people & relationships":
        "Personal relationships, encounters, trust, cooperation, interpersonal behaviour and social interaction. Exclude actions simply because a person performs them.",
    "language & communication":
        "Speaking, writing, listening, naming, conveying information, stance adverbs and conventional conversational acts. An idiom belongs here only when its function is communicative.",
    "work & jobs":
        "Employment, occupations, workplace arrangements, professional responsibilities, vocational training and working conditions. Exclude generic effort, success or activity.",
    "science & academia":
        "Research, academic study, scientific methods, evidence, and scholarly institutions or outputs. Exclude general concepts merely because researchers use them.",
    "technology & media":
        "Devices, technical systems, digital tools, broadcasting, and media production or distribution. Not every act of reporting and not every artificial object.",
    "money & shopping":
        "Prices, payment, wealth, ownership, buying, selling and economic transactions. Exclude general exchange, receipt or waste without a financial meaning.",
    "society & politics":
        "Public institutions, law, governance, collective social structures, rights and public affairs. Distinguish from individual interpersonal relationships.",
    "culture & arts":
        "Literature, visual and performing arts, creative practices, cultural works and their creators. Exclude general attractiveness or beauty.",
    "nature & weather":
        "Animals, plants, landscapes, natural environments, weather and environmental processes. Exclude physical properties that apply equally to manufactured objects.",
    "travel & movement":
        "Journeys, transport, routes, destinations, navigation, locomotion and directional movement. Exclude manipulating an object solely because the object moves.",
    "time":
        "Temporal location, duration, frequency, sequence, deadlines and speed of occurrence. Exclude events merely because they occur in time.",
    "quantity & comparison":
        "Amount, extent, sufficiency, scarcity, similarity, difference and comparative scale.",
    "materials & physical properties":
        "Materials and observable physical characteristics: shape, texture, surface, structural integrity, physical force. Exclude generic handling actions.",
    "change & development":
        "Alteration, growth, decline, increase, decrease, transformation and persistence of a state. Exclude mere movement to a different place.",
    "goals, effort & outcomes":
        "Intentional aims, attempts, effort, obstacles, giving up, achievement and reward. Exclude ordinary actions, events, and evaluative adjectives such as useful or suitable.",
    "connectors & constructions":
        "Connectives, discourse particles, prepositions and reusable grammatical patterns that relate clauses or sentence elements. A grammatical category; not abstract vocabulary.",
}


def clean_topics(raw) -> list:
    """Keep only topics from the closed list, in canonical order, max 2."""
    if isinstance(raw, str):
        raw = [t.strip() for t in raw.split(",")]
    wanted = {str(t).strip().lower() for t in (raw or [])}
    return [t for t in TOPICS if t in wanted][:2]


# ── env / api key ──────────────────────────────────────────────────────────────

def load_api_key() -> str | None:
    """Load ANTHROPIC_API_KEY: environment variable first, then the .env files in ENV_PATHS."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        return os.environ["ANTHROPIC_API_KEY"].strip()
    for path in ENV_PATHS:
        if not os.path.exists(path):
            continue
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("ANTHROPIC_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


# ── AI enrichment ──────────────────────────────────────────────────────────────

def ai_enrich(word: str, api_key: str, word_type: str = None, vocabulary: list = None,
              context: str = None) -> dict | None:
    """
    Call Claude API to get structured info about a German word.
    Returns a dict with suggested fields, or None on failure.
    `vocabulary` is the list of words already in the database; the model may
    only propose related links to words in that list.
    """
    context_block = ""
    if context:
        context_block = (
            f"\n\nI met this word in this sentence: \"{context}\"\n"
            "Put the meaning the word has IN THIS SENTENCE first in \"definitions\". "
            "Also add three fields: \"context_en\": an English translation of my sentence; "
            "\"context_ok\": true if my sentence is correct, natural German, else false; "
            "\"context_fix\": the corrected sentence if context_ok is false, else null. "
            "Your two \"examples\" should show other uses than my sentence.")
    topic_lines = "\n".join(f"- {t}: {d}" for t, d in TOPICS.items())
    type_hint = f"\n\nIMPORTANT: Treat this word strictly as a {word_type}. Fill in all fields accordingly." if word_type else ""
    vocab_block = ""
    if vocabulary:
        vocab_block = ("\n\nMy database already contains these words. For the \"related\" field, "
                       "choose ONLY from this list, and only words with a real semantic relationship "
                       "to the new word. Do not list verb-family members (same root, different prefix) "
                       "unless they are genuinely confusable in meaning.\n"
                       + ", ".join(vocabulary))
    prompt = f"""You are a German language expert. I am learning German and want to add the word "{word}" to my vocabulary database.

Please analyse this word and return a JSON object with the following fields. Be precise and use only English for definitions and translations (never Italian or German in the meaning field).

Return ONLY valid JSON, no explanation, no markdown, no code fences.{type_hint}

{{
  "word": "the word in its canonical form (e.g. with gender for nouns: 'die Sehnsucht', infinitive for verbs: 'erinnern'; reflexive verbs MUST include 'sich': 'sich erinnern')",
  "type": "one of: noun, verb, adj/adv, prep/conj, expression, construction, other",
  "usage": "for adj/adv: adjective only, adverb only, or both; for prep/conj: preposition only, conjunction only, or both — else null",
  "gender": "der/die/das — only for nouns, else null",
  "plural": "plural form with article e.g. 'die Sehnsüchte' — only for nouns, else null",
  "auxiliary": "haben or sein — only for verbs, else null",
  "past_tense": "simple past (Präteritum) e.g. 'erinnerte' — only for verbs, else null",
  "past_participle": "e.g. 'erinnert' — only for verbs, else null",
  "present_3sg": "er/sie/es form in the present, in the same format as past_tense, e.g. 'nimmt mit', 'freut sich' — only for verbs, else null",
  "verb_class": "regular (weak: kaufte, gekauft), irregular (strong: nahm, genommen) or mixed (weak endings with a changed stem: dachte, gedacht) — only for verbs, else null",
  "is_separable": true or false — only for verbs, else null,
  "reflexive": "akk" if the reflexive pronoun is accusative (ich freue mich), "dat" if dative (ich nehme mir etwas vor), false if the verb is not reflexive. Only verbs that cannot drop sich, or whose meaning changes with sich, are reflexive; waschen (sich waschen = wash oneself) is NOT. Only for verbs, else null,
  "preposition": "e.g. 'an + AKK' if the verb requires a fixed preposition, else null",
  "also_adverb": null,
  "family_root": "the root verb — for compounds e.g. 'nehmen' for 'mitnehmen'; for root verbs use the word itself e.g. 'schlafen' for 'schlafen' (never null for verbs)",
  "prefix": "the prefix e.g. 'mit-' for 'mitnehmen', else null",
  "definitions": [
    {{"meaning": "primary English meaning", "note": "optional note e.g. 'used with an + AKK' or null"}},
    {{"meaning": "secondary meaning if exists", "note": null}}
  ],
  "examples": [
    {{"de": "A natural German example sentence", "en": "English translation"}},
    {{"de": "A second example showing a different use", "en": "English translation"}}
  ],
  "compound_parts": "for a compound noun or adjective, its parts in order as a list, nouns with article, linking elements as separate items: [\"die Kündigung\", \"-s-\", \"die Frist\"]; null if not a compound",
  "topics": ["0 to 2 topics from the list below, ONLY if the word is clearly about that domain; core vocabulary like brauchen or bekommen gets an empty list"],
  "notes": "one sentence max — only if there is something genuinely important to note, e.g. easy confusion with another word, or a non-neutral register (umgangssprachlich, gehoben, Schweizerdeutsch), or null",
  "related": [
    {{"word": "an existing word from my list", "kind": "one of: synonym, antonym, contrast, derived, compound"}}
  ]
}}

"related" kinds: synonym = same meaning; antonym = opposite; contrast = easily confused,
worth telling apart (e.g. kennen / wissen); derived = same stem, different word class
(e.g. wählen / die Wahl); compound = one word is a part of the other (der Staub / der Staubsauger,
das Bild / der Bildschirm). Return an empty list if nothing in my list fits.

Topics (use the names exactly as written). Rules: 0 to 2 topics; the FIRST definition
decides; a secondary meaning earns a topic only if one of your example sentences
illustrates it; core vocabulary gets an empty list, which is the correct answer for
words like brauchen, bekommen, liegen, nötig.
{topic_lines}

Word to analyse: {word}{type_hint}{context_block}{vocab_block}"""

    payload = json.dumps({
        "model": MODEL,
        "max_tokens": 1500,
        "messages": [{"role": "user", "content": prompt}]
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
            raw = data["content"][0]["text"].strip()
            raw = re.sub(r'^```[a-z]*\n?', '', raw)
            raw = re.sub(r'\n?```$', '', raw)
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        print(f"  ✗ API error {e.code}: {e.read().decode()}")
        return None
    except Exception as e:
        print(f"  ✗ Could not reach API: {e}")
        return None


def call_claude(prompt: str, api_key: str, max_tokens: int = 2000) -> str | None:
    """Plain text answer from the API, or None (the reason is printed)."""
    payload = json.dumps({"model": MODEL, "max_tokens": max_tokens,
                          "messages": [{"role": "user", "content": prompt}]}).encode("utf-8")
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=payload, headers={
        "Content-Type": "application/json", "x-api-key": api_key, "anthropic-version": "2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read())["content"][0]["text"]
    except urllib.error.HTTPError as e:
        print(f"  ✗ API error {e.code}: {e.read().decode()}")
    except Exception as e:
        print(f"  ✗ Could not reach API: {e}")
    return None


# ── exercise sentences ─────────────────────────────────────────────────────────
# Each word gets a fixed set of gap-fill exercises (see README, field `exercises`). They are filled in
# this order: exercises the word already has (if they still pass the check), your own sentence, the
# other examples, and only then sentences written by the API. Every sentence goes through
# exercise_check.py before it is kept.

def stem_changes(entry: dict) -> bool:
    if "changes_stem" not in globals():
        return False
    return changes_stem(entry["word"], entry.get("present_3sg"), entry.get("prefix"), entry.get("is_separable"))


def _spec_form(entry: dict, slot: str, form=None):
    """The form a slot tests, as the checker expects it."""
    if slot == "praet":
        return entry.get("past_tense")
    if slot == "praes":
        return entry.get("present_3sg")
    if slot == "part":
        return (entry.get("past_participle") or "").split("/")[0].strip()
    if slot == "refl":
        return "mir/dir" if entry.get("reflexive") == "dat" else "mich/dich"
    if slot.startswith("kasus"):
        return form
    return entry["word"]


def _exercise(spec: dict, r: dict, source: str) -> dict:
    ex = {"slot": spec["slot"], "label": spec["label"], "de": r["de"], "en": r["en"],
          "blanks": r["blanks"], "source": source}
    if spec["slot"].startswith("kasus"):
        ex["form"] = spec["form"]
        ex["label"] = EX.kasus_label(spec["form"])
    return ex


def _generate(entry, specs, morph, api_key, used, feedback=None):
    """Ask the API for the given slots; returns {slot: exercise} for the ones that pass, and problems."""
    text = call_claude(EX.generation_prompt(entry, specs, used, feedback), api_key)
    if not text:
        return {}, {}
    answers = {a.get("id", "").split("|")[-1]: a for a in EX.read_answers_text(text)}
    morph.load(EX.with_suffixes({t for a in answers.values() for t in EX.toks(a.get("de", "").replace("[", "").replace("]", ""))}))
    got, problems = {}, {}
    for spec in specs:
        a = answers.get(spec["slot"])
        if not a:
            problems[spec["slot"]] = ["no answer"]
            continue
        if "skip" in a:
            problems[spec["slot"]] = [f"skipped: {a['skip']}"]
            continue
        sp = dict(spec)
        if sp["slot"].startswith("kasus") and a.get("note") in ("singular", "plural"):
            sp["form"] = sp["form"].split(":")[0] + (":SIN" if a["note"] == "singular" else ":PLU")
        r = EX.check(entry, sp["slot"], _spec_form(entry, sp["slot"], sp["form"]), a, morph, used)
        if r["status"] in ("ok", "check"):
            got[spec["slot"]] = _exercise(sp, r, "generated")
            used.append(r["de"])
        else:
            problems[spec["slot"]] = r["problems"]
    return got, problems


def _own_exercise(entry, spec, morph, used):
    """Let the learner type a sentence with [brackets]; returns an exercise or None."""
    while True:
        de = input("    your sentence with [brackets] (Enter: skip): ").strip()
        if not de:
            return None
        morph.load(EX.with_suffixes(set(EX.toks(de.replace("[", "").replace("]", "")))))
        r = EX.check(entry, spec["slot"], _spec_form(entry, spec["slot"], spec["form"]), {"de": de, "en": "-"},
                     morph, used, min_words=3)
        if r["status"] not in ("ok", "check"):
            print("    ✗ " + "; ".join(r["problems"]))
            continue
        if r["problems"]:
            print("    (note: " + "; ".join(r["problems"]) + ")")
        r["en"] = ask("  English")
        return _exercise(spec, r, "own")


def build_exercises(entry: dict, api_key: str | None, interactive: bool = True) -> None:
    """Fill entry["exercises"]: keep what still fits, use your sentences, generate the rest, let you review."""
    if not EX_OK:
        print("  (exercises skipped: exercise_check.py or data/dictionary.dump not found)")
        return
    specs = EX.slots_for(entry, stem_changes)
    if not specs:
        entry.pop("exercises", None)
        return
    print("\n  Exercises: checking the sentences you have…")
    morph = EX.Morph()
    examples = sorted(entry.get("examples", []), key=lambda e: e.get("source") != "own")
    old = entry.get("exercises", [])
    morph.load(EX.with_suffixes({t for x in examples + old for t in EX.toks(x["de"])}))
    chosen, used = {}, []

    # 1. exercises the word already has, if they still pass (forms may have been edited)
    for e in old:
        spec = next((s for s in specs if s["slot"] == e["slot"]), None)
        if not spec:
            continue
        form = e.get("form") if e["slot"].startswith("kasus") else _spec_form(entry, e["slot"])
        r = EX.check(entry, e["slot"], form, {"de": EX.show(e), "en": e.get("en") or "-"}, morph, min_words=3)
        if r["status"] in ("ok", "check"):
            chosen[e["slot"]] = e
            used.append(e["de"])
        else:
            print(f"  ! {spec['label']}: «{EX.show(e)}» no longer fits ({'; '.join(r['problems'])})")

    # 2. your own sentence, then the other examples (each sentence serves one exercise)
    for spec in specs:
        if spec["slot"] in chosen:
            continue
        for ex in examples:
            if ex["de"] in used:
                continue
            sp = dict(spec)
            if sp["slot"].startswith("kasus"):
                other = next((c for k, c in chosen.items() if k.startswith("kasus")), None)
                r = EX.find_in(entry, sp, ex["de"], ex.get("en", ""), morph, used)
                if not r or (other and r["form"] == other.get("form")):
                    continue
                sp["form"] = r["form"]
            else:
                r = EX.find_in(entry, sp, ex["de"], ex.get("en", ""), morph, used)
                if not r:
                    continue
            chosen[spec["slot"]] = _exercise(sp, r, "own" if ex.get("source") == "own" else "example")
            used.append(ex["de"])
            break

    # 3. noun slots still empty get a random case (not one already used)
    rnd = random.Random(entry["id"])
    for spec in specs:
        if spec["slot"].startswith("kasus"):
            if spec["slot"] in chosen:
                spec["form"] = chosen[spec["slot"]].get("form")
            else:
                taken = {c.get("form", ":").split(":")[0] for k, c in chosen.items() if k.startswith("kasus")}
                spec["form"] = EX.kasus_options(entry, taken, rnd)
            if spec["form"]:
                spec["label"] = EX.kasus_label(spec["form"])

    # 4. the API writes the rest; one retry for the ones that fail the check
    missing = [s for s in specs if s["slot"] not in chosen and (not s["slot"].startswith("kasus") or s["form"])]
    problems = {}
    if missing and api_key:
        print(f"  Writing {len(missing)} exercise sentence(s) with AI…")
        used_all = used + [e["de"] for e in examples]
        got, problems = _generate(entry, missing, morph, api_key, used_all)
        chosen.update(got)
        retry = [s for s in missing if s["slot"] in problems and not problems[s["slot"]][0].startswith("skipped")]
        if retry:
            fb = [f"{s['slot']}: {'; '.join(problems[s['slot']])}" for s in retry]
            got, problems2 = _generate(entry, retry, morph, api_key, used_all, feedback=fb)
            chosen.update(got)
            problems = {k: v for k, v in {**problems, **problems2}.items() if k not in chosen}
    elif missing:
        print(f"  ({len(missing)} exercise(s) need a sentence; no API key, so write them yourself below)")

    # 5. review
    def ordered():
        return [chosen[s["slot"]] for s in specs if s["slot"] in chosen]

    while interactive:
        print("\n  Exercises:")
        for i, s in enumerate(specs, 1):
            e = chosen.get(s["slot"])
            if e:
                print(f"    {i}. {e['label']:<28} {EX.show(e)}   ({e['source']})")
            else:
                why = "; ".join(problems.get(s["slot"], [])) or "no sentence yet"
                print(f"    {i}. {s['label'] or 'case (none)':<28} —  ({why})")
        val = input("  Enter to keep; numbers to replace or fill (e.g. 2,4): ").strip()
        if not val:
            break
        for n in sorted({int(x) for x in re.findall(r"\d+", val) if 1 <= int(x) <= len(specs)}):
            spec = specs[n - 1]
            if spec["slot"].startswith("kasus") and not spec["form"]:
                continue
            print(f"  {n}. {spec['label']}")
            e = _own_exercise(entry, spec, morph, used)
            if not e and api_key and input("    generate a new one with AI instead? (y/n) [y]: ").strip().lower() in ("", "y"):
                old_s = chosen.get(spec["slot"])
                fb = [f"the learner did not want: «{old_s['de']}»"] if old_s else None
                got, pr = _generate(entry, [spec], morph, api_key, used + [e2["de"] for e2 in examples], fb)
                e = got.get(spec["slot"])
                if not e:
                    print("    ✗ " + "; ".join(pr.get(spec["slot"], ["no answer"])))
            if e:
                chosen[spec["slot"]] = e
    entry["exercises"] = ordered()
    empty = len(specs) - len(entry["exercises"])
    print(f"  {len(entry['exercises'])} exercise(s)" + (f", {empty} without a sentence" if empty else ""))


# ── helpers ────────────────────────────────────────────────────────────────────

def load() -> list:
    if not os.path.exists(DB_PATH):
        return []
    with open(DB_PATH, encoding="utf-8") as f:
        return json.load(f)

def save(words: list):
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(words, f, ensure_ascii=False, indent=2)
    print(f"  ✓ Saved — {len(words)} entries in database.")

def make_id(word: str) -> str:
    word = word.lower().strip()
    word = re.sub(r'[äöü]', lambda m: {'ä':'ae','ö':'oe','ü':'ue'}[m.group()], word)
    word = re.sub(r'ß', 'ss', word)
    word = re.sub(r'[^a-z0-9]+', '-', word)
    return word.strip('-')

def find(words: list, query: str):
    q = query.lower().strip()
    for w in words:
        if w["word"].lower() == q or w["id"] == make_id(query):
            return w
    return None

def ask(prompt: str, default: str = "") -> str:
    val = input(f"  {prompt}" + (f" [{default}]" if default else "") + ": ").strip()
    return val if val else default

def ask_list(prompt: str) -> list:
    val = input(f"  {prompt} (comma-separated, or Enter to skip): ").strip()
    if not val:
        return []
    return [v.strip() for v in val.split(",") if v.strip()]

def ask_choice(prompt: str, options: list, default: str = "") -> str:
    print(f"  {prompt}")
    for i, opt in enumerate(options, 1):
        print(f"    {i}) {opt}")
    while True:
        val = input(f"  Choose 1-{len(options)}" + (f" [{default}]" if default else "") + ": ").strip()
        if not val and default:
            return default
        if val.isdigit() and 1 <= int(val) <= len(options):
            return options[int(val) - 1]
        print(f"  Please enter a number between 1 and {len(options)}.")

def confirm_or_edit(label: str, value, options: list = None):
    """Show a suggested value and let the user confirm or override."""
    if value is None or value == [] or value == "null":
        display = "—"
    elif isinstance(value, list):
        display = ", ".join(str(v) for v in value)
    elif isinstance(value, bool):
        display = "yes" if value else "no"
    else:
        display = str(value)

    if options:
        override = input(f"  {label} [{display}] (Enter to keep, or number to change): ").strip()
        if override.isdigit() and 1 <= int(override) <= len(options):
            return options[int(override) - 1]
        return value
    else:
        override = input(f"  {label} [{display}]: ").strip()
        if not override:
            return value
        if isinstance(value, bool):
            return override.lower() in ("y", "yes", "true", "1")
        if isinstance(value, list):
            return [v.strip() for v in override.split(",") if v.strip()]
        return override

def print_entry(w: dict):
    print()
    print(f"  ┌─ {w['word']}  [{w['type']}]")

    if w["type"] == "noun":
        print(f"  │  gender: {w.get('gender','?')}   plural: {w.get('plural','?')}")
    elif w["type"] == "verb":
        aux  = w.get("auxiliary", "")
        pt   = w.get("past_tense", "")
        pp   = w.get("past_participle", "")
        sep  = "separable" if w.get("is_separable") else "inseparable"
        ref  = f" · {reflexive_label(w.get('reflexive'))}" if w.get("reflexive") else ""
        prep = f" · {w['preposition']}" if w.get("preposition") else ""
        cls  = f"{w['verb_class']} · " if w.get("verb_class") else ""
        p3   = f"er {w['present_3sg']} · " if w.get("present_3sg") else ""
        print(f"  │  {cls}{p3}{aux} · {pt} · {pp}   ({sep}{ref}{prep})")
        if w.get("imperative") or w.get("konjunktiv_2"):
            bits = [w["imperative"] + "!" if w.get("imperative") else "", "Konj. II " + w["konjunktiv_2"] if w.get("konjunktiv_2") else ""]
            print(f"  │  {' · '.join(b for b in bits if b)}")
        if w.get("family_root") and w["family_root"] != w["word"]:
            print(f"  │  family: {w['family_root']}  (prefix: {w.get('prefix','')})")

    if w.get("usage"):
        print(f"  │  usage: {w['usage']}")

    print(f"  │")
    for i, d in enumerate(w.get("definitions", []), 1):
        note = f"  -> {d['note']}" if d.get("note") else ""
        print(f"  │  {i}. {d['meaning']}{note}")
    if w.get("definition_de"):
        print(f"  │  DE: {w['definition_de']}")

    if w.get("examples"):
        print(f"  │")
        for ex in w["examples"]:
            print(f"  │  > {ex['de']}")
            print(f"  │    {ex['en']}")

    if w.get("topics"):
        print(f"  │  topics:  {', '.join(w['topics'])}")
    if w.get("related"):
        rel = ", ".join(f"{r['word']} ({r['kind']})" if isinstance(r, dict) else str(r)
                        for r in w["related"])
        print(f"  │  related: {rel}")
    if w.get("notes"):
        print(f"  │  note: {w['notes']}")
    if w.get("exercises") and EX:
        print(f"  │")
        for e in w["exercises"]:
            print(f"  │  ▢ {e['label']:<26} {EX.show(e)}")

    print(f"  └─ added: {w.get('added','?')}")
    print()



# ── related word linking ───────────────────────────────────────────────────────

def normalise(word: str) -> str:
    w = word.lower().strip()
    w = re.sub(r"^(der|die|das|sich|ein|eine|einen|einem)\s+", "", w)
    return w.strip()

RELATED_KINDS = ["synonym", "antonym", "contrast", "derived", "compound"]

def related_words(entry: dict) -> set:
    return {r["word"] for r in entry.get("related", []) if isinstance(r, dict)}

def confirm_related(words: list, proposed: list) -> list:
    """Show the AI's proposed links, keep only those that exist, let the user adjust."""
    by_word = {w["word"]: w for w in words}
    by_norm = {normalise(w["word"]): w for w in words}
    kept = []
    for r in proposed or []:
        if not isinstance(r, dict):
            continue
        tgt = by_word.get(r.get("word", "")) or by_norm.get(normalise(r.get("word", "")))
        kind = r.get("kind", "contrast")
        if tgt and kind in RELATED_KINDS:
            kept.append({"word": tgt["word"], "kind": kind})
    if kept:
        print("\n  Related words proposed:")
        for i, r in enumerate(kept, 1):
            print(f"    {i}. {r['word']:<26} ({r['kind']})")
        print("  Enter to keep, numbers to drop (e.g. 2,3), or '+word:kind' to add.")
    else:
        print("\n  No related words proposed. Type '+word:kind' to add, or Enter to skip.")
    while True:
        val = input("  > ").strip()
        if not val:
            return kept
        if val.startswith("+"):
            name, _, kind = val[1:].partition(":")
            tgt = by_word.get(name.strip()) or by_norm.get(normalise(name))
            kind = (kind or "contrast").strip()
            if not tgt:
                print(f"    '{name}' is not in the database.")
            elif kind not in RELATED_KINDS:
                print(f"    kind must be one of {', '.join(RELATED_KINDS)}")
            else:
                kept.append({"word": tgt["word"], "kind": kind})
                print(f"    added {tgt['word']} ({kind})")
        else:
            drop = {int(x) for x in re.findall(r"\d+", val)}
            kept = [r for i, r in enumerate(kept, 1) if i not in drop]
            print(f"    kept {len(kept)}")

def make_bidirectional(words: list, entry: dict) -> int:
    """Ensure every link from `entry` also exists on the target, with the same kind."""
    updated = 0
    by_word = {w["word"]: w for w in words}
    for r in entry.get("related", []):
        tgt = by_word.get(r["word"])
        if not tgt or tgt["id"] == entry["id"]:
            continue
        if entry["word"] not in related_words(tgt):
            tgt.setdefault("related", []).append({"word": entry["word"], "kind": r["kind"]})
            updated += 1
    return updated


# ── commands ───────────────────────────────────────────────────────────────────

def cmd_list(args):
    words = load()
    topic_filter = None
    type_filter  = None
    for i, a in enumerate(args):
        if a == "--topic" and i + 1 < len(args):
            topic_filter = args[i + 1].lower()
        if a == "--type" and i + 1 < len(args):
            type_filter = args[i + 1].lower()

    results = words
    if topic_filter:
        results = [w for w in results if any(topic_filter in t.lower() for t in w.get("topics", []))]
    if type_filter:
        results = [w for w in results if w["type"] == type_filter]

    if not results:
        print("  No entries found.")
        return

    print(f"\n  {'WORD':<30} {'TYPE':<14} {'TOPICS'}")
    print(f"  {'─'*30} {'─'*14} {'─'*30}")
    for w in sorted(results, key=lambda x: x["word"].lower()):
        topics = ", ".join(w.get("topics", []))
        print(f"  {w['word']:<30} {w['type']:<14} {topics}")
    print(f"\n  {len(results)} entry/entries.\n")


def cmd_show(args):
    if not args:
        print("  Usage: python vocab.py show <word>")
        return
    words = load()
    w = find(words, " ".join(args))
    if not w:
        print(f"  X '{' '.join(args)}' not found.")
        return
    print_entry(w)


def cmd_topics(args):
    words = load()
    all_topics = {}
    for w in words:
        for t in w.get("topics", []):
            all_topics[t] = all_topics.get(t, 0) + 1
    print("\n  Topics in your vocabulary:\n")
    for topic, desc in TOPICS.items():
        print(f"  . {topic:<34} {all_topics.get(topic, 0):>4}   {desc.split('.')[0]}")
    for topic, count in sorted(all_topics.items()):
        if topic not in TOPICS:
            print(f"  ! {topic:<28} {count:>4}   (not in the closed list)")
    print(f"  . {'(no topic)':<28} {sum(1 for w in words if not w.get('topics')):>4}")
    print()


def cmd_family(args):
    if not args:
        print("  Usage: python vocab.py family <root-verb>")
        return
    root = " ".join(args).lower()
    words = load()
    members = [w for w in words if w.get("family_root", "").lower() == root]
    if not members:
        print(f"  No family found for '{root}'.")
        return
    print(f"\n  Verb family: {root}\n")
    for m in sorted(members, key=lambda x: x["word"]):
        prefix  = f"  [{m.get('prefix','')}]" if m.get("prefix") else "  [root]"
        meaning = m["definitions"][0]["meaning"] if m.get("definitions") else ""
        print(f"  {prefix:<12} {m['word']:<25} {meaning}")
    print()


def lexicon_verb(entry: dict) -> None:
    """Compare the verb forms in `entry` with the lexicon; fill present_3sg and verb_class.
    The lexicon is right far more often than the model, but it cannot know which meaning
    you mean when a verb has two conjugations (schaffte / schuf), so you decide."""
    if not (LEXICON and LEXICON.ok):
        return
    v = LEXICON.verb(entry["word"], entry.get("prefix"), entry.get("is_separable"),
                     entry.get("past_tense"), entry.get("past_participle"),
                     reflexive_case=norm_reflexive(entry.get("reflexive")))
    if not v:
        print("  (lexicon: verb not found, keeping the forms above)")
        return
    for field in ("past_tense", "past_participle", "present_3sg", "verb_class"):
        mine, lex = entry.get(field), v[field]
        # exact comparison: ß and ss are NOT interchangeable (vergaß, not vergass).
        # The lexicon already prefers current spelling over old forms like schloß.
        if not lex or (mine or "") == lex:
            entry[field] = mine or lex
            continue
        if not mine:
            entry[field] = lex
            continue
        print(f"  ! {field}: you have '{mine}', the lexicon says '{lex}'")
        entry[field] = lex if ask("    Use the lexicon form? (y/n)", "y").lower() == "y" else mine
    # filled silently: both come straight from the lexicon and need no judgement
    if v.get("imperative"):
        entry["imperative"] = v["imperative"]
    if v.get("konjunktiv_2_common"):
        entry["konjunktiv_2"] = v["konjunktiv_2_common"]
    if v["alternatives"]:
        print(f"  (lexicon: also conjugated as {', '.join(v['alternatives'])} in another meaning)")
    extra = "".join(f" · {x}" for x in (entry.get("imperative") and entry["imperative"] + "!",
                                         entry.get("konjunktiv_2") and "Konj. II " + entry["konjunktiv_2"]) if x)
    print(f"  lexicon: {entry['verb_class']} · er {entry['present_3sg']} · {entry['past_tense']} · {entry['past_participle']}{extra}")


def own_example(sentence: str, s: dict) -> dict | None:
    """Turn the learner's sentence into the first example, marked source='own'.
    If the model flagged it as incorrect, offer the corrected version."""
    if not sentence:
        return None
    if s.get("context_ok") is False and s.get("context_fix"):
        print(f"\n  Your sentence:   {sentence}")
        print(f"  Suggested fix:   {s['context_fix']}")
        if ask("  Use the corrected sentence? (y/n)", "y").lower() == "y":
            sentence = s["context_fix"]
    en = s.get("context_en") or ""
    en = confirm_or_edit("English for your sentence", en) if en else ask("English for your sentence")
    return {"de": sentence, "en": en, "source": "own"}


def wiktionary_definition(entry: dict) -> None:
    """Look up a German definition (German Wiktionary) matching the English meaning."""
    if not german_definition or entry.get("definition_de"):
        return
    meanings = [d["meaning"] for d in entry.get("definitions", [])]
    print("  (looking up a German definition in Wiktionary…)")
    g = german_definition(entry["word"], entry.get("type"), meanings)
    if g:
        g = confirm_or_edit("German definition (Enter to keep, '-' to drop)", g)
        if g and g.strip() != "-":
            entry["definition_de"] = g


def lexicon_noun(entry: dict) -> None:
    """Warn if gender or plural disagree with the lexicon."""
    if not (LEXICON and LEXICON.ok):
        return
    n = LEXICON.noun(entry["word"])
    if not n:
        print("  (lexicon: noun not found)")
        return
    if entry.get("gender") and n["genders"] and entry["gender"] not in n["genders"]:
        print(f"  ! gender: you have '{entry['gender']}', the lexicon says {' / '.join(n['genders'])}")
        if ask("    Use the lexicon gender? (y/n)", "y").lower() == "y":
            entry["gender"] = n["genders"][0]
            entry["word"] = entry["gender"] + " " + re.sub(r"^(der|die|das)\s+", "", entry["word"])
    pl = re.sub(r"^die\s+", "", entry.get("plural") or "")
    if pl and n["plurals"] and pl not in n["plurals"]:
        print(f"  ! plural: you have '{pl}', the lexicon has {' / '.join(n['plurals'])} (some nouns have two)")


def cmd_add(args):
    manual  = "--manual" in args
    words   = load()
    api_key = load_api_key()

    print("\n  -- Add a new word --\n")

    word = ask("Word (German)")
    if not word:
        print("  Cancelled.")
        return

    existing = find(words, word)
    if existing:
        print(f"\n  X '{word}' already exists. Use 'show' to view it.")
        return

    # ── ask word type FIRST so AI gets the right context ─────────────────────
    print()
    word_type = ask_choice("Word type", WORD_TYPES)

    # ── the learner's own sentence (optional) ───────────────────────────────
    # Asked before the lookup, so the definition follows the meaning in YOUR sentence.
    print()
    my_sentence = ask("Your sentence with this word (where you met it; Enter to skip)")

    # ── AI enrichment ─────────────────────────────────────────────────────────
    suggestion = None
    if not manual and api_key:
        print(f"\n  Looking up '{word}' as {word_type} with AI...\n")
        suggestion = ai_enrich(word, api_key, word_type=word_type,
                               vocabulary=[w["word"] for w in words],
                               context=my_sentence or None)
        if suggestion:
            # override type from AI with what the user chose
            suggestion["type"] = word_type
            print("  AI suggestions ready. Press Enter to accept each, or type to override.\n")
        else:
            print("  AI lookup failed — falling back to manual entry.\n")
    elif not manual and not api_key:
        print("  (No API key found in .env — using manual entry)\n")

    s = suggestion or {}

    # canonical word form — AI may suggest a better form for the chosen type
    canonical = s.get("word", word)
    if canonical and canonical != word:
        print(f"  AI suggests canonical form: {canonical}")
        use_can = ask("  Use this? (y/n)", "y")
        if use_can.lower() == "y":
            word = canonical

    # if reflexive verb, auto-suggest 'sich' prefix
    if word_type == 'verb':
        is_reflexive = s.get('reflexive', False) if suggestion else False
        if is_reflexive and not word.lower().startswith('sich '):
            suggested = 'sich ' + word
            print(f"  Reflexive verb — canonical form should be '{suggested}'")
            use_sich = ask("  Add 'sich' prefix? (y/n)", "y")
            if use_sich.lower() == 'y':
                word = suggested

    word_id = make_id(word)

    entry = {
        "id":          word_id,
        "word":        word,
        "type":        word_type,
        "definitions": [],
        "examples":    [],
        "topics":      [],
        "notes":       None,
        "added":       datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    # ── type-specific fields ──────────────────────────────────────────────────
    if word_type == "noun":
        if suggestion:
            entry["gender"] = confirm_or_edit("Gender", s.get("gender"), GENDERS)
            entry["plural"] = confirm_or_edit("Plural", s.get("plural"))
        else:
            entry["gender"] = ask_choice("Gender", GENDERS)
            entry["plural"] = ask("Plural form (e.g. die Erinnerungen)")
        lexicon_noun(entry)

    elif word_type == "verb":
        if suggestion:
            entry["auxiliary"]       = confirm_or_edit("Auxiliary", s.get("auxiliary"), ["haben", "sein"])
            entry["past_tense"]      = confirm_or_edit("Past tense", s.get("past_tense"))
            entry["past_participle"] = confirm_or_edit("Past participle", s.get("past_participle"))
            entry["present_3sg"]     = s.get("present_3sg")
            entry["verb_class"]      = s.get("verb_class") if s.get("verb_class") in VERB_CLASSES else None
            entry["is_separable"]    = confirm_or_edit("Separable?", s.get("is_separable", False))
            entry["reflexive"]       = norm_reflexive(confirm_or_edit(
                "Reflexive (akk / dat / no)", norm_reflexive(s.get("reflexive")) or "no"))
            prep = confirm_or_edit("Preposition", s.get("preposition"))
            if prep and str(prep) not in ("—", "None", "null"):
                entry["preposition"] = prep
            family = confirm_or_edit("Family root", s.get("family_root"))
            if family and str(family) not in ("—", "None", "null", word):
                entry["family_root"] = family
                prefix = confirm_or_edit("Prefix", s.get("prefix"))
                if prefix and str(prefix) not in ("—", "None", "null"):
                    entry["prefix"] = prefix
            else:
                entry["family_root"] = word
        else:
            entry["auxiliary"]       = ask_choice("Auxiliary", ["haben", "sein"])
            entry["past_tense"]      = ask("Simple past (Präteritum)")
            entry["past_participle"] = ask("Past participle")
            entry["present_3sg"]     = None
            entry["verb_class"]      = None
            entry["is_separable"]    = ask("Separable? (y/n)", "n").lower() == "y"
            entry["reflexive"]       = norm_reflexive(ask("Reflexive (akk / dat / no)", "no"))
            prep = ask("Preposition + case (or Enter to skip)")
            if prep:
                entry["preposition"] = prep
            family = ask("Family root verb (or Enter if this IS the root)")
            if family:
                entry["family_root"] = family
                prefix = ask("Prefix (e.g. mit-)")
                if prefix:
                    entry["prefix"] = prefix
            else:
                entry["family_root"] = word
        # prefix is known only now, so the lexicon check comes last
        lexicon_verb(entry)
        if not entry.get("present_3sg"):
            entry["present_3sg"] = ask("er/sie/es form, present (e.g. nimmt mit)")
        if entry.get("verb_class") not in VERB_CLASSES:
            entry["verb_class"] = ask_choice("Verb class", VERB_CLASSES, "regular")

    elif word_type == "adj/adv":
        USAGE_OPTIONS = ["both", "adjective only", "adverb only"]
        if suggestion:
            entry["usage"] = confirm_or_edit("Usage", s.get("usage", "both"), USAGE_OPTIONS)
        else:
            entry["usage"] = ask_choice("Usage", USAGE_OPTIONS, "both")

        # ── derived_from detection ────────────────────────────────────────────
        # Check if this adj/adv looks like a past or present participle of a verb
        bare = word.lower().strip()
        is_participle_shape = bool(re.match(
            r'^(ge[a-zäöüß]{3,}(t|en)|'   # ge- + stem(3+) + -t/-en
            r'[a-zäöüß]{4,}iert|'          # -iert (4+ chars before)
            r'(ver|zer|be|er|ent|miss|über|unter|ab|an|auf|aus|durch|nach|vor|zu)'
            r'[a-zäöüß]{3,}(t|en)|'        # prefix + stem(3+) + -t/-en
            r'[a-zäöüß]{4,}end)$',         # -end present participle (4+ chars)
            bare
        ))

        derived_from = None
        if is_participle_shape:
            # First: look for a verb in DB whose past_participle matches exactly
            db_match = None
            for w_db in words:
                if w_db.get("type") != "verb":
                    continue
                pp = (w_db.get("past_participle") or "").lower().strip()
                verb_bare = re.sub(r"^sich\s+", "", w_db["word"].lower()).strip()
                if pp == bare or verb_bare == bare:
                    db_match = w_db["word"]
                    break

            if db_match:
                print(f"\n  ✦ '{word}' looks like a participle-adjective.")
                print(f"    Found in database: derived from '{db_match}'")
                use_it = ask("  Set derived_from to this verb? (y/n/other)", "y").strip().lower()
                if use_it == "y":
                    derived_from = db_match
                elif use_it not in ("n", ""):
                    # they typed something else — use it as the derived_from value
                    derived_from = use_it
            else:
                # Not in DB — if it looks like a participle, ask anyway
                print(f"\n  ✦ '{word}' looks like it could be a participle-adjective.")
                source = ask("  Derived from which verb? (or Enter to skip)").strip()
                if source:
                    derived_from = source

        else:
            # Not a participle shape — still offer the field in case user knows
            source = ask("  Derived from a verb? (e.g. entspannen → entspannt, or Enter to skip)").strip()
            if source:
                derived_from = source

        if derived_from:
            entry["derived_from"] = derived_from

    elif word_type == "prep/conj":
        USAGE_OPTIONS = ["both", "preposition only", "conjunction only"]
        if suggestion:
            entry["usage"] = confirm_or_edit("Usage", s.get("usage", "both"), USAGE_OPTIONS)
        else:
            entry["usage"] = ask_choice("Usage", USAGE_OPTIONS, "both")

    # ── definitions ───────────────────────────────────────────────────────────
    if suggestion and s.get("definitions"):
        print(f"\n  Definitions:")
        for i, d in enumerate(s["definitions"], 1):
            note = f" ({d['note']})" if d.get("note") else ""
            print(f"    {i}. {d['meaning']}{note}")
        action = input("\n  [keep / edit / add more]: ").strip().lower() or "keep"
        if action == "keep":
            entry["definitions"] = s["definitions"]
        elif action == "edit":
            entry["definitions"] = []
            print("  Enter definitions (empty to stop):")
            while True:
                m = ask("  Meaning")
                if not m:
                    break
                n = ask("  Note (or Enter)")
                entry["definitions"].append({"meaning": m, "note": n or None})
        else:
            entry["definitions"] = s["definitions"]
            print("  Add more (empty to stop):")
            while True:
                m = ask("  Meaning")
                if not m:
                    break
                n = ask("  Note (or Enter)")
                entry["definitions"].append({"meaning": m, "note": n or None})
    else:
        print("\n  Definitions (empty to stop):")
        while True:
            m = ask("  Meaning")
            if not m:
                break
            n = ask("  Note (or Enter)")
            entry["definitions"].append({"meaning": m, "note": n or None})

    # ── examples ──────────────────────────────────────────────────────────────
    own = own_example(my_sentence, s if suggestion else {})
    if suggestion and s.get("examples"):
        print(f"\n  Example sentences:")
        for ex in s["examples"]:
            print(f"    > {ex['de']}")
            print(f"      {ex['en']}")
        action = input("\n  [keep / edit / add more]: ").strip().lower() or "keep"
        if action == "keep":
            entry["examples"] = s["examples"]
        elif action == "edit":
            entry["examples"] = []
            print("  Enter examples (empty German to stop):")
            while True:
                de = ask("  German")
                if not de:
                    break
                en = ask("  English")
                entry["examples"].append({"de": de, "en": en})
        else:
            entry["examples"] = s["examples"]
            print("  Add more (empty to stop):")
            while True:
                de = ask("  German")
                if not de:
                    break
                en = ask("  English")
                entry["examples"].append({"de": de, "en": en})
    else:
        print("\n  Examples (empty German to stop):")
        while True:
            de = ask("  German")
            if not de:
                break
            en = ask("  English")
            entry["examples"].append({"de": de, "en": en})

    if own:
        entry["examples"].insert(0, own)

    if word_type in ("noun", "adj/adv") and suggestion and s.get("compound_parts"):
        cp = confirm_or_edit("Compound parts (comma-separated, '-' for none)", ", ".join(s["compound_parts"]))
        parts = [x.strip() for x in (cp if isinstance(cp, str) else ", ".join(cp)).split(",") if x.strip()]
        if parts and parts != ["-"]:
            entry["compound_parts"] = parts
    wiktionary_definition(entry)

    # ── topics, notes ─────────────────────────────────────────
    print()
    proposed = clean_topics(s.get("topics")) if suggestion else []
    entry["topics"] = clean_topics(confirm_or_edit("Topics (0-2, or 'none')", ", ".join(proposed) or "none"))
    if suggestion and set(proposed) != set(entry["topics"]):
        print(f"    (kept: {', '.join(entry['topics']) or 'none'})")

    sn = s.get("notes") if suggestion else None
    if sn and sn not in (None, "null", "None"):
        entry["notes"] = confirm_or_edit("Notes", sn)
    else:
        n = ask("Personal note (or Enter to skip)")
        if n:
            entry["notes"] = n

    # ── related words: typed semantic links proposed by the AI ───────────────
    entry["related"] = confirm_related(words, s.get("related", []) if suggestion else [])

    # ── exercise sentences: yours first, then the examples, then generated ───
    build_exercises(entry, api_key if not manual else None)

    # ── preview & save ────────────────────────────────────────────────────────
    print()
    print_entry(entry)
    confirm = ask("Save this entry? (y/n)", "y")
    if confirm.lower() != "y":
        print("  Cancelled.")
        return

    words.append(entry)

    n_linked = make_bidirectional(words, entry)
    if n_linked > 0:
        print(f"  Linked back from {n_linked} existing entry/entries.")

    save(words)
    print(f"  '{word}' added successfully!\n")


def cmd_edit(args):
    if not args:
        print("  Usage: python vocab.py edit <word>")
        return
    words = load()
    query = " ".join(args)
    w = find(words, query)
    if not w:
        print(f"  X '{query}' not found.")
        return

    print_entry(w)
    print("  What would you like to edit?\n")
    print("    1) definitions")
    print("    2) examples")
    print("    3) notes")
    print("    4) topics")
    print("    5) related words")
    if w["type"] == "noun":
        print("    6) gender / plural")
    elif w["type"] == "verb":
        print("    6) verb forms (past tense, participle, auxiliary…)")
    elif w["type"] == "adj/adv":
        print("    6) usage (adjective only / adverb only / both)")
    elif w["type"] == "prep/conj":
        print("    6) usage (preposition only / conjunction only / both)")
    print("    7) word type")
    print("    8) exercise sentences")
    print("    0) cancel")
    print()

    choice = ask("Choose").strip()

    if choice == "0" or not choice:
        print("  Cancelled.")
        return

    elif choice == "1":
        print(f"\n  Current definitions:")
        for i, d in enumerate(w.get("definitions", []), 1):
            note = f" ({d['note']})" if d.get("note") else ""
            print(f"    {i}. {d['meaning']}{note}")
        print("\n  Options: [add / replace / remove]")
        action = ask("Action", "add").lower()
        if action == "add":
            meaning = ask("New meaning")
            if meaning:
                note = ask("Note (or Enter to skip)")
                w.setdefault("definitions", []).append({"meaning": meaning, "note": note or None})
        elif action == "replace":
            idx = ask("Replace which number?")
            if idx.isdigit() and 1 <= int(idx) <= len(w.get("definitions", [])):
                i = int(idx) - 1
                meaning = ask("New meaning", w["definitions"][i]["meaning"])
                note = ask("Note (or Enter to skip)", w["definitions"][i].get("note") or "")
                w["definitions"][i] = {"meaning": meaning, "note": note or None}
        elif action == "remove":
            idx = ask("Remove which number?")
            if idx.isdigit() and 1 <= int(idx) <= len(w.get("definitions", [])):
                removed = w["definitions"].pop(int(idx) - 1)
                print(f"  Removed: {removed['meaning']}")

    elif choice == "2":
        print(f"\n  Current examples:")
        for i, e in enumerate(w.get("examples", []), 1):
            print(f"    {i}. {e['de']}")
            print(f"       {e['en']}")
        print("\n  Options: [add / replace / remove]")
        action = ask("Action", "add").lower()
        if action == "add":
            de = ask("German sentence")
            if de:
                en = ask("English translation")
                w.setdefault("examples", []).append({"de": de, "en": en})
        elif action == "replace":
            idx = ask("Replace which number?")
            if idx.isdigit() and 1 <= int(idx) <= len(w.get("examples", [])):
                i = int(idx) - 1
                de = ask("German sentence", w["examples"][i]["de"])
                en = ask("English translation", w["examples"][i]["en"])
                w["examples"][i] = {"de": de, "en": en}
        elif action == "remove":
            idx = ask("Remove which number?")
            if idx.isdigit() and 1 <= int(idx) <= len(w.get("examples", [])):
                removed = w["examples"].pop(int(idx) - 1)
                print(f"  Removed: {removed['de']}")

    elif choice == "3":
        current = w.get("notes") or ""
        print(f"\n  Current note: {current or '—'}")
        new_note = ask("New note (or Enter to clear)")
        w["notes"] = new_note if new_note else None

    elif choice == "4":
        current = ", ".join(w.get("topics", []))
        print(f"\n  Current topics: {current or '—'}")
        print("  Allowed: " + ", ".join(TOPICS))
        new_topics = ask("New topics (comma-separated, max 2)", current)
        w["topics"] = clean_topics(new_topics)

    elif choice == "5":
        w["related"] = confirm_related(words, w.get("related", []))
        n_linked = make_bidirectional(words, w)
        if n_linked > 0:
            print(f"  Linked back from {n_linked} existing entry/entries.")

    elif choice == "6":
        if w["type"] == "noun":
            w["gender"] = ask_choice("Gender", GENDERS, w.get("gender", ""))
            w["plural"] = ask("Plural form", w.get("plural", "") or "")
        elif w["type"] == "verb":
            w["auxiliary"]       = ask_choice("Auxiliary", ["haben", "sein"], w.get("auxiliary", "haben"))
            w["past_tense"]      = ask("Past tense", w.get("past_tense", "") or "")
            w["past_participle"] = ask("Past participle", w.get("past_participle", "") or "")
            w["present_3sg"]     = ask("er/sie/es, present", w.get("present_3sg", "") or "")
            w["verb_class"]      = ask_choice("Verb class", VERB_CLASSES, w.get("verb_class", "regular"))
            sep = ask("Separable? (y/n)", "y" if w.get("is_separable") else "n")
            w["is_separable"] = sep.lower() == "y"
            w["reflexive"] = norm_reflexive(ask("Reflexive (akk / dat / no)", norm_reflexive(w.get("reflexive")) or "no"))
            w["preposition"] = ask("Preposition + case (or Enter to clear)", w.get("preposition", "") or "") or None
            w["family_root"]    = ask("Family root", w.get("family_root", "") or "")
            w["prefix"]         = ask("Prefix (or Enter to clear)", w.get("prefix", "") or "") or None
            lexicon_verb(w)
        elif w["type"] == "adj/adv":
            USAGE_OPTIONS = ["both", "adjective only", "adverb only"]
            w["usage"] = ask_choice("Usage", USAGE_OPTIONS, w.get("usage", "both"))
        elif w["type"] == "prep/conj":
            USAGE_OPTIONS = ["both", "preposition only", "conjunction only"]
            w["usage"] = ask_choice("Usage", USAGE_OPTIONS, w.get("usage", "both"))

    elif choice == "7":
        w["type"] = ask_choice("Word type", WORD_TYPES, w.get("type", "other"))

    elif choice == "8":
        build_exercises(w, load_api_key())

    else:
        print("  Invalid choice.")
        return

    # examples, forms and word type decide the exercises: re-check them
    if choice in ("2", "6", "7") and EX_OK:
        if ask("Update the exercise sentences too? (y/n)", "y").lower() == "y":
            build_exercises(w, load_api_key())

    print()
    print_entry(w)
    confirm = ask("Save changes? (y/n)", "y")
    if confirm.lower() != "y":
        print("  Cancelled.")
        return

    # update in list
    for i, entry in enumerate(words):
        if entry["id"] == w["id"]:
            words[i] = w
            break

    save(words)
    print(f"  '{w['word']}' updated.\n")


def cmd_delete(args):
    if not args:
        print("  Usage: python vocab.py delete <word>")
        return
    words = load()
    query = " ".join(args)
    w = find(words, query)
    if not w:
        print(f"  X '{query}' not found.")
        return

    print_entry(w)
    confirm = ask(f"Delete '{w['word']}'? This cannot be undone. (y/n)", "n")
    if confirm.lower() != "y":
        print("  Cancelled.")
        return

    deleted_word = w["word"]
    words = [x for x in words if x["id"] != w["id"]]

    # remove deleted word from all related lists
    cleaned = 0
    for entry in words:
        before = len(entry.get("related", []))
        entry["related"] = [r for r in entry.get("related", []) if r.get("word") != deleted_word]
        if len(entry["related"]) < before:
            cleaned += 1

    if cleaned:
        print(f"  Removed '{deleted_word}' from {cleaned} related list(s).")

    save(words)
    print(f"  '{deleted_word}' deleted.\n")


def cmd_exercises(args):
    """Check one word's exercises against its current forms, fill the empty ones, replace any you choose."""
    if not args:
        print("  Usage: python vocab.py exercises <word>")
        return
    words = load()
    w = find(words, " ".join(args))
    if not w:
        print(f"  X '{' '.join(args)}' not found.")
        return
    build_exercises(w, load_api_key())
    if ask("Save? (y/n)", "y").lower() == "y":
        save(words)


# ── entry point ────────────────────────────────────────────────────────────────

COMMANDS = {
    "list":   cmd_list,
    "show":   cmd_show,
    "add":    cmd_add,
    "edit":   cmd_edit,
    "delete": cmd_delete,
    "topics": cmd_topics,
    "family": cmd_family,
    "exercises": cmd_exercises,
}

def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help", "help"):
        print(__doc__)
        return
    cmd = args[0].lower()
    if cmd not in COMMANDS:
        print(f"  Unknown command '{cmd}'. Try: {', '.join(COMMANDS)}")
        sys.exit(1)
    COMMANDS[cmd](args[1:])

if __name__ == "__main__":
    main()
