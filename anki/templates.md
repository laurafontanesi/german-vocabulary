# Card templates (generated — do not edit by hand)

Note type: **Deutsch**. Create the 125 fields in exactly this order, then one card type per section below, named as in the heading, and paste its front and back.

## Fields

```
Wort, Typ, Formen, Englisch, EnglischKurz, Beispiel, BeispielEN, Beispiel2, Beispiel2EN, Verwandt, Notiz, Praet_Frage, Praet_Antwort, Praet_Ganz, Praet_GanzEN, Praet_Hinweis, Praet_Quelle, Part_Frage, Part_Antwort, Part_Ganz, Part_GanzEN, Part_Hinweis, Part_Quelle, Praes_Frage, Praes_Antwort, Praes_Ganz, Praes_GanzEN, Praes_Hinweis, Praes_Quelle, Refl_Frage, Refl_Antwort, Refl_Ganz, Refl_GanzEN, Refl_Hinweis, Refl_Quelle, Kasus1_Frage, Kasus1_Antwort, Kasus1_Ganz, Kasus1_GanzEN, Kasus1_Hinweis, Kasus1_Quelle, Kasus2_Frage, Kasus2_Antwort, Kasus2_Ganz, Kasus2_GanzEN, Kasus2_Hinweis, Kasus2_Quelle, AdjArt_Frage, AdjArt_Antwort, AdjArt_Ganz, AdjArt_GanzEN, AdjArt_Hinweis, AdjArt_Quelle, AdjDet_Frage, AdjDet_Antwort, AdjDet_Ganz, AdjDet_GanzEN, AdjDet_Hinweis, AdjDet_Quelle, Luecke1_Frage, Luecke1_Antwort, Luecke1_Ganz, Luecke1_GanzEN, Luecke1_Hinweis, Luecke1_Quelle, Luecke2_Frage, Luecke2_Antwort, Luecke2_Ganz, Luecke2_GanzEN, Luecke2_Hinweis, Luecke2_Quelle, Luecke3_Frage, Luecke3_Antwort, Luecke3_Ganz, Luecke3_GanzEN, Luecke3_Hinweis, Luecke3_Quelle, Luecke4_Frage, Luecke4_Antwort, Luecke4_Ganz, Luecke4_GanzEN, Luecke4_Hinweis, Luecke4_Quelle, Luecke5_Frage, Luecke5_Antwort, Luecke5_Ganz, Luecke5_GanzEN, Luecke5_Hinweis, Luecke5_Quelle, Luecke6_Frage, Luecke6_Antwort, Luecke6_Ganz, Luecke6_GanzEN, Luecke6_Hinweis, Luecke6_Quelle, Praep_Frage, Praep_Antwort, Praep_Ganz, Praep_GanzEN, Praep_Hinweis, Praep_Quelle, Kontrast_Frage, Kontrast_Antwort, Kontrast_Ganz, Kontrast_GanzEN, Kontrast_Hinweis, Kontrast_Quelle, Neben_Frage, Neben_Antwort, Neben_Ganz, Neben_GanzEN, Neben_Hinweis, Neben_Quelle, Komma_Frage, Komma_Antwort, Komma_Ganz, Komma_GanzEN, Komma_Hinweis, Komma_Quelle, Defin_Frage, Defin_Antwort, Defin_Ganz, Defin_GanzEN, Defin_Hinweis, Defin_Quelle
```

Tags are column 126.

## 1 — Präteritum

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

## 2 — Partizip II

**Front**
```html
<div class="karte">
{{#Part_Frage}}
<div class="kopf">Partizip II <span class="pill verb">{{Typ}}</span></div>
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
<div class="kopf">Partizip II <span class="pill verb">{{Typ}}</span></div>
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

## 5 — Kasus

**Front**
```html
<div class="karte">
{{#Kasus1_Frage}}
<div class="kopf">Kasus <span class="pill noun">{{Typ}}</span></div>
<div class="satz">{{Kasus1_Frage}}</div>
{{#Kasus1_GanzEN}}<div class="en2">{{Kasus1_GanzEN}}</div>{{/Kasus1_GanzEN}}
<div class="hinweis">{{Kasus1_Hinweis}}</div>
{{type:Kasus1_Antwort}}
{{/Kasus1_Frage}}
</div>
```

**Back**
```html
<div class="karte">
<div class="kopf">Kasus <span class="pill noun">{{Typ}}</span></div>
<div class="wort">{{Wort}}</div>
<hr id=answer>
{{type:Kasus1_Antwort}}
<div class="satz">{{Kasus1_Ganz}} {{tts de_DE voices=Apple_Anna_(Premium),com.google.android.tts-de-de-x-nfh-local:Kasus1_Ganz}}</div>
{{#Kasus1_GanzEN}}<div class="en2">{{Kasus1_GanzEN}}</div>{{/Kasus1_GanzEN}}
{{#Englisch}}<div class="block"><div class="label">Bedeutung</div><div class="en">{{Englisch}}</div></div>{{/Englisch}}
{{#Formen}}<div class="block"><div class="label">Formen</div><div class="chips">{{Formen}}</div></div>{{/Formen}}
{{#Verwandt}}<div class="block"><div class="label">Verwandt</div><div class="chips">{{Verwandt}}</div></div>{{/Verwandt}}
{{#Notiz}}<div class="notiz">{{Notiz}}</div>{{/Notiz}}
{{#Kasus1_Quelle}}<div class="quelle">{{Kasus1_Quelle}}</div>{{/Kasus1_Quelle}}
</div>
```

## 6 — Kasus 2

**Front**
```html
<div class="karte">
{{#Kasus2_Frage}}
<div class="kopf">Kasus <span class="pill noun">{{Typ}}</span></div>
<div class="satz">{{Kasus2_Frage}}</div>
{{#Kasus2_GanzEN}}<div class="en2">{{Kasus2_GanzEN}}</div>{{/Kasus2_GanzEN}}
<div class="hinweis">{{Kasus2_Hinweis}}</div>
{{type:Kasus2_Antwort}}
{{/Kasus2_Frage}}
</div>
```

**Back**
```html
<div class="karte">
<div class="kopf">Kasus <span class="pill noun">{{Typ}}</span></div>
<div class="wort">{{Wort}}</div>
<hr id=answer>
{{type:Kasus2_Antwort}}
<div class="satz">{{Kasus2_Ganz}} {{tts de_DE voices=Apple_Anna_(Premium),com.google.android.tts-de-de-x-nfh-local:Kasus2_Ganz}}</div>
{{#Kasus2_GanzEN}}<div class="en2">{{Kasus2_GanzEN}}</div>{{/Kasus2_GanzEN}}
{{#Englisch}}<div class="block"><div class="label">Bedeutung</div><div class="en">{{Englisch}}</div></div>{{/Englisch}}
{{#Formen}}<div class="block"><div class="label">Formen</div><div class="chips">{{Formen}}</div></div>{{/Formen}}
{{#Verwandt}}<div class="block"><div class="label">Verwandt</div><div class="chips">{{Verwandt}}</div></div>{{/Verwandt}}
{{#Notiz}}<div class="notiz">{{Notiz}}</div>{{/Notiz}}
{{#Kasus2_Quelle}}<div class="quelle">{{Kasus2_Quelle}}</div>{{/Kasus2_Quelle}}
</div>
```

## 7 — Adjektiv nach Artikel

**Front**
```html
<div class="karte">
{{#AdjArt_Frage}}
<div class="kopf">Adjektiv nach Artikel <span class="pill adjadv">{{Typ}}</span></div>
<div class="satz">{{AdjArt_Frage}}</div>
{{#AdjArt_GanzEN}}<div class="en2">{{AdjArt_GanzEN}}</div>{{/AdjArt_GanzEN}}
<div class="hinweis">{{AdjArt_Hinweis}}</div>
{{type:AdjArt_Antwort}}
{{/AdjArt_Frage}}
</div>
```

**Back**
```html
<div class="karte">
<div class="kopf">Adjektiv nach Artikel <span class="pill adjadv">{{Typ}}</span></div>
<div class="wort">{{Wort}}</div>
<hr id=answer>
{{type:AdjArt_Antwort}}
<div class="satz">{{AdjArt_Ganz}} {{tts de_DE voices=Apple_Anna_(Premium),com.google.android.tts-de-de-x-nfh-local:AdjArt_Ganz}}</div>
{{#AdjArt_GanzEN}}<div class="en2">{{AdjArt_GanzEN}}</div>{{/AdjArt_GanzEN}}
{{#Englisch}}<div class="block"><div class="label">Bedeutung</div><div class="en">{{Englisch}}</div></div>{{/Englisch}}
{{#Formen}}<div class="block"><div class="label">Formen</div><div class="chips">{{Formen}}</div></div>{{/Formen}}
{{#Verwandt}}<div class="block"><div class="label">Verwandt</div><div class="chips">{{Verwandt}}</div></div>{{/Verwandt}}
{{#Notiz}}<div class="notiz">{{Notiz}}</div>{{/Notiz}}
{{#AdjArt_Quelle}}<div class="quelle">{{AdjArt_Quelle}}</div>{{/AdjArt_Quelle}}
</div>
```

## 8 — Adjektiv nach Begleiter

**Front**
```html
<div class="karte">
{{#AdjDet_Frage}}
<div class="kopf">Adjektiv nach Begleiter <span class="pill adjadv">{{Typ}}</span></div>
<div class="satz">{{AdjDet_Frage}}</div>
{{#AdjDet_GanzEN}}<div class="en2">{{AdjDet_GanzEN}}</div>{{/AdjDet_GanzEN}}
<div class="hinweis">{{AdjDet_Hinweis}}</div>
{{type:AdjDet_Antwort}}
{{/AdjDet_Frage}}
</div>
```

**Back**
```html
<div class="karte">
<div class="kopf">Adjektiv nach Begleiter <span class="pill adjadv">{{Typ}}</span></div>
<div class="wort">{{Wort}}</div>
<hr id=answer>
{{type:AdjDet_Antwort}}
<div class="satz">{{AdjDet_Ganz}} {{tts de_DE voices=Apple_Anna_(Premium),com.google.android.tts-de-de-x-nfh-local:AdjDet_Ganz}}</div>
{{#AdjDet_GanzEN}}<div class="en2">{{AdjDet_GanzEN}}</div>{{/AdjDet_GanzEN}}
{{#Englisch}}<div class="block"><div class="label">Bedeutung</div><div class="en">{{Englisch}}</div></div>{{/Englisch}}
{{#Formen}}<div class="block"><div class="label">Formen</div><div class="chips">{{Formen}}</div></div>{{/Formen}}
{{#Verwandt}}<div class="block"><div class="label">Verwandt</div><div class="chips">{{Verwandt}}</div></div>{{/Verwandt}}
{{#Notiz}}<div class="notiz">{{Notiz}}</div>{{/Notiz}}
{{#AdjDet_Quelle}}<div class="quelle">{{AdjDet_Quelle}}</div>{{/AdjDet_Quelle}}
</div>
```

## 9 — Lücke 1

**Front**
```html
<div class="karte">
{{#Luecke1_Frage}}
<div class="kopf">Lücke <span class="pill other">{{Typ}}</span></div>
<div class="satz">{{Luecke1_Frage}}</div>
{{#Luecke1_GanzEN}}<div class="en2">{{Luecke1_GanzEN}}</div>{{/Luecke1_GanzEN}}
<div class="hinweis">{{Luecke1_Hinweis}}</div>
{{type:Luecke1_Antwort}}
{{/Luecke1_Frage}}
</div>
```

**Back**
```html
<div class="karte">
<div class="kopf">Lücke <span class="pill other">{{Typ}}</span></div>
<div class="wort">{{Wort}}</div>
<hr id=answer>
{{type:Luecke1_Antwort}}
<div class="satz">{{Luecke1_Ganz}} {{tts de_DE voices=Apple_Anna_(Premium),com.google.android.tts-de-de-x-nfh-local:Luecke1_Ganz}}</div>
{{#Luecke1_GanzEN}}<div class="en2">{{Luecke1_GanzEN}}</div>{{/Luecke1_GanzEN}}
{{#Englisch}}<div class="block"><div class="label">Bedeutung</div><div class="en">{{Englisch}}</div></div>{{/Englisch}}
{{#Formen}}<div class="block"><div class="label">Formen</div><div class="chips">{{Formen}}</div></div>{{/Formen}}
{{#Verwandt}}<div class="block"><div class="label">Verwandt</div><div class="chips">{{Verwandt}}</div></div>{{/Verwandt}}
{{#Notiz}}<div class="notiz">{{Notiz}}</div>{{/Notiz}}
{{#Luecke1_Quelle}}<div class="quelle">{{Luecke1_Quelle}}</div>{{/Luecke1_Quelle}}
</div>
```

## 10 — Lücke 2

**Front**
```html
<div class="karte">
{{#Luecke2_Frage}}
<div class="kopf">Lücke <span class="pill other">{{Typ}}</span></div>
<div class="satz">{{Luecke2_Frage}}</div>
{{#Luecke2_GanzEN}}<div class="en2">{{Luecke2_GanzEN}}</div>{{/Luecke2_GanzEN}}
<div class="hinweis">{{Luecke2_Hinweis}}</div>
{{type:Luecke2_Antwort}}
{{/Luecke2_Frage}}
</div>
```

**Back**
```html
<div class="karte">
<div class="kopf">Lücke <span class="pill other">{{Typ}}</span></div>
<div class="wort">{{Wort}}</div>
<hr id=answer>
{{type:Luecke2_Antwort}}
<div class="satz">{{Luecke2_Ganz}} {{tts de_DE voices=Apple_Anna_(Premium),com.google.android.tts-de-de-x-nfh-local:Luecke2_Ganz}}</div>
{{#Luecke2_GanzEN}}<div class="en2">{{Luecke2_GanzEN}}</div>{{/Luecke2_GanzEN}}
{{#Englisch}}<div class="block"><div class="label">Bedeutung</div><div class="en">{{Englisch}}</div></div>{{/Englisch}}
{{#Formen}}<div class="block"><div class="label">Formen</div><div class="chips">{{Formen}}</div></div>{{/Formen}}
{{#Verwandt}}<div class="block"><div class="label">Verwandt</div><div class="chips">{{Verwandt}}</div></div>{{/Verwandt}}
{{#Notiz}}<div class="notiz">{{Notiz}}</div>{{/Notiz}}
{{#Luecke2_Quelle}}<div class="quelle">{{Luecke2_Quelle}}</div>{{/Luecke2_Quelle}}
</div>
```

## 11 — Lücke 3

**Front**
```html
<div class="karte">
{{#Luecke3_Frage}}
<div class="kopf">Lücke <span class="pill other">{{Typ}}</span></div>
<div class="satz">{{Luecke3_Frage}}</div>
{{#Luecke3_GanzEN}}<div class="en2">{{Luecke3_GanzEN}}</div>{{/Luecke3_GanzEN}}
<div class="hinweis">{{Luecke3_Hinweis}}</div>
{{type:Luecke3_Antwort}}
{{/Luecke3_Frage}}
</div>
```

**Back**
```html
<div class="karte">
<div class="kopf">Lücke <span class="pill other">{{Typ}}</span></div>
<div class="wort">{{Wort}}</div>
<hr id=answer>
{{type:Luecke3_Antwort}}
<div class="satz">{{Luecke3_Ganz}} {{tts de_DE voices=Apple_Anna_(Premium),com.google.android.tts-de-de-x-nfh-local:Luecke3_Ganz}}</div>
{{#Luecke3_GanzEN}}<div class="en2">{{Luecke3_GanzEN}}</div>{{/Luecke3_GanzEN}}
{{#Englisch}}<div class="block"><div class="label">Bedeutung</div><div class="en">{{Englisch}}</div></div>{{/Englisch}}
{{#Formen}}<div class="block"><div class="label">Formen</div><div class="chips">{{Formen}}</div></div>{{/Formen}}
{{#Verwandt}}<div class="block"><div class="label">Verwandt</div><div class="chips">{{Verwandt}}</div></div>{{/Verwandt}}
{{#Notiz}}<div class="notiz">{{Notiz}}</div>{{/Notiz}}
{{#Luecke3_Quelle}}<div class="quelle">{{Luecke3_Quelle}}</div>{{/Luecke3_Quelle}}
</div>
```

## 12 — Lücke 4

**Front**
```html
<div class="karte">
{{#Luecke4_Frage}}
<div class="kopf">Lücke <span class="pill other">{{Typ}}</span></div>
<div class="satz">{{Luecke4_Frage}}</div>
{{#Luecke4_GanzEN}}<div class="en2">{{Luecke4_GanzEN}}</div>{{/Luecke4_GanzEN}}
<div class="hinweis">{{Luecke4_Hinweis}}</div>
{{type:Luecke4_Antwort}}
{{/Luecke4_Frage}}
</div>
```

**Back**
```html
<div class="karte">
<div class="kopf">Lücke <span class="pill other">{{Typ}}</span></div>
<div class="wort">{{Wort}}</div>
<hr id=answer>
{{type:Luecke4_Antwort}}
<div class="satz">{{Luecke4_Ganz}} {{tts de_DE voices=Apple_Anna_(Premium),com.google.android.tts-de-de-x-nfh-local:Luecke4_Ganz}}</div>
{{#Luecke4_GanzEN}}<div class="en2">{{Luecke4_GanzEN}}</div>{{/Luecke4_GanzEN}}
{{#Englisch}}<div class="block"><div class="label">Bedeutung</div><div class="en">{{Englisch}}</div></div>{{/Englisch}}
{{#Formen}}<div class="block"><div class="label">Formen</div><div class="chips">{{Formen}}</div></div>{{/Formen}}
{{#Verwandt}}<div class="block"><div class="label">Verwandt</div><div class="chips">{{Verwandt}}</div></div>{{/Verwandt}}
{{#Notiz}}<div class="notiz">{{Notiz}}</div>{{/Notiz}}
{{#Luecke4_Quelle}}<div class="quelle">{{Luecke4_Quelle}}</div>{{/Luecke4_Quelle}}
</div>
```

## 13 — Lücke 5

**Front**
```html
<div class="karte">
{{#Luecke5_Frage}}
<div class="kopf">Lücke <span class="pill other">{{Typ}}</span></div>
<div class="satz">{{Luecke5_Frage}}</div>
{{#Luecke5_GanzEN}}<div class="en2">{{Luecke5_GanzEN}}</div>{{/Luecke5_GanzEN}}
<div class="hinweis">{{Luecke5_Hinweis}}</div>
{{type:Luecke5_Antwort}}
{{/Luecke5_Frage}}
</div>
```

**Back**
```html
<div class="karte">
<div class="kopf">Lücke <span class="pill other">{{Typ}}</span></div>
<div class="wort">{{Wort}}</div>
<hr id=answer>
{{type:Luecke5_Antwort}}
<div class="satz">{{Luecke5_Ganz}} {{tts de_DE voices=Apple_Anna_(Premium),com.google.android.tts-de-de-x-nfh-local:Luecke5_Ganz}}</div>
{{#Luecke5_GanzEN}}<div class="en2">{{Luecke5_GanzEN}}</div>{{/Luecke5_GanzEN}}
{{#Englisch}}<div class="block"><div class="label">Bedeutung</div><div class="en">{{Englisch}}</div></div>{{/Englisch}}
{{#Formen}}<div class="block"><div class="label">Formen</div><div class="chips">{{Formen}}</div></div>{{/Formen}}
{{#Verwandt}}<div class="block"><div class="label">Verwandt</div><div class="chips">{{Verwandt}}</div></div>{{/Verwandt}}
{{#Notiz}}<div class="notiz">{{Notiz}}</div>{{/Notiz}}
{{#Luecke5_Quelle}}<div class="quelle">{{Luecke5_Quelle}}</div>{{/Luecke5_Quelle}}
</div>
```

## 14 — Lücke 6

**Front**
```html
<div class="karte">
{{#Luecke6_Frage}}
<div class="kopf">Lücke <span class="pill other">{{Typ}}</span></div>
<div class="satz">{{Luecke6_Frage}}</div>
{{#Luecke6_GanzEN}}<div class="en2">{{Luecke6_GanzEN}}</div>{{/Luecke6_GanzEN}}
<div class="hinweis">{{Luecke6_Hinweis}}</div>
{{type:Luecke6_Antwort}}
{{/Luecke6_Frage}}
</div>
```

**Back**
```html
<div class="karte">
<div class="kopf">Lücke <span class="pill other">{{Typ}}</span></div>
<div class="wort">{{Wort}}</div>
<hr id=answer>
{{type:Luecke6_Antwort}}
<div class="satz">{{Luecke6_Ganz}} {{tts de_DE voices=Apple_Anna_(Premium),com.google.android.tts-de-de-x-nfh-local:Luecke6_Ganz}}</div>
{{#Luecke6_GanzEN}}<div class="en2">{{Luecke6_GanzEN}}</div>{{/Luecke6_GanzEN}}
{{#Englisch}}<div class="block"><div class="label">Bedeutung</div><div class="en">{{Englisch}}</div></div>{{/Englisch}}
{{#Formen}}<div class="block"><div class="label">Formen</div><div class="chips">{{Formen}}</div></div>{{/Formen}}
{{#Verwandt}}<div class="block"><div class="label">Verwandt</div><div class="chips">{{Verwandt}}</div></div>{{/Verwandt}}
{{#Notiz}}<div class="notiz">{{Notiz}}</div>{{/Notiz}}
{{#Luecke6_Quelle}}<div class="quelle">{{Luecke6_Quelle}}</div>{{/Luecke6_Quelle}}
</div>
```

## 15 — Präposition und Kasus

**Front**
```html
<div class="karte">
{{#Praep_Frage}}
<div class="kopf">Präposition und Kasus <span class="pill verb">{{Typ}}</span></div>
<div class="satz">{{Praep_Frage}}</div>
<div class="hinweis">Lücken füllen</div>
<div class="hinweis">{{Wort}}</div>
{{type:Praep_Antwort}}
{{/Praep_Frage}}
</div>
```

**Back**
```html
<div class="karte">
<div class="kopf">Präposition und Kasus <span class="pill verb">{{Typ}}</span></div>
<div class="wort">{{Wort}}</div>
<hr id=answer>
{{type:Praep_Antwort}}
<div class="satz">{{Praep_Ganz}} {{tts de_DE voices=Apple_Anna_(Premium),com.google.android.tts-de-de-x-nfh-local:Praep_Ganz}}</div>
{{#Praep_GanzEN}}<div class="en2">{{Praep_GanzEN}}</div>{{/Praep_GanzEN}}
{{#Englisch}}<div class="block"><div class="label">Bedeutung</div><div class="en">{{Englisch}}</div></div>{{/Englisch}}
{{#Formen}}<div class="block"><div class="label">Formen</div><div class="chips">{{Formen}}</div></div>{{/Formen}}
{{#Verwandt}}<div class="block"><div class="label">Verwandt</div><div class="chips">{{Verwandt}}</div></div>{{/Verwandt}}
{{#Notiz}}<div class="notiz">{{Notiz}}</div>{{/Notiz}}
{{#Praep_Quelle}}<div class="quelle">{{Praep_Quelle}}</div>{{/Praep_Quelle}}
</div>
```

## 16 — Welches Wort passt?

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

## 17 — Nebensatz: Wortstellung

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

## 18 — Komma setzen

**Front**
```html
<div class="karte">
{{#Komma_Frage}}
<div class="kopf">Komma setzen <span class="pill other">{{Typ}}</span></div>
<div class="satz">{{Komma_Frage}}</div>
<div class="hinweis">{{Wort}}</div>
{{type:Komma_Antwort}}
{{/Komma_Frage}}
</div>
```

**Back**
```html
<div class="karte">
<div class="kopf">Komma setzen <span class="pill other">{{Typ}}</span></div>
<div class="wort">{{Wort}}</div>
<hr id=answer>
{{type:Komma_Antwort}}
<div class="satz">{{Komma_Ganz}} {{tts de_DE voices=Apple_Anna_(Premium),com.google.android.tts-de-de-x-nfh-local:Komma_Ganz}}</div>
{{#Komma_GanzEN}}<div class="en2">{{Komma_GanzEN}}</div>{{/Komma_GanzEN}}
{{#Englisch}}<div class="block"><div class="label">Bedeutung</div><div class="en">{{Englisch}}</div></div>{{/Englisch}}
{{#Formen}}<div class="block"><div class="label">Formen</div><div class="chips">{{Formen}}</div></div>{{/Formen}}
{{#Verwandt}}<div class="block"><div class="label">Verwandt</div><div class="chips">{{Verwandt}}</div></div>{{/Verwandt}}
{{#Notiz}}<div class="notiz">{{Notiz}}</div>{{/Notiz}}
{{#Komma_Quelle}}<div class="quelle">{{Komma_Quelle}}</div>{{/Komma_Quelle}}
</div>
```

## 19 — Definition

**Front**
```html
<div class="karte">
{{#Defin_Frage}}
<div class="kopf">Definition <span class="pill other">{{Typ}}</span></div>
<div class="satz">{{Defin_Frage}}</div>
{{#Defin_Hinweis}}<div class="hinweis">{{Defin_Hinweis}}</div>{{/Defin_Hinweis}}
{{type:Defin_Antwort}}
{{/Defin_Frage}}
</div>
```

**Back**
```html
<div class="karte">
<div class="kopf">Definition <span class="pill other">{{Typ}}</span></div>
<div class="wort">{{Wort}}</div>
<hr id=answer>
{{type:Defin_Antwort}}
<div class="satz">{{Defin_Ganz}} {{tts de_DE voices=Apple_Anna_(Premium),com.google.android.tts-de-de-x-nfh-local:Defin_Ganz}}</div>
{{#Defin_GanzEN}}<div class="en2">{{Defin_GanzEN}}</div>{{/Defin_GanzEN}}
{{#Englisch}}<div class="block"><div class="label">Bedeutung</div><div class="en">{{Englisch}}</div></div>{{/Englisch}}
{{#Formen}}<div class="block"><div class="label">Formen</div><div class="chips">{{Formen}}</div></div>{{/Formen}}
{{#Verwandt}}<div class="block"><div class="label">Verwandt</div><div class="chips">{{Verwandt}}</div></div>{{/Verwandt}}
{{#Notiz}}<div class="notiz">{{Notiz}}</div>{{/Notiz}}
{{#Defin_Quelle}}<div class="quelle">{{Defin_Quelle}}</div>{{/Defin_Quelle}}
</div>
```

## 20 — Produzieren

**Front**
```html
<div class="karte">
<div class="kopf">Produzieren <span class="pill other">{{Typ}}</span></div>
<div class="en gross">{{Englisch}}</div>
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

## 21 — Bedeutung

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

