#!/usr/bin/env python3
"""
Actualiza data.json con los resultados del Mundial 2026 desde football-data.org.
Solo toca marcadores/estado de los partidos (s, hg, ag) y el timestamp 'updated'.
Las fichas editoriales de las selecciones (teams) NO se tocan.

Requiere: variable de entorno FOOTBALL_API_KEY (token gratis de football-data.org)
Uso local:  set FOOTBALL_API_KEY=xxxx  &&  python scripts/update_data.py
"""
import os, sys, json, datetime, urllib.request

API_KEY = os.environ.get("FOOTBALL_API_KEY", "").strip()
COMP = "WC"  # codigo de la Copa del Mundo en football-data.org
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data.json")

# Mapea nombres de la API (ingles) -> codigos internos del dashboard
NAME_MAP = {
    "mexico": "MEX", "south africa": "RSA", "korea republic": "KOR", "south korea": "KOR",
    "czech republic": "CZE", "czechia": "CZE", "canada": "CAN", "switzerland": "SUI",
    "qatar": "QAT", "bosnia and herzegovina": "BIH", "bosnia-herzegovina": "BIH",
    "brazil": "BRA", "morocco": "MAR", "haiti": "HAI", "scotland": "SCO",
    "united states": "USA", "usa": "USA", "paraguay": "PAR", "australia": "AUS",
    "turkey": "TUR", "turkiye": "TUR", "turkiye (turkey)": "TUR", "germany": "GER",
    "ecuador": "ECU", "ivory coast": "CIV", "cote d'ivoire": "CIV", "curacao": "CUW",
    "netherlands": "NED", "japan": "JPN", "sweden": "SWE", "tunisia": "TUN",
    "belgium": "BEL", "egypt": "EGY", "iran": "IRN", "ir iran": "IRN", "new zealand": "NZL",
    "spain": "ESP", "cape verde": "CPV", "cabo verde": "CPV", "saudi arabia": "KSA",
    "uruguay": "URU", "france": "FRA", "senegal": "SEN", "iraq": "IRQ", "norway": "NOR",
    "argentina": "ARG", "algeria": "ALG", "austria": "AUT", "jordan": "JOR",
    "portugal": "POR", "dr congo": "COD", "congo dr": "COD", "uzbekistan": "UZB",
    "colombia": "COL", "england": "ENG", "croatia": "CRO", "ghana": "GHA", "panama": "PAN",
}

def norm(s):
    return (s or "").strip().lower()

def to_code(name):
    return NAME_MAP.get(norm(name))

def main():
    if not API_KEY:
        print("ERROR: falta FOOTBALL_API_KEY", file=sys.stderr); sys.exit(1)
    with open(DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)

    url = "https://api.football-data.org/v4/competitions/%s/matches" % COMP
    req = urllib.request.Request(url, headers={"X-Auth-Token": API_KEY})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            api = json.loads(r.read().decode("utf-8"))
    except Exception as e:
        print("ERROR consultando la API:", e, file=sys.stderr); sys.exit(2)

    # Indexa partidos de la API por (codigo_local, codigo_visitante)
    api_index = {}
    for mt in api.get("matches", []):
        h = to_code(mt.get("homeTeam", {}).get("name"))
        a = to_code(mt.get("awayTeam", {}).get("name"))
        if h and a:
            api_index[(h, a)] = mt

    updated = 0
    for m in data["matches"]:
        mt = api_index.get((m["h"], m["a"]))
        if not mt:
            continue
        status = mt.get("status")          # SCHEDULED, IN_PLAY, PAUSED, FINISHED
        ft = mt.get("score", {}).get("fullTime", {})
        hg, ag = ft.get("home"), ft.get("away")
        if status == "FINISHED" and hg is not None and ag is not None:
            if m["s"] != "FT" or m["hg"] != hg or m["ag"] != ag:
                m["s"], m["hg"], m["ag"], m["tip"] = "FT", hg, ag, ""
                updated += 1
        elif status in ("IN_PLAY", "PAUSED") and hg is not None and ag is not None:
            if m["hg"] != hg or m["ag"] != ag:
                m["hg"], m["ag"] = hg, ag
                updated += 1

    data["updated"] = datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat(timespec="seconds")
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("OK - partidos actualizados: %d" % updated)

if __name__ == "__main__":
    main()
