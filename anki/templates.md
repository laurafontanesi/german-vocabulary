# Card templates (generated — do not edit by hand)

Note type: **Deutsch**. Create the 96 fields in exactly this order, then one card type per section below, named as in the heading, and paste its front and back.

## Fields

```
Wort, Typ, Formen, Englisch, EnglischFrage, EnglischKurz, Beispiel, BeispielEN, Beispiel2, Beispiel2EN, Verwandt, Notiz, Praet_Frage, Praet_Antwort, Praet_Ganz, Praet_GanzEN, Praet_Hinweis, Praet_Quelle, Part_Frage, Part_Antwort, Part_Ganz, Part_GanzEN, Part_Hinweis, Part_Quelle, Praes_Frage, Praes_Antwort, Praes_Ganz, Praes_GanzEN, Praes_Hinweis, Praes_Quelle, Refl_Frage, Refl_Antwort, Refl_Ganz, Refl_GanzEN, Refl_Hinweis, Refl_Quelle, Dekl_Frage, Dekl_Antwort, Dekl_Ganz, Dekl_GanzEN, Dekl_Hinweis, Dekl_Quelle, DeklPl_Frage, DeklPl_Antwort, DeklPl_Ganz, DeklPl_GanzEN, DeklPl_Hinweis, DeklPl_Quelle, Praep1_Frage, Praep1_Antwort, Praep1_Ganz, Praep1_GanzEN, Praep1_Hinweis, Praep1_Quelle, Praep2_Frage, Praep2_Antwort, Praep2_Ganz, Praep2_GanzEN, Praep2_Hinweis, Praep2_Quelle, Konnektor1_Frage, Konnektor1_Antwort, Konnektor1_Ganz, Konnektor1_GanzEN, Konnektor1_Hinweis, Konnektor1_Quelle, Konnektor2_Frage, Konnektor2_Antwort, Konnektor2_Ganz, Konnektor2_GanzEN, Konnektor2_Hinweis, Konnektor2_Quelle, Konnektor3_Frage, Konnektor3_Antwort, Konnektor3_Ganz, Konnektor3_GanzEN, Konnektor3_Hinweis, Konnektor3_Quelle, Konnektor4_Frage, Konnektor4_Antwort, Konnektor4_Ganz, Konnektor4_GanzEN, Konnektor4_Hinweis, Konnektor4_Quelle, Kontrast_Frage, Kontrast_Antwort, Kontrast_Ganz, Kontrast_GanzEN, Kontrast_Hinweis, Kontrast_Quelle, Neben_Frage, Neben_Antwort, Neben_Ganz, Neben_GanzEN, Neben_Hinweis, Neben_Quelle
```

Tags are column 97.

## 1 — Bedeutung

**Front**
```html
<div class="karte">
<div class="kopf">Bedeutung <span class="pill other">{{Typ}}</span></div>
<div class="wort">{{Wort}}</div>
<div class="hinweis">kurze englische Bedeutung</div>
{{type:EnglischKurz}}
</div>
```

**Back**
```html
<div class="karte">
<div class="kopf">Bedeutung <span class="pill other">{{Typ}}</span></div>
<div class="wort">{{Wort}}</div>
<hr id=answer>
{{type:EnglischKurz}}
{{#Englisch}}<div class="block"><div class="label">Bedeutung</div><div class="en">{{Englisch}}</div></div>{{/Englisch}}
{{#Formen}}<div class="block"><div class="label">Formen</div><div class="chips">{{Formen}}</div></div>{{/Formen}}
{{#Beispiel}}<div class="block"><div class="label">Beispiele</div><div class="bsp">{{Beispiel}} {{tts de_DE voices=Apple_Anna_(Premium),com.google.android.tts-de-de-x-nfh-local:Beispiel}}</div>{{#BeispielEN}}<div class="en2">{{BeispielEN}}</div>{{/BeispielEN}}{{#Beispiel2}}<div class="bsp">{{Beispiel2}} {{tts de_DE voices=Apple_Anna_(Premium),com.google.android.tts-de-de-x-nfh-local:Beispiel2}}</div>{{/Beispiel2}}{{#Beispiel2EN}}<div class="en2">{{Beispiel2EN}}</div>{{/Beispiel2EN}}</div>{{/Beispiel}}
{{#Verwandt}}<div class="block"><div class="label">Verwandt</div><div class="chips">{{Verwandt}}</div></div>{{/Verwandt}}
{{#Notiz}}<div class="notiz">{{Notiz}}</div>{{/Notiz}}
</div>
```

## 2 — Produzieren

**Front**
```html
<div class="karte">
<div class="kopf">Produzieren <span class="pill other">{{Typ}}</span></div>
<div class="en gross">{{EnglischFrage}}</div>
<div class="hinweis">Nomen mit Artikel</div>
{{type:Wort}}
</div>
```

**Back**
```html
<div class="karte">
<div class="kopf">Produzieren <span class="pill other">{{Typ}}</span></div>
<div class="en gross">{{Englisch}}</div>
<hr id=answer>
{{type:Wort}}
{{#Formen}}<div class="block"><div class="label">Formen</div><div class="chips">{{Formen}}</div></div>{{/Formen}}
{{#Beispiel}}<div class="block"><div class="label">Beispiele</div><div class="bsp">{{Beispiel}} {{tts de_DE voices=Apple_Anna_(Premium),com.google.android.tts-de-de-x-nfh-local:Beispiel}}</div>{{#BeispielEN}}<div class="en2">{{BeispielEN}}</div>{{/BeispielEN}}{{#Beispiel2}}<div class="bsp">{{Beispiel2}} {{tts de_DE voices=Apple_Anna_(Premium),com.google.android.tts-de-de-x-nfh-local:Beispiel2}}</div>{{/Beispiel2}}{{#Beispiel2EN}}<div class="en2">{{Beispiel2EN}}</div>{{/Beispiel2EN}}</div>{{/Beispiel}}
{{#Verwandt}}<div class="block"><div class="label">Verwandt</div><div class="chips">{{Verwandt}}</div></div>{{/Verwandt}}
{{#Notiz}}<div class="notiz">{{Notiz}}</div>{{/Notiz}}
</div>
```

## 3 — Präsens (er/sie/es)

**Front**
```html
<div class="karte">
{{#Praes_Frage}}
<div class="kopf">Präsens (er/sie/es) <span class="pill verb">{{Typ}}</span></div>
<div class="satz">{{Praes_Frage}}</div>
{{#Praes_GanzEN}}<div class="en2">{{Praes_GanzEN}}</div>{{/Praes_GanzEN}}
<div class="hinweis">{{Praes_Hinweis}}</div>
{{type:Praes_Antwort}}
{{/Praes_Frage}}
</div>
```

**Back**
```html
<div class="karte">
<div class="kopf">Präsens (er/sie/es) <span class="pill verb">{{Typ}}</span></div>
<div class="wort">{{Wort}}</div>
<hr id=answer>
{{type:Praes_Antwort}}
<div class="satz">{{Praes_Ganz}} {{tts de_DE voices=Apple_Anna_(Premium),com.google.android.tts-de-de-x-nfh-local:Praes_Ganz}}</div>
{{#Praes_GanzEN}}<div class="en2">{{Praes_GanzEN}}</div>{{/Praes_GanzEN}}
{{#Englisch}}<div class="block"><div class="label">Bedeutung</div><div class="en">{{Englisch}}</div></div>{{/Englisch}}
{{#Formen}}<div class="block"><div class="label">Formen</div><div class="chips">{{Formen}}</div></div>{{/Formen}}
{{#Verwandt}}<div class="block"><div class="label">Verwandt</div><div class="chips">{{Verwandt}}</div></div>{{/Verwandt}}
{{#Notiz}}<div class="notiz">{{Notiz}}</div>{{/Notiz}}
{{#Praes_Quelle}}<div class="quelle">{{Praes_Quelle}}</div>{{/Praes_Quelle}}
</div>
```

## 4 — Reflexivpronomen

**Front**
```html
<div class="karte">
{{#Refl_Frage}}
<div class="kopf">Reflexivpronomen <span class="pill verb">{{Typ}}</span></div>
<div class="satz">{{Refl_Frage}}</div>
{{#Refl_GanzEN}}<div class="en2">{{Refl_GanzEN}}</div>{{/Refl_GanzEN}}
<div class="hinweis">{{Refl_Hinweis}}</div>
{{type:Refl_Antwort}}
{{/Refl_Frage}}
</div>
```

**Back**
```html
<div class="karte">
<div class="kopf">Reflexivpronomen <span class="pill verb">{{Typ}}</span></div>
<div class="wort">{{Wort}}</div>
<hr id=answer>
{{type:Refl_Antwort}}
<div class="satz">{{Refl_Ganz}} {{tts de_DE voices=Apple_Anna_(Premium),com.google.android.tts-de-de-x-nfh-local:Refl_Ganz}}</div>
{{#Refl_GanzEN}}<div class="en2">{{Refl_GanzEN}}</div>{{/Refl_GanzEN}}
{{#Englisch}}<div class="block"><div class="label">Bedeutung</div><div class="en">{{Englisch}}</div></div>{{/Englisch}}
{{#Formen}}<div class="block"><div class="label">Formen</div><div class="chips">{{Formen}}</div></div>{{/Formen}}
{{#Verwandt}}<div class="block"><div class="label">Verwandt</div><div class="chips">{{Verwandt}}</div></div>{{/Verwandt}}
{{#Notiz}}<div class="notiz">{{Notiz}}</div>{{/Notiz}}
{{#Refl_Quelle}}<div class="quelle">{{Refl_Quelle}}</div>{{/Refl_Quelle}}
</div>
```

## 5 — Präposition

**Front**
```html
<div class="karte">
{{#Praep1_Frage}}
<div class="kopf">Präposition <span class="pill other">{{Typ}}</span></div>
<div class="satz">{{Praep1_Frage}}</div>
{{#Praep1_GanzEN}}<div class="en2">{{Praep1_GanzEN}}</div>{{/Praep1_GanzEN}}
<div class="hinweis">{{Praep1_Hinweis}}</div>
{{type:Praep1_Antwort}}
{{/Praep1_Frage}}
</div>
```

**Back**
```html
<div class="karte">
<div class="kopf">Präposition <span class="pill other">{{Typ}}</span></div>
<div class="wort">{{Wort}}</div>
<hr id=answer>
{{type:Praep1_Antwort}}
<div class="satz">{{Praep1_Ganz}} {{tts de_DE voices=Apple_Anna_(Premium),com.google.android.tts-de-de-x-nfh-local:Praep1_Ganz}}</div>
{{#Praep1_GanzEN}}<div class="en2">{{Praep1_GanzEN}}</div>{{/Praep1_GanzEN}}
{{#Englisch}}<div class="block"><div class="label">Bedeutung</div><div class="en">{{Englisch}}</div></div>{{/Englisch}}
{{#Formen}}<div class="block"><div class="label">Formen</div><div class="chips">{{Formen}}</div></div>{{/Formen}}
{{#Verwandt}}<div class="block"><div class="label">Verwandt</div><div class="chips">{{Verwandt}}</div></div>{{/Verwandt}}
{{#Notiz}}<div class="notiz">{{Notiz}}</div>{{/Notiz}}
{{#Praep1_Quelle}}<div class="quelle">{{Praep1_Quelle}}</div>{{/Praep1_Quelle}}
</div>
```

## 6 — Präposition 2

**Front**
```html
<div class="karte">
{{#Praep2_Frage}}
<div class="kopf">Präposition <span class="pill other">{{Typ}}</span></div>
<div class="satz">{{Praep2_Frage}}</div>
{{#Praep2_GanzEN}}<div class="en2">{{Praep2_GanzEN}}</div>{{/Praep2_GanzEN}}
<div class="hinweis">{{Praep2_Hinweis}}</div>
{{type:Praep2_Antwort}}
{{/Praep2_Frage}}
</div>
```

**Back**
```html
<div class="karte">
<div class="kopf">Präposition <span class="pill other">{{Typ}}</span></div>
<div class="wort">{{Wort}}</div>
<hr id=answer>
{{type:Praep2_Antwort}}
<div class="satz">{{Praep2_Ganz}} {{tts de_DE voices=Apple_Anna_(Premium),com.google.android.tts-de-de-x-nfh-local:Praep2_Ganz}}</div>
{{#Praep2_GanzEN}}<div class="en2">{{Praep2_GanzEN}}</div>{{/Praep2_GanzEN}}
{{#Englisch}}<div class="block"><div class="label">Bedeutung</div><div class="en">{{Englisch}}</div></div>{{/Englisch}}
{{#Formen}}<div class="block"><div class="label">Formen</div><div class="chips">{{Formen}}</div></div>{{/Formen}}
{{#Verwandt}}<div class="block"><div class="label">Verwandt</div><div class="chips">{{Verwandt}}</div></div>{{/Verwandt}}
{{#Notiz}}<div class="notiz">{{Notiz}}</div>{{/Notiz}}
{{#Praep2_Quelle}}<div class="quelle">{{Praep2_Quelle}}</div>{{/Praep2_Quelle}}
</div>
```

## 7 — Perfekt

**Front**
```html
<div class="karte">
{{#Part_Frage}}
<div class="kopf">Perfekt <span class="pill verb">{{Typ}}</span></div>
<div class="satz">{{Part_Frage}}</div>
{{#Part_GanzEN}}<div class="en2">{{Part_GanzEN}}</div>{{/Part_GanzEN}}
<div class="hinweis">{{Part_Hinweis}}</div>
{{type:Part_Antwort}}
{{/Part_Frage}}
</div>
```

**Back**
```html
<div class="karte">
<div class="kopf">Perfekt <span class="pill verb">{{Typ}}</span></div>
<div class="wort">{{Wort}}</div>
<hr id=answer>
{{type:Part_Antwort}}
<div class="satz">{{Part_Ganz}} {{tts de_DE voices=Apple_Anna_(Premium),com.google.android.tts-de-de-x-nfh-local:Part_Ganz}}</div>
{{#Part_GanzEN}}<div class="en2">{{Part_GanzEN}}</div>{{/Part_GanzEN}}
{{#Englisch}}<div class="block"><div class="label">Bedeutung</div><div class="en">{{Englisch}}</div></div>{{/Englisch}}
{{#Formen}}<div class="block"><div class="label">Formen</div><div class="chips">{{Formen}}</div></div>{{/Formen}}
{{#Verwandt}}<div class="block"><div class="label">Verwandt</div><div class="chips">{{Verwandt}}</div></div>{{/Verwandt}}
{{#Notiz}}<div class="notiz">{{Notiz}}</div>{{/Notiz}}
{{#Part_Quelle}}<div class="quelle">{{Part_Quelle}}</div>{{/Part_Quelle}}
</div>
```

## 8 — Präteritum

**Front**
```html
<div class="karte">
{{#Praet_Frage}}
<div class="kopf">Präteritum <span class="pill verb">{{Typ}}</span></div>
<div class="satz">{{Praet_Frage}}</div>
{{#Praet_GanzEN}}<div class="en2">{{Praet_GanzEN}}</div>{{/Praet_GanzEN}}
<div class="hinweis">{{Praet_Hinweis}}</div>
{{type:Praet_Antwort}}
{{/Praet_Frage}}
</div>
```

**Back**
```html
<div class="karte">
<div class="kopf">Präteritum <span class="pill verb">{{Typ}}</span></div>
<div class="wort">{{Wort}}</div>
<hr id=answer>
{{type:Praet_Antwort}}
<div class="satz">{{Praet_Ganz}} {{tts de_DE voices=Apple_Anna_(Premium),com.google.android.tts-de-de-x-nfh-local:Praet_Ganz}}</div>
{{#Praet_GanzEN}}<div class="en2">{{Praet_GanzEN}}</div>{{/Praet_GanzEN}}
{{#Englisch}}<div class="block"><div class="label">Bedeutung</div><div class="en">{{Englisch}}</div></div>{{/Englisch}}
{{#Formen}}<div class="block"><div class="label">Formen</div><div class="chips">{{Formen}}</div></div>{{/Formen}}
{{#Verwandt}}<div class="block"><div class="label">Verwandt</div><div class="chips">{{Verwandt}}</div></div>{{/Verwandt}}
{{#Notiz}}<div class="notiz">{{Notiz}}</div>{{/Notiz}}
{{#Praet_Quelle}}<div class="quelle">{{Praet_Quelle}}</div>{{/Praet_Quelle}}
</div>
```

## 9 — Deklination

**Front**
```html
<div class="karte">
{{#Dekl_Frage}}
<div class="kopf">Deklination <span class="pill noun">{{Typ}}</span></div>
<div class="satz">{{Dekl_Frage}}</div>
{{#Dekl_GanzEN}}<div class="en2">{{Dekl_GanzEN}}</div>{{/Dekl_GanzEN}}
<div class="hinweis">{{Dekl_Hinweis}}</div>
{{type:Dekl_Antwort}}
{{/Dekl_Frage}}
</div>
```

**Back**
```html
<div class="karte">
<div class="kopf">Deklination <span class="pill noun">{{Typ}}</span></div>
<div class="wort">{{Wort}}</div>
<hr id=answer>
{{type:Dekl_Antwort}}
<div class="satz">{{Dekl_Ganz}} {{tts de_DE voices=Apple_Anna_(Premium),com.google.android.tts-de-de-x-nfh-local:Dekl_Ganz}}</div>
{{#Dekl_GanzEN}}<div class="en2">{{Dekl_GanzEN}}</div>{{/Dekl_GanzEN}}
{{#Englisch}}<div class="block"><div class="label">Bedeutung</div><div class="en">{{Englisch}}</div></div>{{/Englisch}}
{{#Formen}}<div class="block"><div class="label">Formen</div><div class="chips">{{Formen}}</div></div>{{/Formen}}
{{#Verwandt}}<div class="block"><div class="label">Verwandt</div><div class="chips">{{Verwandt}}</div></div>{{/Verwandt}}
{{#Notiz}}<div class="notiz">{{Notiz}}</div>{{/Notiz}}
{{#Dekl_Quelle}}<div class="quelle">{{Dekl_Quelle}}</div>{{/Dekl_Quelle}}
</div>
```

## 10 — Deklination Plural

**Front**
```html
<div class="karte">
{{#DeklPl_Frage}}
<div class="kopf">Deklination Plural <span class="pill noun">{{Typ}}</span></div>
<div class="satz">{{DeklPl_Frage}}</div>
{{#DeklPl_GanzEN}}<div class="en2">{{DeklPl_GanzEN}}</div>{{/DeklPl_GanzEN}}
<div class="hinweis">{{DeklPl_Hinweis}}</div>
{{type:DeklPl_Antwort}}
{{/DeklPl_Frage}}
</div>
```

**Back**
```html
<div class="karte">
<div class="kopf">Deklination Plural <span class="pill noun">{{Typ}}</span></div>
<div class="wort">{{Wort}}</div>
<hr id=answer>
{{type:DeklPl_Antwort}}
<div class="satz">{{DeklPl_Ganz}} {{tts de_DE voices=Apple_Anna_(Premium),com.google.android.tts-de-de-x-nfh-local:DeklPl_Ganz}}</div>
{{#DeklPl_GanzEN}}<div class="en2">{{DeklPl_GanzEN}}</div>{{/DeklPl_GanzEN}}
{{#Englisch}}<div class="block"><div class="label">Bedeutung</div><div class="en">{{Englisch}}</div></div>{{/Englisch}}
{{#Formen}}<div class="block"><div class="label">Formen</div><div class="chips">{{Formen}}</div></div>{{/Formen}}
{{#Verwandt}}<div class="block"><div class="label">Verwandt</div><div class="chips">{{Verwandt}}</div></div>{{/Verwandt}}
{{#Notiz}}<div class="notiz">{{Notiz}}</div>{{/Notiz}}
{{#DeklPl_Quelle}}<div class="quelle">{{DeklPl_Quelle}}</div>{{/DeklPl_Quelle}}
</div>
```

## 11 — Konnektor 1

**Front**
```html
<div class="karte">
{{#Konnektor1_Frage}}
<div class="kopf">Konnektor <span class="pill other">{{Typ}}</span></div>
<div class="satz">{{Konnektor1_Frage}}</div>
{{#Konnektor1_GanzEN}}<div class="en2">{{Konnektor1_GanzEN}}</div>{{/Konnektor1_GanzEN}}
<div class="hinweis">{{Konnektor1_Hinweis}}</div>
{{type:Konnektor1_Antwort}}
{{/Konnektor1_Frage}}
</div>
```

**Back**
```html
<div class="karte">
<div class="kopf">Konnektor <span class="pill other">{{Typ}}</span></div>
<div class="wort">{{Wort}}</div>
<hr id=answer>
{{type:Konnektor1_Antwort}}
<div class="satz">{{Konnektor1_Ganz}} {{tts de_DE voices=Apple_Anna_(Premium),com.google.android.tts-de-de-x-nfh-local:Konnektor1_Ganz}}</div>
{{#Konnektor1_GanzEN}}<div class="en2">{{Konnektor1_GanzEN}}</div>{{/Konnektor1_GanzEN}}
{{#Englisch}}<div class="block"><div class="label">Bedeutung</div><div class="en">{{Englisch}}</div></div>{{/Englisch}}
{{#Formen}}<div class="block"><div class="label">Formen</div><div class="chips">{{Formen}}</div></div>{{/Formen}}
{{#Verwandt}}<div class="block"><div class="label">Verwandt</div><div class="chips">{{Verwandt}}</div></div>{{/Verwandt}}
{{#Notiz}}<div class="notiz">{{Notiz}}</div>{{/Notiz}}
{{#Konnektor1_Quelle}}<div class="quelle">{{Konnektor1_Quelle}}</div>{{/Konnektor1_Quelle}}
</div>
```

## 12 — Konnektor 2

**Front**
```html
<div class="karte">
{{#Konnektor2_Frage}}
<div class="kopf">Konnektor <span class="pill other">{{Typ}}</span></div>
<div class="satz">{{Konnektor2_Frage}}</div>
{{#Konnektor2_GanzEN}}<div class="en2">{{Konnektor2_GanzEN}}</div>{{/Konnektor2_GanzEN}}
<div class="hinweis">{{Konnektor2_Hinweis}}</div>
{{type:Konnektor2_Antwort}}
{{/Konnektor2_Frage}}
</div>
```

**Back**
```html
<div class="karte">
<div class="kopf">Konnektor <span class="pill other">{{Typ}}</span></div>
<div class="wort">{{Wort}}</div>
<hr id=answer>
{{type:Konnektor2_Antwort}}
<div class="satz">{{Konnektor2_Ganz}} {{tts de_DE voices=Apple_Anna_(Premium),com.google.android.tts-de-de-x-nfh-local:Konnektor2_Ganz}}</div>
{{#Konnektor2_GanzEN}}<div class="en2">{{Konnektor2_GanzEN}}</div>{{/Konnektor2_GanzEN}}
{{#Englisch}}<div class="block"><div class="label">Bedeutung</div><div class="en">{{Englisch}}</div></div>{{/Englisch}}
{{#Formen}}<div class="block"><div class="label">Formen</div><div class="chips">{{Formen}}</div></div>{{/Formen}}
{{#Verwandt}}<div class="block"><div class="label">Verwandt</div><div class="chips">{{Verwandt}}</div></div>{{/Verwandt}}
{{#Notiz}}<div class="notiz">{{Notiz}}</div>{{/Notiz}}
{{#Konnektor2_Quelle}}<div class="quelle">{{Konnektor2_Quelle}}</div>{{/Konnektor2_Quelle}}
</div>
```

## 13 — Konnektor 3

**Front**
```html
<div class="karte">
{{#Konnektor3_Frage}}
<div class="kopf">Konnektor <span class="pill other">{{Typ}}</span></div>
<div class="satz">{{Konnektor3_Frage}}</div>
{{#Konnektor3_GanzEN}}<div class="en2">{{Konnektor3_GanzEN}}</div>{{/Konnektor3_GanzEN}}
<div class="hinweis">{{Konnektor3_Hinweis}}</div>
{{type:Konnektor3_Antwort}}
{{/Konnektor3_Frage}}
</div>
```

**Back**
```html
<div class="karte">
<div class="kopf">Konnektor <span class="pill other">{{Typ}}</span></div>
<div class="wort">{{Wort}}</div>
<hr id=answer>
{{type:Konnektor3_Antwort}}
<div class="satz">{{Konnektor3_Ganz}} {{tts de_DE voices=Apple_Anna_(Premium),com.google.android.tts-de-de-x-nfh-local:Konnektor3_Ganz}}</div>
{{#Konnektor3_GanzEN}}<div class="en2">{{Konnektor3_GanzEN}}</div>{{/Konnektor3_GanzEN}}
{{#Englisch}}<div class="block"><div class="label">Bedeutung</div><div class="en">{{Englisch}}</div></div>{{/Englisch}}
{{#Formen}}<div class="block"><div class="label">Formen</div><div class="chips">{{Formen}}</div></div>{{/Formen}}
{{#Verwandt}}<div class="block"><div class="label">Verwandt</div><div class="chips">{{Verwandt}}</div></div>{{/Verwandt}}
{{#Notiz}}<div class="notiz">{{Notiz}}</div>{{/Notiz}}
{{#Konnektor3_Quelle}}<div class="quelle">{{Konnektor3_Quelle}}</div>{{/Konnektor3_Quelle}}
</div>
```

## 14 — Konnektor 4

**Front**
```html
<div class="karte">
{{#Konnektor4_Frage}}
<div class="kopf">Konnektor <span class="pill other">{{Typ}}</span></div>
<div class="satz">{{Konnektor4_Frage}}</div>
{{#Konnektor4_GanzEN}}<div class="en2">{{Konnektor4_GanzEN}}</div>{{/Konnektor4_GanzEN}}
<div class="hinweis">{{Konnektor4_Hinweis}}</div>
{{type:Konnektor4_Antwort}}
{{/Konnektor4_Frage}}
</div>
```

**Back**
```html
<div class="karte">
<div class="kopf">Konnektor <span class="pill other">{{Typ}}</span></div>
<div class="wort">{{Wort}}</div>
<hr id=answer>
{{type:Konnektor4_Antwort}}
<div class="satz">{{Konnektor4_Ganz}} {{tts de_DE voices=Apple_Anna_(Premium),com.google.android.tts-de-de-x-nfh-local:Konnektor4_Ganz}}</div>
{{#Konnektor4_GanzEN}}<div class="en2">{{Konnektor4_GanzEN}}</div>{{/Konnektor4_GanzEN}}
{{#Englisch}}<div class="block"><div class="label">Bedeutung</div><div class="en">{{Englisch}}</div></div>{{/Englisch}}
{{#Formen}}<div class="block"><div class="label">Formen</div><div class="chips">{{Formen}}</div></div>{{/Formen}}
{{#Verwandt}}<div class="block"><div class="label">Verwandt</div><div class="chips">{{Verwandt}}</div></div>{{/Verwandt}}
{{#Notiz}}<div class="notiz">{{Notiz}}</div>{{/Notiz}}
{{#Konnektor4_Quelle}}<div class="quelle">{{Konnektor4_Quelle}}</div>{{/Konnektor4_Quelle}}
</div>
```

## 15 — Welches Wort passt?

**Front**
```html
<div class="karte">
{{#Kontrast_Frage}}
<div class="kopf">Welches Wort passt? <span class="pill other">{{Typ}}</span></div>
<div class="satz">{{Kontrast_Frage}}</div>
{{#Kontrast_Hinweis}}<div class="hinweis">{{Kontrast_Hinweis}}</div>{{/Kontrast_Hinweis}}
{{type:Kontrast_Antwort}}
{{/Kontrast_Frage}}
</div>
```

**Back**
```html
<div class="karte">
<div class="kopf">Welches Wort passt? <span class="pill other">{{Typ}}</span></div>
<div class="wort">{{Wort}}</div>
<hr id=answer>
{{type:Kontrast_Antwort}}
<div class="satz">{{Kontrast_Ganz}} {{tts de_DE voices=Apple_Anna_(Premium),com.google.android.tts-de-de-x-nfh-local:Kontrast_Ganz}}</div>
{{#Kontrast_GanzEN}}<div class="en2">{{Kontrast_GanzEN}}</div>{{/Kontrast_GanzEN}}
{{#Englisch}}<div class="block"><div class="label">Bedeutung</div><div class="en">{{Englisch}}</div></div>{{/Englisch}}
{{#Formen}}<div class="block"><div class="label">Formen</div><div class="chips">{{Formen}}</div></div>{{/Formen}}
{{#Verwandt}}<div class="block"><div class="label">Verwandt</div><div class="chips">{{Verwandt}}</div></div>{{/Verwandt}}
{{#Notiz}}<div class="notiz">{{Notiz}}</div>{{/Notiz}}
{{#Kontrast_Quelle}}<div class="quelle">{{Kontrast_Quelle}}</div>{{/Kontrast_Quelle}}
</div>
```

## 16 — Nebensatz: Wortstellung

**Front**
```html
<div class="karte">
{{#Neben_Frage}}
<div class="kopf">Nebensatz: Wortstellung <span class="pill other">{{Typ}}</span></div>
<div class="satz">{{Neben_Frage}}</div>
<div class="hinweis">{{Wort}}</div>
{{type:Neben_Antwort}}
{{/Neben_Frage}}
</div>
```

**Back**
```html
<div class="karte">
<div class="kopf">Nebensatz: Wortstellung <span class="pill other">{{Typ}}</span></div>
<div class="wort">{{Wort}}</div>
<hr id=answer>
{{type:Neben_Antwort}}
<div class="satz">{{Neben_Ganz}} {{tts de_DE voices=Apple_Anna_(Premium),com.google.android.tts-de-de-x-nfh-local:Neben_Ganz}}</div>
{{#Neben_GanzEN}}<div class="en2">{{Neben_GanzEN}}</div>{{/Neben_GanzEN}}
{{#Englisch}}<div class="block"><div class="label">Bedeutung</div><div class="en">{{Englisch}}</div></div>{{/Englisch}}
{{#Formen}}<div class="block"><div class="label">Formen</div><div class="chips">{{Formen}}</div></div>{{/Formen}}
{{#Verwandt}}<div class="block"><div class="label">Verwandt</div><div class="chips">{{Verwandt}}</div></div>{{/Verwandt}}
{{#Notiz}}<div class="notiz">{{Notiz}}</div>{{/Notiz}}
{{#Neben_Quelle}}<div class="quelle">{{Neben_Quelle}}</div>{{/Neben_Quelle}}
</div>
```

