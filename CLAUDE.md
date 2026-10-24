# Säännöt Claudelle

Tämä repo on käyttäjän henkilökohtainen tietopankki. Rakenne on kuvattu README.md:ssä. Sama data näkyy käyttäjän puhelinsovelluksessa, joten rakenteen on pysyttävä kelvollisena.

## Ennen muokkausta
- Lue kokoelman `_collection.yml` ennen kuin luot tai muokkaat sen tietueita. Käytä vain siellä määriteltyjä kenttiä ja sallittuja arvoja.
- Lue tietue juuri ennen muokkausta (`git pull` ensin). Älä kirjoita arvoja muistista: käyttäjä on voinut muuttaa niitä sovelluksessa.

## Muokkaus
- Muuta vain niitä kenttiä, joita tapahtuma koskee. Säilytä muut kentät, kenttien järjestys, tuntemattomat kentät ja vapaa teksti sellaisinaan.
- Uusi tietue: tiedostonimi kokoelman `id`-säännön mukaan (`slug` tai `datetime`, esim. `2026-10-24-1830.md`).
- Jos tarvitset uuden select-vaihtoehdon tai kentän, lisää se `_collection.yml`:ään samassa commitissa ja mainitse siitä käyttäjälle.
- Viittaukset (`ref`) kirjoitetaan kohdetietueen tiedostonimenä ilman `.md`-päätettä.
- Älä poista tietueita tai kokoelmia ilman käyttäjän nimenomaista pyyntöä.

## Varasto (jos repossa on kokoelma, jossa kentät maara/varattu/tulossa)
| Tapahtuma | Muutos |
|---|---|
| Tilaus tehty | tulossa + |
| Paketti saapui | tulossa −, maara + |
| Varattu projektiin | varattu +, lisää projekti `projektit`-listaan |
| Käytetty / juotettu kiinni | maara −, varattu − |
| Projekti peruttu | varattu −, poista projekti listasta |
| Rikki / hävinnyt | maara −, syy commit-viestiin |

Jos arvo menisi negatiiviseksi, varattu ylittäisi määrän tai tieto on ristiriitainen, kysy ennen muokkausta.

## Ennen committia
- Aja `python .github/scripts/validate.py`. Älä committaa, jos tarkistus antaa virheitä.
- Commit-viesti: `Claude: <kokoelma>/<id> <muutos> (<syy>)`, esim.
  `Claude: varasto/esp32-c3-mini maara 2 → 1 (bitchat-node)`.
  Commit-historia toimii muutoslokina, joten kirjaa syy aina.
- Kerro käyttäjälle lopuksi yhdellä rivillä, mitä muutit.
