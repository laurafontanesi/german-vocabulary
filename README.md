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
├── lexicon.py          ← looks up word forms in the Morphy lexicon (see Data sources)
├── fix_related.py      ← utility to repair bidirectional links
├── anki/
│   ├── make_deck.py        builds the Anki deck from words.json
│   ├── templates.md        note type fields + card templates (generated)
│   ├── styling.css         card styling (generated)
│   └── deutsch.txt         the import file (generated, not in git)
├── README.md           ← this file
└── data/               ← large reference files, NOT in git (see Data sources)
    ├── dictionary.dump     Morphy / LanguageTool full-form lexicon (~250 MB)
    ├── de-extract.jsonl    German Wiktionary, kaikki.org extract (~3 GB)
    ├── deu-eng.tsv         Tatoeba German-English sentence pairs (~56 MB)
    └── deu_sentences.tsv   Tatoeba German sentences (~48 MB, optional)
```

---

## The website

Open `index.html` in a browser, or visit the live GitHub Pages URL above.

**Browsing:**
- Filter by word type (verb, noun, adjective…) and topic in the left sidebar
- Browse alphabetically using the letter grid
- Search across words, definitions, examples and notes — results are ranked by relevance

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

Requires Python 3.10+ and an Anthropic API key (see API key setup).

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
python vocab.py list --topic emotions   # substring match, so 'emotions' finds 'emotions & character'

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

After the word and its type, you are asked for **your own sentence**: the one where you met the word (Enter to skip). It is sent along to the model, so the first definition follows the meaning the word has in *your* sentence; the model also checks it and offers a correction if needed. Your sentence becomes the first example, marked `"source": "own"`, and is preferred as an exercise sentence when it contains the right form.

Then the script calls the Claude API to suggest:
- Canonical form (gender for nouns, infinitive for verbs)
- Word type, auxiliary, past tense, past participle
- Whether it's separable, reflexive, or requires a preposition
- Family root and prefix (for compound verbs)
- English definitions with usage notes
- Two natural example sentences
- Topics (0 to 2 from a closed list, often none)
- Notes, including register when it is not neutral

You confirm or override each suggestion before saving. Related words are proposed from your own database only, and linked bidirectionally.

If `data/` holds the reference files (see Data sources), the script also checks the model against them: verb forms against the lexicon (it asks when they disagree), noun gender and plural, and it fills `present_3sg`, `verb_class`, `imperative`, `konjunktiv_2` and the German definition by itself.

### API key setup

Keep the key **outside** the repo, in a `Claude_API` folder next to it:

```
Projects/
├── Claude_API/
│   └── .env              ANTHROPIC_API_KEY=sk-ant-your-key-here
└── german_vocabulary/    this repo
```

`vocab.py` looks there first, then for a `.env` inside the repo, and an `ANTHROPIC_API_KEY` environment variable overrides both. Keeping it outside means it cannot be committed by accident and is not visible to tools that only have access to the repo folder.

---

## The data model

Each entry in `words.json` is a JSON object. All entries share these fields:

| Field | Type | Description |
|---|---|---|
| `id` | string | URL-safe identifier (auto-generated) |
| `word` | string | The German word in canonical form |
| `type` | string | `noun`, `verb`, `adj/adv`, `prep/conj`, `expression`, `construction`, `other` |
| `definitions` | list | `[{meaning, note}]` — always in English |
| `examples` | list | `[{de, en}]` — German sentence + translation |
| `topics` | list | 0 to 2 entries from the closed list below; empty for core vocabulary |
| `definition_de` | string | German definition from German Wiktionary, matched to the first English meaning; used by the *Definition* card. Optional |
| `notes` | string | One-sentence personal note, or null. Register goes here when it is not neutral (`Register: umgangssprachlich.`) |
| `related` | list | `[{word, kind}]` — semantic links, always bidirectional. `kind` is one of `synonym`, `antonym`, `contrast` (easily confused), `derived` (same stem, other word class). Verb families are **not** stored here; see `family_root`. |
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
| `past_tense` | Simple past (Präteritum), main-clause form, with `sich` for reflexive headwords (`nahm mit`, `freute sich`) |
| `past_participle` | Past participle, without `sich` |
| `present_3sg` | er/sie/es form, same format as `past_tense` (`nimmt mit`, `freut sich`). Shown on cards only when the stem changes (`nimmt`, `fährt`, `weiß`) |
| `imperative` | du-imperative, only when the stem changes (`nimm mit`, `benimm dich`); `fahr!` is regular and not stored |
| `konjunktiv_2` | one-word Konjunktiv II, only for the verbs where it is in everyday use (`käme`, `wüsste`, `bräuchte`; list in `lexicon.KONJ2_IN_USE`). Other verbs use *würde* + infinitive |
| `verb_class` | `regular` (kaufte, gekauft), `irregular` (nahm, genommen) or `mixed` (dachte, gedacht: weak endings, changed stem) |
| `is_separable` | `true` / `false` |
| `reflexive` | `"akk"` (ich freue **mich**), `"dat"` (ich nehme **mir** etwas vor) or `false`. Reflexive means the verb cannot drop *sich*, or changes meaning with it; those have *sich* in the headword. Verbs that merely *can* take *sich* (waschen, umdrehen) are not reflexive. When a verb has a second object, the pronoun moves to the dative (ich ziehe **mir** die Jacke an); that goes in the meaning's note |
| `preposition` | Fixed preposition + case e.g. `an + DAT` |
| `family_root` | Root verb (e.g. `nehmen` for `mitnehmen`) |
| `prefix` | Separable prefix e.g. `mit-` |

**Extra fields for adj/adv:**

| Field | Description |
|---|---|
| `usage` | `both`, `adjective only`, or `adverb only` |
| `derived_from` | source verb for participle-adjectives e.g. `entspannen` for *entspannt* |

**Extra fields for prep/conj:**

| Field | Description |
|---|---|
| `usage` | `both`, `preposition only`, or `conjunction only` |

### Topics

A topic says what a word is **about**. Rules:

- 0 to 2 topics per word. Core vocabulary (*brauchen, bekommen, liegen, nötig*) has an empty list, and that is the correct answer, not a gap. About 100 words are deliberately without a topic.
- The **first definition decides**. A secondary meaning (*drehen* "to shoot a film", *brechen* "to vomit") earns a topic only if one of the stored examples illustrates it.
- The list is closed and lives in `vocab.py` (`TOPICS`), together with the definition the model sees when it proposes topics for a new word. `vocab.py topics` prints it with counts.
- Register (formal, colloquial, Swiss) is not a topic and not a field: it goes into `notes`.

| Topic | Definition and boundary |
|---|---|
| home & objects | Housing, rooms, furnishings, household objects, clothing, cleaning and domestic maintenance. Exclude general physical actions merely illustrated with a household object. |
| food & drink | Food, beverages, preparation, eating, drinking and dining. Include verbs only when a food-related meaning is explicitly recorded. |
| body & health | Anatomy, bodily functions, physical sensations, illness, treatment, hygiene, recovery, sport. Include physical exhaustion; distinguish it from emotional distress. |
| thinking & perception | Knowledge, memory, attention, reasoning, judgement, decisions and sensory perception. Include looking and noticing; exclude general comparisons between objects. |
| emotions & character | Feelings, moods, preferences, temperament and personal dispositions. Exclude general usefulness, size or quality unless the meaning concerns a person's character. |
| people & relationships | Personal relationships, encounters, trust, cooperation, interpersonal behaviour and social interaction. Exclude actions simply because a person performs them. |
| language & communication | Speaking, writing, listening, naming, conveying information, stance adverbs and conventional conversational acts. An idiom belongs here only when its function is communicative. |
| work & jobs | Employment, occupations, workplace arrangements, professional responsibilities, vocational training and working conditions. Exclude generic effort, success or activity. |
| science & academia | Research, academic study, scientific methods, evidence, and scholarly institutions or outputs. Exclude general concepts merely because researchers use them. |
| technology & media | Devices, technical systems, digital tools, broadcasting, and media production or distribution. Not every act of reporting and not every artificial object. |
| money & shopping | Prices, payment, wealth, ownership, buying, selling and economic transactions. Exclude general exchange, receipt or waste without a financial meaning. |
| society & politics | Public institutions, law, governance, collective social structures, rights and public affairs. Distinguish from individual interpersonal relationships. |
| culture & arts | Literature, visual and performing arts, creative practices, cultural works and their creators. Exclude general attractiveness or beauty. |
| nature & weather | Animals, plants, landscapes, natural environments, weather and environmental processes. Exclude physical properties that apply equally to manufactured objects. |
| travel & movement | Journeys, transport, routes, destinations, navigation, locomotion and directional movement. Exclude manipulating an object solely because the object moves. |
| time | Temporal location, duration, frequency, sequence, deadlines and speed of occurrence. Exclude events merely because they occur in time. |
| quantity & comparison | Amount, extent, sufficiency, scarcity, similarity, difference and comparative scale. |
| materials & physical properties | Materials and observable physical characteristics: shape, texture, surface, structural integrity, physical force. Exclude generic handling actions. |
| change & development | Alteration, growth, decline, increase, decrease, transformation and persistence of a state. Exclude mere movement to a different place. |
| goals, effort & outcomes | Intentional aims, attempts, effort, obstacles, giving up, achievement and reward. Exclude ordinary actions, events, and evaluative adjectives such as useful or suitable. |
| connectors & constructions | Connectives, discourse particles, prepositions and reusable grammatical patterns that relate clauses or sentence elements. A grammatical category; not abstract vocabulary. |

---

## Related words — what goes in, what stays out

`related` holds **semantic** neighbours only, each with a kind:

```json
"related": [
  {"word": "wissen",          "kind": "contrast"},
  {"word": "kennenlernen",    "kind": "contrast"}
]
```

| kind | meaning | example |
|---|---|---|
| `contrast` | easily confused, worth telling apart | kennen / wissen |
| `antonym` | opposite | billig / teuer |
| `synonym` | same or near meaning | rasch / zügig |
| `derived` | same stem, different word class | wählen / die Wahl |

Verb families (`nehmen`, `mitnehmen`, `teilnehmen`…) are deliberately **not** linked here.
They are already encoded by `family_root`, and `vocab.py family nehmen` lists them.

When you add a word, the AI proposes links drawn only from words already in the database,
and you confirm or adjust them. `contrast` and `antonym` links feed the "Welches Wort passt?"
cards in the Anki deck.

### Keeping links consistent — `fix_related.py`

```bash
python fix_related.py --db words.json --dry-run   # report only
python fix_related.py --db words.json             # drop dangling links, add back-links
```

Safe to run any time. It never invents links; it only removes broken ones and mirrors
existing ones.

---

## Data sources

Two large reference files live in `data/`. They are not part of the website, so `data/` is in `.gitignore`.

**Morphy / LanguageTool lexicon** (`data/dictionary.dump`, CC BY-SA 4.0, [danielnaber.de/morphologie](https://danielnaber.de/morphologie/)). Every inflected form of about 400,000 German words, one per line: `nehmen_nimmt_VER:3:SIN:PRÄ:NON`. `lexicon.py` reads it; `vocab.py add` uses it to check verb forms, fill `present_3sg` and `verb_class`, and check noun gender and plural. Without the file, `vocab.py` works as before and trusts the model. To produce it (once; needs Java 8 or later):

```bash
# 1. download LanguageTool stand-alone (for its libs/ folder) and the german-pos-dict repo
# 2. from the german-pos-dict folder:
java -cp "/path/to/LanguageTool-6.6/libs/*" morfologik.tools.DictDecompile \
     -i src/main/resources/org/languagetool/resource/de/german.dict -o dictionary.dump
# 3. move dictionary.dump into data/
```

(The `export.sh` in the repo calls LanguageTool's own exporter, which needs Java 17. The command above uses the Morfologik decompiler directly and runs on older Java.)

**German Wiktionary** (`data/de-extract.jsonl`, CC BY-SA, [kaikki.org/dewiktionary](https://kaikki.org/dewiktionary/)). `vocab.py add` looks up a German definition for each new word (about 15 s, with `grep`), and the file also holds pronunciation (IPA), synonyms, antonyms and idioms for later use.

**Tatoeba sentences** (`data/deu-eng.tsv`, renamed from "Sentence pairs in German-English - <date>.tsv"; `data/deu_sentences.tsv`, CC BY 2.0 FR, [tatoeba.org/downloads](https://tatoeba.org/en/downloads)). Human-written example sentences, used as a source for exercise sentences. For English translations, the custom export "Sentence pairs" German to English.

---

## Deploying changes

The site is hosted on GitHub Pages and updates automatically on push.

```bash
# After adding words or making any change:
git add words.json
git commit -m "add: Schadenfreude, Weltschmerz"
git push

# After a batch of additions, check the links are consistent:
python fix_related.py --db words.json

# Rebuild the Anki import file (see anki/templates.md for the one-time note type setup):
python anki/make_deck.py
```

The live site updates within ~60 seconds of pushing.
