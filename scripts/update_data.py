#!/usr/bin/env python3
"""
Actualiza data.json con los resultados del Mundial 2026 desde el MISMO
servidor que usa el dashboard en vivo: el Cloudflare Worker que proxea
balldontlie. NO necesita ninguna API key (el Worker ya la tiene del lado
servidor). Solo toca s/hg/ag de los partidos y el timestamp 'updated';
las fichas editoriales de las selecciones (teams) NO se tocan.
"""
import os, sys, json, datetime, urllib.request

WORKER = "https://mundial-api.lopez-maxi.workers.dev/api"
SEASON = 2026
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data.json")

# Nombres de balldontlie -> codigos internos del dashboard (igual que APINAME)
APINAME = {
    "Mexico": "MEX", "South Africa": "RSA", "South Korea": "KOR", "Korea Republic": "KOR",
    "Republic of Korea": "KOR", "Czech Republic": "CZE", "Czechia": "CZE", "Canada": "CAN",
    "Bosnia and Herzegovina": "BIH", "Qatar": "QAT", "Switzerland": "SUI", "Brazil": "BRA",
    "Morocco": "MAR", "Haiti": "HAI", "Scotland": "SCO", "United States": "USA",
    "United States of America": "USA", "Paraguay": "PAR", "Australia": "AUS", "Turkey": "TUR",
    "T\u00fcrkiye": "TUR", "Germany": "GER", "Cura\u00e7ao": "CUW", "Curacao": "CUW",
    "Ivory Coast": "CIV", "Cote d'Ivoire": "CIV", "C\u00f4te d'Ivoire": "CIV", "Ecuador": "ECU",
    "Netherlands": "NED", "Japan": "JPN", "Sweden": "SWE", "Tunisia": "TUN", "Belgium": "BEL",
    "Egypt": "EGY", "Iran": "IRN", "New Zealand": "NZL", "Spain": "ESP", "Cape Verde": "CPV",
    "Cabo Verde": "CPV", "Saudi Arabia": "KSA", "Uruguay": "URU", "France": "FRA", "Senegal": "SEN",
    "Iraq": "IRQ", "Norway": "NOR", "Argentina": "ARG", "Algeria": "ALG", "Austria": "AUT",
    "Jordan": "JOR", "Portugal": "POR", "Democratic Republic of the Congo": "COD", "DR Congo": "COD",
    "Uzbekistan": "UZB", "Colombia": "COL", "England": "ENG", "Croatia": "CRO", "Ghana": "GHA",
    "Panama": "PAN",
}

def code(team):
    if not team:
        return None
    return APINAME.get((team.get("name") or "").strip()) or (team.get("abbreviation") or "").strip() or None

def grp_letter(g):
    if not g:
        return ""
    name = g.get("name") if isinstance(g, dict) else g
    return str(name or "").replace("Group", "").replace("group", "").replace("GROUP", "").strip()

def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "mundial-updater"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))

def fetch_all_matches():
    out, cursor, guard = [], None, 0
    while guard < 8:
        url = "%s/matches?seasons[]=%d&per_page=100" % (WORKER, SEASON)
        if cursor:
            url += "&cursor=%s" % cursor
        j = get_json(url)
        out += j.get("data", [])
        cursor = (j.get("meta") or {}).get("next_cursor")
        guard += 1
        if not cursor:
            break
    return out

def main():
    with open(DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)

    try:
        api = fetch_all_matches()
    except Exception as e:
        print("ERROR consultando el Worker:", e, file=sys.stderr)
        sys.exit(2)

    if not api:
        print("La API no devolvio partidos; no se toca data.json.", file=sys.stderr)
        sys.exit(0)

    # index de la API por (grupo, equipos ordenados)
    idx = {}
    for x in api:
        hc, ac = code(x.get("home_team")), code(x.get("away_team"))
        if not hc or not ac:
            continue
        idx[grp_letter(x.get("group")) + "|" + "-".join(sorted([hc, ac]))] = (x, hc)

    updated = 0
    for m in data["matches"]:
        rec = idx.get(m["g"] + "|" + "-".join(sorted([m["h"], m["a"]])))
        if not rec:
            continue
        x, hc = rec
        if hc == m["h"]:
            hg, ag = x.get("home_score"), x.get("away_score")
        else:
            hg, ag = x.get("away_score"), x.get("home_score")
        status = x.get("status")
        ns, nhg, nag = m.get("s"), m.get("hg"), m.get("ag")
        if status == "completed" and hg is not None and ag is not None:
            ns, nhg, nag = "FT", hg, ag
        elif status == "in_progress" and hg is not None and ag is not None:
            ns, nhg, nag = "LIVE", hg, ag
        if (ns, nhg, nag) != (m.get("s"), m.get("hg"), m.get("ag")):
            m["s"], m["hg"], m["ag"] = ns, nhg, nag
            if ns == "FT":
                m["tip"] = ""
            updated += 1

    data["updated"] = datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat(timespec="seconds")
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=0)
    print("OK - partidos actualizados: %d  | updated=%s" % (updated, data["updated"]))

if __name__ == "__main__":
    main()
