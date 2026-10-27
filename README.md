# UniGit – tietopankkipohja

Tämä repo on sinun tietopankkisi: varasto, projektit, treenit, reseptit, päiväkirja tai mitä ikinä haluat seurata. Data on tavallisina tekstitiedostoina sinun omassa GitHub-repossasi. Puhelinsovellus, Claude tai muu tekoäly ja GitHubin verkkosivu muokkaavat kaikki samoja tiedostoja.

## Käyttöönotto

1. Paina GitHubissa **Use this template → Create a new repository**.
2. Valitse näkyvyydeksi **Private**.
3. Avaa sovellus, kirjaudu GitHubiin ja valitse juuri luomasi repo.
4. Muokkaa esimerkkikokoelma `collections/kohteet/` omaan käyttöösi tai kopioi valmis malli `examples/`-kansiosta (ks. alla).

Uusi repo on täysin itsenäinen kopio. Pohjaan myöhemmin tehtävät muutokset eivät siirry siihen automaattisesti; tätä varten on `schema_version`, jonka avulla sovellus osaa päivittää vanhemman rakenteen.

## Rakenne

```
config.yml                     repon nimi ja kotinäkymän osiot
collections/
  kohteet/
    _collection.yml            kokoelman määrittely: kentät ja näkymä
    esimerkki-1.md             yksi tietue = yksi tiedosto
    esimerkki-2.md
examples/                      valmiita kokoelmamalleja kopioitavaksi
attachments/                   kuvat ja liitteet
schema/                        rakenteen tarkka määrittely (JSON Schema)
.github/                       automaattinen tarkistus
AGENTS.md                      säännöt kaikille muokkaajille (tekoälyt, skriptit, ihmiset)
CLAUDE.md                      viittaus AGENTS.md:hen Claude Codelle
```

## Tietue

Jokainen tietue on Markdown-tiedosto. Alussa on rakenteiset kentät `---`-rivien välissä, ja niiden jälkeen vapaata tekstiä:

```markdown
---
nimi: Esimerkki 1
kategoria: Kategoria A
alakategoria: Alakategoria A1
maara: 3
---
Vapaat muistiinpanot, ohjeet tai päiväkirjamerkintä tähän.
```

Tiedoston nimi on tietueen tunniste. Kokoelmassa valitaan, kumpaa muotoa käytetään:
- `id: slug` → `oma-kohde.md` (pienet kirjaimet, numerot, `-`)
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

Kaikille: `label`, `required`, `default`, `help`. Kun `multiple: true`, arvo kirjoitetaan listana: `[tagi 1, tagi 2]`.

### Kategoria ja alakategoria

Select-kentän vaihtoehdot voivat riippua toisesta select-kentästä. Lisää `parent` ja kirjoita `options` ryhmiteltynä ylätason arvon mukaan:

```yaml
  - key: kategoria
    type: select
    options: [Elektroniikka, Työkalut]
  - key: alakategoria
    type: select
    parent: kategoria
    options:
      Elektroniikka: [Mikrokontrollerit, Anturit, Kaapelit]
      Työkalut: [Juottaminen, Mittalaitteet]
```

Sovellus näyttää alakategoriassa vain valitun kategorian vaihtoehdot, ja tarkistus varmistaa, että ne sopivat yhteen. Samalla tavalla voi tehdä kolmannenkin tason (`parent: alakategoria`).

## Valmiit mallit

`examples/`-kansiossa on valmiita kokoelmamäärittelyjä. Ota malli käyttöön kopioimalla sen kansio `collections/`-kansioon:

| Malli | Näkymä | Käyttö |
|---|---|---|
| `varasto` | list | osat ja tarvikkeet saldoineen (viittaa `projektit`-kokoelmaan, kopioi molemmat) |
| `projektit` | board | projektit vaiheittain |
| `treenit` | timeline | treeniloki |
| `ruokapaivakirja` | timeline | syödyt ruuat (viittaa `reseptit`-kokoelmaan) |
| `reseptit` | gallery | reseptit kuvineen |
| `paivakirja` | timeline | päiväkirja |

Mallien `group`-arvot (esim. Elektroniikka) kannattaa lisätä `config.yml`:n `groups`-listaan tai vaihtaa omiin osioihin.

Voit lisätä tietueeseen myös kenttiä, joita määrittelyssä ei ole. Ne eivät ole virhe: sovellus näyttää ne kohdassa "Muut tiedot", ja tarkistus antaa vain varoituksen. Kun kenttä vakiintuu, lisää se `_collection.yml`:ään.

## Automaattinen tarkistus

Jokaisen muutoksen jälkeen GitHub Actions ajaa `.github/scripts/validate.py`:n. Se tarkistaa, että määrittelyt ovat kelvollisia, pakolliset kentät löytyvät, arvot ovat oikeaa tyyppiä, valinnat kuuluvat sallittuihin ja viittaukset osuvat olemassa oleviin tietueisiin. Tulos näkyy repon **Actions**-välilehdellä, ja virheet merkitään suoraan kyseiseen tiedostoon.

Paikallisesti:
```bash
pip install pyyaml jsonschema
python .github/scripts/validate.py
```
