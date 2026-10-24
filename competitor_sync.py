"""
LibreGol TV — Automated Competitor Mirror Sync Engine
Tracks https://futbollibretvhd.org/ (via direct API https://agenda.futbollibrehd.com.pe/diaries.json)
Automatically mirrors all matches, kickoff times, channels, and pages.
Runs every 30 minutes.
"""

import urllib.request
import json
import os
import re
import datetime
import unicodedata

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AGENDA_URL = "https://agenda.futbollibrehd.com.pe/diaries.json"
OUTPUT_JS = os.path.join(BASE_DIR, "js", "agenda-data.js")
PARTIDOS_DIR = os.path.join(BASE_DIR, "partidos")
SITEMAP_FILE = os.path.join(BASE_DIR, "sitemap.xml")

TEAM_LOGOS = {
    "alaves": "https://a.espncdn.com/i/teamlogos/soccer/500/96.png",
    "deportivo alaves": "https://a.espncdn.com/i/teamlogos/soccer/500/96.png",
    "valencia": "https://a.espncdn.com/i/teamlogos/soccer/500/94.png",
    "genoa": "https://a.espncdn.com/i/teamlogos/soccer/500/3263.png",
    "sudtirol": "https://a.espncdn.com/i/teamlogos/soccer/500/6817.png",
    "abb": "https://a.espncdn.com/i/teamlogos/soccer/500/22026.png",
    "the strongest": "https://a.espncdn.com/i/teamlogos/soccer/500/3289.png",
    "boyaca chico": "https://a.espncdn.com/i/teamlogos/soccer/500/6249.png",
    "alianza": "https://a.espncdn.com/i/teamlogos/soccer/500/12530.png",
    "sao paulo": "https://a.espncdn.com/i/teamlogos/soccer/500/2026.png",
    "boca juniors": "https://a.espncdn.com/i/teamlogos/soccer/500/5.png",
    "peterborough united": "https://a.espncdn.com/i/teamlogos/soccer/500/346.png",
    "barnsley": "https://a.espncdn.com/i/teamlogos/soccer/500/343.png",
    "liverpool": "https://a.espncdn.com/i/teamlogos/soccer/500/364.png",
    "tottenham hotspur": "https://a.espncdn.com/i/teamlogos/soccer/500/367.png",
    "al ain": "https://a.espncdn.com/i/teamlogos/soccer/500/4099.png",
    "al nassr": "https://a.espncdn.com/i/teamlogos/soccer/500/7339.png",
    "ajax": "https://a.espncdn.com/i/teamlogos/soccer/500/139.png",
    "willem ii": "https://a.espncdn.com/i/teamlogos/soccer/500/150.png",
    "nautico": "https://a.espncdn.com/i/teamlogos/soccer/500/3459.png",
    "operario pr": "https://a.espncdn.com/i/teamlogos/soccer/500/19086.png",
    "union espanola": "https://a.espncdn.com/i/teamlogos/soccer/500/3067.png",
    "deportes temuco": "https://a.espncdn.com/i/teamlogos/soccer/500/15729.png",
    "rayo vallecano": "https://a.espncdn.com/i/teamlogos/soccer/500/101.png",
    "espanyol": "https://a.espncdn.com/i/teamlogos/soccer/500/88.png",
    "elche": "https://a.espncdn.com/i/teamlogos/soccer/500/3751.png",
    "real madrid": "https://a.espncdn.com/i/teamlogos/soccer/500/86.png",
    "fiorentina": "https://a.espncdn.com/i/teamlogos/soccer/500/109.png",
    "pisa": "https://a.espncdn.com/i/teamlogos/soccer/500/2765.png",
    "real oruro": "https://a.espncdn.com/i/teamlogos/soccer/500/22027.png",
    "real potosi": "https://a.espncdn.com/i/teamlogos/soccer/500/6090.png",
    "vasco da gama": "https://a.espncdn.com/i/teamlogos/soccer/500/3457.png",
    "santa fe": "https://a.espncdn.com/i/teamlogos/soccer/500/3930.png",
    "platense": "https://a.espncdn.com/i/teamlogos/soccer/500/14.png",
    "fluminense": "https://a.espncdn.com/i/teamlogos/soccer/500/3445.png",
    "west ham united": "https://a.espncdn.com/i/teamlogos/soccer/500/371.png",
    "fulham": "https://a.espncdn.com/i/teamlogos/soccer/500/370.png",
    "reading": "https://a.espncdn.com/i/teamlogos/soccer/500/338.png",
    "brentford": "https://a.espncdn.com/i/teamlogos/soccer/500/337.png",
    "ipswich town": "https://a.espncdn.com/i/teamlogos/soccer/500/373.png",
    "arsenal": "https://a.espncdn.com/i/teamlogos/soccer/500/359.png",
    "beijing guoan": "https://a.espncdn.com/i/teamlogos/soccer/500/236.png",
    "pohang steelers": "https://a.espncdn.com/i/teamlogos/soccer/500/2083.png",
    "al hilal": "https://a.espncdn.com/i/teamlogos/soccer/500/7338.png",
    "al gharafa": "https://a.espncdn.com/i/teamlogos/soccer/500/7342.png",
    "dorados": "https://a.espncdn.com/i/teamlogos/soccer/500/4096.png",
    "cancun": "https://a.espncdn.com/i/teamlogos/soccer/500/20341.png",
    "argentinos juniors": "https://a.espncdn.com/i/teamlogos/soccer/500/10.png",
    "river plate": "https://a.espncdn.com/i/teamlogos/soccer/500/16.png",
    "bahia": "https://a.espncdn.com/i/teamlogos/soccer/500/3454.png",
    "corinthians": "https://a.espncdn.com/i/teamlogos/soccer/500/874.png",
    "san luis": "https://a.espncdn.com/i/teamlogos/soccer/500/7750.png",
    "antofagasta": "https://a.espncdn.com/i/teamlogos/soccer/500/3932.png",
    "puebla": "https://a.espncdn.com/i/teamlogos/soccer/500/232.png",
    "toluca": "https://a.espncdn.com/i/teamlogos/soccer/500/235.png",
    "texas rangers": "https://a.espncdn.com/i/teamlogos/mlb/500/tex.png",
    "boston red sox": "https://a.espncdn.com/i/teamlogos/mlb/500/bos.png"
}

def clean_slugify(text):
    normalized = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    text = normalized.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')

def get_logo_for_team(team_name):
    slug = clean_slugify(team_name).replace("-", " ")
    for k, v in TEAM_LOGOS.items():
        if k in slug or slug in k:
            return v
    return "https://a.espncdn.com/i/teamlogos/soccer/500/default.png"

def parse_competitor_description(desc):
    desc = desc.strip().replace("\n", " ").replace("–", "-").replace("—", "-")
    if ":" in desc:
        tournament_part, teams_part = desc.split(":", 1)
        tournament = tournament_part.strip()
    elif " - " in desc:
        tournament_part, teams_part = desc.split(" - ", 1)
        tournament = tournament_part.strip()
    else:
        tournament = "Fútbol en Vivo"
        teams_part = desc

    if " vs " in teams_part.lower() or " vs. " in teams_part.lower():
        parts = re.split(r'\s+vs\.?\s+', teams_part, flags=re.IGNORECASE)
        home_team = parts[0].strip()
        away_team = parts[1].strip() if len(parts) > 1 else "Rival"
    elif " - " in teams_part:
        parts = teams_part.split(" - ")
        home_team = parts[0].strip()
        away_team = parts[1].strip() if len(parts) > 1 else "Rival"
    else:
        home_team = teams_part.strip()
        away_team = "Rival"

    return tournament, home_team, away_team

def determine_category_and_flag(tournament):
    t = tournament.lower()
    if "argentina" in t or "reserva" in t:
        return "argentina", "🇦🇷"
    elif "laliga" in t or "españa" in t:
        return "espana", "🇪🇸"
    elif "mexico" in t or "liga mx" in t or "expansión" in t:
        return "mexico", "🇲🇽"
    elif "colombia" in t or "primera a" in t or "betplay" in t:
        return "colombia", "🇨🇴"
    elif "brasil" in t or "serie b" in t or "femenino" in t:
        return "brasil", "🇧🇷"
    elif "chile" in t or "primera b" in t:
        return "chile", "🇨🇱"
    elif "bolivia" in t or "primera división" in t:
        return "bolivia", "🇧🇴"
    elif "libertadores" in t:
        return "conmebol", "🏆"
    elif "sudamericana" in t:
        return "conmebol", "🏆"
    elif "eredivisie" in t:
        return "europa", "🇳🇱"
    elif "coppa" in t or "italia" in t or "serie a" in t:
        return "europa", "🇮🇹"
    elif "efl" in t or "carabao" in t or "premier" in t:
        return "europa", "🇬🇧"
    elif "afc" in t:
        return "europa", "🌏"
    elif "mlb" in t or "baseball" in t:
        return "europa", "⚾"
    else:
        return "europa", "⚽"

def convert_competitor_time_to_utc(date_str, hour_str):
    try:
        clean_hour = hour_str[:8]
        lima_dt = datetime.datetime.strptime(f"{date_str} {clean_hour}", "%Y-%m-%d %H:%M:%S")
        utc_dt = lima_dt + datetime.timedelta(hours=5)
        return utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return f"{date_str}T19:00:00Z"

def extract_channels_from_embeds(embeds_data):
    channels = []
    if embeds_data and "data" in embeds_data:
        for emb in embeds_data["data"]:
            name = emb.get("attributes", {}).get("embed_name", "")
            name = name.replace("|", "").strip()
            name = re.sub(r'\s+', ' ', name)
            if name and name not in channels:
                channels.append(name)
    if not channels:
        channels = ["ESPN", "Fox Sports", "DSports"]
    return channels[:4]

def sync_from_competitor():
    now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{now_str}] Syncing with competitor: {AGENDA_URL}...")
    req = urllib.request.Request(AGENDA_URL, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://futbollibretvhd.org/"
    })

    try:
        resp = urllib.request.urlopen(req, timeout=15)
        raw = resp.read().decode("utf-8")
        data = json.loads(raw)
        items = data.get("data", [])
        if not items:
            print("Competitor feed returned 0 matches, skipping sync.")
            return False

        print(f"Competitor feed active: Retrieved {len(items)} matches!")
        mirrored_matches = []
        seen_slugs = set()

        for it in items:
            attr = it.get("attributes", {})
            desc = attr.get("diary_description", "")
            hour = attr.get("diary_hour", "12:00:00")
            date_diary = attr.get("date_diary", datetime.datetime.utcnow().strftime("%Y-%m-%d"))

            tournament, home_team, away_team = parse_competitor_description(desc)
            slug = f"{clean_slugify(home_team)}-vs-{clean_slugify(away_team)}"
            if slug in seen_slugs:
                continue
            seen_slugs.add(slug)

            category, flag = determine_category_and_flag(tournament)
            utc_kickoff = convert_competitor_time_to_utc(date_diary, hour)
            channels = extract_channels_from_embeds(attr.get("embeds"))
            home_logo = get_logo_for_team(home_team)
            away_logo = get_logo_for_team(away_team)

            mirrored_matches.append({
                "id": f"comp-{it.get('id', slug)}",
                "slug": slug,
                "tournament": tournament,
                "flag": flag,
                "homeTeam": home_team,
                "homeLogo": home_logo,
                "awayTeam": away_team,
                "awayLogo": away_logo,
                "utcKickoff": utc_kickoff,
                "status": "UPCOMING",
                "minute": "",
                "homeScore": None,
                "awayScore": None,
                "channels": channels,
                "venue": "Estadio Principal",
                "category": category,
                "votes": {
                    "team1": 1600 + (len(home_team) * 90),
                    "draw": 480 + (len(home_team) * 20),
                    "team2": 1500 + (len(away_team) * 85)
                }
            })

        mirrored_matches.sort(key=lambda m: m["utcKickoff"])

        # 1. Overwrite js/agenda-data.js
        with open(OUTPUT_JS, "r", encoding="utf-8") as f:
            existing_js = f.read()

        existing_channels = ""
        m_chan = re.search(r'(window\.LIBREGOL_CHANNELS\s*=.*)', existing_js, re.DOTALL)
        if m_chan:
            existing_channels = m_chan.group(1)

        new_js = f"""/**
 * LibreGol TV — Live Matches Feed (Auto-Synced from Competitor)
 * Live Tracked from https://futbollibretvhd.org/
 * Last Updated: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%SZ')}
 */

window.LIBREGOL_MATCHES = {json.dumps(mirrored_matches, indent=2, ensure_ascii=False)};
{existing_channels}
"""
        with open(OUTPUT_JS, "w", encoding="utf-8") as f:
            f.write(new_js)
        print(f"Updated {OUTPUT_JS} with {len(mirrored_matches)} competitor matches!")

        # 2. Generate match HTML pages using sync_matches.py
        import sys
        if BASE_DIR not in sys.path:
            sys.path.insert(0, BASE_DIR)
        import sync_matches

        for match in mirrored_matches:
            fpath = os.path.join(PARTIDOS_DIR, f"{match['slug']}.html")
            code = sync_matches.generate_match_html(match)
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(code)

        print(f"Generated {len(mirrored_matches)} match pages in {PARTIDOS_DIR}!")

        # 3. Update Sitemap
        sync_matches.update_sitemap(mirrored_matches)
        print(f"Updated sitemap.xml with {len(mirrored_matches)} matches!")
        return True

    except Exception as e:
        print(f"Error syncing from competitor: {e}")
        return False

if __name__ == "__main__":
    sync_from_competitor()
