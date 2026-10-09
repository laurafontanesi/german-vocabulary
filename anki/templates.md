# Card templates (generated — do not edit by hand)

Note type: **Deutsch**. Create the 51 fields in exactly this order, then paste each template.

## Fields

```
Wort, Typ, Formen, Englisch, EnglischKurz, Beispiel, BeispielEN, Beispiel2, Beispiel2EN, Verwandt, Notiz, Konj_Frage, Konj_Antwort, Konj_Ganz, Konj_GanzEN, Konj_Hinweis, Kasus_Frage, Kasus_Antwort, Kasus_Ganz, Kasus_GanzEN, Kasus_Hinweis, Praep_Frage, Praep_Antwort, Praep_Ganz, Praep_GanzEN, Praep_Hinweis, Kontrast_Frage, Kontrast_Antwort, Kontrast_Ganz, Kontrast_GanzEN, Kontrast_Hinweis, Neben_Frage, Neben_Antwort, Neben_Ganz, Neben_GanzEN, Neben_Hinweis, Komma_Frage, Komma_Antwort, Komma_Ganz, Komma_GanzEN, Komma_Hinweis, Adj_Frage, Adj_Antwort, Adj_Ganz, Adj_GanzEN, Adj_Hinweis, Defin_Frage, Defin_Antwort, Defin_Ganz, Defin_GanzEN, Defin_Hinweis
```

Tags are column 52.

## 1 — Konjugation

**Front**
```html
{{#Konj_Frage}}
<div class="kopf">Konjugation <span class="pill verb">{{Konj_Hinweis}}</span></div>
<div class="satz">{{Konj_Frage}}</div>
{{type:Konj_Antwort}}
{{/Konj_Frage}}
```

**Back**
```html
<div class="kopf">Konjugation <span class="pill verb">{{Konj_Hinweis}}</span></div>
<div class="wort">{{Wort}}</div>
<hr id=answer>
{{type:Konj_Antwort}}
<div class="en">{{Englisch}}</div>
<div class="satz">{{Konj_Ganz}}</div>
{{#Konj_GanzEN}}<div class="en2">{{Konj_GanzEN}}</div>{{/Konj_GanzEN}}
<div class="formen">{{Formen}}</div>
{{#Verwandt}}<div class="chips">{{Verwandt}}</div>{{/Verwandt}}
{{#Notiz}}<div class="notiz">{{Notiz}}</div>{{/Notiz}}
{{tts de_DE voices=Apple_Anna_(Premium),com.google.android.tts-de-de-x-nfh-local:Konj_Ganz}}
```

## 2 — Artikel und Kasus

**Front**
```html
{{#Kasus_Frage}}
<div class="kopf">Artikel und Kasus</div>
<div class="satz">{{Kasus_Frage}}</div>
<div class="hinweis">Welcher Artikel?</div>
<div class="hinweis">{{Wort}}</div>
{{type:Kasus_Antwort}}
{{/Kasus_Frage}}
```

**Back**
```html
<div class="kopf">Artikel und Kasus</div>
<div class="wort">{{Wort}}</div>
<hr id=answer>
{{type:Kasus_Antwort}}
<div class="en">{{Englisch}}</div>
<div class="satz">{{Kasus_Ganz}}</div>
{{#Kasus_GanzEN}}<div class="en2">{{Kasus_GanzEN}}</div>{{/Kasus_GanzEN}}
<div class="formen">{{Formen}}</div>
{{#Verwandt}}<div class="chips">{{Verwandt}}</div>{{/Verwandt}}
{{#Notiz}}<div class="notiz">{{Notiz}}</div>{{/Notiz}}
{{tts de_DE voices=Apple_Anna_(Premium),com.google.android.tts-de-de-x-nfh-local:Kasus_Ganz}}
```

## 3 — Präposition und Kasus

**Front**
```html
{{#Praep_Frage}}
<div class="kopf">Präposition und Kasus</div>
<div class="satz">{{Praep_Frage}}</div>
<div class="hinweis">Lücken füllen</div>
<div class="hinweis">{{Wort}}</div>
{{type:Praep_Antwort}}
{{/Praep_Frage}}
```

**Back**
```html
<div class="kopf">Präposition und Kasus</div>
<div class="wort">{{Wort}}</div>
<hr id=answer>
{{type:Praep_Antwort}}
<div class="en">{{Englisch}}</div>
<div class="satz">{{Praep_Ganz}}</div>
{{#Praep_GanzEN}}<div class="en2">{{Praep_GanzEN}}</div>{{/Praep_GanzEN}}
<div class="formen">{{Formen}}</div>
{{#Verwandt}}<div class="chips">{{Verwandt}}</div>{{/Verwandt}}
{{#Notiz}}<div class="notiz">{{Notiz}}</div>{{/Notiz}}
{{tts de_DE voices=Apple_Anna_(Premium),com.google.android.tts-de-de-x-nfh-local:Praep_Ganz}}
```

## 4 — Kontrast

**Front**
```html
{{#Kontrast_Frage}}
<div class="kopf">Welches Wort passt?</div>
<div class="satz">{{Kontrast_Frage}}</div>
{{#Kontrast_Hinweis}}<div class="hinweis">{{Kontrast_Hinweis}}</div>{{/Kontrast_Hinweis}}
{{type:Kontrast_Antwort}}
{{/Kontrast_Frage}}
```

**Back**
```html
<div class="kopf">Welches Wort passt?</div>
<div class="wort">{{Wort}}</div>
<hr id=answer>
{{type:Kontrast_Antwort}}
<div class="en">{{Englisch}}</div>
<div class="satz">{{Kontrast_Ganz}}</div>
{{#Kontrast_GanzEN}}<div class="en2">{{Kontrast_GanzEN}}</div>{{/Kontrast_GanzEN}}
<div class="formen">{{Formen}}</div>
{{#Verwandt}}<div class="chips">{{Verwandt}}</div>{{/Verwandt}}
{{#Notiz}}<div class="notiz">{{Notiz}}</div>{{/Notiz}}
{{tts de_DE voices=Apple_Anna_(Premium),com.google.android.tts-de-de-x-nfh-local:Kontrast_Ganz}}
```

## 5 — Nebensatz: Wortstellung

**Front**
```html
{{#Neben_Frage}}
<div class="kopf">Nebensatz: Wortstellung</div>
<div class="satz">{{Neben_Frage}}</div>
<div class="hinweis">{{Wort}}</div>
{{type:Neben_Antwort}}
{{/Neben_Frage}}
```

**Back**
```html
<div class="kopf">Nebensatz: Wortstellung</div>
<div class="wort">{{Wort}}</div>
<hr id=answer>
{{type:Neben_Antwort}}
<div class="en">{{Englisch}}</div>
<div class="satz">{{Neben_Ganz}}</div>
{{#Neben_GanzEN}}<div class="en2">{{Neben_GanzEN}}</div>{{/Neben_GanzEN}}
<div class="formen">{{Formen}}</div>
{{#Verwandt}}<div class="chips">{{Verwandt}}</div>{{/Verwandt}}
{{#Notiz}}<div class="notiz">{{Notiz}}</div>{{/Notiz}}
{{tts de_DE voices=Apple_Anna_(Premium),com.google.android.tts-de-de-x-nfh-local:Neben_Ganz}}
```

## 6 — Komma setzen

**Front**
```html
{{#Komma_Frage}}
<div class="kopf">Komma setzen</div>
<div class="satz">{{Komma_Frage}}</div>
<div class="hinweis">{{Wort}}</div>
{{type:Komma_Antwort}}
{{/Komma_Frage}}
```

**Back**
```html
<div class="kopf">Komma setzen</div>
<div class="wort">{{Wort}}</div>
<hr id=answer>
{{type:Komma_Antwort}}
<div class="en">{{Englisch}}</div>
<div class="satz">{{Komma_Ganz}}</div>
{{#Komma_GanzEN}}<div class="en2">{{Komma_GanzEN}}</div>{{/Komma_GanzEN}}
<div class="formen">{{Formen}}</div>
{{#Verwandt}}<div class="chips">{{Verwandt}}</div>{{/Verwandt}}
{{#Notiz}}<div class="notiz">{{Notiz}}</div>{{/Notiz}}
{{tts de_DE voices=Apple_Anna_(Premium),com.google.android.tts-de-de-x-nfh-local:Komma_Ganz}}
```

## 7 — Adjektivendung

**Front**
```html
{{#Adj_Frage}}
<div class="kopf">Adjektivendung</div>
<div class="satz">{{Adj_Frage}}</div>
<div class="hinweis">{{Wort}}</div>
{{type:Adj_Antwort}}
{{/Adj_Frage}}
```

**Back**
```html
<div class="kopf">Adjektivendung</div>
<div class="wort">{{Wort}}</div>
<hr id=answer>
{{type:Adj_Antwort}}
<div class="en">{{Englisch}}</div>
<div class="satz">{{Adj_Ganz}}</div>
{{#Adj_GanzEN}}<div class="en2">{{Adj_GanzEN}}</div>{{/Adj_GanzEN}}
<div class="formen">{{Formen}}</div>
{{#Verwandt}}<div class="chips">{{Verwandt}}</div>{{/Verwandt}}
{{#Notiz}}<div class="notiz">{{Notiz}}</div>{{/Notiz}}
{{tts de_DE voices=Apple_Anna_(Premium),com.google.android.tts-de-de-x-nfh-local:Adj_Ganz}}
```

## 8 — Definition

**Front**
```html
{{#Defin_Frage}}
<div class="kopf">Definition</div>
<div class="satz">{{Defin_Frage}}</div>
{{#Defin_Hinweis}}<div class="hinweis">{{Defin_Hinweis}}</div>{{/Defin_Hinweis}}
{{type:Defin_Antwort}}
{{/Defin_Frage}}
```

**Back**
```html
<div class="kopf">Definition</div>
<div class="wort">{{Wort}}</div>
<hr id=answer>
{{type:Defin_Antwort}}
<div class="en">{{Englisch}}</div>
<div class="satz">{{Defin_Ganz}}</div>
{{#Defin_GanzEN}}<div class="en2">{{Defin_GanzEN}}</div>{{/Defin_GanzEN}}
<div class="formen">{{Formen}}</div>
{{#Verwandt}}<div class="chips">{{Verwandt}}</div>{{/Verwandt}}
{{#Notiz}}<div class="notiz">{{Notiz}}</div>{{/Notiz}}
{{tts de_DE voices=Apple_Anna_(Premium),com.google.android.tts-de-de-x-nfh-local:Defin_Ganz}}
```

## 9 — Produzieren

**Front**
```html
<div class="kopf">Produzieren <span class="pill other">{{Typ}}</span></div>
<div class="en">{{Englisch}}</div>
<div class="hinweis">Bei Nomen mit Artikel</div>
{{type:Wort}}
```

**Back**
```html
<div class="kopf">Produzieren</div>
<div class="en">{{Englisch}}</div>
<hr id=answer>
{{type:Wort}}
<div class="formen">{{Formen}}</div>
<div class="satz">{{Beispiel}}</div>
{{#BeispielEN}}<div class="en2">{{BeispielEN}}</div>{{/BeispielEN}}
{{#Beispiel2}}<div class="satz">{{Beispiel2}}</div>{{/Beispiel2}}
{{#Beispiel2EN}}<div class="en2">{{Beispiel2EN}}</div>{{/Beispiel2EN}}
{{#Verwandt}}<div class="chips">{{Verwandt}}</div>{{/Verwandt}}
{{#Notiz}}<div class="notiz">{{Notiz}}</div>{{/Notiz}}
{{tts de_DE voices=Apple_Anna_(Premium),com.google.android.tts-de-de-x-nfh-local:Beispiel}}
{{#Beispiel2}}{{tts de_DE voices=Apple_Anna_(Premium),com.google.android.tts-de-de-x-nfh-local:Beispiel2}}{{/Beispiel2}}
```

## 10 — Bedeutung

**Front**
```html
<div class="kopf">Bedeutung <span class="pill other">{{Typ}}</span></div>
<div class="wort">{{Wort}}</div>
<div class="hinweis">Kurze englische Bedeutung</div>
{{type:EnglischKurz}}
```

**Back**
```html
<div class="kopf">Bedeutung</div>
<div class="wort">{{Wort}}</div>
<hr id=answer>
{{type:EnglischKurz}}
<div class="en">{{Englisch}}</div>
<div class="formen">{{Formen}}</div>
<div class="satz">{{Beispiel}}</div>
{{#BeispielEN}}<div class="en2">{{BeispielEN}}</div>{{/BeispielEN}}
{{#Beispiel2}}<div class="satz">{{Beispiel2}}</div>{{/Beispiel2}}
{{#Beispiel2EN}}<div class="en2">{{Beispiel2EN}}</div>{{/Beispiel2EN}}
{{#Verwandt}}<div class="chips">{{Verwandt}}</div>{{/Verwandt}}
{{#Notiz}}<div class="notiz">{{Notiz}}</div>{{/Notiz}}
{{tts de_DE voices=Apple_Anna_(Premium),com.google.android.tts-de-de-x-nfh-local:Beispiel}}
{{#Beispiel2}}{{tts de_DE voices=Apple_Anna_(Premium),com.google.android.tts-de-de-x-nfh-local:Beispiel2}}{{/Beispiel2}}
```

