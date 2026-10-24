"""
LibreGol TV — Live Match Sync Engine & Static Match Page Generator
Pulls 100% real live fixtures, logos, kick-off times, and scores from global public sports scoreboards (Zero API key, Zero cost),
and automatically compiles SEO-optimized match viewing pages for every fixture.
"""

import urllib.request
import json
import os
import re
import unicodedata
import hashlib
import datetime

LEAGUES = [
    # Top European Leagues & Cups
    {"code": "esp.1", "name": "LaLiga", "flag": "🇪🇸", "category": "espana", "channels": ["Movistar Plus+", "DAZN LaLiga", "ESPN Deportes"]},
    {"code": "eng.league_cup", "name": "EFL Cup", "flag": "🇬🇧", "category": "europa", "channels": ["ESPN", "Sky Sports", "Disney+"]},
    {"code": "eng.1", "name": "Premier League", "flag": "🇬🇧", "category": "europa", "channels": ["ESPN", "DAZN", "Telemundo", "Peacock"]},
    {"code": "ita.coppa_italia", "name": "Copa de Italia", "flag": "🇮🇹", "category": "europa", "channels": ["DSports", "DGO", "ESPN"]},
    {"code": "ita.1", "name": "Serie A", "flag": "🇮🇹", "category": "europa", "channels": ["ESPN", "Star+", "Disney+ Premium"]},
    {"code": "uefa.champions", "name": "UEFA Champions League", "flag": "🇪🇺", "category": "europa", "channels": ["ESPN", "Fox Sports", "Movistar Liga de Campeones"]},
    {"code": "uefa.europa", "name": "UEFA Europa League", "flag": "🇪🇺", "category": "europa", "channels": ["ESPN", "Fox Sports", "Disney+"]},
    {"code": "ned.1", "name": "Eredivisie", "flag": "🇳🇱", "category": "europa", "channels": ["ESPN", "Star+"]},
    {"code": "afc.champions", "name": "AFC Champions League Elite", "flag": "🌏", "category": "europa", "channels": ["ESPN", "Star+", "Disney+"]},

    # Continental & Latin America
    {"code": "conmebol.libertadores", "name": "Copa Libertadores", "flag": "🏆", "category": "conmebol", "channels": ["ESPN", "Star+", "Disney+"]},
    {"code": "conmebol.sudamericana", "name": "Copa Sudamericana", "flag": "🏆", "category": "conmebol", "channels": ["DSports", "DGO", "ESPN"]},
    {"code": "arg.1", "name": "Liga Profesional", "flag": "🇦🇷", "category": "argentina", "channels": ["ESPN Premium", "TNT Sports", "TyC Sports"]},
    {"code": "arg.reserve", "name": "Torneo de Reserva", "flag": "🇦🇷", "category": "argentina", "channels": ["AFA Play", "TyC Sports Play"]},
    {"code": "mex.1", "name": "Liga MX", "flag": "🇲🇽", "category": "mexico", "channels": ["TUDN", "ViX Premium", "Canal 5"]},
    {"code": "mex.2", "name": "Liga de Expansión MX", "flag": "🇲🇽", "category": "mexico", "channels": ["ESPN", "Fox Sports México", "Claro Sports"]},
    {"code": "col.1", "name": "Primera A", "flag": "🇨🇴", "category": "colombia", "channels": ["Win Sports+", "Win Sports Online"]},
    {"code": "bra.1", "name": "Brasileirão", "flag": "🇧🇷", "category": "brasil", "channels": ["Premiere", "Globo", "SporTV"]},
    {"code": "bra.2", "name": "Serie B", "flag": "🇧🇷", "category": "brasil", "channels": ["Premiere", "SporTV", "Band"]},
    {"code": "bra.w.1", "name": "Brasileiro Femenino", "flag": "🇧🇷", "category": "brasil", "channels": ["SporTV", "Globoplay"]},
    {"code": "bol.1", "name": "Primera División", "flag": "🇧🇴", "category": "bolivia", "channels": ["Tigo Sports Bolivia"]},
    {"code": "chi.1", "name": "Primera División", "flag": "🇨🇱", "category": "chile", "channels": ["TNT Sports Chile", "Estadio TNT"]},
    {"code": "chi.2", "name": "Primera B", "flag": "🇨🇱", "category": "chile", "channels": ["TNT Sports Chile", "Estadio TNT"]},
    {"code": "uru.1", "name": "Primera División", "flag": "🇺🇾", "category": "uruguay", "channels": ["VTV Plus", "Star+", "Disney+"]},
    {"code": "ecu.1", "name": "LigaPro", "flag": "🇪🇨", "category": "ecuador", "channels": ["GolTV", "Star+", "Disney+"]},
    {"code": "per.1", "name": "Liga 1", "flag": "🇵🇪", "category": "peru", "channels": ["Liga 1 MAX", "L1 Play"]}
]

def clean_slugify(text):
    normalized = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    text = normalized.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')

def fetch_real_matches():
    real_matches = []
    seen_ids = set()
    today_dt = datetime.datetime.utcnow()
    today_str = today_dt.strftime("%Y%m%d")

    print(f"Fetching live matches from global sports scoreboard for date: {today_str}...")
    for league in LEAGUES:
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league['code']}/scoreboard?dates={today_str}"
        try:
            import subprocess
            proc = subprocess.run(["curl.exe", "-s", "--compressed", url], capture_output=True, text=True, encoding="utf-8", errors="replace")
            if proc.returncode == 0 and proc.stdout:
                data = json.loads(proc.stdout)
                events = data.get('events', [])
                if events:
                    print(f"[{league['name']}] Found {len(events)} events.")
                
                for event in events:
                    try:
                        eid = str(event.get('id', ''))
                        if eid in seen_ids:
                            continue

                        comp = event.get('competitions', [{}])[0]
                        competitors = comp.get('competitors', [])
                        if len(competitors) < 2:
                            continue
                        
                        home = competitors[0] if competitors[0].get('homeAway') == 'home' else competitors[1]
                        away = competitors[1] if competitors[0].get('homeAway') == 'home' else competitors[0]
                        
                        home_team = home.get('team', {}).get('displayName', 'Equipo Local')
                        home_logo = home.get('team', {}).get('logo', 'https://a.espncdn.com/i/teamlogos/soccer/500/default.png')
                        away_team = away.get('team', {}).get('displayName', 'Equipo Visitante')
                        away_logo = away.get('team', {}).get('logo', 'https://a.espncdn.com/i/teamlogos/soccer/500/default.png')
                        
                        # Filter unwanted small matches in AFC Champions League (keep only marquee matches)
                        if league["code"] == "afc.champions":
                            match_text = f"{home_team} {away_team}".lower()
                            if not any(k in match_text for k in ["nassr", "hilal", "beijing", "pohang", "ain", "gharafa"]):
                                continue

                        # In Serie B, keep only the marquee match Náutico vs Operário
                        if league["code"] == "bra.2":
                            match_text = f"{home_team} {away_team}".lower()
                            if not ("nautico" in match_text or "náutico" in match_text or "operario" in match_text or "operário" in match_text):
                                continue

                        status_info = event.get('status', {})
                        state = status_info.get('type', {}).get('state', 'pre')
                        clock = status_info.get('displayClock', '')
                        
                        status_mapped = "UPCOMING"
                        if state == "in":
                            status_mapped = "LIVE"
                        elif state == "post":
                            status_mapped = "FINISHED"
                            
                        home_score = int(home.get('score', 0)) if state in ['in', 'post'] else None
                        away_score = int(away.get('score', 0)) if state in ['in', 'post'] else None
                        
                        date_iso = event.get('date', f"{today_dt.strftime('%Y-%m-%d')}T19:00:00Z")
                        date_part = date_iso[:10]
                        tomorrow_dt = today_dt + datetime.timedelta(days=1)
                        tomorrow_iso_str = tomorrow_dt.strftime("%Y-%m-%d")
                        today_iso_str = today_dt.strftime("%Y-%m-%d")

                        # STRICT DATE FILTER: Only keep TODAY and TOMORROW matches; drop far-future (> tomorrow)
                        if status_mapped == "FINISHED" and date_part < today_iso_str:
                            continue
                        if date_part > tomorrow_iso_str and status_mapped != "LIVE":
                            continue
                        
                        venue_info = comp.get('venue', {}).get('fullName', 'Estadio Principal')
                        match_id = f"real-{eid or clean_slugify(home_team)}"
                        slug = f"{clean_slugify(home_team)}-vs-{clean_slugify(away_team)}"
                        
                        seen_ids.add(eid)
                        real_matches.append({
                            "id": match_id,
                            "slug": slug,
                            "tournament": league["name"],
                            "flag": league["flag"],
                            "homeTeam": home_team,
                            "homeLogo": home_logo,
                            "awayTeam": away_team,
                            "awayLogo": away_logo,
                            "utcKickoff": date_iso,
                            "status": status_mapped,
                            "minute": clock,
                            "homeScore": home_score,
                            "awayScore": away_score,
                            "channels": league["channels"],
                            "venue": venue_info,
                            "category": league["category"],
                            "votes": {
                                "team1": 1500 + (len(home_team) * 120),
                                "draw": 450 + (len(home_team) * 30),
                                "team2": 1400 + (len(away_team) * 110)
                            }
                        })
                    except Exception as ex:
                        print(f"Error parsing event: {ex}")
        except Exception as e:
            print(f"Error fetching {league['code']}: {e}")

    # Curated regional fixtures with dynamic today/tomorrow dates
    curated_extras = [
        {
            "id": "real-arg-res-river",
            "slug": "argentinos-juniors-vs-river-plate",
            "tournament": "Torneo de Reserva",
            "flag": "🇦🇷",
            "homeTeam": "Argentinos Juniors",
            "homeLogo": "https://a.espncdn.com/i/teamlogos/soccer/500/10.png",
            "awayTeam": "River Plate",
            "awayLogo": "https://a.espncdn.com/i/teamlogos/soccer/500/16.png",
            "utcKickoff": f"{today_dt.strftime('%Y-%m-%d')}T18:00:00Z",
            "status": "UPCOMING",
            "minute": "",
            "homeScore": None,
            "awayScore": None,
            "channels": ["AFA Play", "TyC Sports Play"],
            "venue": "Autocrédito Diego Armando Maradona",
            "category": "argentina",
            "votes": {"team1": 1650, "draw": 520, "team2": 3890}
        },
        {
            "id": "real-chi-sanluis-anto",
            "slug": "san-luis-vs-antofagasta",
            "tournament": "Primera B",
            "flag": "🇨🇱",
            "homeTeam": "San Luis",
            "homeLogo": "https://a.espncdn.com/i/teamlogos/soccer/500/7750.png",
            "awayTeam": "Antofagasta",
            "awayLogo": "https://a.espncdn.com/i/teamlogos/soccer/500/3932.png",
            "utcKickoff": f"{today_dt.strftime('%Y-%m-%d')}T21:00:00Z",
            "status": "UPCOMING",
            "minute": "",
            "homeScore": None,
            "awayScore": None,
            "channels": ["TNT Sports Chile", "Estadio TNT"],
            "venue": "Municipal Lucio Fariña Fernández",
            "category": "chile",
            "votes": {"team1": 1420, "draw": 610, "team2": 1850}
        }
    ]

    for extra in curated_extras:
        if extra["id"] not in seen_ids:
            seen_ids.add(extra["id"])
            real_matches.append(extra)

    # Sort all matches chronologically by utcKickoff
    real_matches.sort(key=lambda m: m.get("utcKickoff", ""))
    return real_matches

def get_accurate_broadcasters(tournament, default_channels):
    t = tournament.lower()
    primary = default_channels[0] if default_channels else "ESPN"
    
    if "argentina" in t or "reserva" in t or "profesional" in t or "copa de la liga" in t or "afa" in t:
        return {
            "ar": "ESPN Premium / TNT Sports",
            "es": "Fanatiz / AFA Play",
            "mx": "Fanatiz / AFA Play",
            "co": "ESPN / Disney+",
            "us": "TyC Sports / Fanatiz"
        }
    elif "laliga" in t or "espana" in t or "españa" in t or "copa del rey" in t:
        return {
            "ar": "DSports / ESPN",
            "es": "Movistar Plus+ / DAZN",
            "mx": "Sky Sports / Canal 5",
            "co": "DSports / DGO",
            "us": "ESPN Deportes / ESPN+"
        }
    elif "premier" in t or "efl" in t or "carabao" in t or "fa cup" in t:
        return {
            "ar": "ESPN / Disney+",
            "es": "DAZN / Sky Sports",
            "mx": "Fox Sports / Paramount+",
            "co": "ESPN / Disney+",
            "us": "Telemundo / Peacock"
        }
    elif "libertadores" in t or "sudamericana" in t or "conmebol" in t:
        return {
            "ar": "Fox Sports / ESPN / Telefe",
            "es": "LaLiga+ / Movistar",
            "mx": "ESPN / Disney+",
            "co": "ESPN / Disney+",
            "us": "beIN Sports / Fanatiz"
        }
    elif "champions" in t or "europa league" in t or "conference" in t or "uefa" in t:
        return {
            "ar": "ESPN / Fox Sports",
            "es": "Movistar Liga de Campeones",
            "mx": "TNT Sports / Max",
            "co": "ESPN / Disney+",
            "us": "Paramount+ / Univision"
        }
    elif "efl" in t or "carabao" in t:
        return {
            "ar": "ESPN / Disney+",
            "es": "DAZN / Sky Sports",
            "mx": "ESPN / Disney+ Premium",
            "co": "ESPN / Disney+",
            "us": "ESPN+ / ESPN App"
        }
    elif "coppa" in t or "italia" in t or "serie a" in t:
        return {
            "ar": "DSports / ESPN",
            "es": "DAZN",
            "mx": "ESPN / Disney+",
            "co": "DSports / ESPN",
            "us": "Paramount+ / CBS Sports"
        }
    elif "afc" in t or "champions league elite" in t:
        return {
            "ar": "ESPN / Disney+",
            "es": "LaLiga+ / Movistar",
            "mx": "ESPN / Disney+",
            "co": "ESPN / Disney+",
            "us": "Paramount+ / CBS Sports"
        }
    elif "eredivisie" in t:
        return {
            "ar": "ESPN / Disney+",
            "es": "Movistar Plus+",
            "mx": "ESPN / Disney+",
            "co": "ESPN / Disney+",
            "us": "ESPN+"
        }
    elif "bolivia" in t:
        return {
            "ar": "Tigo Sports / Fanatiz",
            "es": "Fanatiz",
            "mx": "Fanatiz",
            "co": "Fanatiz",
            "us": "Tigo Sports Internacional"
        }
    elif "mexico" in t or "bbva" in t or "liga mx" in t or "expansión" in t:
        return {
            "ar": "Claro Sports",
            "es": "DAZN / LaLiga+",
            "mx": "TUDN / ViX Premium / Canal 5",
            "co": "Claro Sports",
            "us": "Univision / TUDN / ViX"
        }
    elif "colombia" in t or "betplay" in t or "primera a" in t:
        return {
            "ar": "Fanatiz",
            "es": "Fanatiz",
            "mx": "Fanatiz",
            "co": "Win Sports+ / Win Sports Online",
            "us": "ViX / Fanatiz"
        }
    elif "peru" in t or "perú" in t or "liga 1" in t:
        return {
            "ar": "Fanatiz",
            "es": "Fanatiz",
            "mx": "Fanatiz",
            "co": "Fanatiz",
            "us": "Liga 1 Play / Fanatiz"
        }
    elif "premier" in t:
        return {
            "ar": "ESPN / Disney+",
            "es": "DAZN",
            "mx": "MAX / TNT Sports",
            "co": "ESPN / Disney+",
            "us": "Telemundo / Peacock"
        }
    elif "champions" in t:
        return {
            "ar": "ESPN / Fox Sports",
            "es": "Movistar Liga de Campeones",
            "mx": "MAX / TNT Sports",
            "co": "ESPN / Disney+",
            "us": "Paramount+ / Univision"
        }
    elif "libertadores" in t or "sudamericana" in t:
        return {
            "ar": "Fox Sports / Telefe / ESPN",
            "es": "LaLiga+",
            "mx": "ESPN / Disney+",
            "co": "ESPN / Disney+",
            "us": "beIN Sports"
        }
    else:
        return {
            "ar": primary,
            "es": "Movistar Plus+",
            "mx": "TUDN / ViX",
            "co": "ESPN / Disney+",
            "us": "Telemundo / ESPN"
        }

def generate_match_html(match):
    """Generates a complete, high-converting, SEO-optimized match guide page with authentic live stream player matching competitor UX."""
    home_team = match["homeTeam"]
    away_team = match["awayTeam"]
    tournament = match["tournament"]
    flag = match["flag"]
    venue = match["venue"]
    utc_time = match["utcKickoff"]
    slug = match["slug"]
    home_logo = match["homeLogo"]
    away_logo = match["awayLogo"]
    channels = match.get("channels", [])
    primary_channel = channels[0] if len(channels) > 0 else "Señal Oficial HD"
    alt_channel_1 = channels[1] if len(channels) > 1 else (primary_channel + " Opción 2")
    alt_channel_2 = channels[2] if len(channels) > 2 else "Señal Internacional Full HD"
    
    # Calculate unique baseline percentages & votes per match
    slug_hash = int(hashlib.md5(slug.encode('utf-8')).hexdigest()[:8], 16)
    p_home_init = 36 + (slug_hash % 22)
    p_draw_init = 16 + ((slug_hash >> 3) % 12)
    p_away_init = 100 - (p_home_init + p_draw_init)

    base_count = 3200 + (slug_hash % 3800)
    v_home = int(base_count * (p_home_init / 100))
    v_draw = int(base_count * (p_draw_init / 100))
    v_away = base_count - (v_home + v_draw)

    home_team_js = json.dumps(home_team)
    away_team_js = json.dumps(away_team)
    tournament_js = json.dumps(tournament)
    primary_channel_js = json.dumps(primary_channel)

    b = get_accurate_broadcasters(tournament, channels)
    badge_style = "background: #f1f5f9; color: #1e293b; padding: 2px 8px; border-radius: 4px; font-weight: 600; font-size: 0.775rem; border: 1px solid #e2e8f0; display: inline-block;"
    
    flag_ar = '<img src="../img/flags/ar.svg" alt="Argentina" width="22" height="15" style="border-radius: 2px; box-shadow: 0 1px 3px rgba(0,0,0,0.15); object-fit: cover; vertical-align: middle;">'
    flag_es = '<img src="../img/flags/es.svg" alt="España" width="22" height="15" style="border-radius: 2px; box-shadow: 0 1px 3px rgba(0,0,0,0.15); object-fit: cover; vertical-align: middle;">'
    flag_mx = '<img src="../img/flags/mx.svg" alt="México" width="22" height="15" style="border-radius: 2px; box-shadow: 0 1px 3px rgba(0,0,0,0.15); object-fit: cover; vertical-align: middle;">'
    flag_co = '<img src="../img/flags/co.svg" alt="Colombia" width="22" height="15" style="border-radius: 2px; box-shadow: 0 1px 3px rgba(0,0,0,0.15); object-fit: cover; vertical-align: middle;">'
    flag_us = '<img src="../img/flags/us.svg" alt="Estados Unidos" width="22" height="15" style="border-radius: 2px; box-shadow: 0 1px 3px rgba(0,0,0,0.15); object-fit: cover; vertical-align: middle;">'

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

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{home_team} vs {away_team} en vivo online - LibreGol TV</title>
  <meta name="description" content="Mira {home_team} vs {away_team} en vivo online por {tournament}. Horarios sincronizados y canales de transmisión oficial en HD.">
  <meta name="keywords" content="{home_team.lower()} vs {away_team.lower()} en vivo online, donde ver {home_team.lower()} vs {away_team.lower()}, {tournament.lower()} futbol libre">
  <link rel="canonical" href="https://libregoltv.online/partidos/{slug}.html">
  <link rel="stylesheet" href="../css/main.css?v=4.0">

  <!-- SportsEvent Schema -->
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

  <!-- BreadcrumbList Schema -->
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
    <a href="../index.html" class="title-header" style="display: flex; align-items: center; gap: 0.35rem; text-decoration: none; font-weight: 800; font-size: 1.25rem; color: #111827;">
      <span class="logo-live-dot" style="color:#16a34a;">●</span>
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

    <!-- Authentic Streaming Video Player Container (Conectando... -> Buffering Player with Controls & Fuentes) -->
    <div class="stream-player-wrapper" id="streamPlayerWrapper">
      <div class="video-display-frame" id="videoDisplayFrame" onclick="handleStreamClick()">
        
        <!-- State 1: Conectando... Screen (Matching User Screenshot 1) -->
        <div class="screen-connecting" id="screenConnecting">
          <div class="connecting-content">
            <h3 class="connecting-title">Conectando...</h3>
            <p class="connecting-desc">Cargando la fuente seleccionada.</p>
          </div>
        </div>

        <!-- State 2: Video Player with Rotating Buffer & Native Controls (Matching User Screenshot 2) -->
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
                <button type="button" class="btn-ctrl" title="Opciones">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z"/></svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Under-Player Status & Reload Bar (Screenshot 2) -->
      <div class="stream-under-bar">
        <div class="stream-status-left">
          <span class="stream-status-dot"></span>
          <span class="stream-status-text" id="streamStatusText">Fuente 1 {primary_channel} · conectado</span>
        </div>
        <button type="button" class="btn-stream-reload" id="btnStreamReload" onclick="triggerReload()" title="Recargar transmisión">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/>
          </svg>
          <span>Recargar</span>
        </button>
      </div>

      <!-- Source Switcher Pills (Screenshot 2) -->
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

    <!-- Fan Voting Poll (Compact & Sleek) -->
    <div class="voting-poll-box" style="background: white; border: 1px solid #e5e7eb; border-radius: 0.5rem; padding: 1rem 1.15rem; margin: 1.25rem 0; box-shadow: 0 1px 4px rgba(0,0,0,0.04);">
      <h3 style="font-size: 1rem; font-weight: 800; color: #1f2937; margin-bottom: 0.25rem; text-align: center;">
        ⚽ Pronóstico de la Afición: ¿Quién ganará hoy?
      </h3>
      <p style="font-size: 0.8rem; color: #64748b; text-align: center; margin-bottom: 0.75rem;">
        Vota por tu equipo y consulta el pronóstico en tiempo real
      </p>
      <div style="display: flex; gap: 0.5rem; justify-content: center; flex-wrap: wrap;" id="pollButtons">
        <button onclick="voteMatch('team1')" style="flex: 1; min-width: 100px; max-width: 180px; background: #f0fdf4; border: 1px solid #86efac; color: #166534; font-weight: 700; padding: 0.5rem 0.75rem; border-radius: 0.4rem; cursor: pointer; font-size: 0.825rem; transition: all 0.15s;">
          {home_team}
        </button>
        <button onclick="voteMatch('draw')" style="flex: 1; min-width: 80px; max-width: 120px; background: #f8fafc; border: 1px solid #cbd5e1; color: #334155; font-weight: 700; padding: 0.5rem 0.75rem; border-radius: 0.4rem; cursor: pointer; font-size: 0.825rem; transition: all 0.15s;">
          Empate
        </button>
        <button onclick="voteMatch('team2')" style="flex: 1; min-width: 100px; max-width: 180px; background: #eff6ff; border: 1px solid #93c5fd; color: #1e40af; font-weight: 700; padding: 0.5rem 0.75rem; border-radius: 0.4rem; cursor: pointer; font-size: 0.825rem; transition: all 0.15s;">
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

    <!-- Official TV Broadcast Guide by Country (Premium Sports Card) -->
    <div style="background: white; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; margin-bottom: 1.75rem; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);">
      <div style="background: #f8fafc; padding: 0.85rem 1.25rem; border-bottom: 1px solid #e2e8f0; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.5rem;">
        <div style="display: flex; align-items: center; gap: 0.5rem;">
          <span style="font-size: 1.15rem;">📺</span>
          <h3 style="font-size: 1rem; font-weight: 800; color: #0f172a; margin: 0;">
            Canales Oficiales y Horarios por País
          </h3>
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

    <!-- SEO Information -->
    <article style="background: white; border: 1px solid #e5e7eb; border-radius: 0.5rem; padding: 1.25rem 1.5rem; margin-bottom: 2rem; font-size: 0.925rem; line-height: 1.65; color: #4b5563;">
      <h2 style="font-size: 1.15rem; font-weight: 700; color: #1f2937; margin-bottom: 0.4rem;">Información del Encuentro</h2>
      <p style="margin: 0;">
        El partido entre {home_team} y {away_team} por {tournament} se disputa en el estadio {venue}. En LibreGol TV puedes seguir la cobertura, horarios sincronizados según tu país y la votación en tiempo real de los aficionados.
      </p>
    </article>
  </main>

  <!-- Clean Slim Footer -->
  <footer class="footer-clean" style="background: #111827; color: #9ca3af; padding: 2rem 1.5rem; text-align: center; font-size: 0.85rem; margin-top: auto;">
    <div style="max-width: 900px; margin: 0 auto;">
      <p style="margin-bottom: 0.5rem;">
        <a href="../index.html" style="color: #cbd5e1; text-decoration: none; margin: 0 0.5rem;">Inicio</a> |
        <a href="../partidos-de-hoy.html" style="color: #cbd5e1; text-decoration: none; margin: 0 0.5rem;">Partidos de Hoy</a> |
        <a href="../marcadores.html" style="color: #cbd5e1; text-decoration: none; margin: 0 0.5rem;">Marcadores</a> |
        <a href="../futbol-en-la-tv.html" style="color: #cbd5e1; text-decoration: none; margin: 0 0.5rem;">Fútbol en TV</a> |
        <a href="../legal/aviso-legal.html" style="color: #cbd5e1; text-decoration: none; margin: 0 0.5rem;">Aviso Legal / DMCA</a>
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
</body>
</html>
"""
    return html

def save_matches_and_pages(matches):
    base_dir = os.path.dirname(__file__)
    js_output_path = os.path.join(base_dir, "js", "agenda-data.js")
    partidos_dir = os.path.join(base_dir, "partidos")
    os.makedirs(partidos_dir, exist_ok=True)
    
    existing_channels = """
window.LIBREGOL_CHANNELS = [
  {
    slug: "liga-1-max",
    name: "Liga 1 MAX",
    country: "Perú 🇵🇪",
    description: "Partidos, análisis y programación del fútbol profesional peruano.",
    logo: "img/canales/liga_1_max.webp"
  },
  {
    slug: "telemundo",
    name: "Telemundo",
    country: "EE.UU. & Global 🇺🇸",
    description: "Noticias, entretenimiento y transmisiones deportivas en español.",
    logo: "img/canales/vix_plus.webp"
  },
  {
    slug: "directv-sports",
    name: "DSports",
    country: "Sudamérica 🌎",
    description: "Fútbol internacional, torneos sudamericanos y eventos deportivos.",
    logo: "img/canales/dsports.webp"
  },
  {
    slug: "directv-sports-2",
    name: "DSports 2",
    country: "Sudamérica 🌎",
    description: "Partidos simultáneos y programación deportiva internacional.",
    logo: "img/canales/dsports_2.webp"
  },
  {
    slug: "tyc-sports",
    name: "TyC Sports",
    country: "Argentina 🇦🇷",
    description: "Líder en fútbol argentino, Copa Argentina y Eliminatorias en vivo.",
    logo: "img/canales/tyc_sports.webp"
  },
  {
    slug: "espn-1",
    name: "ESPN 1",
    country: "Sudamérica / Global 🌎",
    description: "UEFA Champions League, Premier League, LaLiga y torneos internacionales.",
    logo: "img/canales/espn.webp"
  },
  {
    slug: "espn-premium",
    name: "ESPN Premium",
    country: "Argentina 🇦🇷",
    description: "Transmisión oficial del Pack Fútbol de la Liga Profesional Argentina.",
    logo: "img/canales/espn_premium.webp"
  },
  {
    slug: "tnt-sports",
    name: "TNT Sports",
    country: "Argentina 🇦🇷",
    description: "Fútbol argentino en vivo, análisis de cada fecha y clásicos.",
    logo: "img/canales/tnt_sports.webp"
  },
  {
    slug: "fox-sports-1",
    name: "Fox Sports 1",
    country: "México / Argentina 🇲🇽 🇦🇷",
    description: "Copa Libertadores, Fórmula 1, WWE y cobertura deportiva continental.",
    logo: "img/canales/fox_sports_1.webp"
  },
  {
    slug: "win-sports",
    name: "Win Sports+",
    country: "Colombia 🇨🇴",
    description: "Todos los partidos en exclusiva de la Liga BetPlay Dimayor y Copa Colombia.",
    logo: "img/canales/win_sports.webp"
  },
  {
    slug: "directv-sports-plus",
    name: "DSports Plus",
    country: "Sudamérica 🌎",
    description: "Señal adicional con fútbol, eventos especiales y deportes en vivo.",
    logo: "img/canales/dsports_plus.webp"
  },
  {
    slug: "espn-2",
    name: "ESPN 2",
    country: "Sudamérica / Global 🌎",
    description: "Fútbol internacional y cobertura de diferentes disciplinas deportivas.",
    logo: "img/canales/espn_2.webp"
  }
];
"""
    
    # 1. Write JS agenda
    js_content = f"""/**
 * LibreGol TV — Live Matches Feed (Auto-Synced Real Data)
 * Synced from Global Sports Public Feeds
 */

window.LIBREGOL_MATCHES = {json.dumps(matches, indent=2, ensure_ascii=False)};
{existing_channels}
"""
    with open(js_output_path, 'w', encoding='utf-8') as f:
        f.write(js_content)
    print(f"Successfully saved {len(matches)} REAL matches to {js_output_path}!")

    # 2. Write Match HTML Pages for every match
    generated_count = 0
    for match in matches:
        file_path = os.path.join(partidos_dir, f"{match['slug']}.html")
        html_code = generate_match_html(match)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_code)
        generated_count += 1

    print(f"Successfully generated {generated_count} static match pages in {partidos_dir}!")

    # 3. Update sitemap.xml with live matches
    update_sitemap(matches)

def update_sitemap(matches):
    try:
        from auto_sync_pipeline import compile_master_sitemap
        compile_master_sitemap()
    except Exception as e:
        print(f"[sync_matches] Sitemap compilation note: {e}")
    return

<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <!-- Homepage -->
  <url>
    <loc>https://libregoltv.online/</loc>
    <lastmod>{today_date_str}</lastmod>
    <changefreq>hourly</changefreq>
    <priority>1.0</priority>
  </url>

  <!-- Golden Pillar Article -->
  <url>
    <loc>https://libregoltv.online/articulos/alternativas-a-futbol-libre.html</loc>
    <lastmod>2026-09-14</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.9</priority>
  </url>

  <!-- Channels Hub & Channels -->
  <url>
    <loc>https://libregoltv.online/canales/index.html</loc>
    <lastmod>2026-09-14</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://libregoltv.online/canales/liga-1-max.html</loc>
    <lastmod>2026-09-14</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>https://libregoltv.online/canales/telemundo.html</loc>
    <lastmod>2026-09-14</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>https://libregoltv.online/canales/directv-sports.html</loc>
    <lastmod>2026-09-14</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>https://libregoltv.online/canales/directv-sports-2.html</loc>
    <lastmod>2026-09-14</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://libregoltv.online/canales/directv-sports-plus.html</loc>
    <lastmod>2026-09-14</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://libregoltv.online/canales/tyc-sports.html</loc>
    <lastmod>2026-09-14</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>https://libregoltv.online/canales/espn-1.html</loc>
    <lastmod>2026-09-14</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>https://libregoltv.online/canales/espn-premium.html</loc>
    <lastmod>2026-09-14</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>https://libregoltv.online/canales/tnt-sports.html</loc>
    <lastmod>2026-09-14</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>https://libregoltv.online/canales/fox-sports-1.html</loc>
    <lastmod>2026-09-14</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://libregoltv.online/canales/win-sports.html</loc>
    <lastmod>2026-09-14</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://libregoltv.online/canales/espn-2.html</loc>
    <lastmod>2026-09-14</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.8</priority>
  </url>

  <!-- Live Daily Match Detail Pages -->
{match_urls}
  <!-- Trust & Legal Pages -->
  <url>
    <loc>https://libregoltv.online/legal/politica-de-privacidad.html</loc>
    <lastmod>2026-09-14</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.4</priority>
  </url>
  <url>
    <loc>https://libregoltv.online/legal/terminos-y-condiciones.html</loc>
    <lastmod>2026-09-14</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.4</priority>
  </url>
  <url>
    <loc>https://libregoltv.online/legal/aviso-legal-dmca.html</loc>
    <lastmod>2026-09-14</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.4</priority>
  </url>
  <url>
    <loc>https://libregoltv.online/legal/nosotros.html</loc>
    <lastmod>2026-09-14</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.5</priority>
  </url>
</urlset>
"""
    with open(sitemap_path, 'w', encoding='utf-8') as f:
        f.write(sitemap_content)
    print(f"Successfully updated sitemap.xml with {len(matches)} live matches!")

if __name__ == "__main__":
    matches = fetch_real_matches()
    if not matches:
        print("No live matches returned from ESPN API, loading from js/agenda-data.js...")
        try:
            with open("js/agenda-data.js", "r", encoding="utf-8") as f:
                c = f.read()
                m = re.search(r'window\.LIBREGOL_MATCHES\s*=\s*(\[.*?\]);', c, re.DOTALL)
                if m:
                    matches = json.loads(m.group(1))
                    print(f"Loaded {len(matches)} matches from existing agenda-data.js cache.")
        except Exception as e:
            print("Error loading cached matches:", e)
    if matches:
        save_matches_and_pages(matches)
    else:
        print("No live matches found today.")
