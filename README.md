# UniGit – tietopankkipohja

Tämä repo on sinun tietopankkisi: varasto, projektit, treenit, reseptit, päiväkirja tai mitä ikinä haluat seurata. Data on tavallisina tekstitiedostoina sinun omassa GitHub-repossasi. Puhelinsovellus, Claude ja GitHubin verkkosivu muokkaavat kaikki samoja tiedostoja.

## Käyttöönotto

1. Paina GitHubissa **Use this template → Create a new repository**.
2. Valitse näkyvyydeksi **Private**.
3. Avaa sovellus, kirjaudu GitHubiin ja valitse juuri luomasi repo.
4. Poista kokoelmat, joita et tarvitse (kansio `collections/<nimi>/`), ja muokkaa loppuja mieleiseksesi.

Uusi repo on täysin itsenäinen kopio. Pohjaan myöhemmin tehtävät muutokset eivät siirry siihen automaattisesti; tätä varten on `schema_version`, jonka avulla sovellus osaa päivittää vanhemman rakenteen.

## Rakenne

```
config.yml                     repon nimi ja kotinäkymän osiot
collections/
  varasto/
    _collection.yml            kokoelman määrittely: kentät ja näkymä
    esp32-c3-mini.md           yksi tietue = yksi tiedosto
  treenit/
    _collection.yml
    2026-10-24-1800.md
attachments/                   kuvat ja liitteet
schema/                        rakenteen tarkka määrittely (JSON Schema)
.github/                       automaattinen tarkistus
CLAUDE.md                      säännöt Claudelle
```

## Tietue

Jokainen tietue on Markdown-tiedosto. Alussa on rakenteiset kentät `---`-rivien välissä, ja niiden jälkeen vapaata tekstiä:

```markdown
---
nimi: ESP32-C3 Super Mini
kategoria: Mikrokontrollerit
maara: 2
---
Vapaat muistiinpanot, ohjeet tai päiväkirjamerkintä tähän.
```

Tiedoston nimi on tietueen tunniste. Kokoelmassa valitaan, kumpaa muotoa käytetään:
- `id: slug` → `esp32-c3-mini.md` (pienet kirjaimet, numerot, `-`)
- `id: datetime` → `2026-10-24-1830.md` (lokit, päiväkirjat). Loppuun voi lisätä tarkenteen: `2026-10-24-1830-iltalenkki.md`.

## Uuden kokoelman lisääminen

Tee kansio `collections/<nimi>/` ja sinne `_collection.yml`:

```yaml
name: Kirjat
icon: books.vertical        # SF Symbol
color: indigo
group: Elämä                # kotinäkymän osio (config.yml)
view: board                 # list | board | timeline | gallery
id: slug
title: nimi
subtitle: [kirjailija]
group_by: tila              # board: sarakkeet

fields:
  - key: nimi
    type: text
    label: Nimi
    required: true
  - key: kirjailija
    type: text
    label: Kirjailija
  - key: tila
    type: select
    label: Tila
    options: [luettava, luen, luettu]
  - key: arvio
    type: rating
    label: Arvio
```

Sovellus rakentaa näkymän ja lomakkeen tästä automaattisesti.

### Näkymät

| view | Käyttö | Tarvitsee |
|---|---|---|
| `list` | Varasto, kontaktit, laitteet | – |
| `board` | Projektit, luettavat kirjat | `group_by` (select-kenttä) |
| `timeline` | Treenit, ruokapäiväkirja, päiväkirja | `date_field` (date/datetime) |
| `gallery` | Reseptit, kasvit, keräilyesineet | `image_field` (suositus) |

### Kenttätyypit

| type | Esimerkki | Lisäasetukset |
|---|---|---|
| `text` | `nimi: Linssikeitto` | |
| `number` | `kesto: 35` | `unit`, `min`, `max`, `integer`, `stepper` (+/- -napit) |
| `date` | `paivitetty: 2026-10-24` | |
| `datetime` | `aika: 2026-10-24T18:00` | |
| `select` | `tila: työn alla` | `options` (pakollinen), `multiple` |
| `boolean` | `valmis: true` | |
| `rating` | `arvio: 4` | arvo 1–5 |
| `url` | `lahde: https://...` | |
| `ref` | `resepti: linssikeitto` | `to` (kohdekokoelma), `multiple` |
| `image` | `kuva: attachments/keitto.jpg` | |

Kaikille: `label`, `required`, `default`, `help`. Kun `multiple: true`, arvo kirjoitetaan listana: `[ESP32, BLE]`.

Voit lisätä tietueeseen myös kenttiä, joita määrittelyssä ei ole. Ne eivät ole virhe: sovellus näyttää ne kohdassa "Muut tiedot", ja tarkistus antaa vain varoituksen. Kun kenttä vakiintuu, lisää se `_collection.yml`:ään.

## Automaattinen tarkistus

Jokaisen muutoksen jälkeen GitHub Actions ajaa `.github/scripts/validate.py`:n. Se tarkistaa, että määrittelyt ovat kelvollisia, pakolliset kentät löytyvät, arvot ovat oikeaa tyyppiä, valinnat kuuluvat sallittuihin ja viittaukset osuvat olemassa oleviin tietueisiin. Tulos näkyy repon **Actions**-välilehdellä, ja virheet merkitään suoraan kyseiseen tiedostoon.

Paikallisesti:
```bash
pip install pyyaml jsonschema
python .github/scripts/validate.py
```
