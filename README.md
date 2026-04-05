# Laura's Wörterbuch 🇩🇪

A personal German vocabulary app — a live website for browsing and practising words, backed by a JSON database managed from the command line.

**Live site:** https://laurafontanesi.github.io/german-vocabulary

---

## Project structure

```
german_vocabulary/
├── words.json          ← vocabulary database (all entries)
├── index.html          ← the website (browse + practice)
├── vocab.py            ← CLI tool for adding/managing words
├── fix_related.py      ← utility to repair bidirectional links
└── README.md           ← this file
```

---

## The website

Open `index.html` in a browser, or visit the live GitHub Pages URL above.

**Browsing:**
- Filter by word type (verb, noun, adjective…) and topic in the left sidebar
- Browse alphabetically using the letter grid
- Search across words, definitions, examples, notes and tags — results are ranked by relevance

**Practice mode** (click the red Practice button):

| Task | What you do |
|---|---|
| DE → EN | See a German word, type the English meaning |
| EN → DE | See an English meaning, type the German word |
| Conjugation | See a verb + a sentence with a blank, type the conjugated form |
| Articles | See a noun + a sentence with a blank, type the correct article/case |

After each answer the word card is revealed (definitions, grammar, example sentence). A progress bar and percentage score track your session. Click **Summary** at any time to see all correct and incorrect answers from the current session.

---

## Adding words — `vocab.py`

Requires Python 3.10+ and an Anthropic API key in `.env`.

```bash
# Add a new word (AI-assisted — looks up grammar, definitions, examples)
python vocab.py add

# Add without AI (fully manual)
python vocab.py add --manual

# Edit an existing entry (definitions, examples, notes, grammar fields…)
python vocab.py edit "die Erinnerung"

# List all words
python vocab.py list

# Filter by type or topic
python vocab.py list --type verb
python vocab.py list --topic emotions

# Show full entry for a word
python vocab.py show aufhören

# Show all members of a verb family
python vocab.py family nehmen

# Show all topics and word counts
python vocab.py topics

# Delete a word (asks for confirmation)
python vocab.py delete aufhören
```

### AI-assisted add

When you type a word, the script calls the Claude API to suggest:
- Canonical form (gender for nouns, infinitive for verbs)
- Word type, auxiliary, past tense, past participle
- Whether it's separable, reflexive, or requires a preposition
- Family root and prefix (for compound verbs)
- English definitions with usage notes
- Two natural example sentences
- Topic and register

You confirm or override each suggestion before saving. Related words in the database are detected automatically and linked bidirectionally.

### API key setup

Create a `.env` file in the project folder:
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

This file is in `.gitignore` and will never be committed.

---

## The data model

Each entry in `words.json` is a JSON object. All entries share these fields:

| Field | Type | Description |
|---|---|---|
| `id` | string | URL-safe identifier (auto-generated) |
| `word` | string | The German word in canonical form |
| `type` | string | `noun`, `verb`, `adj/adv`, `expression`, `construction`, `other` |
| `definitions` | list | `[{meaning, note}]` — always in English |
| `examples` | list | `[{de, en}]` — German sentence + translation |
| `topics` | list | Thematic categories (see below) |
| `tags` | list | Grammatical/learning tags e.g. `separable`, `similar to: X` |
| `register` | string | `neutral`, `formal`, `informal`, `Swiss German` |
| `notes` | string | One-sentence personal note, or null |
| `related` | list | Related word forms (always bidirectional) |
| `added` | string | Date added (YYYY-MM-DD) |

**Extra fields for nouns:**

| Field | Description |
|---|---|
| `gender` | `der`, `die`, or `das` |
| `plural` | Plural form with article |

**Extra fields for verbs:**

| Field | Description |
|---|---|
| `auxiliary` | `haben` or `sein` |
| `past_tense` | Simple past (Präteritum) |
| `past_participle` | Past participle |
| `is_separable` | `true` / `false` |
| `reflexive` | `true` / `false` |
| `preposition` | Fixed preposition + case e.g. `an + DAT` |
| `family_root` | Root verb (e.g. `nehmen` for `mitnehmen`) |
| `prefix` | Separable prefix e.g. `mit-` |

**Extra fields for adj/adv:**

| Field | Description |
|---|---|
| `usage` | `both`, `adjective only`, or `adverb only` |

### Topics

| Topic | What goes there |
|---|---|
| daily life | Everyday actions, routines, common verbs |
| emotions | Feelings, moods, character traits |
| people & relationships | Social interactions, trust, family |
| body & mind | Health, memory, physical states |
| work & academia | Research, jobs, university life |
| nature & weather | Weather, landscape, environment |
| travel & places | Transport, geography, directions |
| time | Temporal expressions |
| language & communication | Speaking, writing, expressions |
| money & shopping | Buying, prices, finances |
| culture & arts | Film, literature, art |
| society & politics | Government, social issues |
| grammar & structure | Constructions, patterns, connectors |
| various | Anything that doesn't fit cleanly |

---

## Fixing related word links — `fix_related.py`

Related words are kept bidirectional automatically when adding via `vocab.py`. If you ever edit `words.json` by hand or notice a one-sided link, run:

```bash
# Preview what would change
python fix_related.py --db words.json --dry-run

# Apply fixes
python fix_related.py --db words.json
```

The script detects connections via:
1. Shared `family_root` (verb family members)
2. Existing `related` lists → makes them bidirectional
3. Tags like `similar to: X` or `verb family: X`

Safe to run multiple times — never duplicates links.

---

## Deploying changes

The site is hosted on GitHub Pages and updates automatically on push.

```bash
# After adding words or making any change:
git add words.json
git commit -m "add: Schadenfreude, Weltschmerz"
git push

# After a batch of additions, also run fix_related:
python fix_related.py --db words.json
git add words.json
git commit -m "fix related links"
git push
```

The live site updates within ~60 seconds of pushing.
