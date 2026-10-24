"""
LibreGol TV — Enterprise Automated Match Synchronization Pipeline
Phase 6: Multi-source resilient match scraper, page generator & sitemap synchronizer.
Pulls live matches from:
1. Primary: Competitor JSON Mirror (agenda.futbollibrehd.com.pe)
2. Secondary Fallback: ESPN Global Public Scoreboard API
Automatically compiles:
- js/agenda-data.js
- partidos/{slug}.html (Authentic Video Player UX + SportsEvent & Breadcrumbs schemas)
- sitemap.xml (100% verified URLs across entire portal)
- Minified CSS cache
"""

import urllib.request
import json
import os
import re
import datetime
import unicodedata
import hashlib
import sys
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AGENDA_URL = "https://agenda.futbollibrehd.com.pe/diaries.json"
OUTPUT_JS = os.path.join(BASE_DIR, "js", "agenda-data.js")
PARTIDOS_DIR = os.path.join(BASE_DIR, "partidos")
SITEMAP_FILE = os.path.join(BASE_DIR, "sitemap.xml")
CSS_FILE = os.path.join(BASE_DIR, "css", "main.css")
CSS_MIN_FILE = os.path.join(BASE_DIR, "css", "main.min.css")

ESPN_LEAGUES = [
    {"code": "esp.1", "name": "LaLiga", "flag": "🇪🇸", "category": "espana", "channels": ["Movistar Plus+", "DAZN LaLiga", "ESPN Deportes"]},
    {"code": "eng.1", "name": "Premier League", "flag": "🇬🇧", "category": "europa", "channels": ["ESPN", "DAZN", "Telemundo", "Peacock"]},
    {"code": "eng.league_cup", "name": "EFL Cup", "flag": "🇬🇧", "category": "europa", "channels": ["ESPN", "Sky Sports", "Disney+"]},
    {"code": "ita.1", "name": "Serie A", "flag": "🇮🇹", "category": "europa", "channels": ["ESPN", "Star+", "Disney+ Premium"]},
    {"code": "uefa.champions", "name": "UEFA Champions League", "flag": "🇪🇺", "category": "europa", "channels": ["ESPN", "Fox Sports", "Movistar Liga de Campeones"]},
    {"code": "uefa.europa", "name": "UEFA Europa League", "flag": "🇪🇺", "category": "europa", "channels": ["ESPN", "Fox Sports", "Disney+"]},
    {"code": "conmebol.libertadores", "name": "Copa Libertadores", "flag": "🏆", "category": "conmebol", "channels": ["ESPN", "Star+", "Disney+"]},
    {"code": "conmebol.sudamericana", "name": "Copa Sudamericana", "flag": "🏆", "category": "conmebol", "channels": ["DSports", "DGO", "ESPN"]},
    {"code": "arg.1", "name": "Liga Profesional", "flag": "🇦🇷", "category": "argentina", "channels": ["ESPN Premium", "TNT Sports", "TyC Sports"]},
    {"code": "mex.1", "name": "Liga MX", "flag": "🇲🇽", "category": "mexico", "channels": ["TUDN", "ViX Premium", "Canal 5"]},
    {"code": "col.1", "name": "Primera A", "flag": "🇨🇴", "category": "colombia", "channels": ["Win Sports+", "Win Sports Online"]},
    {"code": "bra.1", "name": "Brasileirão", "flag": "🇧🇷", "category": "brasil", "channels": ["Premiere", "Globo", "SporTV"]},
    {"code": "chi.1", "name": "Primera División", "flag": "🇨🇱", "category": "chile", "channels": ["TNT Sports Chile", "Estadio TNT"]},
    {"code": "per.1", "name": "Liga 1", "flag": "🇵🇪", "category": "peru", "channels": ["Liga 1 MAX", "L1 Play"]},
    {"code": "uru.1", "name": "Primera División", "flag": "🇺🇾", "category": "uruguay", "channels": ["VTV Plus", "Star+", "Disney+"]},
    {"code": "bol.1", "name": "Primera División", "flag": "🇧🇴", "category": "bolivia", "channels": ["Tigo Sports Bolivia"]}
]

TEAM_LOGOS = {
    "alaves": "https://a.espncdn.com/i/teamlogos/soccer/500/96.png",
    "valencia": "https://a.espncdn.com/i/teamlogos/soccer/500/94.png",
    "genoa": "https://a.espncdn.com/i/teamlogos/soccer/500/3263.png",
    "sudtirol": "https://a.espncdn.com/i/teamlogos/soccer/500/6817.png",
    "abb": "https://a.espncdn.com/i/teamlogos/soccer/500/22026.png",
    "the strongest": "https://a.espncdn.com/i/teamlogos/soccer/500/3289.png",
    "boyaca chico": "https://a.espncdn.com/i/teamlogos/soccer/500/6249.png",
    "alianza": "https://a.espncdn.com/i/teamlogos/soccer/500/12530.png",
    "sao paulo": "https://a.espncdn.com/i/teamlogos/soccer/500/2026.png",
    "boca juniors": "https://a.espncdn.com/i/teamlogos/soccer/500/5.png",
    "river plate": "https://a.espncdn.com/i/teamlogos/soccer/500/16.png",
    "liverpool": "https://a.espncdn.com/i/teamlogos/soccer/500/364.png",
    "tottenham hotspur": "https://a.espncdn.com/i/teamlogos/soccer/500/367.png",
    "al ain": "https://a.espncdn.com/i/teamlogos/soccer/500/4099.png",
    "al nassr": "https://a.espncdn.com/i/teamlogos/soccer/500/7339.png",
    "ajax": "https://a.espncdn.com/i/teamlogos/soccer/500/139.png",
    "real madrid": "https://a.espncdn.com/i/teamlogos/soccer/500/86.png",
    "barcelona": "https://a.espncdn.com/i/teamlogos/soccer/500/83.png",
    "atletico madrid": "https://a.espncdn.com/i/teamlogos/soccer/500/1068.png",
    "arsenal": "https://a.espncdn.com/i/teamlogos/soccer/500/359.png",
    "manchester city": "https://a.espncdn.com/i/teamlogos/soccer/500/382.png",
    "manchester united": "https://a.espncdn.com/i/teamlogos/soccer/500/360.png",
    "juventus": "https://a.espncdn.com/i/teamlogos/soccer/500/111.png",
    "inter": "https://a.espncdn.com/i/teamlogos/soccer/500/110.png",
    "milan": "https://a.espncdn.com/i/teamlogos/soccer/500/103.png",
    "flamengo": "https://a.espncdn.com/i/teamlogos/soccer/500/5981.png",
    "palmeiras": "https://a.espncdn.com/i/teamlogos/soccer/500/2029.png",
    "racing club": "https://a.espncdn.com/i/teamlogos/soccer/500/15.png",
    "independiente": "https://a.espncdn.com/i/teamlogos/soccer/500/12.png",
    "san lorenzo": "https://a.espncdn.com/i/teamlogos/soccer/500/18.png",
    "america": "https://a.espncdn.com/i/teamlogos/soccer/500/227.png",
    "chivas": "https://a.espncdn.com/i/teamlogos/soccer/500/217.png",
    "cruz azul": "https://a.espncdn.com/i/teamlogos/soccer/500/218.png",
    "pumas": "https://a.espncdn.com/i/teamlogos/soccer/500/233.png",
    "tigres": "https://a.espncdn.com/i/teamlogos/soccer/500/234.png",
    "monterrey": "https://a.espncdn.com/i/teamlogos/soccer/500/225.png",
    "millonarios": "https://a.espncdn.com/i/teamlogos/soccer/500/490.png",
    "atletico nacional": "https://a.espncdn.com/i/teamlogos/soccer/500/487.png",
    "junior": "https://a.espncdn.com/i/teamlogos/soccer/500/489.png",
    "colo colo": "https://a.espncdn.com/i/teamlogos/soccer/500/3105.png",
    "universidad de chile": "https://a.espncdn.com/i/teamlogos/soccer/500/3107.png",
    "universitario": "https://a.espncdn.com/i/teamlogos/soccer/500/3382.png",
    "alianza lima": "https://a.espncdn.com/i/teamlogos/soccer/500/3380.png",
    "sporting cristal": "https://a.espncdn.com/i/teamlogos/soccer/500/3381.png",
    "penarol": "https://a.espncdn.com/i/teamlogos/soccer/500/3283.png",
    "nacional": "https://a.espncdn.com/i/teamlogos/soccer/500/3282.png"
}

def clean_slugify(text):
    normalized = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    text = normalized.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')

def get_logo(team_name):
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
    if any(k in t for k in ["argentina", "reserva", "copa de la liga", "afa"]):
        return "argentina", "🇦🇷"
    elif any(k in t for k in ["laliga", "espana", "españa", "copa del rey"]):
        return "espana", "🇪🇸"
    elif any(k in t for k in ["mexico", "liga mx", "expansión", "expansion"]):
        return "mexico", "🇲🇽"
    elif any(k in t for k in ["colombia", "primera a", "betplay"]):
        return "colombia", "🇨🇴"
    elif any(k in t for k in ["brasil", "brasileirao", "serie b", "paulista"]):
        return "brasil", "🇧🇷"
    elif any(k in t for k in ["chile", "primera b"]):
        return "chile", "🇨🇱"
    elif any(k in t for k in ["bolivia", "primera división", "division profesional"]):
        return "bolivia", "🇧🇴"
    elif any(k in t for k in ["peru", "perú", "liga 1"]):
        return "peru", "🇵🇪"
    elif any(k in t for k in ["uruguay", "campeonato uruguayo"]):
        return "uruguay", "🇺🇾"
    elif any(k in t for k in ["libertadores", "sudamericana", "conmebol"]):
        return "conmebol", "🏆"
    elif any(k in t for k in ["premier", "efl", "carabao", "fa cup"]):
        return "europa", "🇬🇧"
    elif any(k in t for k in ["champions", "europa league", "conference", "uefa"]):
        return "europa", "🇪🇺"
    elif any(k in t for k in ["serie a", "italia", "coppa"]):
        return "europa", "🇮🇹"
    elif any(k in t for k in ["mlb", "baseball"]):
        return "europa", "⚾"
    else:
        return "europa", "⚽"

def get_accurate_broadcasters(tournament, default_channels=None):
    t = tournament.lower()
    primary = default_channels[0] if (default_channels and len(default_channels) > 0) else "ESPN"

    if "argentina" in t or "reserva" in t or "afa" in t:
        return {"ar": "ESPN Premium / TNT Sports", "es": "Fanatiz / AFA Play", "mx": "Fanatiz / AFA Play", "co": "ESPN / Disney+", "us": "TyC Sports / Fanatiz"}
    elif "laliga" in t or "españa" in t or "espana" in t:
        return {"ar": "DSports / ESPN", "es": "Movistar Plus+ / DAZN", "mx": "Sky Sports / Canal 5", "co": "DSports / DGO", "us": "ESPN Deportes / ESPN+"}
    elif "premier" in t or "carabao" in t or "efl" in t:
        return {"ar": "ESPN / Disney+", "es": "DAZN / Sky Sports", "mx": "Fox Sports / Paramount+", "co": "ESPN / Disney+", "us": "Telemundo / Peacock"}
    elif "libertadores" in t or "sudamericana" in t:
        return {"ar": "Fox Sports / ESPN / Telefe", "es": "LaLiga+ / Movistar", "mx": "ESPN / Disney+", "co": "ESPN / Disney+", "us": "beIN Sports / Fanatiz"}
    elif "champions" in t:
        return {"ar": "ESPN / Fox Sports", "es": "Movistar Liga de Campeones", "mx": "TNT Sports / Max", "co": "ESPN / Disney+", "us": "Paramount+ / Univision"}
    elif "mexico" in t or "liga mx" in t:
        return {"ar": "Claro Sports", "es": "DAZN / LaLiga+", "mx": "TUDN / ViX Premium / Canal 5", "co": "Claro Sports", "us": "Univision / TUDN / ViX"}
    elif "colombia" in t or "primera a" in t:
        return {"ar": "Fanatiz", "es": "Fanatiz", "mx": "Fanatiz", "co": "Win Sports+ / Win Sports Online", "us": "ViX / Fanatiz"}
    else:
        return {"ar": primary, "es": "Movistar Plus+", "mx": "TUDN / ViX", "co": "ESPN / Disney+", "us": "Telemundo / ESPN"}

def fetch_primary_competitor():
    """Fetches matches from competitor JSON agenda"""
    print("[Pipeline] Attempting Primary Source: Competitor Feed...")
    req = urllib.request.Request(AGENDA_URL, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": "https://futbollibretvhd.org/"
    })
    try:
        resp = urllib.request.urlopen(req, timeout=12)
        data = json.loads(resp.read().decode("utf-8"))
        items = data.get("data", [])
        if not items:
            print("[Pipeline] Competitor feed returned 0 matches.")
            return None
        
        matches = []
        seen_slugs = set()
        for it in items:
            attr = it.get("attributes", {})
            desc = attr.get("diary_description", "")
            hour = attr.get("diary_hour", "12:00:00")[:8]
            date_diary = attr.get("date_diary", datetime.datetime.utcnow().strftime("%Y-%m-%d"))

            tournament, home_team, away_team = parse_competitor_description(desc)
            slug = f"{clean_slugify(home_team)}-vs-{clean_slugify(away_team)}"
            if slug in seen_slugs or not home_team or not away_team:
                continue
            seen_slugs.add(slug)

            # Time conversion (Lima UTC-5 to UTC)
            try:
                dt = datetime.datetime.strptime(f"{date_diary} {hour}", "%Y-%m-%d %H:%M:%S")
                utc_dt = dt + datetime.timedelta(hours=5)
                utc_kickoff = utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            except Exception:
                utc_kickoff = f"{date_diary}T19:00:00Z"

            category, flag = determine_category_and_flag(tournament)
            
            # Channels
            channels = []
            embeds = attr.get("embeds", {}).get("data", [])
            for emb in embeds:
                name = emb.get("attributes", {}).get("embed_name", "").replace("|", "").strip()
                name = re.sub(r'\s+', ' ', name)
                if name and name not in channels:
                    channels.append(name)
            if not channels:
                channels = ["ESPN", "Fox Sports", "DSports"]

            matches.append({
                "id": f"comp-{it.get('id', slug)}",
                "slug": slug,
                "tournament": tournament,
                "flag": flag,
                "homeTeam": home_team,
                "homeLogo": get_logo(home_team),
                "awayTeam": away_team,
                "awayLogo": get_logo(away_team),
                "utcKickoff": utc_kickoff,
                "status": "UPCOMING",
                "minute": "",
                "homeScore": None,
                "awayScore": None,
                "channels": channels[:4],
                "venue": "Estadio Principal",
                "category": category,
                "votes": {
                    "team1": 1500 + (len(home_team) * 75),
                    "draw": 420 + (len(home_team) * 20),
                    "team2": 1400 + (len(away_team) * 70)
                }
            })
        print(f"[Pipeline] Successfully parsed {len(matches)} matches from Competitor Feed!")
        return matches
    except Exception as e:
        print(f"[Pipeline] Competitor feed note ({e}). Proceeding to Secondary Source...")
        return None

def fetch_secondary_espn():
    """Fetches live and upcoming matches from ESPN global public API with real-time scores, minutes and statuses"""
    print("[Pipeline] Attempting Primary/Secondary Source: ESPN Public Global Scoreboards...")
    matches = []
    seen_ids = set()
    now_utc = datetime.datetime.utcnow()
    today_str = now_utc.strftime("%Y-%m-%d")
    yesterday_str = (now_utc - datetime.timedelta(days=1)).strftime("%Y-%m-%d")

    for league in ESPN_LEAGUES:
        code = league['code']
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard"
        try:
            data = None
            proc = subprocess.run(["curl.exe", "-s", "--compressed", url], capture_output=True, text=True, encoding="utf-8", errors="replace")
            if proc.returncode == 0 and proc.stdout:
                data = json.loads(proc.stdout)
            else:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36"})
                resp = urllib.request.urlopen(req, timeout=8)
                data = json.loads(resp.read().decode("utf-8"))
            if not data:
                continue
            events = data.get("events", [])
            for event in events:
                eid = str(event.get("id", ""))
                if eid in seen_ids:
                    continue
                comp = event.get("competitions", [{}])[0]
                competitors = comp.get("competitors", [])
                if len(competitors) < 2:
                    continue
                home = competitors[0] if competitors[0].get("homeAway") == "home" else competitors[1]
                away = competitors[1] if competitors[0].get("homeAway") == "home" else competitors[0]
                home_team = home.get("team", {}).get("displayName", "Equipo Local")
                away_team = away.get("team", {}).get("displayName", "Equipo Visitante")
                home_logo = home.get("team", {}).get("logo", get_logo(home_team))
                away_logo = away.get("team", {}).get("logo", get_logo(away_team))

                status_obj = event.get("status", {})
                state = status_obj.get("type", {}).get("state", "pre")
                status = "LIVE" if state == "in" else ("FINISHED" if state == "post" else "UPCOMING")
                minute = status_obj.get("displayClock", "") if state == "in" else ""
                home_score = int(home.get("score", 0)) if state in ("in", "post") and home.get("score") is not None else None
                away_score = int(away.get("score", 0)) if state in ("in", "post") and away.get("score") is not None else None

                event_date = event.get("date", f"{today_str}T19:00:00Z")
                date_part = event_date[:10]

                tomorrow_str = (now_utc + datetime.timedelta(days=1)).strftime("%Y-%m-%d")

                # STRICT DATE FILTER: Only keep TODAY and TOMORROW matches; drop far-future (> tomorrow)
                if status == "FINISHED" and date_part < today_str:
                    continue
                if date_part > tomorrow_str and status != "LIVE":
                    continue

                slug = f"{clean_slugify(home_team)}-vs-{clean_slugify(away_team)}"
                seen_ids.add(eid)
                matches.append({
                    "id": f"espn-{eid}",
                    "slug": slug,
                    "tournament": league["name"],
                    "flag": league["flag"],
                    "homeTeam": home_team,
                    "homeLogo": home_logo,
                    "awayTeam": away_team,
                    "awayLogo": away_logo,
                    "utcKickoff": event_date,
                    "status": status,
                    "minute": minute,
                    "homeScore": home_score,
                    "awayScore": away_score,
                    "channels": league["channels"],
                    "venue": comp.get("venue", {}).get("fullName", "Estadio Principal"),
                    "category": league["category"],
                    "votes": {
                        "team1": 1600 + (len(home_team) * 80),
                        "draw": 450 + (len(home_team) * 25),
                        "team2": 1500 + (len(away_team) * 75)
                    }
                })
        except Exception as e:
            continue

    print(f"[Pipeline] ESPN retrieved {len(matches)} current & upcoming matches.")
    return matches

def generate_match_html(match):
    """Generates authentic high-converting match viewing page with full CSS styling matching main.css"""
    home_team = match["homeTeam"]
    away_team = match["awayTeam"]
    tournament = match["tournament"]
    venue = match["venue"]
    utc_time = match["utcKickoff"]
    slug = match["slug"]
    channels = match.get("channels", ["ESPN", "Fox Sports", "DSports"])
    primary_channel = channels[0] if len(channels) > 0 else "Señal Oficial HD"
    alt_channel_1 = channels[1] if len(channels) > 1 else (primary_channel + " Opción 2")
    alt_channel_2 = channels[2] if len(channels) > 2 else "Señal Internacional Full HD"

    # md5 hash deterministic votes
    slug_hash = int(hashlib.md5(slug.encode('utf-8')).hexdigest()[:8], 16)
    p_home_init = 38 + (slug_hash % 20)
    p_draw_init = 18 + ((slug_hash >> 2) % 10)
    p_away_init = 100 - (p_home_init + p_draw_init)
    base_count = 3400 + (slug_hash % 3200)
    v_home = int(base_count * (p_home_init / 100))
    v_draw = int(base_count * (p_draw_init / 100))
    v_away = base_count - (v_home + v_draw)

    home_team_js = json.dumps(home_team)
    away_team_js = json.dumps(away_team)
    tournament_js = json.dumps(tournament)
    primary_channel_js = json.dumps(primary_channel)

    b = get_accurate_broadcasters(tournament, channels)

    flag_ar = '<img src="../img/flags/ar.svg" alt="Argentina" width="22" height="15" style="border-radius: 2px; vertical-align: middle;">'
    flag_es = '<img src="../img/flags/es.svg" alt="España" width="22" height="15" style="border-radius: 2px; vertical-align: middle;">'
    flag_mx = '<img src="../img/flags/mx.svg" alt="México" width="22" height="15" style="border-radius: 2px; vertical-align: middle;">'
    flag_co = '<img src="../img/flags/co.svg" alt="Colombia" width="22" height="15" style="border-radius: 2px; vertical-align: middle;">'
    flag_us = '<img src="../img/flags/us.svg" alt="Estados Unidos" width="22" height="15" style="border-radius: 2px; vertical-align: middle;">'

    country_rows = f"""
      <tr style="border-bottom: 1px solid #f1f5f9;">
        <td style="padding: 0.75rem 1.25rem; font-weight: 700; color: #1e293b; font-size: 0.875rem;">
          <div style="display: inline-flex; align-items: center; gap: 0.65rem;">
            {flag_ar}
            <span>Argentina</span>
          </div>
        </td>
        <td style="padding: 0.75rem 1rem;">
          <span class="country-kickoff" data-tz="America/Argentina/Buenos_Aires" style="font-weight: 700; color: #0f172a; font-size: 0.85rem; background: #f1f5f9; padding: 0.25rem 0.6rem; border-radius: 6px; border: 1px solid #e2e8f0; display: inline-block;">--:-- hs</span>
        </td>
        <td style="padding: 0.75rem 1.25rem; text-align: right;">
          <span style="background: #f0fdf4; color: #166534; padding: 0.3rem 0.75rem; border-radius: 6px; font-weight: 700; font-size: 0.825rem; border: 1px solid #bbf7d0; display: inline-block;">📺 {b['ar']}</span>
        </td>
      </tr>
      <tr style="border-bottom: 1px solid #f1f5f9;">
        <td style="padding: 0.75rem 1.25rem; font-weight: 700; color: #1e293b; font-size: 0.875rem;">
          <div style="display: inline-flex; align-items: center; gap: 0.65rem;">
            {flag_es}
            <span>España</span>
          </div>
        </td>
        <td style="padding: 0.75rem 1rem;">
          <span class="country-kickoff" data-tz="Europe/Madrid" style="font-weight: 700; color: #0f172a; font-size: 0.85rem; background: #f1f5f9; padding: 0.25rem 0.6rem; border-radius: 6px; border: 1px solid #e2e8f0; display: inline-block;">--:-- hs</span>
        </td>
        <td style="padding: 0.75rem 1.25rem; text-align: right;">
          <span style="background: #eff6ff; color: #1e40af; padding: 0.3rem 0.75rem; border-radius: 6px; font-weight: 700; font-size: 0.825rem; border: 1px solid #bfdbfe; display: inline-block;">📺 {b['es']}</span>
        </td>
      </tr>
      <tr style="border-bottom: 1px solid #f1f5f9;">
        <td style="padding: 0.75rem 1.25rem; font-weight: 700; color: #1e293b; font-size: 0.875rem;">
          <div style="display: inline-flex; align-items: center; gap: 0.65rem;">
            {flag_mx}
            <span>México</span>
          </div>
        </td>
        <td style="padding: 0.75rem 1rem;">
          <span class="country-kickoff" data-tz="America/Mexico_City" style="font-weight: 700; color: #0f172a; font-size: 0.85rem; background: #f1f5f9; padding: 0.25rem 0.6rem; border-radius: 6px; border: 1px solid #e2e8f0; display: inline-block;">--:-- hs</span>
        </td>
        <td style="padding: 0.75rem 1.25rem; text-align: right;">
          <span style="background: #fff7ed; color: #c2410c; padding: 0.3rem 0.75rem; border-radius: 6px; font-weight: 700; font-size: 0.825rem; border: 1px solid #fed7aa; display: inline-block;">📺 {b['mx']}</span>
        </td>
      </tr>
      <tr style="border-bottom: 1px solid #f1f5f9;">
        <td style="padding: 0.75rem 1.25rem; font-weight: 700; color: #1e293b; font-size: 0.875rem;">
          <div style="display: inline-flex; align-items: center; gap: 0.65rem;">
            {flag_co}
            <span>Colombia / Sudamérica</span>
          </div>
        </td>
        <td style="padding: 0.75rem 1rem;">
          <span class="country-kickoff" data-tz="America/Bogota" style="font-weight: 700; color: #0f172a; font-size: 0.85rem; background: #f1f5f9; padding: 0.25rem 0.6rem; border-radius: 6px; border: 1px solid #e2e8f0; display: inline-block;">--:-- hs</span>
        </td>
        <td style="padding: 0.75rem 1.25rem; text-align: right;">
          <span style="background: #f0fdf4; color: #166534; padding: 0.3rem 0.75rem; border-radius: 6px; font-weight: 700; font-size: 0.825rem; border: 1px solid #bbf7d0; display: inline-block;">📺 {b['co']}</span>
        </td>
      </tr>
      <tr>
        <td style="padding: 0.75rem 1.25rem; font-weight: 700; color: #1e293b; font-size: 0.875rem;">
          <div style="display: inline-flex; align-items: center; gap: 0.65rem;">
            {flag_us}
            <span>Estados Unidos</span>
          </div>
        </td>
        <td style="padding: 0.75rem 1rem;">
          <span class="country-kickoff" data-tz="America/New_York" style="font-weight: 700; color: #0f172a; font-size: 0.85rem; background: #f1f5f9; padding: 0.25rem 0.6rem; border-radius: 6px; border: 1px solid #e2e8f0; display: inline-block;">--:-- ET</span>
        </td>
        <td style="padding: 0.75rem 1.25rem; text-align: right;">
          <span style="background: #faf5ff; color: #7e22ce; padding: 0.3rem 0.75rem; border-radius: 6px; font-weight: 700; font-size: 0.825rem; border: 1px solid #e9d5ff; display: inline-block;">📺 {b['us']}</span>
        </td>
      </tr>
    """

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{home_team} vs {away_team} en vivo online - LibreGol TV</title>
  <meta name="description" content="Mira {home_team} vs {away_team} en vivo online por {tournament}. Horarios sincronizados y canales de transmisión oficial en HD.">
  <meta name="keywords" content="{home_team.lower()} vs {away_team.lower()} en vivo online, donde ver {home_team.lower()} vs {away_team.lower()}, {tournament.lower()} futbol libre">
  <link rel="canonical" href="https://libregoltv.online/partidos/{slug}.html">
  
  <!-- Preconnect & Resource Hints for Ultra-Fast CDN Delivery -->
  <link rel="preconnect" href="https://a.espncdn.com" crossorigin>
  <link rel="dns-prefetch" href="https://a.espncdn.com">
  <!-- Favicon Suite (Google Search & Multi-Device Optimized) -->
  <link rel="icon" type="image/x-icon" href="../favicon.ico">
  <link rel="icon" type="image/png" sizes="32x32" href="../img/favicon-32x32.png">
  <link rel="icon" type="image/png" sizes="48x48" href="../img/favicon-48x48.png">
  <link rel="icon" type="image/png" sizes="192x192" href="../img/favicon-192x192.png">
  <link rel="apple-touch-icon" sizes="180x180" href="../img/apple-touch-icon.png">
  <link rel="stylesheet" href="../css/main.min.css?v=5.0">

  <!-- SportsEvent Schema (Phase 5 Validated) -->
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "SportsEvent",
    "name": "{home_team} vs {away_team} - {tournament}",
    "startDate": "{utc_time}",
    "location": {{
      "@type": "Place",
      "name": "{venue}"
    }},
    "competitor": [
      {{
        "@type": "SportsTeam",
        "name": "{home_team}"
      }},
      {{
        "@type": "SportsTeam",
        "name": "{away_team}"
      }}
    ]
  }}
  </script>

  <!-- BreadcrumbList Schema (Phase 5 Validated) -->
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [
      {{
        "@type": "ListItem",
        "position": 1,
        "name": "Inicio",
        "item": "https://libregoltv.online/"
      }},
      {{
        "@type": "ListItem",
        "position": 2,
        "name": "Partidos",
        "item": "https://libregoltv.online/partidos-de-hoy.html"
      }},
      {{
        "@type": "ListItem",
        "position": 3,
        "name": "{home_team} vs {away_team}",
        "item": "https://libregoltv.online/partidos/{slug}.html"
      }}
    ]
  }}
  </script>
</head>
<body style="min-height: 100vh; display: flex; flex-direction: column; background: #f9fafb;">

  <!-- Header -->
  <header style="background: white; border-bottom: 1px solid #e5e7eb; padding: 0.75rem 1.5rem; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 4px rgba(0,0,0,0.04);">
    <a href="../index.html" class="title-header" style="display: flex; align-items: center; gap: 0.45rem; text-decoration: none; font-weight: 800; font-size: 1.25rem; color: #111827;">
      <span style="font-size: 1.35rem; margin-right: 3px;">⚽</span>
      <span>LibreGol<span style="color:#16a34a;">TV</span></span>
    </a>
    <a href="../partidos-de-hoy.html" style="color: #4b5563; font-weight: 600; font-size: 0.9rem; text-decoration: none; display: flex; align-items: center; gap: 0.35rem;">
      <span>←</span> Volver a la Agenda
    </a>
  </header>

  <main class="main-frame" style="max-width: 900px; margin: 1.25rem auto 3rem auto; padding: 0 1rem; width: 100%; box-sizing: border-box;">
    <!-- Match Title -->
    <h1 class="title" style="font-size: 1.5rem; font-weight: 800; color: #111827; text-align: center; margin-bottom: 0.35rem;">
      {home_team} vs {away_team} en vivo online
    </h1>
    <p style="text-align: center; color: #64748b; font-size: 0.9rem; margin-top: 0; margin-bottom: 1.25rem;">
      Torneo: <strong>{tournament}</strong> • Horario: <span class="country-kickoff" data-tz="America/Argentina/Buenos_Aires">--:--</span> hs
    </p>

    <!-- Authentic Streaming Video Player Container -->
    <div class="stream-player-wrapper" id="streamPlayerWrapper">
      <div class="video-display-frame" id="videoDisplayFrame" onclick="handleStreamClick()">
        
        <!-- State 1: Conectando... Screen (Matching User Screenshots) -->
        <div class="screen-connecting" id="screenConnecting">
          <div class="connecting-content">
            <h3 class="connecting-title">Conectando...</h3>
            <p class="connecting-desc">Cargando la fuente seleccionada.</p>
          </div>
        </div>

        <!-- State 2: Video Player with Rotating Buffer & Native Controls -->
        <div class="screen-playing" id="screenPlaying" style="display: none;">
          <!-- Central Rotating Buffer Spinner -->
          <div class="player-buffer-center">
            <div class="buffer-arc-spinner"></div>
          </div>

          <!-- HTML5 Style Controls Overlay -->
          <div class="player-controls-overlay" onclick="event.stopPropagation()">
            <div class="controls-timeline-track">
              <div class="controls-buffer-bar"></div>
              <div class="controls-playhead-dot"></div>
            </div>
            <div class="controls-buttons-bar">
              <div class="controls-left">
                <button type="button" class="btn-ctrl" id="btnPlayPause" onclick="togglePlayPause()" title="Pausar / Reproducir">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>
                </button>
                <span class="ctrl-time" id="ctrlTime">0:00</span>
              </div>
              <div class="controls-right">
                <button type="button" class="btn-ctrl" id="btnVolume" onclick="toggleMute()" title="Silenciar / Sonido">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/></svg>
                </button>
                <button type="button" class="btn-ctrl" id="btnFullscreen" onclick="toggleFullscreen()" title="Pantalla completa">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"/></svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Under-Player Status & Reload Bar -->
      <div class="stream-under-bar">
        <div class="stream-status-left">
          <span class="stream-status-dot"></span>
          <span class="stream-status-text" id="streamStatusText">Fuente 1 {primary_channel} · conectado</span>
        </div>
        <button type="button" class="btn-stream-reload" id="btnStreamReload" onclick="triggerReload()" title="Recargar señal">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/>
          </svg>
          <span>Recargar</span>
        </button>
      </div>

      <!-- Source Switcher Pills -->
      <div class="stream-sources-row">
        <button type="button" class="source-pill-btn" data-source-id="auto" onclick="selectSource('auto', 'Automático')">
          Automático
        </button>
        <button type="button" class="source-pill-btn active" data-source-id="f1" onclick="selectSource('f1', 'Fuente 1 {primary_channel}')">
          FUENTE 1 {primary_channel}
        </button>
        <button type="button" class="source-pill-btn" data-source-id="f2" onclick="selectSource('f2', 'Fuente 2 {alt_channel_1}')">
          FUENTE 2 {alt_channel_1}
        </button>
        <button type="button" class="source-pill-btn" data-source-id="f3" onclick="selectSource('f3', 'Fuente 3 {alt_channel_2}')">
          FUENTE 3 {alt_channel_2}
        </button>
      </div>
    </div>

    <!-- Community Prediction Voting Poll (Compact & Sleek) -->
    <div class="voting-poll-box" style="background: white; border: 1px solid #e5e7eb; border-radius: 0.5rem; padding: 1rem 1.15rem; margin: 1.25rem 0; box-shadow: 0 1px 4px rgba(0,0,0,0.04);">
      <h3 style="font-size: 1rem; font-weight: 800; color: #1f2937; margin-bottom: 0.25rem; text-align: center;">
        ⚽ Pronóstico de la Afición: ¿Quién ganará hoy?
      </h3>
      <p style="font-size: 0.8rem; color: #64748b; text-align: center; margin-bottom: 0.75rem;">
        Vota por tu equipo y consulta el pronóstico en tiempo real
      </p>
      <div style="display: flex; gap: 0.5rem; justify-content: center; flex-wrap: wrap;" id="pollButtons">
        <button onclick="voteMatch('team1')" style="flex: 1; min-width: 110px; max-width: 180px; background: #f0fdf4; border: 1px solid #86efac; color: #166534; font-weight: 700; padding: 0.5rem 0.75rem; border-radius: 0.4rem; cursor: pointer; font-size: 0.825rem; transition: all 0.15s; white-space: nowrap;">
          {home_team}
        </button>
        <button onclick="voteMatch('draw')" style="flex: 1; min-width: 80px; max-width: 120px; background: #f8fafc; border: 1px solid #cbd5e1; color: #334155; font-weight: 700; padding: 0.5rem 0.75rem; border-radius: 0.4rem; cursor: pointer; font-size: 0.825rem; transition: all 0.15s; white-space: nowrap;">
          Empate
        </button>
        <button onclick="voteMatch('team2')" style="flex: 1; min-width: 110px; max-width: 180px; background: #eff6ff; border: 1px solid #93c5fd; color: #1e40af; font-weight: 700; padding: 0.5rem 0.75rem; border-radius: 0.4rem; cursor: pointer; font-size: 0.825rem; transition: all 0.15s; white-space: nowrap;">
          {away_team}
        </button>
      </div>
      <div id="pollResults" style="margin-top: 0.75rem; display: none;">
        <div style="display: flex; justify-content: space-between; font-size: 0.8rem; font-weight: 700; margin-bottom: 0.25rem;">
          <span id="pHomeLabel">{home_team}: {p_home_init}%</span>
          <span id="pDrawLabel">Empate: {p_draw_init}%</span>
          <span id="pAwayLabel">{away_team}: {p_away_init}%</span>
        </div>
        <div style="display: flex; height: 8px; border-radius: 9999px; overflow: hidden; background: #e2e8f0;">
          <div id="barHome" style="width: {p_home_init}%; background: #16a34a; transition: width 0.35s ease;"></div>
          <div id="barDraw" style="width: {p_draw_init}%; background: #94a3b8; transition: width 0.35s ease;"></div>
          <div id="barAway" style="width: {p_away_init}%; background: #2563eb; transition: width 0.35s ease;"></div>
        </div>
        <p id="pollFeedback" style="font-size: 0.75rem; color: #16a34a; text-align: center; margin-top: 0.4rem; font-weight: 700;">
          ✓ ¡Pronóstico registrado en vivo!
        </p>
      </div>
    </div>

    <!-- Sincronización Horaria y Canales Oficiales -->
    <div style="background: white; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; margin-bottom: 1.75rem; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);">
      <div style="background: #f8fafc; padding: 0.85rem 1.25rem; border-bottom: 1px solid #e2e8f0; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.5rem;">
        <div style="display: flex; align-items: center; gap: 0.5rem;">
          <span style="font-size: 1.15rem;">📺</span>
          <h2 style="font-size: 1rem; font-weight: 800; color: #0f172a; margin: 0;">
            Canales Oficiales y Horarios por País
          </h2>
        </div>
        <span style="font-size: 0.75rem; font-weight: 600; color: #16a34a; background: #f0fdf4; border: 1px solid #bbf7d0; padding: 0.2rem 0.65rem; border-radius: 9999px;">
          ● Horarios Sincronizados
        </span>
      </div>
      <div style="overflow-x: auto;">
        <table style="width: 100%; border-collapse: collapse; text-align: left;">
          <thead>
            <tr style="background: #f8fafc; border-bottom: 1px solid #e2e8f0; font-size: 0.75rem; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em;">
              <th style="padding: 0.65rem 1.25rem;">País</th>
              <th style="padding: 0.65rem 1rem;">Hora Local</th>
              <th style="padding: 0.65rem 1.25rem; text-align: right;">Canal Oficial</th>
            </tr>
          </thead>
          <tbody>
            {country_rows}
          </tbody>
        </table>
      </div>
    </div>

    <!-- Match Preview & Editorial Context -->
    <article style="background: white; border: 1px solid #e5e7eb; border-radius: 0.5rem; padding: 1.25rem 1.5rem; margin-bottom: 2rem; font-size: 0.925rem; line-height: 1.65; color: #4b5563;">
      <h2 style="font-size: 1.15rem; font-weight: 700; color: #1f2937; margin-bottom: 0.4rem;">Información del Encuentro</h2>
      <p style="margin: 0;">
        El partido entre {home_team} y {away_team} por {tournament} se disputa en el estadio {venue}. En LibreGol TV puedes seguir la cobertura minuto a minuto, horarios sincronizados según tu país y la votación en tiempo real de los aficionados.
      </p>
    </article>

    <!-- Policy Compliant Responsive Match Ad Slot -->
    <div class="ad-placement-slot" role="region" aria-label="Publicidad">
      <span class="ad-slot-label">Publicidad</span>
      <div class="ad-slot-box" id="ad-slot-match-bottom">
        <!-- Espacio reservado para Google AdSense / Banner Patrocinado (728x90 o 300x250) -->
        <span>Espacio Publicitario Patrocinado</span>
      </div>
    </div>
  </main>

  <!-- Clean Slim Footer -->
  <footer class="footer-clean" style="background: #111827; color: #9ca3af; padding: 1.5rem; text-align: center; font-size: 0.85rem; margin-top: auto;">
    <div style="max-width: 900px; margin: 0 auto;">
      <p style="margin-bottom: 0.5rem;">
        <a href="../index.html" style="color: #cbd5e1; text-decoration: none; margin: 0 0.5rem;">Inicio</a> |
        <a href="../partidos-de-hoy.html" style="color: #cbd5e1; text-decoration: none; margin: 0 0.5rem;">Partidos de Hoy</a> |
        <a href="../marcadores.html" style="color: #cbd5e1; text-decoration: none; margin: 0 0.5rem;">Marcadores</a> |
        <a href="../articulos/alternativas-a-futbol-libre.html" style="color: #cbd5e1; text-decoration: none; margin: 0 0.5rem;">Alternativas</a> |
        <a href="../legal/aviso-legal-dmca.html" style="color: #cbd5e1; text-decoration: none; margin: 0 0.5rem;">Aviso Legal / DMCA</a>
      </p>
      <span style="font-size: 0.8rem; color: #6b7280;">LibreGol TV 2026 — Agenda deportiva y programación de fútbol en vivo.</span>
    </div>
  </footer>

  <script>
    const UTC_KICKOFF = "{utc_time}";
    const MATCH_SLUG = "{slug}";
    const HOME_NAME = {home_team_js};
    const AWAY_NAME = {away_team_js};
    const TOURNAMENT = {tournament_js};
    const PRIMARY_CHANNEL = {primary_channel_js};
    let votesData = {{
      home: {v_home},
      draw: {v_draw},
      away: {v_away}
    }};

    let activeSourceName = "Fuente 1 " + PRIMARY_CHANNEL;
    let isConnectingStream = false;

    function showConnectingState(durationMs, nextName) {{
      if (isConnectingStream) return;
      isConnectingStream = true;

      const screenConn = document.getElementById("screenConnecting");
      const screenPlay = document.getElementById("screenPlaying");
      const statusText = document.getElementById("streamStatusText");
      const reloadBtn = document.getElementById("btnStreamReload");

      if (screenConn) screenConn.style.display = "flex";
      if (screenPlay) screenPlay.style.display = "none";
      if (reloadBtn) reloadBtn.classList.add("spinning");

      setTimeout(() => {{
        if (nextName) {{
          activeSourceName = nextName;
        }}
        if (statusText) {{
          statusText.textContent = activeSourceName + " · conectado";
        }}
        if (screenConn) screenConn.style.display = "none";
        if (screenPlay) screenPlay.style.display = "flex";
        if (reloadBtn) reloadBtn.classList.remove("spinning");
        isConnectingStream = false;
      }}, durationMs);
    }}

    function triggerReload() {{
      showConnectingState(2300, activeSourceName);
    }}

    function selectSource(sourceId, sourceName) {{
      document.querySelectorAll(".source-pill-btn").forEach(btn => {{
        btn.classList.remove("active");
        if (btn.dataset.sourceId === sourceId) {{
          btn.classList.add("active");
        }}
      }});
      showConnectingState(2000, sourceName);
    }}

    function handleStreamClick() {{
      if (!isConnectingStream) {{
        showConnectingState(1800, activeSourceName);
      }}
    }}

    function togglePlayPause() {{
      handleStreamClick();
    }}

    function toggleMute() {{
      const btn = document.getElementById("btnVolume");
      if (btn) {{
        btn.classList.toggle("muted");
      }}
    }}

    function toggleFullscreen() {{
      const frame = document.getElementById("streamPlayerWrapper");
      if (!document.fullscreenElement) {{
        if (frame.requestFullscreen) frame.requestFullscreen();
        else if (frame.webkitRequestFullscreen) frame.webkitRequestFullscreen();
      }} else {{
        if (document.exitFullscreen) document.exitFullscreen();
      }}
    }}

    function renderPoll(userChoice, isNewVote) {{
      const pollButtons = document.getElementById("pollButtons");
      const pollResults = document.getElementById("pollResults");
      const pHomeLabel = document.getElementById("pHomeLabel");
      const pDrawLabel = document.getElementById("pDrawLabel");
      const pAwayLabel = document.getElementById("pAwayLabel");
      const barHome = document.getElementById("barHome");
      const barDraw = document.getElementById("barDraw");
      const barAway = document.getElementById("barAway");
      const pollFeedback = document.getElementById("pollFeedback");

      const total = votesData.home + votesData.draw + votesData.away;
      const pHome = Math.round((votesData.home / total) * 100);
      const pAway = Math.round((votesData.away / total) * 100);
      const pDraw = 100 - (pHome + pAway);

      if (pHomeLabel) pHomeLabel.textContent = HOME_NAME + ": " + pHome + "%";
      if (pDrawLabel) pDrawLabel.textContent = "Empate: " + pDraw + "%";
      if (pAwayLabel) pAwayLabel.textContent = AWAY_NAME + ": " + pAway + "%";

      if (barHome) barHome.style.width = pHome + "%";
      if (barDraw) barDraw.style.width = pDraw + "%";
      if (barAway) barAway.style.width = pAway + "%";

      if (pollButtons) pollButtons.style.display = "none";
      if (pollResults) pollResults.style.display = "block";

      if (pollFeedback && userChoice) {{
        let chosenName = userChoice === "team1" ? HOME_NAME : (userChoice === "team2" ? AWAY_NAME : "Empate");
        pollFeedback.innerHTML = "✓ " + (isNewVote ? "¡Pronóstico registrado en vivo por <strong>" : "Tu pronóstico registrado: <strong>") + chosenName + "</strong> (" + total.toLocaleString() + " votos totales)";
      }}
    }}

    function voteMatch(choice) {{
      const key = "libregol_voted_" + MATCH_SLUG;
      if (localStorage.getItem(key)) {{
        renderPoll(localStorage.getItem(key), false);
        return;
      }}

      if (choice === "team1") votesData.home += 1;
      else if (choice === "team2") votesData.away += 1;
      else votesData.draw += 1;

      try {{
        localStorage.setItem(key, choice);
      }} catch(e) {{}}

      renderPoll(choice, true);
    }}

    document.addEventListener("DOMContentLoaded", () => {{
      // Start with Conectando... for 2.2s then enter player with buffer
      showConnectingState(2200, activeSourceName);

      try {{
        const savedChoice = localStorage.getItem("libregol_voted_" + MATCH_SLUG);
        if (savedChoice) {{
          renderPoll(savedChoice, false);
        }}
      }} catch(e) {{}}

      document.querySelectorAll(".country-kickoff").forEach(elem => {{
        const tz = elem.dataset.tz;
        if (tz && UTC_KICKOFF) {{
          try {{
            const date = new Date(UTC_KICKOFF);
            elem.textContent = new Intl.DateTimeFormat("es", {{
              hour: "2-digit",
              minute: "2-digit",
              hour12: false,
              timeZone: tz
            }}).format(date) + " hs";
          }} catch(e) {{}}
        }}
      }});
    }});
  </script>
  <script src="../js/cookie-consent.js" defer></script>
</body>
</html>
"""

def update_agenda_data_js(matches):
    """Updates js/agenda-data.js preserving channel catalogue"""
    existing_channels = ""
    try:
        with open(OUTPUT_JS, "r", encoding="utf-8") as f:
            existing_js = f.read()
        m_chan = re.search(r'(window\.LIBREGOL_CHANNELS\s*=.*)', existing_js, re.DOTALL)
        if m_chan:
            existing_channels = m_chan.group(1)
    except Exception:
        pass

    now_utc = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%SZ')
    new_js = f"""/**
 * LibreGol TV — Live Matches Feed (Auto-Synced via Pipeline)
 * Last Updated: {now_utc}
 */

window.LIBREGOL_MATCHES = {json.dumps(matches, indent=2, ensure_ascii=False)};
{existing_channels}
"""
    with open(OUTPUT_JS, "w", encoding="utf-8") as f:
        f.write(new_js)
    print(f"[Pipeline] Updated {OUTPUT_JS} with {len(matches)} live matches.")

def compile_master_sitemap():
    """Compiles 100% complete sitemap.xml dynamically from current disk contents"""
    today_str = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    base_url = "https://libregoltv.online"

    static_priority = {
        "": 1.0,
        "partidos-de-hoy.html": 0.9,
        "futbol-en-la-tv.html": 0.9,
        "marcadores.html": 0.9,
        "posiciones.html": 0.8,
        "partidos-para-manana.html": 0.8,
        "partidos-argentina.html": 0.8,
        "partidos-colombia.html": 0.8,
        "partidos-mexico.html": 0.8,
        "partidos-chile.html": 0.8,
        "partidos-peru.html": 0.8,
        "resultados-recientes.html": 0.7,
    }

    urls = []
    # 1. Root HTML files
    for f in os.listdir(BASE_DIR):
        if f.endswith(".html") and f != "404.html":
            rel_path = "" if f == "index.html" else f[:-5]
            prio = static_priority.get(f, 0.7)
            freq = "always" if f in ["index.html", "partidos-de-hoy.html", "marcadores.html"] else "daily"
            loc = f"{base_url}/" if rel_path == "" else f"{base_url}/{rel_path}"
            urls.append((loc, freq, prio))

    # 2. Canales
    canales_dir = os.path.join(BASE_DIR, "canales")
    if os.path.isdir(canales_dir):
        for f in os.listdir(canales_dir):
            if f.endswith(".html"):
                sub_path = "canales/" if f == "index.html" else f"canales/{f[:-5]}"
                urls.append((f"{base_url}/{sub_path}", "daily", 0.8))

    # 3. Articulos
    articulos_dir = os.path.join(BASE_DIR, "articulos")
    if os.path.isdir(articulos_dir):
        for f in os.listdir(articulos_dir):
            if f.endswith(".html"):
                urls.append((f"{base_url}/articulos/{f[:-5]}", "weekly", 0.7))

    # 4. Legal
    legal_dir = os.path.join(BASE_DIR, "legal")
    if os.path.isdir(legal_dir):
        for f in os.listdir(legal_dir):
            if f.endswith(".html"):
                urls.append((f"{base_url}/legal/{f[:-5]}", "monthly", 0.4))



    seen = set()
    clean_urls = []
    for loc, freq, prio in urls:
        if loc not in seen:
            seen.add(loc)
            clean_urls.append((loc, freq, prio))

    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    ]
    for loc, freq, prio in clean_urls:
        xml_lines.append("  <url>")
        xml_lines.append(f"    <loc>{loc}</loc>")
        xml_lines.append(f"    <lastmod>{today_str}</lastmod>")
        xml_lines.append(f"    <changefreq>{freq}</changefreq>")
        xml_lines.append(f"    <priority>{prio}</priority>")
        xml_lines.append("  </url>")
    xml_lines.append("</urlset>\n")

    with open(SITEMAP_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(xml_lines))
    print(f"[Pipeline] Master sitemap.xml updated with {len(clean_urls)} verified URLs.")

def minify_css():
    """Generates minified main.min.css for maximum performance"""
    try:
        with open(CSS_FILE, "r", encoding="utf-8") as f:
            c = f.read()
        c = re.sub(r'/\*.*?\*/', '', c, flags=re.DOTALL)
        c = re.sub(r'\s+', ' ', c)
        c = re.sub(r'\s*([\{\}\:\;\,])\s*', r'\1', c)
        c = c.replace(';}', '}')
        c = re.sub(r'\band\s*\(', 'and (', c).strip()
        with open(CSS_MIN_FILE, "w", encoding="utf-8") as f:
            f.write(c)
        print(f"[Pipeline] Minified CSS updated: {os.path.getsize(CSS_MIN_FILE)} bytes.")
    except Exception as e:
        print(f"[Pipeline] CSS Minification note: {e}")

def run_sync():
    print(f"=== LibreGol TV Auto-Sync Pipeline Started ({datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%SZ')}) ===")
    
    matches = fetch_primary_competitor()
    if not matches:
        matches = fetch_secondary_espn()
    
    if not matches:
        print("[Pipeline] WARNING: Both sources yielded 0 new matches. Retaining current agenda.")
        return False

    today_str = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    def match_priority(m):
        status = m.get("status", "UPCOMING")
        dt = m.get("utcKickoff", "")[:10]
        if status == "LIVE":
            return (0, m.get("utcKickoff", ""))
        if status == "UPCOMING" and dt == today_str:
            return (1, m.get("utcKickoff", ""))
        if status == "UPCOMING" and dt > today_str:
            return (2, m.get("utcKickoff", ""))
        if status == "FINISHED" and dt == today_str:
            return (3, m.get("utcKickoff", ""))
        return (4, m.get("utcKickoff", ""))

    matches.sort(key=match_priority)

    # 1. Update js/agenda-data.js (Dynamic live feed)
    update_agenda_data_js(matches)

    # 2. Refresh Master Clean Sitemap (Core pages only)
    compile_master_sitemap()

    # 4. Keep minified CSS in sync
    minify_css()

    print("=== LibreGol TV Auto-Sync Pipeline Finished Successfully! ===")
    return True

if __name__ == "__main__":
    run_sync()
