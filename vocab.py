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
  python vocab.py delete nehmen         delete a word
  python vocab.py topics                show all topics
  python vocab.py family nehmen         show a verb family
"""

import json
import sys
import os
import re
import urllib.request
import urllib.error
from datetime import date

DB_PATH  = os.path.join(os.path.dirname(__file__), "words.json")
ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")

WORD_TYPES = ["noun", "verb", "adjective", "adverb", "expression", "construction", "other"]
GENDERS    = ["der", "die", "das"]
REGISTERS  = ["neutral", "formal", "informal", "Swiss German"]


# ── env / api key ──────────────────────────────────────────────────────────────

def load_api_key() -> str | None:
    """Load ANTHROPIC_API_KEY from .env file."""
    if not os.path.exists(ENV_PATH):
        return None
    with open(ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if line.startswith("ANTHROPIC_API_KEY="):
                return line.split("=", 1)[1].strip()
    return None


# ── AI enrichment ──────────────────────────────────────────────────────────────

def ai_enrich(word: str, api_key: str) -> dict | None:
    """
    Call Claude API to get structured info about a German word.
    Returns a dict with suggested fields, or None on failure.
    """
    prompt = f"""You are a German language expert. I am learning German and want to add the word "{word}" to my vocabulary database.

Please analyse this word and return a JSON object with the following fields. Be precise and use only English for definitions and translations (never Italian or German in the meaning field).

Return ONLY valid JSON, no explanation, no markdown, no code fences.

{{
  "word": "the word in its canonical form (e.g. with gender for nouns: 'die Sehnsucht', infinitive for verbs: 'erinnern')",
  "type": "one of: noun, verb, adjective, adverb, expression, construction, other",
  "gender": "der/die/das — only for nouns, else null",
  "plural": "plural form with article e.g. 'die Sehnsüchte' — only for nouns, else null",
  "auxiliary": "haben or sein — only for verbs, else null",
  "past_tense": "simple past (Präteritum) e.g. 'erinnerte' — only for verbs, else null",
  "past_participle": "e.g. 'erinnert' — only for verbs, else null",
  "is_separable": true or false — only for verbs, else null,
  "reflexive": true or false — only for verbs, else null,
  "preposition": "e.g. 'an + AKK' if the verb requires a fixed preposition, else null",
  "also_adverb": true or false — only for adjectives that double as adverbs, else null,
  "family_root": "the root verb if this is a compound e.g. 'nehmen' for 'mitnehmen', else null",
  "prefix": "the prefix e.g. 'mit-' for 'mitnehmen', else null",
  "definitions": [
    {{"meaning": "primary English meaning", "note": "optional note e.g. 'used with an + AKK' or null"}},
    {{"meaning": "secondary meaning if exists", "note": null}}
  ],
  "examples": [
    {{"de": "A natural German example sentence", "en": "English translation"}},
    {{"de": "A second example showing a different use", "en": "English translation"}}
  ],
  "topics": ["suggested topic from: useful verbs, everyday actions, states, characters, emotions, work, grammar, time, weather, places, travel, food, money, culture, various"],
  "register": "neutral, formal, informal, or Swiss German",
  "notes": "one sentence max — only if there is something genuinely important to note, e.g. easy confusion with another word, or null"
}}

Word to analyse: {word}"""

    payload = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1000,
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
        ref  = " · reflexive" if w.get("reflexive") else ""
        prep = f" · {w['preposition']}" if w.get("preposition") else ""
        print(f"  │  {aux} · {pt} · {pp}   ({sep}{ref}{prep})")
        if w.get("family_root") and w["family_root"] != w["word"]:
            print(f"  │  family: {w['family_root']}  (prefix: {w.get('prefix','')})")

    if w.get("also_adverb"):
        print(f"  │  * also used as adverb")
    if w.get("register") and w["register"] != "neutral":
        print(f"  │  register: {w['register']}")

    print(f"  │")
    for i, d in enumerate(w.get("definitions", []), 1):
        note = f"  -> {d['note']}" if d.get("note") else ""
        print(f"  │  {i}. {d['meaning']}{note}")

    if w.get("examples"):
        print(f"  │")
        for ex in w["examples"]:
            print(f"  │  > {ex['de']}")
            print(f"  │    {ex['en']}")

    if w.get("topics"):
        print(f"  │  topics:  {', '.join(w['topics'])}")
    if w.get("related"):
        print(f"  │  related: {', '.join(w['related'])}")
    if w.get("notes"):
        print(f"  │  note: {w['notes']}")

    print(f"  └─ added: {w.get('added','?')}")
    print()


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
    for topic, count in sorted(all_topics.items()):
        print(f"  . {topic:<30} ({count} words)")
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

    # ── AI enrichment ─────────────────────────────────────────────────────────
    suggestion = None
    if not manual and api_key:
        print(f"\n  Looking up '{word}' with AI...\n")
        suggestion = ai_enrich(word, api_key)
        if suggestion:
            print("  AI suggestions ready. Press Enter to accept each, or type to override.\n")
        else:
            print("  AI lookup failed — falling back to manual entry.\n")
    elif not manual and not api_key:
        print("  (No API key found in .env — using manual entry)\n")

    s = suggestion or {}

    # canonical word form
    canonical = s.get("word", word)
    if canonical and canonical != word:
        print(f"  AI suggests canonical form: {canonical}")
        use_can = ask("  Use this? (y/n)", "y")
        if use_can.lower() == "y":
            word = canonical

    word_id   = make_id(word)
    word_type = s.get("type", "other")

    if suggestion:
        word_type = confirm_or_edit("Type", word_type, WORD_TYPES)
    else:
        word_type = ask_choice("Word type", WORD_TYPES)

    entry = {
        "id":          word_id,
        "word":        word,
        "type":        word_type,
        "definitions": [],
        "examples":    [],
        "topics":      [],
        "tags":        [],
        "register":    "neutral",
        "notes":       None,
        "added":       str(date.today())
    }

    # ── type-specific fields ──────────────────────────────────────────────────
    if word_type == "noun":
        if suggestion:
            entry["gender"] = confirm_or_edit("Gender", s.get("gender"), GENDERS)
            entry["plural"] = confirm_or_edit("Plural", s.get("plural"))
        else:
            entry["gender"] = ask_choice("Gender", GENDERS)
            entry["plural"] = ask("Plural form (e.g. die Erinnerungen)")

    elif word_type == "verb":
        if suggestion:
            entry["auxiliary"]       = confirm_or_edit("Auxiliary", s.get("auxiliary"), ["haben", "sein"])
            entry["past_tense"]      = confirm_or_edit("Past tense", s.get("past_tense"))
            entry["past_participle"] = confirm_or_edit("Past participle", s.get("past_participle"))
            entry["is_separable"]    = confirm_or_edit("Separable?", s.get("is_separable", False))
            entry["reflexive"]       = confirm_or_edit("Reflexive?", s.get("reflexive", False))
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
            entry["is_separable"]    = ask("Separable? (y/n)", "n").lower() == "y"
            entry["reflexive"]       = ask("Reflexive? (y/n)", "n").lower() == "y"
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

    elif word_type == "adjective":
        if suggestion:
            entry["also_adverb"] = confirm_or_edit("Also adverb?", s.get("also_adverb", False))
        else:
            entry["also_adverb"] = ask("Also used as adverb? (y/n)", "n").lower() == "y"

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

    # ── topics, tags, register, notes ─────────────────────────────────────────
    print()
    if suggestion and s.get("topics"):
        entry["topics"] = confirm_or_edit("Topics", s["topics"])
        if isinstance(entry["topics"], str):
            entry["topics"] = [t.strip() for t in entry["topics"].split(",")]
    else:
        entry["topics"] = ask_list("Topics (e.g. work, states, grammar)")

    entry["tags"] = ask_list("Tags (optional)")

    if suggestion:
        entry["register"] = confirm_or_edit("Register", s.get("register", "neutral"), REGISTERS)
    else:
        entry["register"] = ask_choice("Register", REGISTERS, "neutral")

    sn = s.get("notes") if suggestion else None
    if sn and sn not in (None, "null", "None"):
        entry["notes"] = confirm_or_edit("Notes", sn)
    else:
        n = ask("Personal note (or Enter to skip)")
        if n:
            entry["notes"] = n

    related = ask_list("Related words (synonyms, family members)")
    if related:
        entry["related"] = related

    # ── preview & save ────────────────────────────────────────────────────────
    print()
    print_entry(entry)
    confirm = ask("Save this entry? (y/n)", "y")
    if confirm.lower() != "y":
        print("  Cancelled.")
        return

    words.append(entry)
    save(words)
    print(f"  '{word}' added successfully!\n")


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

    words = [x for x in words if x["id"] != w["id"]]
    save(words)
    print(f"  '{w['word']}' deleted.\n")


# ── entry point ────────────────────────────────────────────────────────────────

COMMANDS = {
    "list":   cmd_list,
    "show":   cmd_show,
    "add":    cmd_add,
    "delete": cmd_delete,
    "topics": cmd_topics,
    "family": cmd_family,
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
