#!/usr/bin/env python3
"""Tarkistaa tietopankkirepon rakenteen.

Ajetaan GitHub Actionsissa jokaisesta pushista, mutta toimii myös paikallisesti:
    pip install pyyaml jsonschema
    python .github/scripts/validate.py [repon-polku]

Virheet (error) kaatavat tarkistuksen, varoitukset (warning) eivät.
GitHubissa viestit näkyvät suoraan kyseisen tiedoston kohdalla.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
IN_ACTIONS = os.environ.get("GITHUB_ACTIONS") == "true"

ID_PATTERNS = {
    "slug": re.compile(r"^[a-z0-9][a-z0-9-]*$"),
    "datetime": re.compile(r"^\d{4}-\d{2}-\d{2}-\d{4}(-[a-z0-9-]+)?$"),
}
URL_RE = re.compile(r"^https?://\S+$")

errors = 0
warnings = 0


def rel(p: Path) -> str:
    return p.relative_to(ROOT).as_posix()


def report(level: str, path: Path, msg: str) -> None:
    global errors, warnings
    if level == "error":
        errors += 1
    else:
        warnings += 1
    if IN_ACTIONS:
        print(f"::{level} file={rel(path)}::{msg}")
    else:
        mark = "VIRHE" if level == "error" else "varoitus"
        print(f"[{mark}] {rel(path)}: {msg}")


def load_yaml(path: Path):
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        report("error", path, f"YAML ei ole kelvollista: {e}")
        return None


def schema_validator(name: str) -> Draft202012Validator:
    schema = json.loads((ROOT / "schema" / name).read_text(encoding="utf-8"))
    return Draft202012Validator(schema)


def check_schema(validator: Draft202012Validator, data, path: Path) -> bool:
    ok = True
    for err in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
        where = "/".join(str(p) for p in err.path) or "(juuri)"
        report("error", path, f"{where}: {err.message}")
        ok = False
    return ok


def split_frontmatter(path: Path):
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        report("error", path, "Tiedoston pitää alkaa '---'-rivillä (YAML-otsake)")
        return None
    parts = text.split("\n---", 1)
    if len(parts) < 2:
        report("error", path, "YAML-otsakkeen loppurivi '---' puuttuu")
        return None
    try:
        data = yaml.safe_load(parts[0][3:]) or {}
    except yaml.YAMLError as e:
        report("error", path, f"YAML-otsake ei ole kelvollista: {e}")
        return None
    if not isinstance(data, dict):
        report("error", path, "YAML-otsakkeen pitää olla avain: arvo -pareja")
        return None
    return data


def is_date(v) -> bool:
    if isinstance(v, dt.date) and not isinstance(v, dt.datetime):
        return True
    if isinstance(v, str):
        try:
            dt.date.fromisoformat(v)
            return True
        except ValueError:
            return False
    return False


def is_datetime(v) -> bool:
    if isinstance(v, (dt.datetime, dt.date)):
        return True
    if isinstance(v, str):
        try:
            dt.datetime.fromisoformat(v)
            return True
        except ValueError:
            return False
    return False


def is_number(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


# ---------------------------------------------------------------------------
# 1. config.yml
# ---------------------------------------------------------------------------
config_path = ROOT / "config.yml"
groups: list[str] = []
if not config_path.exists():
    report("error", ROOT, "config.yml puuttuu repon juuresta")
else:
    config = load_yaml(config_path)
    if config is not None and check_schema(schema_validator("config.schema.json"), config, config_path):
        groups = config.get("groups", [])

# ---------------------------------------------------------------------------
# 2. Kokoelmamäärittelyt
# ---------------------------------------------------------------------------
col_validator = schema_validator("collection.schema.json")
collections: dict[str, dict] = {}
col_dir = ROOT / "collections"
if not col_dir.is_dir():
    report("error", ROOT, "collections/-kansio puuttuu")
    col_dirs = []
else:
    col_dirs = sorted(p for p in col_dir.iterdir() if p.is_dir())

for d in col_dirs:
    defn_path = d / "_collection.yml"
    if not ID_PATTERNS["slug"].match(d.name):
        report("error", d, "Kansion nimessä saa olla vain pieniä kirjaimia a–z, numeroita ja '-'")
        continue
    if not defn_path.exists():
        report("error", d, "_collection.yml puuttuu, joten kansio ei ole kokoelma")
        continue
    defn = load_yaml(defn_path)
    if defn is None or not check_schema(col_validator, defn, defn_path):
        continue

    fields = {f["key"]: f for f in defn["fields"]}
    if len(fields) != len(defn["fields"]):
        report("error", defn_path, "Sama kentän key on määritelty useammin kuin kerran")

    def need(key_name: str, allowed: tuple[str, ...]) -> None:
        k = defn.get(key_name)
        if k is None:
            return
        name = k.lstrip("-") if key_name == "sort" else k
        if name not in fields:
            report("error", defn_path, f"{key_name}: kenttää '{name}' ei ole fields-listassa")
        elif allowed and fields[name]["type"] not in allowed:
            report("error", defn_path, f"{key_name}: kentän '{name}' tyypin pitää olla {' tai '.join(allowed)}")

    need("title", ())
    need("sort", ())
    need("group_by", ("select",))
    need("date_field", ("date", "datetime"))
    need("image_field", ("image",))
    for s in defn.get("subtitle", []):
        if s not in fields:
            report("error", defn_path, f"subtitle: kenttää '{s}' ei ole fields-listassa")

    view = defn["view"]
    if view == "board" and "group_by" not in defn:
        report("error", defn_path, "board-näkymä tarvitsee group_by-kentän (select)")
    if view == "timeline" and "date_field" not in defn:
        report("error", defn_path, "timeline-näkymä tarvitsee date_field-kentän")
    if view == "gallery" and "image_field" not in defn:
        report("warning", defn_path, "gallery-näkymä ilman image_field-kenttää näyttää kortit ilman kuvia")
    if "group" in defn and groups and defn["group"] not in groups:
        report("warning", defn_path, f"Osiota '{defn['group']}' ei ole config.yml:n groups-listassa; näytetään osiossa Muut")

    for f in defn["fields"]:
        t = f["type"]
        if t == "select" and "options" not in f:
            report("error", defn_path, f"Kenttä '{f['key']}': select tarvitsee options-listan")
        if "parent" in f:
            parent = fields.get(f["parent"])
            if t != "select":
                report("error", defn_path, f"Kenttä '{f['key']}': parent toimii vain select-kentässä")
            elif parent is None or parent["type"] != "select":
                report("error", defn_path, f"Kenttä '{f['key']}': parent '{f['parent']}' ei ole saman kokoelman select-kenttä")
            elif parent.get("multiple"):
                report("error", defn_path, f"Kenttä '{f['key']}': parent-kenttä '{f['parent']}' ei voi olla multiple")
            elif not isinstance(f.get("options"), dict):
                report("error", defn_path, f"Kenttä '{f['key']}': kun parent on asetettu, options kirjoitetaan muodossa "
                                           f"{{Ylätason arvo: [vaihtoehto, ...]}}")
            elif isinstance(parent.get("options"), list):
                for k in f["options"]:
                    if k not in parent["options"]:
                        report("error", defn_path, f"Kenttä '{f['key']}': '{k}' ei ole kentän '{f['parent']}' vaihtoehto")
        elif isinstance(f.get("options"), dict):
            report("error", defn_path, f"Kenttä '{f['key']}': options-ryhmittely vaatii parent-kentän")
        if t == "ref" and "to" not in f:
            report("error", defn_path, f"Kenttä '{f['key']}': ref tarvitsee to-kohdekokoelman")

    collections[d.name] = {"dir": d, "path": defn_path, "defn": defn, "fields": fields, "ids": set()}

# examples/-mallit: vain rakenteen tarkistus (niissä ei ole tietueita)
ex_dir = ROOT / "examples"
if ex_dir.is_dir():
    for p in sorted(ex_dir.glob("*/_collection.yml")):
        defn = load_yaml(p)
        if defn is not None:
            check_schema(col_validator, defn, p)

# ref-kohteiden olemassaolo
for name, c in collections.items():
    for f in c["defn"]["fields"]:
        if f["type"] == "ref" and f.get("to") and f["to"] not in collections:
            report("error", c["path"], f"Kenttä '{f['key']}': kokoelmaa '{f['to']}' ei ole")

# ---------------------------------------------------------------------------
# 3. Tietueet
# ---------------------------------------------------------------------------
records: list[tuple[str, Path, dict]] = []
for name, c in collections.items():
    id_rule = c["defn"].get("id", "slug")
    for p in sorted(c["dir"].iterdir()):
        if p.name == "_collection.yml":
            continue
        if p.is_dir() or p.suffix != ".md":
            report("warning", p, "Kokoelmakansiossa kuuluu olla vain .md-tietueita; sovellus ohittaa tämän")
            continue
        rid = p.stem
        if not ID_PATTERNS[id_rule].match(rid):
            example = "oma-kohde.md" if id_rule == "slug" else "2026-10-24-1830.md"
            report("error", p, f"Tiedostonimi ei vastaa muotoa '{id_rule}' (esim. {example})")
        c["ids"].add(rid)
        data = split_frontmatter(p)
        if data is not None:
            records.append((name, p, data))


def allowed_options(f: dict, data: dict) -> list:
    opts = f.get("options", [])
    if isinstance(opts, dict):
        return opts.get(data.get(f.get("parent")), [])
    return opts


def check_value(f: dict, v, path: Path, data: dict) -> None:
    key, t = f["key"], f["type"]
    pre = f"Kenttä '{key}'"
    if f.get("multiple"):
        if not isinstance(v, list):
            report("error", path, f"{pre}: odotettiin listaa, esim. [a, b]")
            return
        values = v
    else:
        if isinstance(v, list):
            report("error", path, f"{pre}: odotettiin yhtä arvoa, ei listaa")
            return
        values = [v]

    for x in values:
        if t == "text":
            if not isinstance(x, (str, int, float)) or isinstance(x, bool):
                report("error", path, f"{pre}: odotettiin tekstiä")
        elif t == "number":
            if not is_number(x):
                report("error", path, f"{pre}: odotettiin numeroa, saatiin {x!r}")
                continue
            if f.get("integer") and not float(x).is_integer():
                report("error", path, f"{pre}: odotettiin kokonaislukua")
            if "min" in f and x < f["min"]:
                report("error", path, f"{pre}: {x} on pienempi kuin minimi {f['min']}")
            if "max" in f and x > f["max"]:
                report("error", path, f"{pre}: {x} on suurempi kuin maksimi {f['max']}")
        elif t == "date":
            if not is_date(x):
                report("error", path, f"{pre}: odotettiin päivämäärää muodossa 2026-10-24")
        elif t == "datetime":
            if not is_datetime(x):
                report("error", path, f"{pre}: odotettiin aikaa muodossa 2026-10-24T18:30")
        elif t == "select":
            opts = allowed_options(f, data)
            if "parent" in f and not data.get(f["parent"]):
                report("error", path, f"{pre}: valitse ensin '{f['parent']}'")
            elif x not in opts:
                ctx = f" kun {f['parent']} = {data.get(f['parent'])}" if "parent" in f else ""
                report("error", path, f"{pre}: '{x}' ei ole sallittu{ctx}. Sallitut: {', '.join(opts) or '(ei vaihtoehtoja)'}. "
                                      f"Lisää uusi vaihtoehto kokoelman _collection.yml-tiedostoon.")
        elif t == "boolean":
            if not isinstance(x, bool):
                report("error", path, f"{pre}: odotettiin true tai false")
        elif t == "rating":
            if not (isinstance(x, int) and not isinstance(x, bool) and 1 <= x <= 5):
                report("error", path, f"{pre}: odotettiin kokonaislukua 1–5")
        elif t == "url":
            if not (isinstance(x, str) and URL_RE.match(x)):
                report("error", path, f"{pre}: odotettiin osoitetta, joka alkaa http:// tai https://")
        elif t == "ref":
            target = collections.get(f.get("to", ""))
            if target is not None and str(x) not in target["ids"]:
                report("error", path, f"{pre}: tietuetta '{x}' ei löydy kokoelmasta '{f['to']}'")
        elif t == "image":
            if not isinstance(x, str) or not (ROOT / x).is_file():
                report("error", path, f"{pre}: kuvatiedostoa '{x}' ei löydy (polku repon juuresta, esim. attachments/kuva.jpg)")


for name, p, data in records:
    fields = collections[name]["fields"]
    for key, f in fields.items():
        v = data.get(key)
        if v is None or v == "" or v == []:
            if f.get("required"):
                report("error", p, f"Pakollinen kenttä '{key}' puuttuu")
            continue
        check_value(f, v, p, data)
    for key in data:
        if key not in fields:
            report("warning", p, f"Kenttä '{key}' ei ole kokoelman määrittelyssä; sovellus näyttää sen kohdassa 'Muut tiedot'")

    # Varastokohtainen järkevyystarkistus: varattu ei voi ylittää määrää
    if "maara" in fields and "varattu" in fields:
        m, r = data.get("maara"), data.get("varattu")
        if is_number(m) and is_number(r) and r > m:
            report("error", p, f"varattu ({r}) on suurempi kuin maara ({m})")

# ---------------------------------------------------------------------------
# Yhteenveto
# ---------------------------------------------------------------------------
summary = ["| Kokoelma | Näkymä | Tietueita |", "|---|---|---|"]
for name, c in collections.items():
    summary.append(f"| {c['defn']['name']} (`{name}`) | {c['defn']['view']} | {len(c['ids'])} |")
summary.append("")
summary.append(f"**Virheitä:** {errors} · **Varoituksia:** {warnings}")
text = "\n".join(summary)

if IN_ACTIONS and os.environ.get("GITHUB_STEP_SUMMARY"):
    with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as fh:
        fh.write("## Tietopankin tarkistus\n\n" + text + "\n")
print()
print(text)
sys.exit(1 if errors else 0)
