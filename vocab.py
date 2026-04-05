#!/usr/bin/env python3
"""
vocab.py — Laura's German vocabulary manager
Usage:
  python vocab.py list                  show all words
  python vocab.py list --topic work     filter by topic
  python vocab.py list --type verb      filter by word type
  python vocab.py show nehmen          show full entry for a word
  python vocab.py add                   add a new word (interactive)
  python vocab.py delete nehmen        delete a word
  python vocab.py topics               show all topics
  python vocab.py family nehmen        show a verb family
"""

import json
import sys
import os
import re
from datetime import date

DB_PATH = os.path.join(os.path.dirname(__file__), "words.json")

WORD_TYPES = ["noun", "verb", "adjective", "adverb", "expression", "construction", "other"]
GENDERS    = ["der", "die", "das"]
REGISTERS  = ["neutral", "formal", "informal", "Swiss German"]


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
    """Turn a word into a safe ID, e.g. 'die Erinnerung' → 'die-erinnerung'"""
    word = word.lower().strip()
    word = re.sub(r'[äöü]', lambda m: {'ä':'ae','ö':'oe','ü':'ue'}[m.group()], word)
    word = re.sub(r'ß', 'ss', word)
    word = re.sub(r'[^a-z0-9]+', '-', word)
    return word.strip('-')

def find(words: list, query: str):
    """Find entry by word text or id (case-insensitive)."""
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
        val = input(f"  Choose 1–{len(options)}" + (f" [{default}]" if default else "") + ": ").strip()
        if not val and default:
            return default
        if val.isdigit() and 1 <= int(val) <= len(options):
            return options[int(val) - 1]
        print(f"  Please enter a number between 1 and {len(options)}.")

def print_entry(w: dict):
    """Pretty-print a single word entry."""
    print()
    print(f"  ┌─ {w['word']}  [{w['type']}]")

    if w["type"] == "noun":
        print(f"  │  gender:   {w.get('gender', '?')}   plural: {w.get('plural', '?')}")
    elif w["type"] == "verb":
        aux  = w.get("auxiliary", "")
        pt   = w.get("past_tense", "")
        pp   = w.get("past_participle", "")
        sep  = "separable" if w.get("is_separable") else "inseparable"
        ref  = " · reflexive" if w.get("reflexive") else ""
        prep = f"  · {w['preposition']}" if w.get("preposition") else ""
        print(f"  │  {aux} · {pt} · {pp}   ({sep}{ref}{prep})")
        if w.get("family_root") and w["family_root"] != w["word"]:
            print(f"  │  family:   {w['family_root']}  (prefix: {w.get('prefix','')})")

    if w.get("also_adverb"):
        print(f"  │  ★ also used as adverb")

    if w.get("register") and w["register"] != "neutral":
        print(f"  │  register: {w['register']}")

    print(f"  │")
    for i, d in enumerate(w.get("definitions", []), 1):
        note = f"  → {d['note']}" if d.get("note") else ""
        print(f"  │  {i}. {d['meaning']}{note}")

    if w.get("examples"):
        print(f"  │")
        for ex in w["examples"]:
            print(f"  │  ▸ {ex['de']}")
            print(f"  │    {ex['en']}")

    if w.get("topics"):
        print(f"  │  topics:  {', '.join(w['topics'])}")

    if w.get("related"):
        print(f"  │  related: {', '.join(w['related'])}")

    if w.get("notes"):
        print(f"  │  ✎ {w['notes']}")

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
        print(f"  ✗ '{' '.join(args)}' not found.")
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
        print(f"  • {topic:<30} ({count} words)")
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
        prefix = f"  [{m.get('prefix','')}]" if m.get("prefix") else "  [root]"
        meaning = m["definitions"][0]["meaning"] if m.get("definitions") else ""
        print(f"  {prefix:<12} {m['word']:<25} {meaning}")
    print()


def cmd_add(args):
    words = load()
    print("\n  ── Add a new word ──────────────────────────────────\n")

    word = ask("Word (German)")
    if not word:
        print("  Cancelled.")
        return

    # check for duplicates
    existing = find(words, word)
    if existing:
        print(f"\n  ✗ '{word}' already exists. Use 'show' to view it.")
        return

    word_id = make_id(word)
    word_type = ask_choice("Word type", WORD_TYPES)

    entry = {
        "id": word_id,
        "word": word,
        "type": word_type,
        "definitions": [],
        "examples": [],
        "topics": [],
        "tags": [],
        "register": "neutral",
        "notes": None,
        "added": str(date.today())
    }

    # type-specific fields
    if word_type == "noun":
        entry["gender"] = ask_choice("Gender", GENDERS)
        entry["plural"] = ask("Plural form (e.g. die Erinnerungen)")

    elif word_type == "verb":
        entry["auxiliary"]       = ask_choice("Auxiliary", ["haben", "sein"])
        entry["past_tense"]      = ask("Simple past (Präteritum, e.g. nahm)")
        entry["past_participle"] = ask("Past participle (e.g. genommen)")
        sep = ask("Separable verb? (y/n)", "n")
        entry["is_separable"] = sep.lower() == "y"
        ref = ask("Reflexive? (y/n)", "n")
        entry["reflexive"] = ref.lower() == "y"
        prep = ask("Preposition + case (e.g. 'an + DAT'), or Enter to skip")
        if prep:
            entry["preposition"] = prep
        family = ask("Family root verb (e.g. nehmen), or Enter if this IS the root")
        if family:
            entry["family_root"] = family
            prefix = ask("Prefix (e.g. mit-, ab-)")
            if prefix:
                entry["prefix"] = prefix
        else:
            entry["family_root"] = word

    elif word_type == "adjective":
        adv = ask("Also used as adverb? (y/n)", "n")
        entry["also_adverb"] = adv.lower() == "y"

    # definitions
    print("\n  Add definitions (press Enter with empty meaning to stop):")
    while True:
        meaning = ask("  Meaning")
        if not meaning:
            break
        note = ask("  Optional note (or Enter to skip)")
        entry["definitions"].append({"meaning": meaning, "note": note if note else None})

    # examples
    print("\n  Add example sentences (press Enter with empty German to stop):")
    while True:
        de = ask("  German sentence")
        if not de:
            break
        en = ask("  English translation")
        entry["examples"].append({"de": de, "en": en})

    # topics & tags
    print()
    entry["topics"]   = ask_list("Topics (e.g. work, states, grammar)")
    entry["tags"]     = ask_list("Tags (e.g. emotions, memory, idioms)")
    entry["register"] = ask_choice("Register", REGISTERS, "neutral")
    note = ask("Personal note (or Enter to skip)")
    if note:
        entry["notes"] = note

    # related words
    related = ask_list("Related words (e.g. other family members, synonyms)")
    if related:
        entry["related"] = related

    # confirm
    print()
    print_entry(entry)
    confirm = ask("Save this entry? (y/n)", "y")
    if confirm.lower() != "y":
        print("  Cancelled.")
        return

    words.append(entry)
    save(words)
    print(f"  ✓ '{word}' added successfully!\n")


def cmd_delete(args):
    if not args:
        print("  Usage: python vocab.py delete <word>")
        return
    words = load()
    query = " ".join(args)
    w = find(words, query)
    if not w:
        print(f"  ✗ '{query}' not found.")
        return

    print_entry(w)
    confirm = ask(f"Delete '{w['word']}'? This cannot be undone. (y/n)", "n")
    if confirm.lower() != "y":
        print("  Cancelled.")
        return

    words = [x for x in words if x["id"] != w["id"]]
    save(words)
    print(f"  ✓ '{w['word']}' deleted.\n")


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
